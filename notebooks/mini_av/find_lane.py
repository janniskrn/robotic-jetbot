"""Finds the lane again after the robot has left it, in small steps with the motors off between them.

    python3 find_lane.py

Each round: turn left in short pulses, a bit over one full turn, looking for the lane (on_lane). Lane not
found: turn on to the heading with the nearest tape and drive across it, into the lane, then the next round. Stops
for a cup close ahead. Exit code 0 with the lane found, 1 otherwise. The robot may end up facing either way along the
lane: lane_found cannot tell. Saves every stop to usb/images/datasets/<time>_find_lane. Run inside the container.
"""

import os
import sys
import time

import cv2
from jetbot import Camera, Robot

import lane_mask
from control import turn_speed
from decision import band_cm, lane_found
from perception import Perception
from recorder import DATASET_ROOT
from safety import BatteryGuard, MotorWatchdog, wait_for_new_frame

TURN_PULSE = 0.15     # seconds of one turn pulse (kick plus a little): about 15-25 degrees
PUSH_PULSE = 0.3      # seconds of one forward pulse
PUSH_SPEED = 0.33     # wheel speed forward
PUSHES = 10           # forward pulses per round at most, about 40 cm
PAST_TAPE = 3         # forward pulses after the tape has left the image's lower edge: into the lane
SCAN_PULSES = 30      # turn pulses per round, a bit over one full turn
ROUNDS = 4            # rounds before giving up
SETTLE_SECONDS = 0.3  # standing still before looking: the camera shows the robot late
CUP_STOP_CM = 25.0    # no forward pulse with a cup this close in the middle of the image
CUP_STOP_X = 0.5
NEAR_ROW = 0.8        # fraction of the image height at which tape must be seen: close to the robot
SURE_LANE = 0.9       # lane model value that counts as standing well in the lane
BEST_SHARE = 0.8      # share of the scan's largest amount of near tape that counts as the heading of the nearest tape
NEAR_FROM = 0.7       # fraction of the image height from which tape counts as near
BOTTOM_ROW = 0.93     # fraction of the image height from which tape counts as at the robot's nose
WARMUP_FRAMES = 5     # model calls with the motors off (the first call took up to 1.1 s)


def on_lane(percept):
    """True if the robot stands well in the lane, pointing along it: at the border lane_found held, but the lane
    model then fell below 0.5 at the start of the drive (run avoid4_4)"""
    return lane_found(percept) and percept['lane_visible'] >= SURE_LANE


def near_blue(frame):
    """Amount of tape in the lower part of the image: the larger, the nearer the tape"""
    return int((lane_mask.blue_mask(frame)[int(NEAR_FROM * frame.shape[0]):] > 0).sum())


def tape_close(frame):
    """True if tape crosses the image's lower part: a distant lane also reads as found (run avoid4_5, known since v3_ccw_3)"""
    return len(lane_mask.line_centers(lane_mask.blue_mask(frame), NEAR_ROW)) >= 1


class FindLane(object):
    def __init__(self, perception, robot, camera, watchdog, battery):
        self.perception, self.robot, self.camera, self.watchdog, self.battery = perception, robot, camera, watchdog, battery
        self.frame = None
        self.out = None
        self.stops = 0

    def pulse(self, seconds, wheels):
        """Runs wheels(elapsed) -> (left, right) for some seconds, then motors off"""
        since = time.time()
        while time.time() - since < seconds:
            with self.watchdog.lock:
                self.robot.set_motors(*wheels(time.time() - since))
            self.watchdog.feed()
            self.frame = wait_for_new_frame(self.camera, self.frame)
        with self.watchdog.lock:
            self.robot.stop()

    def look(self):
        """Stands still, then returns what the models see now (and saves the frame)"""
        self.battery.check()
        time.sleep(SETTLE_SECONDS)
        self.frame = wait_for_new_frame(self.camera, self.camera.value)
        for _ in range(4):  # the obstacle and curve models run on every second frame
            self.frame = wait_for_new_frame(self.camera, self.frame)
            percept = self.perception.observe(self.frame)
        cv2.imwrite(os.path.join(self.out, 'frame_%05d.jpg' % self.stops), self.frame)
        self.stops += 1
        return percept

    def turn_left(self):
        def wheels(elapsed):
            speed = turn_speed(elapsed)
            return -speed, speed
        self.pulse(TURN_PULSE, wheels)
        return self.look()

    def cup_blocks(self, percept):
        return any(band_cm(band) <= CUP_STOP_CM and abs(band[0]) < CUP_STOP_X for band in percept['cup_bands'])

    def round(self):
        """One scan and one push across the nearest tape. Returns 'found', 'blocked' or 'again'"""
        best = 0
        for _ in range(SCAN_PULSES):
            percept = self.turn_left()
            if on_lane(percept) and tape_close(self.frame):
                return 'found'
            best = max(best, near_blue(self.frame))
        for _ in range(SCAN_PULSES):  # on to the heading with the nearest tape
            if near_blue(self.frame) >= BEST_SHARE * best:
                break
            percept = self.turn_left()
        over_tape, past = False, 0
        for _ in range(PUSHES):
            if self.cup_blocks(percept):
                return 'blocked'
            self.pulse(PUSH_PULSE, lambda elapsed: (PUSH_SPEED, PUSH_SPEED))
            percept = self.look()
            if on_lane(percept) and tape_close(self.frame):
                return 'found'
            at_bottom = lane_mask.blue_mask(self.frame)[int(BOTTOM_ROW * self.frame.shape[0]):].any()
            over_tape = over_tape or at_bottom
            past = past + 1 if over_tape and not at_bottom else 0
            if past >= PAST_TAPE:
                break
        return 'again'

    def run(self):
        """Searches for the lane. Returns 'found', 'blocked' or 'again' (not found)"""
        self.frame = wait_for_new_frame(self.camera, self.camera.value)
        self.out = os.path.join(DATASET_ROOT, time.strftime('%Y-%m-%d_%H-%M-%S') + '_find_lane')
        os.makedirs(self.out)
        self.stops = 0
        result = 'again'
        for number in range(ROUNDS):
            result = self.round()
            print('round %d: %s (%d stops)' % (number + 1, result, self.stops))
            if result != 'again':
                break
        return result


def main():
    battery = BatteryGuard()
    if not battery.start_ok():
        raise SystemExit('battery %.2f V is too low: charge first' % battery.volts)
    perception = Perception()
    robot = Robot()
    camera = Camera.instance()
    watchdog = MotorWatchdog(robot)
    finder = FindLane(perception, robot, camera, watchdog, battery)
    try:
        frame = wait_for_new_frame(camera, camera.value, timeout=2.0)
        for _ in range(WARMUP_FRAMES):
            frame = wait_for_new_frame(camera, frame)
            perception.observe(frame)
        watchdog.start()
        result = finder.run()
    except KeyboardInterrupt:
        result = 'stopped by hand'
    finally:
        watchdog.running = False
        with watchdog.lock:
            robot.stop()
        camera.stop()
    print('find_lane: %s, %d stops, frames in %s, battery %.2f V' % (result, finder.stops, finder.out, battery.volts))
    sys.exit(0 if result == 'found' else 1)


if __name__ == '__main__':
    main()
