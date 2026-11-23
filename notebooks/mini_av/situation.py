"""Where the robot is relative to the lane (SIT1): tape traced over the whole floor part of the image, near and far.

Tape lines become chains of points (rows for lines running away, columns for lines across the view); two lines
leaning toward each other about one lane width apart are the two borders of a lane. Result:

    zone      'in lane', 'on a line', 'lane to the left', 'lane to the right', 'line ahead' (tape across the view),
              'one line only', 'no lane'
    center    lane center at the robot's nose, -1 (left image edge) .. 1 (right), None without a lane
    heading   which way the lane runs ahead, degrees in the image: positive = it bends off to the right of the robot

Far tape looks pale, so the masks are looser than lane_mask's. A script measurement (HYBRID), no decisions here.
"""

import math

import cv2
import numpy as np

import lane_mask

IMAGE_SIZE = 224     # all frames are 224 x 224
FAR_TOP = 0.40       # tape counts from this fraction of the image height down
NEAR_TOP = 0.55      # below: the near mask; above: the far mask
FAR_ROW = NEAR_TOP * IMAGE_SIZE  # the same boundary as an image row
FAR_SAT_MIN = 15     # saturation from which far tape counts
NEAR_SAT_MIN = 35    # saturation from which near tape counts (lane_mask uses 70)
STEP = 4             # pixels between two traced rows (or columns)
LINK = 14            # pixels a line may move sideways per step and still be the same line
MAX_SKIP = 4         # steps a line may be missing (far tape breaks into pieces)
MAX_LEAN = 3.0       # a line traced by columns takes part in the pairing up to this many pixels sideways per row
WALL_ABOVE = (5, 10)  # image rows above a line that are checked for wall
WALL_HUE = 90        # hue from which that looks like the wall (the floor is beige, hue 5-35)
WALL_SAT = 40        # and a saturation below this
SAME = 8             # pixels: a column point this close to a row point is the same tape
MIN_POINTS = 6       # points a chain needs to count as a line
MIN_POINTS_FAR = 4   # the same in the far band only
MAX_WIGGLE = 3.0     # median pixels a line may bend from one point to the next: tape is smooth, floor marks scatter
TAPE_SHARE = (0.025, 0.3)  # width of a tape piece as a share of the lane width at its row: narrower is a speck,
                           # wider is tape across the row
ACROSS_MAX = 0.12    # the same widest share for tape traced by columns (thin seen from above)
NOSE_X = 112         # image column of the robot's nose
NOSE_ROW = 190       # from this row down, a line near the middle runs under the nose
ON_LINE_X = 30       # pixels from NOSE_X within which that line is under the nose
# Lane width in pixels by image row, centered in the lane
WIDTH_ROWS = (74, 80, 89, 94, 98, 103, 107, 112, 123, 134, 145, 156, 168, 179)
WIDTH_PX = (32, 42, 56, 64, 74, 89, 102, 110, 133, 158, 178, 192, 204, 212)
NEAR_STEP = 20       # pixels: pairs whose nearer end lies within the same such step count as equally near
PAIR_WIDTH = (0.5, 1.7)  # share of the lane width two lines may be apart to be one lane


def lane_width(row):
    return np.interp(row, WIDTH_ROWS, WIDTH_PX)


WIDTH_AT_ROW = lane_width(np.arange(IMAGE_SIZE))  # the lane width of each image row, looked up once (SPEED1)


def tape_mask(bgr):
    """Tape on the floor part of the image: a looser threshold far away"""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    near, far = [cv2.inRange(hsv, (lane_mask.HUE_MIN, saturation, lane_mask.VAL_MIN), (lane_mask.HUE_MAX, 255, 255))
                 for saturation in (NEAR_SAT_MIN, FAR_SAT_MIN)]
    height = bgr.shape[0]
    mask = near.copy()
    mask[:int(FAR_ROW)] = far[:int(FAR_ROW)]
    mask[:int(FAR_TOP * height)] = 0
    return mask > 0


