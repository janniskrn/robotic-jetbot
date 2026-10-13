"""Decision: the state machine (Task 6). Which state the robot is in, from what perception sees.

States (names from PROJECT_GUIDE_1.md), highest priority first; the full table with entry condition, action,
exit condition and priority, plus the diagram, is in STATE_MACHINE.md and must stay in step with this file.
    HALT                lane lost, recovery timeout (battery and camera stops are in drive.py): the run ends
    OBSTACLE_AVOIDANCE  a cup is close ahead in the lane: timed swerve to the inside of the oval (control.avoid)
    ROAD_RECOVERY       after the swerve: back to the lane until it is seen near the center for a few steps
    STOP                required stop: with stop_only, wait in front of a cup until it is gone
    SLOW_DOWN           sharp curve ahead: lane following with the speed capped
    ROAD_FOLLOWING      normal lane following
Planned, not coded until their perception exists: TURN_LEFT / TURN_RIGHT (intersection + sign), PARKING,
STOP for a STOP sign.
"""

import config

ROAD_FOLLOWING = 'ROAD_FOLLOWING'
SLOW_DOWN = 'SLOW_DOWN'
OBSTACLE_AVOIDANCE = 'OBSTACLE_AVOIDANCE'
ROAD_RECOVERY = 'ROAD_RECOVERY'
STOP = 'STOP'
HALT = 'HALT'
FOLLOWING = (ROAD_FOLLOWING, SLOW_DOWN)  # the states that follow the lane with the normal controller


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
        """stop_only: wait in front of a cup (STOP) instead of avoiding it.
        pass_side: 'left' or 'right' to fix the side; None measures the inside of the oval while driving."""
        self.stop_only = stop_only
        self.fixed_side = pass_side
        self.state = ROAD_FOLLOWING
        self.state_since = 0.0
        self.lost_since = None
        self.lane_seen = False
        self.close_frames = 0     # control steps in a row with a close cup (in the lane, unless stop_only)
        self.clear_frames = 0     # control steps in a row with the cup gone (STOP)
        self.centered_frames = 0  # control steps in a row with the lane near the center (ROAD_RECOVERY)
        self.curve_sum = 0.0      # sum of curve_dir in curves: negative = curves turn left = counterclockwise

    def pass_side(self):
        """Side to pass a cup on: the inside of the oval (PASS), left until the direction is known"""
        if self.fixed_side:
            return self.fixed_side
        return 'right' if self.curve_sum > 0 else 'left'

    def enter(self, state, now):
        self.state, self.state_since = state, now

    def update(self, percept, now):
        """Returns the state for this frame"""
        if self.state == HALT:
            return HALT
        if self.state == OBSTACLE_AVOIDANCE:  # blind, timed: the camera is not asked until the swerve is done
            if now - self.state_since >= avoid_duration():
                self.centered_frames = 0
                self.enter(ROAD_RECOVERY, now)
            return self.state
        if self.state == ROAD_RECOVERY:
            centered = (percept['lane_visible'] >= config.LANE_VISIBLE_THRESHOLD
                        and abs(percept['lane_x']) < config.RECOVER_CENTERED)
            self.centered_frames = self.centered_frames + 1 if centered else 0
            if self.centered_frames >= config.RECOVER_FRAMES:  # a distant lane is not centered: no false end
                self.lost_since = None
                self.close_frames = 0
                self.enter(ROAD_FOLLOWING, now)
            elif now - self.state_since > config.RECOVER_TIMEOUT:
                self.enter(HALT, now)
            return self.state

        close = cup_close(percept) and (self.stop_only or cup_in_lane(percept))
        self.close_frames = self.close_frames + 1 if close else 0
        if self.stop_only:
            self.clear_frames = self.clear_frames + 1 if cup_gone(percept) else 0
            if self.state == STOP and self.clear_frames >= config.OBSTACLE_CLEAR_FRAMES:
                self.enter(ROAD_FOLLOWING, now)
            elif self.state != STOP and self.close_frames >= config.OBSTACLE_FRAMES:
                self.enter(STOP, now)
            if self.state == STOP:
                self.lost_since = None  # standing still is not losing the lane
                return STOP
        elif self.close_frames >= config.OBSTACLE_FRAMES:
            self.enter(OBSTACLE_AVOIDANCE, now)
            return self.state

        # following the lane: ROAD_FOLLOWING or SLOW_DOWN
        p_sharp = percept['curve_probs'][2]
        if self.state == ROAD_FOLLOWING and p_sharp > config.SLOW_DOWN_ENTER:
            self.enter(SLOW_DOWN, now)
        elif self.state == SLOW_DOWN and p_sharp < config.SLOW_DOWN_EXIT:
            self.enter(ROAD_FOLLOWING, now)
        if percept['curve_probs'][1] + p_sharp > 0.5:
            self.curve_sum += percept['curve_dir']
        if percept['lane_visible'] >= config.LANE_VISIBLE_THRESHOLD:
            self.lost_since = None
            self.lane_seen = True
            return self.state
        if not self.lane_seen:
            self.enter(HALT, now)  # never start without seeing the lane (the grace time is only for short gaps)
            return HALT
        if self.lost_since is None:
            self.lost_since = now
        # a short gap (one or two bad frames) keeps following on the last steering
        if now - self.lost_since >= config.LANE_LOST_TIMEOUT:
            self.enter(HALT, now)
        return self.state
