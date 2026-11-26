"""Driving program: camera -> perception -> decision -> control -> motors, with logging.

    python3 drive.py --name adaptive --seconds 60            # our controller (Task 1)
    python3 drive.py --name baseline --seconds 60 --baseline # stock-style comparison run
    python3 drive.py --name nocurve --seconds 60 --no-curve  # our steering, baseline speed
    add --stop-only to wait in front of a cup instead of avoiding it, --pass-side left/right to fix the side

Or from 04_drive.ipynb or the web cockpit (dashboard.py). Stop from a terminal: scripts/stop_robot.sh.
"""

import argparse
import collections
import queue
import threading
import time

import cv2

from jetbot import Camera, Robot

import config
from control import Controller
from find_lane import FOUND, FindLane, StopRecovery
from decision import (FOLLOWING, HALT, LINE_RECOVERY, OBSTACLE_AVOIDANCE, ROAD_RECOVERY, SLOW_DOWN, STOP, Decision,
                      band_cm, cup_ahead, sees_lane)
from logger import RunLogger
from perception import Perception
from recorder import Recorder
from safety import BatteryGuard, BatteryLow, CameraFrozen, MotorWatchdog, wait_for_new_frame


UNDO_STEPS = 60        # recent wheel commands kept for the undo in LINE_RECOVERY: more than its 1.5 s
RECORD_HZ = 4.0        # camera frames saved per second as a dataset session
STARTUP_TIMEOUT = 3.0  # seconds to wait (motors off) for the lane at the start: the exposure needs a moment


class NoLaneAtStart(Exception):
    """The lane was not visible when the run started: put the robot on the lane"""


def start_frame_saver(recorder):
    """Saves frames in a background thread, so a slow USB write never blocks the control loop.
    Put camera frames into the returned queue (full queue: the frame is skipped); put None to finish."""
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


def wait_for_lane(camera, perception, frame):
    """Waits with the motors off until the lane is seen; NoLaneAtStart after STARTUP_TIMEOUT"""
    waited = time.time()
    while not sees_lane(perception.observe(frame)):
        if time.time() - waited > STARTUP_TIMEOUT:
            raise NoLaneAtStart()
        frame = wait_for_new_frame(camera, frame)
    return frame


def wheel_command(state, percept, decision, controller, dt, now):
    """(left, right) for this state, or None when the run ends (HALT)"""
    if state in FOLLOWING or (state == ROAD_RECOVERY and (sees_lane(percept) or decision.short_gap(now))):
        if not sees_lane(percept):  # short gap: lane_x is not trained on frames without a lane
            return controller.hold(percept['curve_probs'], percept['curve_dir'], dt)
        limit = config.SPEED_SHARP if state == SLOW_DOWN else None
        return controller.update(percept['lane_x'], percept['curve_probs'], percept['curve_dir'], dt, limit)
    if state == OBSTACLE_AVOIDANCE:
        return controller.avoid(decision.avoid_action(), decision.pass_side(), now - decision.phase_since)
    if state == ROAD_RECOVERY:
        return controller.recover(decision.pass_side())
    if state == STOP:  # brake, back up if too close, wait
        return controller.stop(decision.stop_phase, now - decision.phase_since)
    return None


def halt_reason(previous_state, decision):
    return {ROAD_RECOVERY: 'lane not found after avoiding',
            OBSTACLE_AVOIDANCE: 'swerve %s did not reach its camera mark' % decision.avoid_phase
            }.get(previous_state, 'lane lost')


def step_values(t, dt, state, percept, decision, controller, left, right, volts):
    """One line of steps.csv (logger.COLUMNS)"""
    probs = percept['curve_probs']
    ahead = cup_ahead(percept)  # the cup the decision looks at
    return dict(time=t, dt=dt, mode=state, lane_visible=percept['lane_visible'], lane_x=percept['lane_x'],
                p_straight=probs[0], p_gentle=probs[1], p_sharp=probs[2], curve_dir=percept['curve_dir'],
                curve_class=percept['curve_class'], steering=controller.steering, speed=controller.speed,
                left=left, right=right, battery_v=volts, inference_ms=percept['inference_ms'],
                cup_visible=percept['cup_visible'], cup_row=percept['cup_row'], cup_x=percept['cup_x'],
                lane_aligned=int(percept['lane_aligned']), tape_angle=percept['tape_angle'],
                band_x=ahead[0] if ahead else None, band_row=ahead[1] if ahead else None,
                band_cm=band_cm(ahead) if ahead else None, bands=len(percept['cup_bands']),
                phase={OBSTACLE_AVOIDANCE: decision.avoid_action(), STOP: decision.stop_phase}.get(state, ''),
                tape_row=percept['tape_row'])


