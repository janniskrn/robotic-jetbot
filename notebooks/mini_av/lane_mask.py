"""Classical detection of the blue-tape lane with a color mask.

Only a helper for data collection and automatic pre-labels (D10). The driving
program itself uses the learned models, not this.
"""

import cv2
import numpy as np

# Blue tape in OpenCV HSV (hue 0-180). Measured on the track: tape hue 105-114, floor saturation mostly below 80.
HUE_MIN = 95
HUE_MAX = 125
SAT_MIN = 70
VAL_MIN = 60

ROI_TOP = 0.45        # ignore everything above this fraction of the image height (furniture, blue couch)
LOOKAHEAD_ROW = 0.65  # row, as a fraction of the height, where the lane center is measured
BAND_HALF = 5         # rows above and below the lookahead row that are combined
MIN_GAP = 12          # pixels between two tape pieces that make them separate lines
LANE_WIDTH = 162      # lane width in pixels at the lookahead row, measured on a straight (224x224 image)
MAX_LINE_WIDTH = 50   # wider tape pieces are a line crossing the row sideways (sharp curve), not a lane edge
NEAR_OFFSET = 0.15    # second, closer row used to see which way a single line leans


def blue_mask(bgr):
    """Returns a 0/255 mask of blue tape pixels in the floor region"""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (HUE_MIN, SAT_MIN, VAL_MIN), (HUE_MAX, 255, 255))
    mask[:int(ROI_TOP * mask.shape[0])] = 0
    return mask


def line_centers(mask, row_frac=LOOKAHEAD_ROW):
    """x positions of the tape lines crossing the lookahead row, left to right"""
    row = int(row_frac * mask.shape[0])
    columns = np.nonzero(mask[row - BAND_HALF:row + BAND_HALF + 1].any(axis=0))[0]
    if len(columns) == 0:
        return []
    # split the tape columns into separate lines wherever there is a gap
    pieces = np.split(columns, np.nonzero(np.diff(columns) > MIN_GAP)[0] + 1)
    return [float(piece.mean()) for piece in pieces if piece[-1] - piece[0] <= MAX_LINE_WIDTH]


def is_left_line(mask, x, row_frac=LOOKAHEAD_ROW):
    """True if the line at x leans like a left lane line ('/'), False if like a right one ('\\').

    A left line is further right the further away it is; a right line the opposite.
    Returns None if the line is not visible in the closer row.
    """
    near = line_centers(mask, min(row_frac + NEAR_OFFSET, 0.97))
    if not near:
        return None
    near_x = min(near, key=lambda n: abs(n - x))
    return x > near_x


class LaneTracker(object):
    """Turns the visible lines into a lane center, remembering the lane width for when one line is missing"""

    def __init__(self, width, row_frac=LOOKAHEAD_ROW, lane_width=LANE_WIDTH):
        self.image_width = width
        self.row_frac = row_frac
        self.center = width / 2.0
        self.lane_width = lane_width

    def update(self, mask):
        """Returns the lane center x in pixels (clamped to the image), or None if no line is visible"""
        lines = line_centers(mask, self.row_frac)
        if len(lines) >= 2:
            left, right = lines[0], lines[-1]
            self.lane_width = right - left
            self.center = (left + right) / 2.0
        elif len(lines) == 1:
            line = lines[0]
            left = is_left_line(mask, line, self.row_frac)
            if left is None:
                left = line < self.center  # no lean visible: keep the side from the last frame
            self.center = line + self.lane_width / 2.0 if left else line - self.lane_width / 2.0
        else:
            return None
        self.center = min(max(self.center, 0.0), float(self.image_width))
        return self.center
