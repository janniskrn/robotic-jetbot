"""Driving program: camera -> perception -> decision -> control -> motors, with logging.

    python3 drive.py --name adaptive --seconds 60            # our controller (Task 1)
    python3 drive.py --name baseline --seconds 60 --baseline # stock-style comparison run
    python3 drive.py --name nocurve --seconds 60 --no-curve  # our steering, constant speed

Or from 04_drive.ipynb with start and stop buttons. Stop from a terminal: scripts/stop_robot.sh.
"""

import argparse
import time

from jetbot import Camera, Robot

import config
from control import Controller
from decision import FOLLOW, Decision
from logger import RunLogger
from perception import Perception
from safety import BatteryGuard, BatteryLow, CameraFrozen, wait_for_new_frame


def run(name, seconds, baseline=False, use_curve=True, stop_event=None):
    """Drives until the time is up, the lane is lost, a safety check fails or stop_event is set.

    Returns the stop reason and the log folder.
    """
    battery = BatteryGuard()
    if not battery.start_ok():
        return 'battery %.2f V is too low: charge first' % battery.volts, None
    perception = Perception(use_curve=use_curve and not baseline)
    controller = Controller(baseline=baseline)
    decision = Decision()
    robot = Robot()
    camera = Camera.instance()
    log = RunLogger(name, {'baseline': baseline, 'use_curve': use_curve, 'seconds': seconds,
                           'battery_start_v': round(battery.volts, 2)})
    reason = 'time up'
    try:
        frame = wait_for_new_frame(camera, camera.value, timeout=2.0)  # is the camera alive at all?
        start = last = time.time()
        while time.time() - start < seconds:
            if stop_event is not None and stop_event.is_set():
                reason = 'stopped by hand'
                break
            frame = wait_for_new_frame(camera, frame)
            now = time.time()
            dt, last = max(now - last, 1e-3), now
            percept = perception.observe(frame)
            mode = decision.update(percept, now)
            if mode == FOLLOW:
                left, right = controller.update(percept['lane_x'], percept['curve_probs'], dt)
                robot.set_motors(left, right)
            else:
                robot.stop()
                reason = 'lane lost'
                left = right = 0.0
            probs = percept['curve_probs']
            log.step(time=now - start, dt=dt, mode=mode, lane_visible=percept['lane_visible'],
                     lane_x=percept['lane_x'], p_straight=probs[0], p_gentle=probs[1], p_sharp=probs[2],
                     curve_class=percept['curve_class'], steering=controller.steering, speed=controller.speed,
                     left=left, right=right, battery_v=battery.check(), inference_ms=percept['inference_ms'])
            if mode != FOLLOW:
                break
    except CameraFrozen:
        reason = 'camera frozen'
    except BatteryLow as low:
        reason = str(low)
    except KeyboardInterrupt:
        reason = 'stopped by hand'  # scripts/stop_robot.sh sends Ctrl-C (SIGINT)
    finally:
        robot.stop()
        camera.stop()
        log.close(reason)
    return reason, log.dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', default='drive')
    parser.add_argument('--seconds', type=float, default=30.0)
    parser.add_argument('--baseline', action='store_true', help='constant speed, plain P steering')
    parser.add_argument('--no-curve', action='store_true', help='our steering, but constant speed')
    args = parser.parse_args()
    reason, log_dir = run(args.name, args.seconds, args.baseline, not args.no_curve)
    print('%s, log in %s' % (reason, log_dir))


if __name__ == '__main__':
    main()
