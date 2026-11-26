"""Motion tests of the swerve's moves on the robot (AVOID3, ARC1), without a cup.

    python3 tools/motion_test.py turn [repeats]  # on the lane: turn left until the edge looks horizontal, back right
                                                 # until the lane is found
    python3 tools/motion_test.py swerve          # on a straight, 1 m of lane ahead: turn out, curve, turn in
    python3 tools/motion_test.py arc             # the swerve's curve for ARC_TURN_MIN: measure the angle by hand,
                                                 # it should be about 90 degrees

Saves every frame with time, phase and measurements to usb/images/datasets/<time>_<test>_test.
Start it from the cockpit (COCK1); the command line, inside the container from notebooks/mini_av, needs the
cockpit service stopped.
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
from control import Controller, turn_speed
from decision import lane_found, reached_horizontal
from perception import Perception
from recorder import DATASET_ROOT
from safety import BatteryGuard, BatteryLow, CameraFrozen, MotorWatchdog, wait_for_new_frame

HOLD_SECONDS = 2.0  # standing still after a move: the overshoot settles and can be seen in the frames


class Stopped(Exception):
    """STOP in the cockpit"""


def spin(direction):
    """Wheels of a turn in place, -1 left, +1 right"""
    return lambda elapsed: (direction * turn_speed(elapsed), -direction * turn_speed(elapsed))


def still(elapsed):
    return 0.0, 0.0


def curve(elapsed):
    return Controller().avoid('arc', 'left', elapsed)  # curves right, as when passing on the left (ARC9: with the trim)


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


def run(test, repeats=1, stop_event=None, on_step=None, perception=None, camera=None):
    """Runs one test until its phases are done, a phase takes too long, a safety check fails or stop_event is set.
    on_step(frame, values), perception and camera as in drive.run (the cockpit passes its own).
    Returns the result and the folder of the saved frames"""
    battery = BatteryGuard()
    if not battery.start_ok():
        return 'battery %.2f V is too low: charge first' % battery.volts, None
    if perception is None:
        perception = Perception(use_curve=False)
    else:
        perception.use_curve_model(False)  # a shared Perception: the models of a test of its own
    robot = Robot()
    own_camera = camera is None
    if own_camera:
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
                    if stop_event is not None and stop_event.is_set():
                        raise Stopped()
                    elapsed = time.time() - since
                    volts = battery.check()
                    frame = wait_for_new_frame(camera, frame)
                    angle = lane_mask.tape_angle(frame)
                    percept = perception.observe(frame)
                    found = lane_found(percept)
                    if limit is not None and elapsed >= limit:
                        raise RuntimeError('%s took too long' % name)
                    done = done_when(elapsed, angle, found)
                    left, right = still(elapsed) if done else wheels(elapsed)
                    with watchdog.lock:
                        robot.set_motors(left, right)
                    watchdog.feed()
                    shots.append((time.time() - start, name, left, right, angle, found, frame.copy()))
                    if on_step is not None:
                        on_step(frame, dict(time=time.time() - start, mode='MOTION_TEST', phase='%s: %s' % (test, name),
                                            left=left, right=right, lane_visible=percept['lane_visible'],
                                            lane_x=percept['lane_x'], lane_aligned=int(percept['lane_aligned']),
                                            battery_v=volts, inference_ms=percept['inference_ms']))
    except (KeyboardInterrupt, Stopped):  # Ctrl-C or scripts/stop_robot.sh, or the cockpit's STOP
        result = 'stopped by hand'
    except CameraFrozen:
        result = 'camera frozen'
    except (BatteryLow, RuntimeError) as error:
        result = str(error)
    finally:
        watchdog.running = False
        with watchdog.lock:
            robot.stop()
        if own_camera:
            camera.stop()
    save(out, shots)
    return '%s: %d frames, battery %.2f V' % (result, len(shots), battery.volts), out


def main():
    test = sys.argv[1] if len(sys.argv) > 1 else ''
    if test not in TESTS:
        raise SystemExit('test must be one of: %s' % ', '.join(TESTS))
    repeats = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    result, out = run(test, repeats)
    print('%s, saved in %s' % (result, out))


if __name__ == '__main__':
    main()
