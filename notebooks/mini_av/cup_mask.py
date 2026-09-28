"""Classical detection of the obstacle cups with a color mask: white paper cups (about 8 cm high)
marked with a red tape band all around.

Only a helper for data collection and automatic labels, like lane_mask.py. The driving program
will use the learned obstacle model, not this.
"""

import cv2
import numpy as np

# Red wraps around the hue scale (OpenCV hue 0-180). Measured on the band 2026-09-27: median hue 178, saturation
# about 130-140, brightness about 150. Hue 5-12 is left out: wooden chair legs, a rope basket and a flag at the
# wall (hue 9-10) gave 56 false cups in 2755 lap frames without cups.
RED_LOW = ((0, 100, 60), (4, 255, 255))
RED_HIGH = ((165, 100, 60), (180, 255, 255))
ROI_TOP = 0.25     # ignore everything above this fraction of the image height (a red flag on the wall)
MIN_PIXELS = 30    # smallest red blob that counts as a cup (the band at 50 cm has about 70 pixels)

# Lower edge of the band (row in the 224x224 image) at a measured distance from the robot's front,
# 2026-09-27 (usb/images/obstacle_survey/): 20 cm -> row 109, 30 cm -> row 98, 50 cm -> row 84.


def red_mask(bgr):
    """Returns a 0/255 mask of red pixels below the ROI"""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, *RED_LOW) | cv2.inRange(hsv, *RED_HIGH)
    mask[:int(ROI_TOP * mask.shape[0])] = 0
    return mask


def find_cup(bgr):
    """Returns (center x, lower edge row, pixels) of the largest red blob, or None if there is no cup"""
    count, _, stats, _ = cv2.connectedComponentsWithStats((red_mask(bgr) > 0).astype(np.uint8))
    if count < 2:
        return None
    x, y, w, h, pixels = max(stats[1:], key=lambda s: s[4])
    if pixels < MIN_PIXELS:
        return None
    return x + w / 2.0, y + h - 1, int(pixels)
