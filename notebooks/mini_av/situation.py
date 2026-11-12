"""Where the robot is relative to the lane (SIT1): the "broader picture" the professor asked for.

Instead of one image row, the tape is traced over the whole floor part of the image, near and far. Each tape line
becomes a chain of points: lines that run away from the robot are traced row by row, lines that run across the image
column by column. Two lines that lean toward each other and are about one lane width apart are the two borders of a
lane. From that:

    zone      'in lane', 'on a line', 'lane to the left', 'lane to the right', 'line ahead' (tape across the view),
              'one line only', 'no lane'
    center    lane center at the robot's nose, -1 (left image edge) .. 1 (right), None without a lane
    heading   which way the lane runs ahead, degrees in the image: positive = it bends off to the right of the robot

Far tape looks pale (saturation about 16 against 70 near), so the masks here are looser than lane_mask's; a piece
only counts if it is about as wide as tape at its distance, and a chain only if it forms a smooth line.
A script measurement (HYBRID), no decisions here.
"""

import math

import cv2
import numpy as np

import lane_mask

FAR_TOP = 0.40       # tape counts from this fraction of the image height down. Higher (0.33) did not find the faint far
                     # lines at the wall the team saw, and let the strip at the bottom of the wall in (check 2026-11-11)
NEAR_TOP = 0.55      # below: the near mask; above: the far mask
FAR_ROW = int(NEAR_TOP * 224)  # the same as an image row
FAR_SAT_MIN = 15     # saturation from which far tape counts (the background line read 16 in run line3_1)
NEAR_SAT_MIN = 35    # and near tape: half the pixels of pale lines lay at 20-70, below lane_mask's 70; the bluish-gray floor
                     # near a wall reached 34 (check 2026-11-11)
STEP = 4             # pixels between two traced rows (or columns)
LINK = 14            # pixels a line may move sideways per step and still be the same line
MAX_SKIP = 4         # steps a line may be missing (far tape breaks into pieces)
MAX_LEAN = 3.0       # a line traced by columns takes part in the pairing up to this many pixels sideways per row
WALL_ABOVE = (5, 10)  # image rows above a line where the floor (or the wall) is looked at
WALL_HUE = 90        # hue from which that looks like the wall: the floor is beige (hue 5-35)
WALL_SAT = 40        # with a saturation below this (tape itself is far more saturated)
SAME = 8             # pixels: a column point this close to a row point is the same tape
MIN_POINTS = 6       # points a chain needs to count as a line
MIN_POINTS_FAR = 4   # in the far band only: far tape breaks into pieces
MAX_WIGGLE = 3.0     # pixels a line may bend from one point to the next, typically (median): tape bends smoothly, floor
                     # marks scatter. Local, so that S-bends and U-turns of the tape pass (frames 48, 90 of the check)
TAPE_SHARE = (0.025, 0.3)  # width of a tape piece as a share of the lane width at its row: narrower is a speck, wider
                           # is tape running across the row (traced by columns instead). The fisheye lens squeezes tape
                           # near the image edges: at 0.04 those lines were lost (check 2026-11-11)
ACROSS_MAX = 0.12    # tape across the view is thin seen from above; the dark strip at the bottom of the wall (same color as
                     # pale far tape) is 7-15 pixels tall (check 2026-11-11)
NOSE_X = 112         # image column of the robot's nose (224 x 224 image)
NOSE_ROW = 190       # from this row down, a line near the middle runs under the nose
ON_LINE_X = 30       # pixels from NOSE_X within which that line is under the nose
# Lane width in pixels by image row, centered in the lane (354 frames of runs line1_1, line2_1, avoid4_7); rows 74 and 80
# continue the trend of rows 89-107 (no reliable measurement that close to the horizon)
WIDTH_ROWS = (74, 80, 89, 94, 98, 103, 107, 112, 123, 134, 145, 156, 168, 179)
WIDTH_PX = (32, 42, 56, 64, 74, 89, 102, 110, 133, 158, 178, 192, 204, 212)
NEAR_STEP = 20       # pixels: pairs whose nearer end lies within the same such step count as equally near
PAIR_WIDTH = (0.5, 1.7)  # share of that width two lines may be apart to be one lane (at an angle the gap grows)


