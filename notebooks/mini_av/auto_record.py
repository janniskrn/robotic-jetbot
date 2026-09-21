"""Drives the lane slowly with the color-mask detector and records a dataset session.

Alternative to 01_record_dataset.ipynb for the clean laps: no gamepad needed.
Only a data tool; the real driving program uses the learned models.

Run inside the Jupyter container, from this folder:
    python3 auto_record.py --name lap_a --seconds 60                  # clean laps
    python3 auto_record.py --name weave_a --seconds 60 --weave 45     # off-center views
    python3 auto_record.py --name spin_a --seconds 60 --spin-every 5  # views without the lane
    add --turn-around to drive the lane in the other direction
"""

import math

import argparse
import csv
import os
import time

import cv2
from jetbot import Camera, Robot

from battery import read_voltage
from lane_mask import LaneTracker, blue_mask, is_left_line, line_centers
from recorder import Recorder

BASE_SPEED = 0.32     # wheel speed on the lane; below about 0.27 the motors do not move the robot
STEERING_GAIN = 0.15  # P: wheel speed difference per unit of lane-center error (-1..1)
STEERING_DAMPING = 0.03  # D: wheel speed difference per unit of error change per second; stops the weave from growing
LOST_TIMEOUT = 0.5    # seconds without any tape line before the robot stops
RECORD_HZ = 4.0       # frames saved per second, same as the gamepad recorder
LOOP_PERIOD = 0.03    # seconds between control updates (camera runs at 30 Hz)

WEAVE_PERIOD = 3.0    # seconds per left-right cycle of the weaving target
PIVOT_SPEED = 0.35    # wheel speed while turning in place
PIVOT_PULSE = 0.15    # seconds per turning pulse (roughly 20 degrees)
PIVOT_SETTLE = 0.5    # seconds to stand still after a pulse, so the frame is sharp
SPIN_PULSES = 16      # pulses before looking for the lane again: most of a full circle
TURN_AROUND_PULSES = 6  # pulses before looking for the lane again: roughly half a circle
MAX_PULSES = 40       # give up after this many pulses without finding the lane
ALIGN_TOLERANCE = 30  # pixels the lane center may be off the image center to count as aligned

STALE_TIMEOUT = 0.5  # seconds without a new camera frame before the robot stops (the camera froze on 2026-09-20)

# Battery guard: on 2026-09-20 the Jetson lost power mid-session (voltage sag under motor load).
MIN_START_VOLTAGE = 11.4  # volts at rest (about 50 %) needed to start a session
MIN_RUN_VOLTAGE = 10.8    # volts under load; staying below this ends the session before the Jetson browns out
LOW_VOLTAGE_TIME = 2.0    # seconds below MIN_RUN_VOLTAGE before stopping (short dips at start-up are normal)
VOLTAGE_PERIOD = 0.5      # seconds between battery readings


def steering_error(center, image_width):
    """Lane center offset from the image center, -1 (left edge) .. 1 (right edge)"""
    half = image_width / 2.0
    return (center - half) / half


class CameraFrozen(Exception):
    """The camera stopped delivering new frames: the robot must not drive on an old image"""


def wait_for_new_frame(camera, old, timeout=STALE_TIMEOUT):
    """Returns a frame newer than old; raises CameraFrozen if none arrives in time.

    The JetBot camera thread ends silently on a read error and camera.value then keeps the last
    image forever, so every new frame is a new array object: the same object means no new frame.
    """
    start = time.time()
    while camera.value is old:
        if time.time() - start > timeout:
            raise CameraFrozen()
        time.sleep(0.005)
    return camera.value


def save(recorder, labels, frame, lines, center):
    """Offers the frame to the recorder and writes its pre-label if it was saved"""
    if recorder.offer(bytes(cv2.imencode('.jpg', frame)[1])):
        labels.writerow(['frame_%05d.jpg' % (recorder.count - 1), len(lines),
                         '' if center is None else round(center, 1)])


def lane_aligned(mask, width):
    """True if both lane lines are visible, lean the right way and the lane is roughly centered"""
    lines = line_centers(mask)
    if len(lines) != 2:
        return False
    centered = abs((lines[0] + lines[1]) / 2.0 - width / 2.0) < ALIGN_TOLERANCE
    return centered and is_left_line(mask, lines[0]) is True and is_left_line(mask, lines[1]) is False


