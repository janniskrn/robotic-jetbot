"""Decision: the state machine (Task 6). Which state the robot is in, from what perception sees.

States (names from PROJECT_GUIDE_1.md), highest priority first; the full table with entry condition, action,
exit condition and priority, plus the diagram, is in STATE_MACHINE.md and must stay in step with this file.
    HALT                lane lost, recovery timeout, a swerve phase that does not reach its camera mark in time
                        (battery and camera stops are in drive.py): the run ends
    OBSTACLE_AVOIDANCE  a cup is close ahead in the lane: swerve to the inside of the oval in AVOID_PHASES (stop, turn
                        90 degrees, curve around the cup, turn back onto the lane; control.avoid), the turns and the
                        curve each ended by a camera mark
    ROAD_RECOVERY       after the swerve: steer on the lane until it is seen near the center and aligned for a few steps
    STOP                required stop: with stop_only, brake, back up if the cup is too close, wait until it is gone
    SLOW_DOWN           sharp curve ahead, or a cup in the lane within about 60 cm: lane following with the speed
                        capped
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
AVOID_PHASES = ('brake', 'turn_out', 'arc', 'turn_in')  # the swerve (AVOID3), in this order
STOP_PHASES = ('brake', 'back', 'wait')  # standing in front of a cup: back only when it is too close, once


def cup_ahead(percept):
    """(x, row) of the nearest red band about where the lane is, or None. A band beside the lane, or a second cup
    behind the first, does not count (HYBRID: the cup mask measures, the lane model says where the lane is)"""
    if percept['lane_visible'] < config.LANE_VISIBLE_THRESHOLD:
        return None
    for x, row, _ in percept['cup_bands']:  # nearest first
        if abs(x - percept['lane_x']) < config.CUP_IN_LANE:
            return x, row
    return None


def cup_close(percept):
    """True if the obstacle model sees a cup and the cup mask measures the nearest one in the lane at or closer than
    the trigger distance. The model's own row was up to 28 rows off with people behind the cup (S1d1)"""
    cup = cup_ahead(percept)
    return (percept['cup_visible'] >= config.OBSTACLE_VISIBLE_THRESHOLD
            and cup is not None and cup[1] >= config.OBSTACLE_ROW)


def cup_near(percept):
    """True if the obstacle model sees a cup and the nearest one in the lane is within the approach distance"""
    cup = cup_ahead(percept)
    return (percept['cup_visible'] >= config.OBSTACLE_VISIBLE_THRESHOLD
            and cup is not None and cup[1] >= config.APPROACH_ROW)


def cup_gone(percept):
    """True if no red band is at or below the clear row anywhere: standing in front of the cup, it can hide the lane,
    so this must not need the lane"""
    return all(row < config.OBSTACLE_CLEAR_ROW for _, row, _ in percept['cup_bands'])


def reached_horizontal(angle, direction, early):
    """True if a turn (direction -1 left, +1 right) has brought the lane edge ahead to within `early` degrees before
    horizontal (lane_mask.tape_angle): turning left its angle rises toward 0, turning right it falls. A window, not
    a limit: a lane line leaning the other way (+39 degrees at one start) must not end a left turn"""
    return angle is not None and 0 <= direction * angle <= early


