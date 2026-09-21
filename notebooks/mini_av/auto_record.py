"""Drives the lane slowly with the color-mask detector and records a dataset session.

Alternative to 01_record_dataset.ipynb for the clean laps: no gamepad needed.
Only a data tool; the real driving program uses the learned models.

Run inside the Jupyter container, from this folder:
    python3 auto_record.py --name lap_ccw --seconds 60
"""

import argparse
import csv
import os
import time

import cv2
from jetbot import Camera, Robot

from lane_mask import LaneTracker, blue_mask, line_centers
from recorder import Recorder

BASE_SPEED = 0.32     # wheel speed on the lane; below about 0.27 the motors do not move the robot
STEERING_GAIN = 0.15  # P: wheel speed difference per unit of lane-center error (-1..1)
STEERING_DAMPING = 0.03  # D: wheel speed difference per unit of error change per second; stops the weave from growing
LOST_TIMEOUT = 0.5    # seconds without any tape line before the robot stops
RECORD_HZ = 4.0       # frames saved per second, same as the gamepad recorder
LOOP_PERIOD = 0.03    # seconds between control updates (camera runs at 30 Hz)


def steering_error(center, image_width):
    """Lane center offset from the image center, -1 (left edge) .. 1 (right edge)"""
    half = image_width / 2.0
    return (center - half) / half


def drive(robot, camera, recorder, seconds, labels, trace):
    """Follows the lane until the time is up or the lane is lost; returns the stop reason.

    For every saved frame, writes what the color mask saw: these are the automatic pre-labels (D10).
    """
    tracker = LaneTracker(camera.width)
    start = last_seen = last_time = time.time()
    last_error = None
    while time.time() - start < seconds:
        frame = camera.value
        mask = blue_mask(frame)
        lines = line_centers(mask)
        center = tracker.update(mask)
        now = time.time()
        if center is None:
            robot.stop()
            if now - last_seen > LOST_TIMEOUT:
                return 'lane lost'
        else:
            last_seen = now
            error = steering_error(center, camera.width)
            change = 0.0 if last_error is None else (error - last_error) / max(now - last_time, 1e-3)
            turn = STEERING_GAIN * error + STEERING_DAMPING * change
            robot.set_motors(BASE_SPEED + turn, BASE_SPEED - turn)
            trace.writerow([round(now - start, 3), round(center, 1), round(turn, 3)])
            last_error = error
        last_time = now
        if recorder.offer(bytes(cv2.imencode('.jpg', frame)[1])):
            labels.writerow(['frame_%05d.jpg' % (recorder.count - 1), len(lines),
                             '' if center is None else round(center, 1)])
        time.sleep(LOOP_PERIOD)
    return 'time up'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', default='auto')
    parser.add_argument('--seconds', type=float, default=30.0)
    parser.add_argument('--notes', default='')
    args = parser.parse_args()

    robot = Robot()
    camera = Camera.instance()
    recorder = Recorder(period=1.0 / RECORD_HZ)
    time.sleep(2.0)  # let the camera settle its exposure
    recorder.start(args.name, {
        'mode': 'auto_color_mask',
        'tape_color': 'blue',
        'section': 'mixed',
        'obstacle': 'none',
        'notes': args.notes,
        'frame_width': camera.width,
        'frame_height': camera.height,
        'base_speed': BASE_SPEED,
        'steering_gain': STEERING_GAIN,
        'steering_damping': STEERING_DAMPING,
    })
    try:
        with open(os.path.join(recorder.session_dir, 'auto_labels.csv'), 'w') as f, \
                open(os.path.join(recorder.session_dir, 'trace.csv'), 'w') as g:
            labels = csv.writer(f)
            labels.writerow(['frame', 'lines_seen', 'lane_center_x'])
            trace = csv.writer(g)  # every control step, for tuning and the week 1 graphs
            trace.writerow(['time', 'lane_center_x', 'turn'])
            reason = drive(robot, camera, recorder, args.seconds, labels, trace)
    finally:
        robot.stop()
        session_dir = recorder.stop()
        camera.stop()
    print('%s: saved %d frames in %s' % (reason, recorder.count, session_dir))


if __name__ == '__main__':
    main()
