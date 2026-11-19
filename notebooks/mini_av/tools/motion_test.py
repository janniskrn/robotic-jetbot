"""Motion tests of the swerve's moves on the robot (AVOID3, ARC1), without a cup.

    python3 tools/motion_test.py turn [repeats]  # on the lane: turn left until the edge looks horizontal, back right
                                                 # until the lane is found
    python3 tools/motion_test.py swerve          # on a straight, 1 m of lane ahead: turn out, curve, turn in
    python3 tools/motion_test.py arc             # the swerve's curve for ARC_TURN_MIN: measure the angle by hand,
                                                 # it should be about 90 degrees

Saves every frame with time, phase and measurements to usb/images/datasets/<time>_<test>_test.
Run inside the container from notebooks/mini_av.
"""

import csv
import os
import sys
import time

import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # the driving modules
from jetbot import Camera, Robot

import config
import lane_mask
from control import turn_speed
from decision import lane_found, reached_horizontal
from perception import Perception
from recorder import DATASET_ROOT
from safety import BatteryGuard, MotorWatchdog, wait_for_new_frame

HOLD_SECONDS = 2.0  # standing still after a move: the overshoot settles and can be seen in the frames


def spin(direction):
    """Wheels of a turn in place, -1 left, +1 right"""
    return lambda elapsed: (direction * turn_speed(elapsed), -direction * turn_speed(elapsed))


def still(elapsed):
    return 0.0, 0.0


def curve(elapsed):
    return config.ARC_WHEELS  # curves right


def held(elapsed, angle, found):
    return elapsed >= HOLD_SECONDS


def horizontal(direction, early):
    """Done when the lane edge ahead looks horizontal, turning `direction`"""
    return lambda elapsed, angle, found: reached_horizontal(angle, direction, early)


def lane(elapsed, angle, found):
    return found


def curved(elapsed, angle, found):
    """The swerve's curve: about 90 degrees turned, then the edge ahead looks horizontal"""
    return elapsed >= config.ARC_TURN_MIN and reached_horizontal(angle, 1, config.ARC_EARLY)


# test: phases of (name, wheels(elapsed), done(elapsed, tape angle, lane found), time limit or None)
TESTS = {
    'turn': [('out', spin(-1), horizontal(-1, config.TURN_EARLY), config.TURN_OUT_MAX), ('hold_out', still, held, None),
             ('back', spin(1), lane, config.TURN_IN_MAX), ('hold_back', still, held, None)],
    'swerve': [('out', spin(-1), horizontal(-1, config.TURN_EARLY), config.TURN_OUT_MAX),
               ('arc', curve, curved, config.ARC_MAX), ('in', spin(-1), lane, config.TURN_IN_MAX),
               ('hold', still, held, None)],
    'arc': [('arc', curve, lambda elapsed, angle, found: elapsed >= config.ARC_TURN_MIN, None),
            ('hold', still, held, None)],
}


def save(out, shots):
    with open(os.path.join(out, 'frames.csv'), 'w') as f:
        rows = csv.writer(f)
        rows.writerow(['frame', 'time', 'phase', 'left', 'right', 'tape_angle', 'lane_found'])
        for i, (t, name, left, right, angle, found, image) in enumerate(shots):
            cv2.imwrite(os.path.join(out, 'frame_%05d.jpg' % i), image)
            rows.writerow(['frame_%05d.jpg' % i, '%.3f' % t, name, left, right,
                           '' if angle is None else '%.1f' % angle, int(found)])


def main():
    test = sys.argv[1] if len(sys.argv) > 1 else ''
    if test not in TESTS:
        raise SystemExit('test must be one of: %s' % ', '.join(TESTS))
    repeats = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    battery = BatteryGuard()
    if not battery.start_ok():
        raise SystemExit('battery %.2f V is too low: charge first' % battery.volts)
    perception = Perception(use_curve=False)
    robot = Robot()
    camera = Camera.instance()
    watchdog = MotorWatchdog(robot)
    out = os.path.join(DATASET_ROOT, time.strftime('%Y-%m-%d_%H-%M-%S') + '_%s_test' % test)
    os.makedirs(out)
    shots = []  # (time, phase, left, right, tape angle, lane found, frame), written after the motors are off
    result = 'done'
    try:
        frame = perception.warm_up(camera)
        watchdog.start()
        start = time.time()
        for _ in range(repeats):
            for name, wheels, done_when, limit in TESTS[test]:
                since, done = time.time(), False
                while not done:
                    elapsed = time.time() - since
                    battery.check()
                    frame = wait_for_new_frame(camera, frame)
                    angle = lane_mask.tape_angle(frame)
                    found = lane_found(perception.observe(frame))
                    if limit is not None and elapsed >= limit:
                        raise RuntimeError('%s took too long' % name)
                    done = done_when(elapsed, angle, found)
                    left, right = still(elapsed) if done else wheels(elapsed)
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
    save(out, shots)
    print('%s: %d frames in %s, battery %.2f V' % (result, len(shots), out, battery.volts))


if __name__ == '__main__':
    main()
