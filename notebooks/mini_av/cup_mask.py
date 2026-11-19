"""Classical detection of the obstacle cups with a color mask: white paper cups (about 8 cm high)
marked with a red tape band all around.

A helper for data collection and labels, like lane_mask.py. Driving uses it to measure how far the cups are
(HYBRID): the obstacle model says a cup is there, the band's lower edge gives the distance.
"""

import cv2
import numpy as np

# Red wraps around the hue scale (OpenCV hue 0-180); hue 5-12 is left out (wood and rope gave false cups)
RED_LOW = ((0, 100, 60), (4, 255, 255))
RED_HIGH = ((165, 100, 60), (180, 255, 255))
ROI_TOP = 0.25     # ignore everything above this fraction of the image height
MIN_PIXELS = 30    # smallest red blob that counts as a cup


def red_mask(bgr):
    """Returns a 0/255 mask of red pixels below the ROI"""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, *RED_LOW) | cv2.inRange(hsv, *RED_HIGH)
    mask[:int(ROI_TOP * mask.shape[0])] = 0
    return mask


def find_cups(bgr):
    """Returns (center x, lower edge row, pixels) of every red blob large enough to be a cup, nearest (lowest) first"""
    _, _, stats, _ = cv2.connectedComponentsWithStats((red_mask(bgr) > 0).astype(np.uint8))
    cups = [(x + w / 2.0, y + h - 1, int(pixels)) for x, y, w, h, pixels in stats[1:] if pixels >= MIN_PIXELS]
    return sorted(cups, key=lambda cup: -cup[1])


def find_cup(bgr):
    """Returns (center x, lower edge row, pixels) of the largest red blob, or None if there is no cup"""
    cups = find_cups(bgr)
    return max(cups, key=lambda cup: cup[2]) if cups else None
