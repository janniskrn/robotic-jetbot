"""Decision: the state machine (Task 6). Which state the robot is in, from what perception sees.

States (names from PROJECT_GUIDE_1.md), highest priority first; the full table with entry condition, action,
exit condition and priority, plus the diagram, is in STATE_MACHINE.md and must stay in step with this file.
    HALT                lane lost, recovery timeout, cup still beside after the pass time (battery and camera stops
                        are in drive.py): the run ends
    OBSTACLE_AVOIDANCE  a cup is close ahead in the lane: swerve to the inside of the oval in phases
                        (config.AVOID_STEPS, control.avoid); the pass lasts until the cup mask sees the cup behind
    ROAD_RECOVERY       after the swerve: back to the lane until it is seen near the center and aligned for a few steps
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


def cup_beside(percept, pass_side):
    """True if the cup mask sees a large red band on the cup's side of the image while passing it (HYBRID): passing
    on the left, the cup is on the right; a small band is a cup further along the track. The mask also finds the
    band at the image edge, where the model misses cups"""
    x = percept['mask_cup_x']
    return (percept['mask_cup_pixels'] >= config.AVOID_BESIDE_PIXELS
            and (x > 0 if pass_side == 'left' else x < 0))


def lane_found(percept):
    """True if the lane is seen near the center and the robot points along it. lane_x alone was near 0 when the
    robot stood crosswise to the lane (run avoid_ccw_1); the lane mask's two-line check rejects that"""
    return (percept['lane_visible'] >= config.LANE_VISIBLE_THRESHOLD and percept['lane_aligned']
            and abs(percept['lane_x']) < config.RECOVER_CENTERED)


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
        self.centered_frames = 0  # control steps in a row with the lane found (ROAD_RECOVERY)
        self.avoid_phase = 0      # index of the current swerve phase in config.AVOID_STEPS
        self.phase_since = 0.0
        self.cup_seen_at = 0.0    # last time the cup mask saw the cup beside the robot (pass phase)
        self.curve_sum = 0.0      # sum of curve_dir in curves: negative = curves turn left = counterclockwise

    def pass_side(self):
        """Side to pass a cup on: the inside of the oval (PASS), left until the direction is known"""
        if self.fixed_side:
            return self.fixed_side
        return 'right' if self.curve_sum > 0 else 'left'

    def enter(self, state, now):
        self.state, self.state_since = state, now
        if state == OBSTACLE_AVOIDANCE:
            self.avoid_phase, self.phase_since = 0, now

    def avoid_turn(self):
        """Turn of the current swerve phase: +1 toward the pass side, -1 away from it, 0 straight"""
        return config.AVOID_STEPS[self.avoid_phase][2]

    def update_avoidance(self, percept, now):
        """Moves through the swerve phases. All are timed except the pass, which lasts at least its time and then
        until the cup has not been seen beside the robot for AVOID_PASS_CLEAR seconds"""
        name, seconds, _ = config.AVOID_STEPS[self.avoid_phase]
        elapsed = now - self.phase_since
        done = elapsed >= seconds
        if name == 'pass':
            beside = cup_beside(percept, self.pass_side())
            if beside:
                self.cup_seen_at = now
                if elapsed > config.AVOID_PASS_MAX:
                    self.enter(HALT, now)  # the cup is still beside the robot: turning in would hit it
                    return
            done = done and now - self.cup_seen_at >= config.AVOID_PASS_CLEAR
        if not done:
            return
        self.avoid_phase += 1
        # timed phases keep their exact length (a frame late here does not lengthen the next pivot); the pass ends now
        self.phase_since = now if name == 'pass' else self.phase_since + seconds
        self.cup_seen_at = now
        if self.avoid_phase == len(config.AVOID_STEPS):
            self.centered_frames = 0
            self.enter(ROAD_RECOVERY, now)

    def update(self, percept, now):
        """Returns the state for this frame"""
        if self.state == HALT:
            return HALT
        if self.state == OBSTACLE_AVOIDANCE:  # the lane is not asked until the swerve is done
            self.update_avoidance(percept, now)
            return self.state
        if self.state == ROAD_RECOVERY:
            self.centered_frames = self.centered_frames + 1 if lane_found(percept) else 0
            if self.centered_frames >= config.RECOVER_FRAMES:  # a distant or crosswise lane does not count
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