def edge_left_view(last, angle, direction):
    """True if the lane edge, last seen within TURN_LOST degrees of horizontal, has left the image: it is gone, or the
    largest piece is now another, steeper one. The robot then stands close to the edge, which is horizontal below the
    camera's view (run avoid3_ccw_1)"""
    return (reached_horizontal(last, direction, config.TURN_LOST)
            and (angle is None or direction * angle > direction * last + config.TURN_JUMP))


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
        self.avoid_phase = AVOID_PHASES[0]
        self.phase_since = 0.0
        self.edge_angle = None    # last tape angle seen in the turn out
        self.stop_phase = STOP_PHASES[0]
        self.backed = False       # backed up once in this stop
        self.curve_sum = 0.0      # sum of curve_dir in curves: negative = curves turn left = counterclockwise

    def pass_side(self):
        """Side to pass a cup on: the inside of the oval (PASS), left until the direction is known"""
        if self.fixed_side:
            return self.fixed_side
        return 'right' if self.curve_sum > 0 else 'left'

    def enter(self, state, now):
        self.state, self.state_since = state, now
        if state == OBSTACLE_AVOIDANCE:
            self.avoid_phase, self.phase_since, self.edge_angle = AVOID_PHASES[0], now, None
        if state == STOP:
            self.stop_phase, self.phase_since, self.backed = STOP_PHASES[0], now, False

    def update_stop(self, percept, now):
        """Standing in front of the cup: a short reverse pulse against coasting, then wait; if the cup turns out to
        be closer than BACKUP_ROW (the camera shows the robot's position late), back up once until it is above
        BACKUP_TARGET_ROW. The nearest band anywhere: close in front, the cup can hide the lane"""
        bands = percept['cup_bands']
        row = bands[0][1] if bands else 0.0
        elapsed = now - self.phase_since
        if self.stop_phase == 'brake' and elapsed >= config.BRAKE[1]:
            self.stop_phase, self.phase_since = 'wait', now
        elif self.stop_phase == 'wait' and not self.backed and row >= config.BACKUP_ROW:
            self.stop_phase, self.phase_since, self.backed = 'back', now, True
        elif self.stop_phase == 'back' and (row < config.BACKUP_TARGET_ROW or elapsed >= config.BACKUP_MAX):
            self.stop_phase, self.phase_since = 'wait', now

    def update_avoidance(self, percept, now):
        """Moves through the swerve phases. Passing on the left: stand still briefly, turn left until the lane edge
        looks horizontal or leaves the image near horizontal (90 degrees), curve right until the edge ahead looks
        horizontal again (facing the lane), turn left until the lane is found. Passing on the right mirrored. The
        marks come from the lane mask (HYBRID). A phase that takes too long: HALT"""
        elapsed = now - self.phase_since
        toward = -1 if self.pass_side() == 'left' else 1  # turn direction toward the pass side (-1 left)
        angle = percept['tape_angle']
        if self.avoid_phase == 'brake':
            done, limit = elapsed >= config.AVOID_BRAKE, config.AVOID_BRAKE
        elif self.avoid_phase == 'turn_out':
            done = (reached_horizontal(angle, toward, config.TURN_EARLY)
                    or edge_left_view(self.edge_angle, angle, toward))
            limit = config.TURN_OUT_MAX
            self.edge_angle = angle
        elif self.avoid_phase == 'arc':  # the lane edge is horizontal ahead at its start: ARC_MIN
            done = elapsed >= config.ARC_MIN and reached_horizontal(angle, -toward, config.ARC_EARLY)
            limit = config.ARC_MAX
        else:
            done, limit = lane_found(percept), config.TURN_IN_MAX
        if done and self.avoid_phase == AVOID_PHASES[-1]:
            self.centered_frames = 0
            self.enter(ROAD_RECOVERY, now)
        elif done:
            self.avoid_phase = AVOID_PHASES[AVOID_PHASES.index(self.avoid_phase) + 1]
            self.phase_since = now
        elif elapsed >= limit:
            self.enter(HALT, now)  # a stall, or the mark was not seen: do not drive on blind

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

        close = cup_close(percept)
        self.close_frames = self.close_frames + 1 if close else 0
        if self.stop_only:
            # drive on only with the lane in sight: a hand measuring in front of the camera hid the cup and the lane,
            # and the robot drove on blind (run stop_s1d2_2)
            clear = cup_gone(percept) and percept['lane_visible'] >= config.LANE_VISIBLE_THRESHOLD
            self.clear_frames = self.clear_frames + 1 if clear else 0
            if self.state == STOP and self.clear_frames >= config.OBSTACLE_CLEAR_FRAMES:
                self.enter(ROAD_FOLLOWING, now)
            elif self.state != STOP and self.close_frames >= config.OBSTACLE_FRAMES:
                self.enter(STOP, now)
            if self.state == STOP:
                self.update_stop(percept, now)
                self.lost_since = None  # standing still is not losing the lane
                return STOP
        elif self.close_frames >= config.OBSTACLE_FRAMES:
            self.enter(OBSTACLE_AVOIDANCE, now)
            return self.state

        # following the lane: ROAD_FOLLOWING or SLOW_DOWN (sharp curve, or a cup ahead: less rolling on after a stop)
        p_sharp = percept['curve_probs'][2]
        near = cup_near(percept)
        if self.state == ROAD_FOLLOWING and (p_sharp > config.SLOW_DOWN_ENTER or near):
            self.enter(SLOW_DOWN, now)
        elif self.state == SLOW_DOWN and p_sharp < config.SLOW_DOWN_EXIT and not near:
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
