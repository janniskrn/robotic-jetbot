"""Teaches the cup distances: the robot backs away from a cup in small pulses and measures after each one.

    python3 cup_learn.py straight         # a label for the place; the robot starts touching the cup
    python3 cup_learn.py straight 0       # last number: pulses at most; 0 measures once with the motors off

At every stop (motors off) it saves one frame and one line of measurements: where the cup mask sees the band and what
all models return on those frames. The distance comes from the band's size afterwards: 405 / sqrt(band pixels) cm
(LEARN1). The pulses are timed and uneven (no encoders: 2 cm on average, the first ones barely moved), so they are
not a distance.

Saves to usb/images/obstacle_survey/learn_<label>_<time>/ (stop_NN.jpg, stops.csv). Needs about 70 cm of free floor
behind the robot. Run inside the container. Stop with Ctrl-C (scripts/stop_robot.sh).
"""

import csv
import os
import statistics
import sys
import time

import cv2
from jetbot import Camera, Robot

import config
import cup_mask
from perception import Perception
from safety import BatteryGuard, MotorWatchdog, wait_for_new_frame

SURVEY_DIR = '/workspace/usb/images/obstacle_survey'
PULSE_SECONDS = 0.2   # one pulse backwards at BACKUP_SPEED: a few cm
SETTLE_SECONDS = 0.6  # standing still before measuring: the robot has stopped rolling and the camera has caught up
STOP_FRAMES = 6       # frames measured at each stop (the obstacle and curve models run on every second one)
MAX_PULSES = 30       # at most this many pulses per run
FAR_ROW = 72          # band row above which the run ends (about a meter away)
EDGE_X = 0.85         # the run ends when the band drifts this far toward the image edge
LOST_STOPS = 3        # stops in a row without a band before the run ends
WARMUP_FRAMES = 5     # model calls with the motors off (the first call took up to 1.1 s)
COLUMNS = ['stop', 'band_row', 'band_x', 'band_pixels', 'bands', 'cup_visible', 'cup_row', 'cup_x', 'lane_visible',
           'lane_x', 'lane_aligned', 'tape_angle', 'p_straight', 'p_gentle', 'p_sharp', 'curve_dir', 'battery_v']


def median(values):
    """Median of the numbers among values, or None if there are none"""
    numbers = [v for v in values if v is not None]
    return statistics.median(numbers) if numbers else None


def measure(camera, frame, perception, stop, volts):
    """Observes STOP_FRAMES frames standing still. Returns the last frame and one dict for stops.csv"""
    seen = []
    for _ in range(STOP_FRAMES):
        frame = wait_for_new_frame(camera, frame)
        seen.append(perception.observe(frame))
    nearest = [p['cup_bands'][0] if p['cup_bands'] else (None, None, None) for p in seen]
    row = median([b[1] for b in nearest])
    return frame, {
        'stop': stop,
        'band_row': None if row is None else row * 224,
        'band_x': median([b[0] for b in nearest]),
        'band_pixels': median([b[2] for b in nearest]),
        'bands': median([len(p['cup_bands']) for p in seen]),
        'cup_visible': median([p['cup_visible'] for p in seen]),
        'cup_row': median([p['cup_row'] * 224 for p in seen]),
        'cup_x': median([p['cup_x'] for p in seen]),
        'lane_visible': median([p['lane_visible'] for p in seen]),
        'lane_x': median([p['lane_x'] for p in seen]),
        'lane_aligned': median([int(p['lane_aligned']) for p in seen]),
        'tape_angle': median([p['tape_angle'] for p in seen]),
        'p_straight': median([p['curve_probs'][0] for p in seen]),
        'p_gentle': median([p['curve_probs'][1] for p in seen]),
        'p_sharp': median([p['curve_probs'][2] for p in seen]),
        'curve_dir': median([p['curve_dir'] for p in seen]),
        'battery_v': volts,
    }


def pulse_back(robot, watchdog, camera, frame):
    """One timed pulse backwards, then motors off. Returns the newest frame (raises CameraFrozen without new frames)"""
    since = time.time()
    while time.time() - since < PULSE_SECONDS:
        with watchdog.lock:
            robot.set_motors(-config.BACKUP_SPEED, -config.BACKUP_SPEED)
        watchdog.feed()
        frame = wait_for_new_frame(camera, frame)
    with watchdog.lock:
        robot.stop()
    return frame


def show(row):
    """Prints one stop"""
    band = 'no band' if row['band_row'] is None else 'band row %3.0f x %+.2f (%d px)' % (
        row['band_row'], row['band_x'], row['band_pixels'])
    print('stop %2d: %-30s | model cup %.2f row %3.0f x %+.2f | lane %.2f x %+.2f' % (
        row['stop'], band, row['cup_visible'], row['cup_row'], row['cup_x'], row['lane_visible'], row['lane_x']))


def main():
    label = sys.argv[1]
    pulses = int(sys.argv[2]) if len(sys.argv) > 2 else MAX_PULSES
    battery = BatteryGuard()
    if not battery.start_ok():
        raise SystemExit('battery %.2f V is too low: charge first' % battery.volts)
    perception = Perception()
    robot = Robot()
    camera = Camera.instance()
    watchdog = MotorWatchdog(robot)
    out = os.path.join(SURVEY_DIR, 'learn_%s_%s' % (label, time.strftime('%Y-%m-%d_%H-%M-%S')))
    os.makedirs(out)
    rows = []
    result = 'all pulses done'
    try:
        frame = wait_for_new_frame(camera, camera.value, timeout=2.0)
        for _ in range(WARMUP_FRAMES):
            frame = wait_for_new_frame(camera, frame)
            perception.observe(frame)
        watchdog.start()
        lost = 0
        seen_band = False
        for stop in range(pulses + 1):
            if stop > 0:
                frame = pulse_back(robot, watchdog, camera, frame)
            time.sleep(SETTLE_SECONDS)
            frame = wait_for_new_frame(camera, camera.value)
            frame, row = measure(camera, frame, perception, stop, battery.check())
            rows.append(row)
            cv2.imwrite(os.path.join(out, 'stop_%02d.jpg' % stop), frame)
            show(row)
            seen_band = seen_band or row['band_row'] is not None  # touching the cup, the band can be below the view
            lost = lost + 1 if row['band_row'] is None and seen_band else 0
            if lost >= LOST_STOPS:
                result = 'band lost'
                break
            if row['band_row'] is not None and row['band_row'] < FAR_ROW:
                result = 'cup far away'
                break
            before = rows[-2]['band_x'] if stop > 0 else None
            if row['band_x'] is not None and before is not None and abs(before) < abs(row['band_x']) and abs(
                    row['band_x']) > EDGE_X:  # moving outward: a cup beside the robot starts at the edge and moves in
                result = 'band moving out of the image'
                break
    except KeyboardInterrupt:
        result = 'stopped by hand'
    finally:
        watchdog.running = False
        with watchdog.lock:
            robot.stop()
        camera.stop()
    with open(os.path.join(out, 'stops.csv'), 'w') as f:
        writer = csv.DictWriter(f, COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print('%s: %d stops, saved in %s, battery %.2f V' % (result, len(rows), out, battery.volts))


if __name__ == '__main__':
    main()
