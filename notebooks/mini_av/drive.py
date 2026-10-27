"""Driving program: camera -> perception -> decision -> control -> motors, with logging.

    python3 drive.py --name adaptive --seconds 60            # our controller (Task 1)
    python3 drive.py --name baseline --seconds 60 --baseline # stock-style comparison run
    python3 drive.py --name nocurve --seconds 60 --no-curve  # our steering, baseline speed
    add --stop-only to wait in front of a cup instead of avoiding it, --pass-side left/right to fix the side

Or from 04_drive.ipynb with start and stop buttons. Stop from a terminal: scripts/stop_robot.sh.
"""

import argparse
import queue
import threading
import time

import cv2

from jetbot import Camera, Robot

import config
from control import Controller
from decision import FOLLOWING, HALT, OBSTACLE_AVOIDANCE, ROAD_RECOVERY, SLOW_DOWN, STOP, Decision
from logger import RunLogger
from perception import Perception
from recorder import Recorder
from safety import BatteryGuard, BatteryLow, CameraFrozen, MotorWatchdog, wait_for_new_frame


RECORD_HZ = 4.0  # camera frames saved per second as a dataset session, to see what went wrong and to retrain
WARMUP_FRAMES = 5  # model calls with the motors off before driving (the first call took up to 1.1 s)
STARTUP_TIMEOUT = 3.0  # seconds to wait (motors off) for the first sight of the lane: the camera's
                       # exposure needs a moment after start, and the first frames can be too dark


def start_frame_saver(recorder):
    """Saves frames in a background thread, so a slow USB write never blocks the control loop.

    Put camera frames into the returned queue (full queue: the frame is skipped); put None to finish.
    """
    frames = queue.Queue(maxsize=8)

    def save():
        while True:
            frame = frames.get()
            if frame is None:
                return
            recorder.offer(bytes(cv2.imencode('.jpg', frame)[1]))

    thread = threading.Thread(target=save, daemon=True)
    thread.start()
    return frames, thread


class NoLaneAtStart(Exception):
    """The lane was not visible when the run started: put the robot on the lane"""