def runs(lines):
    """For each row of a 2-D bool array, its runs of True as (start, end), end not included; all rows in one go"""
    padded = np.zeros((lines.shape[0], lines.shape[1] + 2), dtype=bool)
    padded[:, 1:-1] = lines
    # row by row, so a run's start and end come in pairs; plain ints, as numpy numbers are slow one at a time
    line, edge = (part.tolist() for part in np.nonzero(padded[:, 1:] != padded[:, :-1]))
    found = [[] for _ in range(lines.shape[0])]
    for i in range(0, len(edge), 2):
        found[line[i]].append((edge[i], edge[i + 1]))
    return found


def pieces(spans, row=None, widest=TAPE_SHARE[1]):
    """Centers of the runs (start, end) whose length fits tape; row: the image row of a traced row, None for a
    traced column (the row is then the run's middle); widest: largest length as a share of the lane width"""
    found = []
    for start, end in spans:
        middle = (start + end - 1) / 2.0
        at = int(middle) if row is None else row
        width = WIDTH_AT_ROW[at]
        narrowest = 1 if at < int(FAR_ROW) else TAPE_SHARE[0] * width  # far tape is 1-2 pixels thin
        if narrowest <= end - start <= widest * width:
            found.append(middle)
    return found


def chains_of(lines_of_points, far_row):
    """Links points of successive rows (or columns), given as [(position, [values])], into chains; far_row(point)
    tells whether a point lies in the far band"""
    chains = []
    for position, values in lines_of_points:
        taken = set()
        for value in values:
            fits = [i for i, chain in enumerate(chains) if i not in taken and
                    abs(chain[-1][0] - position) // STEP <= MAX_SKIP + 1 and
                    abs(value - chain[-1][1]) <= LINK * (abs(chain[-1][0] - position) // STEP)]
            if fits:
                best = min(fits, key=lambda i: abs(value - chains[i][-1][1]))
                chains[best].append((position, value))
            else:
                chains.append([(position, value)])
                best = len(chains) - 1
            taken.add(best)
    return [chain for chain in chains if len(chain) >= (
        MIN_POINTS_FAR if all(far_row(point) for point in chain) else MIN_POINTS) and smooth(chain)]


def smooth(chain):
    """True if the line bends little from point to point (the median ignores a kink at the image edge)"""
    values = np.array([value for _, value in chain], dtype=float)
    return np.median(np.abs(np.diff(values, 2))) <= MAX_WIGGLE


def below_wall(chain, hsv):
    """True if the image just above a line across the view looks like the wall, not the floor: the dark strip at the
    bottom of the wall has the color of pale far tape"""
    above = []
    for column, row in chain:
        column, row = int(column), int(round(row))
        if row - WALL_ABOVE[1] >= 0:
            above.append(hsv[row - WALL_ABOVE[1]:row - WALL_ABOVE[0], column])
    if not above:
        return False
    above = np.concatenate(above)
    return np.median(above[:, 0]) >= WALL_HUE and np.median(above[:, 1]) < WALL_SAT


def trace(bgr):
    """(lines away from the robot as chains of (row, x), lines across the view as chains of (x, row))"""
    mask = tape_mask(bgr)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    height, width = mask.shape
    rows, columns = list(range(height - 3, int(FAR_TOP * height), -STEP)), list(range(2, width, STEP))
    by_row = [(row, pieces(spans, row)) for row, spans in zip(rows, runs(mask[rows]))]
    by_column = [(column, pieces(spans, None, ACROSS_MAX))
                 for column, spans in zip(columns, runs(mask[:, columns].T))]
    along = chains_of(by_row, lambda point: point[0] < FAR_ROW)
    near = set((int(row) // SAME, int(x) // SAME) for chain in along for row, x in chain)
    across = [chain for chain in chains_of(by_column, lambda point: point[1] < FAR_ROW)  # only tape the rows did not
              if sum((int(row) // SAME, int(column) // SAME) in near for column, row in chain) < len(chain) / 2.0  # find
              and not below_wall(chain, hsv)]
    return along, across


def fit(chain):
    """Straight line value = a * position + b through a chain, with its range"""
    positions, values = zip(*chain)
    a, b = np.polyfit(positions, values, 1)
    return {'a': a, 'b': b, 'top': min(positions), 'bottom': max(positions), 'points': chain}


def x_at(line, row):
    return line['a'] * row + line['b']


def lane_pair(lines):
    """The nearest two lines (left, right) that look like the borders of one lane, or None (a far pair can fit by chance)"""
    best, best_key = None, None
    for i, first in enumerate(lines):
        for second in lines[i + 1:]:
            row = max(first['top'], second['top'])  # the highest row both reach: compare the gap there
            if row > min(first['bottom'], second['bottom']) + 30:
                continue  # they do not overlap in height
            left, right = sorted((first, second), key=lambda line: x_at(line, row))
            if right['a'] - left['a'] <= 0:
                continue  # they do not lean toward each other going up
            ratio = (x_at(right, row) - x_at(left, row)) / lane_width(row)
            key = (-(min(left['bottom'], right['bottom']) // NEAR_STEP), abs(ratio - 1))
            if PAIR_WIDTH[0] <= ratio <= PAIR_WIDTH[1] and (best is None or key < best_key):
                best, best_key = (left, right), key
    return best


def picture(bgr):
    """The picture twice as large with situation() drawn on it: yellow = lines running away (cyan: only far), green =
    tape across the view, red = the lane pair, red dot = lane center at the nose, pink triangle = the nose"""
    seen = situation(bgr)
    scale = 2
    image = cv2.resize(bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    height = bgr.shape[0]
    for line in seen['lines']:
        color = (0, 230, 255) if line['bottom'] >= FAR_ROW else (255, 255, 0)
        for row, x in line['points']:
            cv2.circle(image, (int(x * scale), int(row * scale)), 3, color, -1)
    for line in seen['across']:
        for column, row in line['points']:
            cv2.circle(image, (int(column * scale), int(row * scale)), 3, (0, 255, 0), -1)
    for line in seen['pair'] or ():
        top, bottom = line['top'], height - 1
        cv2.line(image, (int(x_at(line, top) * scale), int(top * scale)),
                 (int(x_at(line, bottom) * scale), int(bottom * scale)), (0, 0, 255), 2)
    if seen['center'] is not None:
        cv2.circle(image, (int((seen['center'] + 1) * bgr.shape[1] / 2.0 * scale), height * scale - 6), 6, (0, 0, 255), -1)
    cv2.drawMarker(image, (NOSE_X * scale, height * scale - 6), (255, 0, 255), cv2.MARKER_TRIANGLE_UP, 16, 3)
    cv2.rectangle(image, (0, 0), (image.shape[1], 26), (255, 255, 255), -1)
    cv2.putText(image, seen['zone'], (6, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    return image


def situation(bgr):
    """Returns a dict: zone, center, heading (see the module text), lines, across and pair (for pictures)"""
    height = bgr.shape[0]
    bottom = height - 1
    along, across = trace(bgr)
    lines = [fit(chain) for chain in along]
    across = [fit(chain) for chain in across]
    turned = [fit([(row, column) for column, row in line['points']]) for line in across]  # as rows, for the pairing
    pair = lane_pair(lines + [line for line in turned if abs(line['a']) <= MAX_LEAN])
    under_nose = any(abs(x - NOSE_X) <= ON_LINE_X for line in lines for row, x in line['points'] if row >= NOSE_ROW)
    ahead = any(line['top'] <= NOSE_X <= line['bottom'] for line in across)  # tape across the middle of the view
    center = heading = None
    if pair:
        left, right = pair
        middle = (x_at(left, bottom) + x_at(right, bottom)) / 2.0
        top = max(left['top'], right['top'])
        middle_top = (x_at(left, top) + x_at(right, top)) / 2.0
        center = middle / (bgr.shape[1] / 2.0) - 1.0
        heading = math.degrees(math.atan2(middle_top - middle, bottom - top))
    if under_nose:
        zone = 'on a line'
    elif pair and x_at(pair[0], bottom) < NOSE_X < x_at(pair[1], bottom):
        zone = 'in lane'
    elif pair:
        zone = 'lane to the left' if x_at(pair[1], bottom) <= NOSE_X else 'lane to the right'
    elif ahead:
        zone = 'line ahead'
    else:
        zone = 'one line only' if lines or across else 'no lane'
    return {'zone': zone, 'center': center, 'heading': heading, 'lines': lines, 'across': across, 'pair': pair}
