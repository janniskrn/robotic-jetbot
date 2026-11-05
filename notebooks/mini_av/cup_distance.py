"""Teaches the cup distances: one camera frame with the robot standing (motors off), the band rows printed.

    python3 cup_distance.py 30            # cup 30 cm in front of the robot's front edge, on the straight
    python3 cup_distance.py 30 curve      # a label for where it stands (curve, left, right, ...)

Saves the frame to usb/images/obstacle_survey/ (cup_<cm>cm_<label>_<time>.jpg, like the survey of 2026-09-27), so
the table in config.py can be checked against it later. Run inside the container.
"""

import os
import sys
import time

import cv2
from jetbot import Camera

import cup_mask
from safety import wait_for_new_frame

SURVEY_DIR = '/workspace/usb/images/obstacle_survey'


def main():
    cm = int(sys.argv[1])
    label = sys.argv[2] if len(sys.argv) > 2 else 'straight'
    camera = Camera.instance()
    try:
        frame = wait_for_new_frame(camera, camera.value, timeout=2.0)
        for _ in range(5):  # the exposure settles after the start
            frame = wait_for_new_frame(camera, frame)
    finally:
        camera.stop()
    path = os.path.join(SURVEY_DIR, 'cup_%dcm_%s_%s.jpg' % (cm, label, time.strftime('%H-%M-%S')))
    cv2.imwrite(path, frame)
    cups = cup_mask.find_cups(frame)
    print('%d cm %s: %s -> %s' % (cm, label, ', '.join('band row %d at x %+.2f (%d px)' % (
        row, x / (frame.shape[1] / 2.0) - 1.0, px) for x, row, px in cups) or 'no band', path))


if __name__ == '__main__':
    main()