def run(name, seconds, baseline=False, use_curve=True, stop_event=None, stop_only=False, pass_side=None):
    """Drives until the time is up, the lane is lost, a safety check fails or stop_event is set.

    stop_only: wait in front of a cup instead of avoiding it; pass_side: 'left'/'right' or None (measured).

    Returns the stop reason and the log folder. The camera frames go to a dataset session drive_<name>.
    """
    battery = BatteryGuard()
    if not battery.start_ok():
        return 'battery %.2f V is too low: charge first' % battery.volts, None
    perception = Perception(use_curve=use_curve and not baseline)
    controller = Controller(baseline=baseline, use_curve=use_curve)
    decision = Decision(stop_only=stop_only, pass_side=pass_side)
    robot = Robot()
    camera = Camera.instance()
    log = RunLogger(name, {'baseline': baseline, 'use_curve': use_curve, 'seconds': seconds,
                           'stop_only': stop_only, 'pass_side': pass_side,
                           'battery_start_v': round(battery.volts, 2)})
    recorder = Recorder(period=1.0 / RECORD_HZ)
    recorder.start('drive_' + name, {'mode': 'drive', 'curves_trusted': False, 'log': log.dir, 'baseline': baseline, 'use_curve': use_curve,
                                     'frame_width': camera.width, 'frame_height': camera.height})
    frames, saver = start_frame_saver(recorder)
    watchdog = MotorWatchdog(robot)
    reason = 'time up'
    try:
        frame = wait_for_new_frame(camera, camera.value, timeout=2.0)  # is the camera alive at all?
        for _ in range(WARMUP_FRAMES):
            frame = wait_for_new_frame(camera, frame)
            perception.observe(frame)
        # wait for the lane with the motors off instead of judging one unsettled frame
        waited = time.time()
        while perception.observe(frame)['lane_visible'] < config.LANE_VISIBLE_THRESHOLD:
            if time.time() - waited > STARTUP_TIMEOUT:
                raise NoLaneAtStart()
            frame = wait_for_new_frame(camera, frame)
        watchdog.start()
        left = right = 0.0
        start = last = last_saved = time.time()
        while time.time() - start < seconds:
            if stop_event is not None and stop_event.is_set():
                reason = 'stopped by hand'
                break
            frame = wait_for_new_frame(camera, frame)
            now = time.time()
            dt, last = max(now - last, 1e-3), now
            percept = perception.observe(frame)
            if now - last_saved >= 1.0 / RECORD_HZ:
                last_saved = now
                try:
                    frames.put_nowait(frame)
                except queue.Full:
                    pass
            previous_state, state = decision.state, decision.update(percept, now)
            if state != previous_state and state in (OBSTACLE_AVOIDANCE, STOP):
                controller.reset()  # restart slowly afterwards, without old steering or damping memory
            lane_seen = percept['lane_visible'] >= config.LANE_VISIBLE_THRESHOLD
            if state in FOLLOWING or (state == ROAD_RECOVERY and lane_seen):
                if lane_seen:
                    limit = config.SPEED_SHARP if state == SLOW_DOWN else None
                    left, right = controller.update(percept['lane_x'], percept['curve_probs'], percept['curve_dir'],
                                                    dt, speed_limit=limit)
                else:  # short gap: steer without lane_x, which is not trained on frames without a lane
                    left, right = controller.hold(percept['curve_probs'], percept['curve_dir'], dt)
                with watchdog.lock:
                    robot.set_motors(left, right)
                watchdog.feed()
            elif state in (OBSTACLE_AVOIDANCE, ROAD_RECOVERY):
                if state == OBSTACLE_AVOIDANCE:
                    left, right = controller.avoid(decision.avoid_turn(), decision.pass_side())
                else:
                    left, right = controller.recover(decision.pass_side())
                with watchdog.lock:
                    robot.set_motors(left, right)
                watchdog.feed()
            elif state == STOP:  # wait in front of the cup; drive on (from slow) once it is gone
                with watchdog.lock:
                    robot.stop()
                watchdog.feed()
                left = right = 0.0
            else:
                robot.stop()
                reason = {ROAD_RECOVERY: 'lane not found after avoiding',
                          OBSTACLE_AVOIDANCE: 'cup still beside the robot after the pass'}.get(previous_state, 'lane lost')
                left = right = 0.0
            probs = percept['curve_probs']
            log.step(time=now - start, dt=dt, mode=state, lane_visible=percept['lane_visible'],
                     lane_x=percept['lane_x'], p_straight=probs[0], p_gentle=probs[1], p_sharp=probs[2],
                     curve_dir=percept['curve_dir'],
                     curve_class=percept['curve_class'], steering=controller.steering, speed=controller.speed,
                     left=left, right=right, battery_v=battery.check(), inference_ms=percept['inference_ms'],
                     cup_visible=percept['cup_visible'], cup_row=percept['cup_row'], cup_x=percept['cup_x'],
                     lane_aligned=int(percept['lane_aligned']), mask_cup_x=percept['mask_cup_x'],
                     mask_cup_pixels=percept['mask_cup_pixels'],
                     avoid_phase=config.AVOID_STEPS[decision.avoid_phase][0] if state == OBSTACLE_AVOIDANCE else '')
            if state == HALT:
                break
    except NoLaneAtStart:
        reason = 'no lane at start: put the robot on the lane'
    except CameraFrozen:
        reason = 'camera frozen'
    except BatteryLow as low:
        reason = str(low)
    except KeyboardInterrupt:
        reason = 'stopped by hand'  # scripts/stop_robot.sh sends Ctrl-C (SIGINT)
    finally:
        watchdog.running = False
        robot.stop()
        camera.stop()
        frames.put(None)
        saver.join(timeout=2.0)
        recorder.stop()
        log.close(reason)
    return reason, log.dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', default='drive')
    parser.add_argument('--seconds', type=float, default=30.0)
    parser.add_argument('--baseline', action='store_true', help='constant speed, plain P steering')
    parser.add_argument('--no-curve', action='store_true', help='our steering at the baseline speed')
    parser.add_argument('--stop-only', action='store_true', help='wait in front of a cup instead of avoiding it')
    parser.add_argument('--pass-side', choices=['left', 'right'], help='side to pass cups on (default: inside of the oval)')
    args = parser.parse_args()
    reason, log_dir = run(args.name, args.seconds, args.baseline, not args.no_curve,
                          stop_only=args.stop_only, pass_side=args.pass_side)
    print('%s, log in %s' % (reason, log_dir))


if __name__ == '__main__':
    main()
