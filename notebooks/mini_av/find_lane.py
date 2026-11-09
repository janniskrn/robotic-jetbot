"""Finds the lane again after the robot has left it (state LINE_RECOVERY), from quick to thorough.

    python3 find_lane.py     # the full search alone, for a robot put down off the lane

    1. undo: drive the last second of wheel commands backwards. The lane was seen about 15 cm before it was lost (all 8
       losses up to 2026-11-08) and the robot keeps its driving direction. Only right after following, at most twice in
       a row.
    2. sweep: turn about 100 degrees to each side, first toward where the lane should be.
    3. search, in small steps with the motors off between them: turn one full turn looking for the lane; not found: turn
       the shorter way to the nearest tape and drive across it, into the lane, then the next round. A lane more than
       about 130 degrees from the heading at the start of the search is the wrong way along it and only counts in the
       last round. No forward pulse with a cup close ahead: that heading is skipped.

Saves every stop and a stops.csv to usb/images/datasets/<time>_find_lane. Run inside the container.
"""

import csv
import os
import sys
import time

import cv2
import numpy as np

import config
import lane_mask
from control import turn_speed
from decision import band_cm, lane_found
from recorder import DATASET_ROOT
from safety import BatteryGuard, MotorWatchdog, wait_for_new_frame

UNDO_SECONDS = 1.0    # seconds of wheel commands driven backwards
UNDO_TRIES = 2        # undos in a row before the robot looks around instead: the same curve may lose the lane again
UNDO_RESET = 5.0      # seconds after an undo from which the count of undos starts anew
TURN_PULSE = 0.15     # seconds of one turn pulse (kick plus a little)
PULSES_PER_TURN = 22  # turn pulses for one full turn: 19-25 measured, 2026-11-08
SWEEP_PULSES = 6      # turn pulses to each side in the sweep, about 100 degrees
HEADING_WINDOW = 7    # turn pulses from the heading at the start within which a found lane counts as the right way
PUSH_PULSE = 0.3      # seconds of one forward pulse
PUSH_SPEED = 0.33     # wheel speed forward
PUSHES = 10           # forward pulses per round at most
PAST_TAPE = 3         # forward pulses after the tape has left the image's lower edge: into the lane
ROUNDS = 4            # rounds of the search before giving up
SETTLE_SECONDS = 0.3  # standing still before looking: the camera shows the robot late
CONFIRM_FRAMES = 3    # further frames that must agree before the lane counts as found: a single look was borderline
CUP_STOP_CM = 25.0    # no forward pulse with a cup this close in the middle of the image
CUP_STOP_X = 0.5
NEAR_ROW = 0.8        # fraction of the image height at which tape must be seen: close to the robot
SURE_LANE = 0.9       # lane model value that counts as standing well in the lane
TAPE_ROW_PIXELS = 5   # blue pixels in an image row that count as tape in that row
TAPE_SLACK = 8        # image rows above the scan's lowest tape that still count as the heading of the nearest tape
NUDGES = 4            # extra turn pulses to reach that heading (the pulses are uneven)
BOTTOM_ROW = 0.93     # fraction of the image height from which tape counts as at the robot's nose
WARMUP_FRAMES = 5     # model calls with the motors off (the first call took up to 1.1 s)
FOUND = ('undo', 'sweep', 'search', 'search_any')  # results of run() with the lane found
KEPT_DIRECTION = ('undo', 'sweep', 'search')       # those with the robot still driving the same way along the lane
STOP_COLUMNS = ['stop', 'stage', 'heading', 'lane_visible', 'lane_x', 'lane_aligned', 'tape_row', 'tape_close']


class StopRecovery(Exception):
    """The run is over during the search: stopped by hand or time up (the text says which)"""


def on_lane(percept):
    """True if the robot stands well in the lane, pointing along it: at the border lane_found held, but the lane
    model then fell below 0.5 at the start of the drive (run avoid4_4)"""
    return lane_found(percept) and percept['lane_visible'] >= SURE_LANE


def lane_back(percept):
    """True if the lane is seen again after the undo: the driving direction is known, so the two-line check (which a
    curve can fail) is not needed"""
    return percept['lane_visible'] >= SURE_LANE and abs(percept['lane_x']) < config.TURN_IN_CENTERED