def run(name, seconds, baseline=False, use_curve=True, stop_event=None, stop_only=False, pass_side=None, on_step=None,
        perception=None, camera=None):
    """Drives until the time is up, the lane is lost, a safety check fails or stop_event is set.

    stop_only: wait in front of a cup instead of avoiding it; pass_side: 'left'/'right' or None (inside of the oval).
    on_step(frame, values): called after each logged step with the camera frame and the logged values (keep it cheap).
    perception: an already loaded Perception (the cockpit shares its own: one copy of the models in memory).
    camera: an open camera the caller owns; it stays open (Argus cannot reopen a camera in the same process).

    Returns the stop reason and the log folder. The camera frames go to a dataset session drive_<name>.
    """
    battery = BatteryGuard()
    if not battery.start_ok():
        return 'battery %.2f V is too low: charge first' % battery.volts, None
    if perception is None:
        perception = Perception(use_curve=use_curve and not baseline)
    else:
        perception.use_curve_model(use_curve and not baseline)  # a shared Perception: the models of a run of its own
    controller = Controller(baseline=baseline, use_curve=use_curve)
    decision = Decision(stop_only=stop_only, pass_side=pass_side, line_recovery=not baseline)
    robot = Robot()
    own_camera = camera is None
    if own_camera:
        camera = Camera.instance()
    log = RunLogger(name, {'baseline': baseline, 'use_curve': use_curve, 'seconds': seconds,
                           'stop_only': stop_only, 'pass_side': pass_side,
                           'battery_start_v': round(battery.volts, 2)})
    recorder = Recorder(period=1.0 / RECORD_HZ)
    recorder.start('drive_' + name, {'mode': 'drive', 'curves_trusted': False, 'log': log.dir, 'baseline': baseline,
                                     'use_curve': use_curve, 'frame_width': camera.width, 'frame_height': camera.height})
    frames, saver = start_frame_saver(recorder)
    watchdog = MotorWatchdog(robot)
    finder = FindLane(perception, robot, camera, watchdog, battery)
    reason = 'time up'
    try:
        frame = wait_for_lane(camera, perception, perception.warm_up(camera))
        watchdog.start()
        last_lane_x = 0.0
        history = collections.deque(maxlen=UNDO_STEPS)  # (dt, left, right) of the recent steps, for the undo
        start = last = last_saved = time.time()
        if on_step is not None:  # the search takes many seconds: the cockpit shows each frame it looks at
            finder.on_frame = lambda seen, p: on_step(seen, dict(
                time=time.time() - start, mode=LINE_RECOVERY, phase=finder.stage, lane_visible=p['lane_visible'],
                lane_x=p['lane_x'], curve_class=p['curve_class'], cup_visible=p['cup_visible'],
                battery_v=battery.volts))
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

            if state == LINE_RECOVERY:  # many seconds, in small steps with their own safety checks
                with watchdog.lock:
                    robot.stop()
                followed = previous_state in FOLLOWING  # the lane is near: undo and sweep make sense
                # where the lane should be: the way the curve bends, else where it was last seen
                turn = percept['curve_dir'] if abs(percept['curve_dir']) >= config.FEEDFORWARD_MIN_DIR else last_lane_x
                side = (-1 if turn < 0 else 1) if followed else 0
                result = finder.run(history if followed else (), side, start + seconds, stop_event)
                values = dict(time=now - start, dt=dt, mode=LINE_RECOVERY, phase=result)
                log.step(**values)
                if on_step is not None:
                    on_step(finder.frame, values)
                last, frame = time.time(), finder.frame
                decision.line_recovery_done(result in FOUND, last)
                controller.reset()
                history.clear()
                if result in FOUND:
                    continue
                reason = 'lane not found by line recovery (%s)' % result
                break

            if state != previous_state and state in (OBSTACLE_AVOIDANCE, STOP):
                controller.reset()  # restart slowly afterwards, without old steering or damping memory
            if sees_lane(percept):
                last_lane_x = percept['lane_x']
            wheels = wheel_command(state, percept, decision, controller, dt, now)
            if wheels is None:
                robot.stop()
                reason = halt_reason(previous_state, decision)
                left = right = 0.0
            else:
                left, right = wheels
                with watchdog.lock:
                    robot.set_motors(left, right)
                watchdog.feed()
            values = step_values(now - start, dt, state, percept, decision, controller, left, right, battery.check())
            log.step(**values)
            if on_step is not None:
                on_step(frame, dict(values, direction=decision.direction, pass_side=decision.pass_side()))
            history.append((dt, left, right))
            if state == HALT:
                break
    except StopRecovery as over:
        reason = str(over)
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
        if own_camera:
            camera.stop()
        try:
            frames.put(None, timeout=2.0)  # a stalled USB write must not hold up the end of the run
        except queue.Full:
            pass
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
