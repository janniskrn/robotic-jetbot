"""Tests the camera-ended turns of the new swerve (AVOID3) without driving forward.

    python3 turn_test.py [repeats]

The robot stands aligned on the lane. Each repeat: turn left until the near lane edge looks horizontal (90 degrees,
lane_mask.tape_angle), wait, turn right until the lane check sees the lane again (decision.lane_found), wait.
Saves every frame with time, phase and the measurements, so the overshoot after each stop can be read offline.
Run inside the container.
"""

import csv
import os
import sys
import time

import cv2
from jetbot import Camera, Robot

import config
import lane_mask
from decision import lane_found
from perception import Perception
from recorder import DATASET_ROOT
from safety import BatteryGuard, MotorWatchdog, wait_for_new_frame

HOLD_SECONDS = 2.0  # standing still after each turn: the overshoot settles and can be seen in the frames
WARMUP_FRAMES = 5   # model calls with the motors off (the first call took up to 1.1 s)


def turn_speed(elapsed):
    """Wheel speed of a turn: a short kick to break the robot free, then the slow speed"""
    return config.TURN_KICK[0] if elapsed < config.TURN_KICK[1] else config.TURN_SPEED


def reached_horizontal(angle, direction, early):
    """True if a turn (direction -1 left, +1 right) has brought the near lane edge to within `early` degrees before
    horizontal: turning left its angle rises toward 0, turning right it falls. A window, not a limit: a lane line
    leaning the other way (+39 degrees at one start) must not end a left turn"""
    return angle is not None and 0 <= direction * angle <= early


def main():
    repeats = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    battery = BatteryGuard()
    if not battery.start_ok():
        raise SystemExit('battery %.2f V is too low: charge first' % battery.volts)
    perception = Perception(use_curve=False)
    robot = Robot()
    camera = Camera.instance()
    watchdog = MotorWatchdog(robot)
    out = os.path.join(DATASET_ROOT, time.strftime('%Y-%m-%d_%H-%M-%S') + '_turn_test')
    os.makedirs(out)
    shots = []  # (time, phase, left, tape angle, lane found, frame), written after the motors are off
    result = 'done'
    try:
        frame = wait_for_new_frame(camera, camera.value, timeout=2.0)
        for _ in range(WARMUP_FRAMES):
            frame = wait_for_new_frame(camera, frame)
            perception.observe(frame)
        watchdog.start()
        start = time.time()
        for _ in range(repeats):
            # phase: (name, direction: -1 left / +1 right / 0 still, ends when)
            for name, direction in (('out', -1), ('hold_out', 0), ('back', 1), ('hold_back', 0)):
                since = time.time()
                while True:
                    elapsed = time.time() - since
                    battery.check()
                    frame = wait_for_new_frame(camera, frame)
                    angle = lane_mask.tape_angle(frame)
                    found = lane_found(perception.observe(frame))
                    if direction == 0:
                        done = elapsed >= HOLD_SECONDS
                    elif elapsed >= config.TURN_MAX:
                        raise RuntimeError('%s turn took longer than %.1f s' % (name, config.TURN_MAX))
                    elif name == 'out':
                        done = reached_horizontal(angle, direction, config.TURN_EARLY)
                    else:
                        done = found
                    left = 0.0 if done or direction == 0 else direction * turn_speed(elapsed)
                    with watchdog.lock:
                        robot.set_motors(left, -left)
                    watchdog.feed()
                    shots.append((time.time() - start, name, left, angle, found, frame.copy()))
                    if done:
                        break
    except KeyboardInterrupt:
        result = 'stopped by hand'
    except RuntimeError as error:
        result = str(error)
    finally:
        watchdog.running = False
        with watchdog.lock:
            robot.stop()
        camera.stop()
    with open(os.path.join(out, 'frames.csv'), 'w') as f:
        rows = csv.writer(f)
        rows.writerow(['frame', 'time', 'phase', 'left', 'tape_angle', 'lane_found'])
        for i, (t, name, left, angle, found, image) in enumerate(shots):
            cv2.imwrite(os.path.join(out, 'frame_%05d.jpg' % i), image)
            rows.writerow(['frame_%05d.jpg' % i, '%.3f' % t, name, left, '' if angle is None else '%.1f' % angle,
                           int(found)])
    print('%s: %d frames in %s, battery %.2f V' % (result, len(shots), out, battery.volts))


if __name__ == '__main__':
    main()