def lane_width(row):
    return np.interp(row, WIDTH_ROWS, WIDTH_PX)


def tape_mask(bgr):
    """Tape on the floor part of the image: a looser threshold far away, where the thin tape looks pale"""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    near, far = [cv2.inRange(hsv, (lane_mask.HUE_MIN, saturation, lane_mask.VAL_MIN), (lane_mask.HUE_MAX, 255, 255))
                 for saturation in (NEAR_SAT_MIN, FAR_SAT_MIN)]
    height = bgr.shape[0]
    mask = near.copy()
    mask[:int(NEAR_TOP * height)] = far[:int(NEAR_TOP * height)]
    mask[:int(FAR_TOP * height)] = 0
    return mask > 0


def pieces(values, rows, widest=TAPE_SHARE[1]):
    """Centers of the runs of True in values whose length fits tape; rows: the image row of each value (one row
    for a row, every row for a column); widest: largest length as a share of the lane width"""
    padded = np.concatenate(([False], values, [False]))
    edges = np.flatnonzero(padded[1:] != padded[:-1])
    found = []
    for start, end in zip(edges[::2], edges[1::2]):
        middle = (start + end - 1) / 2.0
        row = rows[int(middle)]
        width = lane_width(row)
        narrowest = 1 if row < FAR_ROW else TAPE_SHARE[0] * width  # far tape is 1-2 pixels thin
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
            best = None
            for i, chain in enumerate(chains):
                last_position, last_value = chain[-1]
                steps = abs(last_position - position) // STEP
                if i in taken or steps > MAX_SKIP + 1 or abs(value - last_value) > LINK * steps:
                    continue
                if best is None or abs(value - last_value) < abs(value - chains[best][-1][1]):
                    best = i
            if best is None:
                chains.append([(position, value)])
                taken.add(len(chains) - 1)
            else:
                chains[best].append((position, value))
                taken.add(best)
    return [chain for chain in chains if len(chain) >= (
        MIN_POINTS_FAR if all(far_row(point) for point in chain) else MIN_POINTS) and smooth(chain)]


def smooth(chain):
    """True if the line bends little from point to point, as tape does and floor specks do not. A piece cut by the
    image edge gives one kink; the median ignores it"""
    values = np.array([value for _, value in chain], dtype=float)
    return np.median(np.abs(np.diff(values, 2))) <= MAX_WIGGLE


def below_wall(chain, hsv):
    """True if the image just above a line across the view looks like the wall, not the floor: the dark strip at the
    bottom of the wall has the color of pale far tape, but above real tape lies beige floor (hue 5-35), above the
    strip the gray-blue wall (hue 100-150, saturation under 30; check 2026-11-11). Lines running away from the robot
    are not checked: above them lies the line itself"""
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
    all_rows = np.arange(height)
    by_row = [(row, pieces(mask[row], np.full(width, row)))
              for row in range(height - 3, int(FAR_TOP * height), -STEP)]
    by_column = [(column, pieces(mask[:, column], all_rows, ACROSS_MAX)) for column in range(2, width, STEP)]
    far_from = NEAR_TOP * height
    along = chains_of(by_row, lambda point: point[0] < far_from)
    near = set((int(row) // SAME, int(x) // SAME) for chain in along for row, x in chain)
    across = [chain for chain in chains_of(by_column, lambda point: point[1] < far_from)  # only tape the rows did not
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
    """The two lines (left, right) that best look like the borders of one lane, or None. The nearest such pair: a
    far pair can fit the lane width by chance (another part of the track)"""
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
