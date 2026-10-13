"""Decision: what the robot should do now, from what perception sees.

Modes (D9b, Task 2), highest priority first:
    STOP     lane lost, recovery timeout (battery and camera stops are in drive.py): motors off, the run ends
    AVOID    a cup is close ahead in the lane: timed swerve to the inside of the oval (control.avoid)
    RECOVER  after the swerve: back to the lane until it is seen near the center for a few steps
    BLOCKED  only with stop_only (demo of step 5.2): wait in front of the cup until it is gone
    FOLLOW   normal lane following
Entry and exit conditions are in update(); the table is in DECISIONS.md (AVOID1).
"""

import config

FOLLOW = 'FOLLOW'
BLOCKED = 'BLOCKED'
AVOID = 'AVOID'
RECOVER = 'RECOVER'
STOP = 'STOP'


def cup_close(percept):
    """True if the obstacle model sees a cup at or closer than the trigger distance"""
    return (percept['cup_visible'] >= config.OBSTACLE_VISIBLE_THRESHOLD
            and percept['cup_row'] >= config.OBSTACLE_ROW)


def cup_gone(percept):
    """True if no cup is seen, or only one clearly further away than the trigger distance"""
    return (percept['cup_visible'] < config.OBSTACLE_VISIBLE_THRESHOLD
            or percept['cup_row'] < config.OBSTACLE_CLEAR_ROW)


def cup_in_lane(percept):
    """True if the cup is about where the lane is (a cup beside the lane is not in the way)"""
    return (percept['lane_visible'] >= config.LANE_VISIBLE_THRESHOLD
            and abs(percept['cup_x'] - percept['lane_x']) < config.CUP_IN_LANE)


def avoid_duration():
    """Seconds the timed swerve takes (sum of its steps)"""
    return sum(seconds for _, seconds, _ in config.AVOID_STEPS)


class Decision(object):
    def __init__(self, stop_only=False, pass_side=None):
        """stop_only: wait in front of a cup instead of avoiding it.
        pass_side: 'left' or 'right' to fix the side; None measures the inside of the oval while driving."""
        self.stop_only = stop_only
        self.fixed_side = pass_side
        self.mode = FOLLOW
        self.mode_since = 0.0
        self.lost_since = None
        self.lane_seen = False
        self.close_frames = 0     # control steps in a row with a close cup (in the lane, unless stop_only)
        self.clear_frames = 0     # control steps in a row with the cup gone (BLOCKED only)
        self.centered_frames = 0  # control steps in a row with the lane near the center (RECOVER)
        self.curve_sum = 0.0      # sum of curve_dir in curves: negative = curves turn left = counterclockwise

    def pass_side(self):
        """Side to pass a cup on: the inside of the oval (PASS), left until the direction is known"""
        if self.fixed_side:
            return self.fixed_side
        return 'right' if self.curve_sum > 0 else 'left'

    def enter(self, mode, now):
        self.mode, self.mode_since = mode, now

    def update(self, percept, now):
        """Returns the mode for this frame"""
        if self.mode == AVOID:  # blind, timed: the camera is not asked until the swerve is done
            if now - self.mode_since >= avoid_duration():
                self.centered_frames = 0
                self.enter(RECOVER, now)
            return self.mode
        if self.mode == RECOVER:
            centered = (percept['lane_visible'] >= config.LANE_VISIBLE_THRESHOLD
                        and abs(percept['lane_x']) < config.RECOVER_CENTERED)
            self.centered_frames = self.centered_frames + 1 if centered else 0
            if self.centered_frames >= config.RECOVER_FRAMES:  # a distant lane is not centered: no false end
                self.lost_since = None
                self.close_frames = 0
                self.enter(FOLLOW, now)
            elif now - self.mode_since > config.RECOVER_TIMEOUT:
                self.enter(STOP, now)
            return self.mode
        if self.mode == STOP:
            return STOP

        close = cup_close(percept) and (self.stop_only or cup_in_lane(percept))
        self.close_frames = self.close_frames + 1 if close else 0
        if self.stop_only:
            self.clear_frames = self.clear_frames + 1 if cup_gone(percept) else 0
            if self.mode == BLOCKED and self.clear_frames >= config.OBSTACLE_CLEAR_FRAMES:
                self.enter(FOLLOW, now)
            elif self.mode != BLOCKED and self.close_frames >= config.OBSTACLE_FRAMES:
                self.enter(BLOCKED, now)
            if self.mode == BLOCKED:
                self.lost_since = None  # standing still is not losing the lane
                return BLOCKED
        elif self.close_frames >= config.OBSTACLE_FRAMES:
            self.enter(AVOID, now)
            return AVOID

        if percept['curve_probs'][1] + percept['curve_probs'][2] > 0.5:
            self.curve_sum += percept['curve_dir']
        if percept['lane_visible'] >= config.LANE_VISIBLE_THRESHOLD:
            self.lost_since = None
            self.lane_seen = True
            return FOLLOW
        if not self.lane_seen:
            self.enter(STOP, now)  # never start without seeing the lane (the grace time is only for short gaps)
            return STOP
        if self.lost_since is None:
            self.lost_since = now
        # a short gap (one or two bad frames) keeps following on the last steering
        if now - self.lost_since >= config.LANE_LOST_TIMEOUT:
            self.enter(STOP, now)
        return self.mode