def tape_row(frame):
    """Lowest image row with tape, 0 without tape: the lower, the nearer. Counting only the image's lower part gave 0
    in every direction away from the lane, and the robot wandered (run line2_3)"""
    rows = np.nonzero((lane_mask.blue_mask(frame) > 0).sum(axis=1) >= TAPE_ROW_PIXELS)[0]
    return int(rows[-1]) if len(rows) else 0


def tape_close(frame):
    """True if tape crosses the image's lower part: a distant lane also reads as found (run avoid4_5, known since v3_ccw_3)"""
    return len(lane_mask.line_centers(lane_mask.blue_mask(frame), NEAR_ROW)) >= 1


def right_way(heading):
    """True if a heading (turn pulses, left positive) is within HEADING_WINDOW of the heading at the start, a full turn
    counting as none"""
    return abs((heading + PULSES_PER_TURN // 2) % PULSES_PER_TURN - PULSES_PER_TURN // 2) <= HEADING_WINDOW


class FindLane(object):
    def __init__(self, perception, robot, camera, watchdog, battery):
        self.perception, self.robot, self.camera, self.watchdog, self.battery = perception, robot, camera, watchdog, battery
        self.frame = None
        self.out = None
        self.stops = 0
        self.heading = 0
        self.rows = []
        self.stage = ''
        self.deadline = None
        self.stop_event = None
        self.undos = 0
        self.last_undo = 0.0

    def check_run(self):
        """Ends the search when the run is over, like the driving loop would"""
        if self.stop_event is not None and self.stop_event.is_set():
            raise StopRecovery('stopped by hand')
        if self.deadline is not None and time.time() >= self.deadline:
            raise StopRecovery('time up')

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

    def observe_next(self):
        self.frame = wait_for_new_frame(self.camera, self.frame)
        return self.perception.observe(self.frame)

    def look(self):
        """Stands still, then returns what the models see now (saves the frame and one line for stops.csv)"""
        self.check_run()
        self.battery.check()
        time.sleep(SETTLE_SECONDS)
        self.frame = wait_for_new_frame(self.camera, self.camera.value)
        for _ in range(4):  # the obstacle and curve models run on every second frame
            percept = self.observe_next()
        cv2.imwrite(os.path.join(self.out, 'frame_%05d.jpg' % self.stops), self.frame)
        self.rows.append(dict(stop=self.stops, stage=self.stage, heading=self.heading,
                              lane_visible=round(percept['lane_visible'], 3), lane_x=round(percept['lane_x'], 3),
                              lane_aligned=int(percept['lane_aligned']), tape_row=tape_row(self.frame),
                              tape_close=int(tape_close(self.frame))))
        self.stops += 1
        return percept

    def turn(self, direction):
        """One turn pulse, direction -1 left, +1 right, and a look"""
        def wheels(elapsed):
            spin = direction * turn_speed(elapsed)
            return spin, -spin
        self.pulse(TURN_PULSE, wheels)
        self.heading -= direction
        return self.look()

    def confirmed(self, test, percept):
        """True if the test holds for this look and the next CONFIRM_FRAMES frames"""
        if not (test(percept) and tape_close(self.frame)):
            return False
        return all(test(self.observe_next()) and tape_close(self.frame) for _ in range(CONFIRM_FRAMES))

    def cup_blocks(self, percept):
        return any(band_cm(band) <= CUP_STOP_CM and abs(band[0]) < CUP_STOP_X for band in percept['cup_bands'])

    def undo(self, history):
        """Drives the last UNDO_SECONDS of commands backwards, newest first, until the lane is seen again. True if found"""
        self.stage = 'undo'
        remaining = UNDO_SECONDS
        for dt, left, right in reversed(list(history)):
            if remaining <= 0.0:
                break
            remaining -= dt
            with self.watchdog.lock:
                self.robot.set_motors(-left, -right)
            self.watchdog.feed()
            if lane_back(self.observe_next()) and tape_close(self.frame):
                break
        with self.watchdog.lock:
            self.robot.stop()
        return self.confirmed(lane_back, self.look())

    def sweep(self, side):
        """Turns about 100 degrees to each side, first to `side` (-1 left, +1 right), and back. True if found"""
        self.stage = 'sweep'
        for direction, pulses in ((side, SWEEP_PULSES), (-side, 2 * SWEEP_PULSES), (side, SWEEP_PULSES)):
            for _ in range(pulses):
                if self.confirmed(on_lane, self.turn(direction)):
                    return True
        return False

    def accepted(self, percept, any_way):
        """'search' or 'search_any' if the lane is found here, else None. The wrong way along it counts only if any_way"""
        if not any_way and not right_way(self.heading):
            return None
        if not self.confirmed(on_lane, percept):
            return None
        return 'search' if right_way(self.heading) else 'search_any'

    def search_round(self, any_way):
        """One scan and one push across the nearest tape. Returns a result of run(), or 'again'"""
        self.stage = 'search'
        amounts = []  # lowest tape row after each pulse of the scan
        for _ in range(PULSES_PER_TURN):
            percept = self.turn(-1)
            found = self.accepted(percept, any_way)
            if found:
                return found
            amounts.append(0 if self.cup_blocks(percept) else tape_row(self.frame))  # never head for a cup
        best = max(amounts)
        left = amounts.index(best) + 1  # pulses to the left from the end of the scan (a full turn: back at its start)
        direction, steps = (-1, left) if left <= PULSES_PER_TURN - left else (1, PULSES_PER_TURN - left)
        for _ in range(steps):
            percept = self.turn(direction)
        for _ in range(NUDGES):
            if tape_row(self.frame) >= best - TAPE_SLACK:
                break
            percept = self.turn(direction)
        over_tape, past = False, 0
        for _ in range(PUSHES):
            if self.cup_blocks(percept):  # a cup came into view on the way: the next round picks another heading
                break
            self.pulse(PUSH_PULSE, lambda elapsed: (PUSH_SPEED, PUSH_SPEED))
            percept = self.look()
            found = self.accepted(percept, any_way)
            if found:
                return found
            at_bottom = lane_mask.blue_mask(self.frame)[int(BOTTOM_ROW * self.frame.shape[0]):].any()
            over_tape = over_tape or at_bottom
            past = past + 1 if over_tape and not at_bottom else 0
            if past >= PAST_TAPE:
                break
        return 'again'

    def stages(self, history, side):
        """Tries undo, sweep and search in turn. Returns a result: FOUND or 'again'"""
        now = time.time()
        if now - self.last_undo > UNDO_RESET:
            self.undos = 0
        if history and self.undos < UNDO_TRIES:
            self.undos += 1
            self.last_undo = now
            if self.undo(history):
                return 'undo'
        if side != 0 and self.sweep(side):
            return 'sweep'
        result = 'again'
        for number in range(ROUNDS):
            result = self.search_round(any_way=number == ROUNDS - 1)
            if result != 'again':
                break
        return result

    def run(self, history=(), side=0, deadline=None, stop_event=None):
        """Finds the lane. history: recent (dt, left, right) wheel commands, empty when undoing them makes no sense;
        side: where the lane should be (-1 left, +1 right, 0 unknown: no sweep); deadline: time.time() at which the run
        ends. Returns a result (FOUND or 'again'); raises StopRecovery when the run ends meanwhile"""
        self.deadline, self.stop_event = deadline, stop_event
        self.frame = wait_for_new_frame(self.camera, self.camera.value)
        self.out = os.path.join(DATASET_ROOT, time.strftime('%Y-%m-%d_%H-%M-%S') + '_find_lane')
        os.makedirs(self.out, exist_ok=True)
        self.stops, self.heading, self.rows = 0, 0, []
        try:
            result = self.stages(history, side)
        finally:
            with open(os.path.join(self.out, 'stops.csv'), 'w') as f:
                writer = csv.DictWriter(f, STOP_COLUMNS)
                writer.writeheader()
                writer.writerows(self.rows)
        print('line recovery: %s after %d stops' % (result, self.stops))
        return result


def main():
    from jetbot import Camera, Robot
    from perception import Perception

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
    sys.exit(0 if result in FOUND else 1)


if __name__ == '__main__':
    main()
