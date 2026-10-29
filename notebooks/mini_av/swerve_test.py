"""Tests the new swerve (AVOID3) without a cup: turn 90 degrees left, curve right around where the cup would be,
turn left back onto the lane.

    python3 swerve_test.py

The robot stands aligned on a straight, with about 1 m of lane ahead. Saves every frame with time, phase and the
measurements. Run inside the container.
"""

import csv
import os
import time

import cv2
from jetbot import Camera, Robot

import config
import lane_mask
from decision import lane_found
from perception import Perception
from recorder import DATASET_ROOT
from safety import BatteryGuard, MotorWatchdog, wait_for_new_frame
from turn_test import WARMUP_FRAMES, reached_horizontal, turn_speed

HOLD_SECONDS = 2.0  # standing still at the end: the final heading can be seen in the frames


def wheels(name, elapsed):
    """(left, right) wheel speeds of a phase: turns to the left in place, the curve to the right"""
    if name == 'arc':
        return config.ARC_WHEELS
    if name == 'hold':
        return 0.0, 0.0
    speed = turn_speed(elapsed)
    return -speed, speed


def phase_done(name, elapsed, angle, found):
    """True when the phase has reached its camera mark; raises RuntimeError when it took too long"""
    if name == 'hold':
        return elapsed >= HOLD_SECONDS
    if elapsed >= (config.ARC_MAX if name == 'arc' else config.TURN_MAX):
        raise RuntimeError('%s took too long' % name)
    if name == 'out':
        return reached_horizontal(angle, -1, config.TURN_EARLY)
    if name == 'arc':
        return elapsed >= config.ARC_MIN and reached_horizontal(angle, 1, config.ARC_EARLY)
    return found  # 'in'


def main():
    battery = BatteryGuard()
    if not battery.start_ok():
        raise SystemExit('battery %.2f V is too low: charge first' % battery.volts)
    perception = Perception(use_curve=False)
    robot = Robot()
    camera = Camera.instance()
    watchdog = MotorWatchdog(robot)
    out = os.path.join(DATASET_ROOT, time.strftime('%Y-%m-%d_%H-%M-%S') + '_swerve_test')
    os.makedirs(out)
    shots = []  # (time, phase, left, right, tape angle, lane found, frame), written after the motors are off
    result = 'done'
    try:
        frame = wait_for_new_frame(camera, camera.value, timeout=2.0)
        for _ in range(WARMUP_FRAMES):
            frame = wait_for_new_frame(camera, frame)
            perception.observe(frame)
        watchdog.start()
        start = time.time()
        for name in ('out', 'arc', 'in', 'hold'):
            since = time.time()
            done = False
            while not done:
                elapsed = time.time() - since
                battery.check()
                frame = wait_for_new_frame(camera, frame)
                angle = lane_mask.tape_angle(frame)
                found = lane_found(perception.observe(frame))
                done = phase_done(name, elapsed, angle, found)
                left, right = (0.0, 0.0) if done else wheels(name, elapsed)
                with watchdog.lock:
                    robot.set_motors(left, right)
                watchdog.feed()
                shots.append((time.time() - start, name, left, right, angle, found, frame.copy()))
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
        rows.writerow(['frame', 'time', 'phase', 'left', 'right', 'tape_angle', 'lane_found'])
        for i, (t, name, left, right, angle, found, image) in enumerate(shots):
            cv2.imwrite(os.path.join(out, 'frame_%05d.jpg' % i), image)
            rows.writerow(['frame_%05d.jpg' % i, '%.3f' % t, name, left, right,
                           '' if angle is None else '%.1f' % angle, int(found)])
    print('%s: %d frames in %s, battery %.2f V' % (result, len(shots), out, battery.volts))


if __name__ == '__main__':
    main()