def spin(robot, camera, recorder, labels, min_pulses):
    """Turns in place in pulses, saving a frame after each, until the lane is ahead again.

    Gives views with the lane at every angle and without it (negatives for "lane visible").
    Returns False if the lane was not found again.
    """
    for pulse in range(MAX_PULSES):
        robot.set_motors(PIVOT_SPEED, -PIVOT_SPEED)
        time.sleep(PIVOT_PULSE)
        robot.stop()
        before = camera.value
        time.sleep(PIVOT_SETTLE)
        frame = wait_for_new_frame(camera, before)
        mask = blue_mask(frame)
        save(recorder, labels, frame, line_centers(mask), None)
        if pulse + 1 >= min_pulses and lane_aligned(mask, camera.width):
            return True
    return False


def drive(robot, camera, recorder, seconds, labels, trace, weave=0.0, spin_every=0.0):
    """Follows the lane until the time is up or the lane is lost; returns the stop reason.

    weave: pixels the steering target swings left and right of the image center (0 = drive centered).
    spin_every: seconds between turns in place (0 = never).
    For every saved frame, writes what the color mask saw: these are the automatic pre-labels (D10).
    """
    tracker = LaneTracker(camera.width)
    start = last_seen = last_time = last_spin = last_volt_time = time.time()
    last_error = None
    volts = read_voltage()
    low_since = None
    frame = None
    while time.time() - start < seconds:
        if time.time() - last_volt_time > VOLTAGE_PERIOD:
            volts, last_volt_time = read_voltage(), time.time()
            low_since = (low_since or last_volt_time) if volts < MIN_RUN_VOLTAGE else None
            if low_since and last_volt_time - low_since > LOW_VOLTAGE_TIME:
                return 'battery low (%.2f V)' % volts
        if spin_every and time.time() - last_spin > spin_every:
            robot.stop()
            if not spin(robot, camera, recorder, labels, SPIN_PULSES):
                return 'lane not found after spin'
            tracker = LaneTracker(camera.width)
            last_error = None
            last_spin = last_seen = last_time = time.time()
        frame = wait_for_new_frame(camera, frame)
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
            offset = weave * math.sin(2 * math.pi * (now - start) / WEAVE_PERIOD)  # where the robot should be
            error = steering_error(center - offset, camera.width)
            change = 0.0 if last_error is None else (error - last_error) / max(now - last_time, 1e-3)
            turn = STEERING_GAIN * error + STEERING_DAMPING * change
            robot.set_motors(BASE_SPEED + turn, BASE_SPEED - turn)
            trace.writerow([round(now - start, 3), round(center, 1), round(turn, 3), round(volts, 2)])
            last_error = error
        last_time = now
        save(recorder, labels, frame, lines, center)
        time.sleep(LOOP_PERIOD)
    return 'time up'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', default='auto')
    parser.add_argument('--seconds', type=float, default=30.0)
    parser.add_argument('--notes', default='')
    parser.add_argument('--weave', type=float, default=0.0, help='pixels the target swings left and right')
    parser.add_argument('--spin-every', type=float, default=0.0, help='seconds between turns in place')
    parser.add_argument('--turn-around', action='store_true', help='turn to the other lane direction first')
    args = parser.parse_args()

    volts = read_voltage()
    if volts < MIN_START_VOLTAGE:
        print('battery %.2f V is below %.1f V: charge before recording' % (volts, MIN_START_VOLTAGE))
        return

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
        'weave': args.weave,
        'spin_every': args.spin_every,
        'turn_around': args.turn_around,
        'battery_start_v': round(volts, 2),
    })
    try:
        # line-buffered, so the files survive a sudden power loss
        with open(os.path.join(recorder.session_dir, 'auto_labels.csv'), 'w', buffering=1) as f, \
                open(os.path.join(recorder.session_dir, 'trace.csv'), 'w', buffering=1) as g:
            labels = csv.writer(f)
            labels.writerow(['frame', 'lines_seen', 'lane_center_x'])
            trace = csv.writer(g)  # every control step, for tuning and the week 1 graphs
            trace.writerow(['time', 'lane_center_x', 'turn', 'battery_v'])
            try:
                wait_for_new_frame(camera, camera.value, timeout=2.0)  # is the camera alive at all?
                if args.turn_around and not spin(robot, camera, recorder, labels, TURN_AROUND_PULSES):
                    reason = 'lane not found after turning around'
                else:
                    reason = drive(robot, camera, recorder, args.seconds, labels, trace, args.weave, args.spin_every)
            except CameraFrozen:
                reason = 'camera frozen'
            except KeyboardInterrupt:
                reason = 'stopped by hand'  # stop_robot.sh sends Ctrl-C (SIGINT), so the motors stop below
    finally:
        robot.stop()
        session_dir = recorder.stop()
        camera.stop()
    print('%s: saved %d frames in %s' % (reason, recorder.count, session_dir))


if __name__ == '__main__':
    main()
