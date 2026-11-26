"""Decision: the state machine (Task 6). Picks the robot's state from what perception sees.

States, highest priority first (table and diagram: STATE_MACHINE.md, keep it in step with this file):
    HALT                the run ends (recovery failed, a cup in the way of the swerve)
    OBSTACLE_AVOIDANCE  a cup close ahead: swerve around it on the inside of the oval (AVOID_PHASES)
    LINE_RECOVERY       the lane is lost: find_lane.py looks for it, drive.py runs it
    ROAD_RECOVERY       after the swerve: steer onto the lane until it is centered and aligned
    STOP                stop_only mode: wait in front of the cup until it is gone
    SLOW_DOWN           sharp curve or a cup ahead: lane following with the speed capped
    ROAD_FOLLOWING      normal lane following
Planned: TURN_LEFT / TURN_RIGHT (intersection + sign), PARKING, STOP for a STOP sign.
"""

import math

import config

ROAD_FOLLOWING = 'ROAD_FOLLOWING'
SLOW_DOWN = 'SLOW_DOWN'
OBSTACLE_AVOIDANCE = 'OBSTACLE_AVOIDANCE'
ROAD_RECOVERY = 'ROAD_RECOVERY'
LINE_RECOVERY = 'LINE_RECOVERY'
STOP = 'STOP'
HALT = 'HALT'
FOLLOWING = (ROAD_FOLLOWING, SLOW_DOWN)  # the states that follow the lane with the normal controller
AVOID_PHASES = ('brake', 'turn_out', 'arc', 'turn_in')  # the swerve (AVOID3), in this order
TURN_BACK = 'turn_back'  # extra phase: turn_in went past the lane, turn the other way (TURN1)
STOP_PHASES = ('brake', 'back', 'wait')  # standing in front of a cup: back up once if it is too close
PHASE_LIMITS = {'brake': config.AVOID_BRAKE, 'turn_out': config.TURN_OUT_MAX, 'arc': config.ARC_MAX,
                'turn_in': config.TURN_IN_MAX, TURN_BACK: config.TURN_BACK_MAX}  # seconds before the lane counts as lost


# --- what the camera shows, as yes/no tests (HYBRID: the models recognize, the color masks measure) ---

def sees_lane(percept):
    return percept['lane_visible'] >= config.LANE_VISIBLE_THRESHOLD


def band_cm(band):
    """Distance in cm to a red band (x, row, pixels) from its size (OBST9). Cut off by the image edge: 0, right in front"""
    return 0.0 if band[1] >= config.BAND_CUT_ROW else config.CUP_SIZE_CM / math.sqrt(band[2])


def cup_ahead(percept):
    """The nearest red band in the robot's way (in the lane, or straight ahead: a close cup hides the lane), or None"""
    for band in percept['cup_bands']:  # nearest first
        if abs(band[0]) < config.CUP_DEAD_AHEAD or (sees_lane(percept)
                                                     and abs(band[0] - percept['lane_x']) < config.CUP_IN_LANE):
            return band
    return None


def cup_close(percept):
    """True if the obstacle model sees a cup and the nearest one in the way is within the trigger distance"""
    cup = cup_ahead(percept)
    return (percept['cup_visible'] >= config.OBSTACLE_VISIBLE_THRESHOLD
            and cup is not None and band_cm(cup) <= config.OBSTACLE_CM)


def cup_near(percept):
    """True if a cup in the way is within the approach distance (cup mask alone: the model misses far cups, OBST8)"""
    cup = cup_ahead(percept)
    return cup is not None and band_cm(cup) <= config.APPROACH_CM


def cup_gone(percept):
    """True if no red band is within the clear distance anywhere (the cup can hide the lane, so no lane needed)"""
    return all(band_cm(band) > config.OBSTACLE_CLEAR_CM for band in percept['cup_bands'])


def near_band(percept):
    """The nearest red band close enough to be the cup being passed, or None"""
    bands = percept['cup_bands']
    return bands[0] if bands and band_cm(bands[0]) <= config.CUP_NEAR_CM else None


def cup_left_view(last_x, band, toward):
    """True if the cup was last seen at the image edge away from the turn and is gone now: about 70-85 degrees turned"""
    return band is None and last_x is not None and -toward * last_x >= config.CUP_EDGE


def cup_beside_curve(band, toward):
    """True if the cup is in view on the side the curve bends to (or in front): drive straight past it first"""
    return band is not None and -toward * band[0] > -0.1


def cup_in_the_way(band):
    """True if a band is very close in the middle of the image during the curve: stop rather than hit it"""
    return band is not None and band_cm(band) <= config.ARC_STOP_CM and abs(band[0]) < config.ARC_STOP_X


def reached_horizontal(angle, direction, early):
    """True if a turn (direction -1 left, +1 right) brought the lane edge ahead to within `early` degrees before
    horizontal. A window, not a limit: a line leaning the other way must not end the turn"""
    return angle is not None and 0 <= direction * angle <= early


def edge_left_view(last, angle, direction):
    """True if the lane edge, last seen close to horizontal, has left the image (gone, or another steeper piece now)"""
    return (reached_horizontal(last, direction, config.TURN_LOST)
            and (angle is None or direction * angle > direction * last + config.TURN_JUMP))


def lane_found(percept, centered=config.RECOVER_CENTERED):
    """True if the lane is seen within `centered` of the middle and the robot points along it (two-line check)"""
    return sees_lane(percept) and percept['lane_aligned'] and abs(percept['lane_x']) < centered


def lane_near(percept):
    """True if the lane model is sure and sees the lane near the middle, without the two-line check (curves fail it)"""
    return percept['lane_visible'] >= config.TURN_BACK_SURE and abs(percept['lane_x']) < config.TURN_IN_CENTERED


def bends_our_way(percept, direction):
    """True if the curve model sees the lane bend the way the robot drives the oval (DIR1): it is our lane"""
    probs, turn = percept['curve_probs'], percept['curve_dir']
    return (direction is not None and probs[1] + probs[2] >= 0.5 and abs(turn) >= config.DIRECTION_MIN_DIR
            and (turn > 0) == (direction == 'cw'))


def curve_inside(percept):
    """'left' or 'right': the inside of the curve the curve model sees, or None on a straight (PASS3)"""
    probs, turn = percept['curve_probs'], percept['curve_dir']
    if probs[1] + probs[2] < 0.5 or abs(turn) < config.DIRECTION_MIN_DIR:
        return None
    return 'left' if turn < 0 else 'right'


def count(frames, condition):
    """Steps in a row with the condition true"""
    return frames + 1 if condition else 0


class Decision(object):
    def __init__(self, stop_only=False, pass_side=None, line_recovery=False):
        """stop_only: wait in front of a cup (STOP) instead of avoiding it.
        pass_side: 'left' or 'right' to fix the side; None takes the inside of the oval.
        line_recovery: find a lost lane again (LINE_RECOVERY) instead of ending the run (HALT)."""
        self.line_recovery = line_recovery
        self.stop_only = stop_only
        self.fixed_side = pass_side
        self.state = ROAD_FOLLOWING
        self.state_since = 0.0
        self.lost_since = None    # time the lane was last lost (short gaps are bridged)
        self.close_frames = 0     # steps in a row with a close cup
        self.clear_frames = 0     # steps in a row with the cup gone (STOP)
        self.centered_frames = 0  # steps in a row with the lane found (ROAD_RECOVERY)
        self.recover_seen_at = None  # last time the lane was seen in ROAD_RECOVERY (RECOV3)
        self.direction = None     # 'cw' or 'ccw', from the first sharp curve, kept for the run (DIR1)
        self.sharp_steps = 0      # steps in a row with a sharp curve the same way: + right, - left
        # the swerve
        self.avoid_phase = AVOID_PHASES[0]
        self.phase_since = 0.0
        self.edge_angle = None    # last tape angle seen
        self.turn_cup_x = None    # last x of the cup in the turn out
        self.go_straight = False  # the curve is paused ('pass'): the cup is beside it, or it took long
        self.tape_under = False   # the lane's border has been under the robot's nose during the curve
        self.arc_turned = 0.0     # seconds the curve has actually curved (ARC_TURN_MIN)
        self.arc_last = 0.0       # time of the last step in the curve
        self.curve_side = None    # the inside of the curve the cup stands in, None on a straight (PASS3)
        self.cup_in_curve = False  # the cup stands in a curve bending toward the pass side (ARC3)
        self.crossed_at = None    # time the lane's border was crossed in the curve (ARC4)
        self.past_from = None     # the curve has ended: straight on until ARC_PAST after this time (ARC2, ARC4)
        self.turn_lane_at = None  # last time the lane was seen in turn_in
        # the stop (stop_only)
        self.stop_phase = STOP_PHASES[0]
        self.backed = False       # backed up once in this stop

    def pass_side(self):
        """Side to pass a cup on: in a curve always its inside (PASS3), else the inside of the oval (PASS), left until
        the direction is known"""
        if self.fixed_side:
            return self.fixed_side
        if self.curve_side:
            return self.curve_side
        return 'right' if self.direction == 'cw' else 'left'

    def avoid_action(self):
        """What the wheels do in this swerve phase: the phase, or 'pass' while the curve is paused"""
        return 'pass' if self.avoid_phase == 'arc' and self.go_straight else self.avoid_phase

    def enter(self, state, now):
        self.state, self.state_since = state, now
        if state == OBSTACLE_AVOIDANCE:
            self.avoid_phase, self.phase_since, self.edge_angle = AVOID_PHASES[0], now, None
            self.turn_cup_x, self.go_straight, self.tape_under = None, False, False
            self.turn_lane_at, self.cup_in_curve, self.crossed_at, self.past_from = None, False, None, None
            self.curve_side = None  # decided at the end of the brake
        if state == STOP:
            self.stop_phase, self.phase_since, self.backed = STOP_PHASES[0], now, False
        if state == ROAD_RECOVERY:
            self.recover_seen_at = None

    def short_gap(self, now):
        """True if ROAD_RECOVERY saw the lane within LANE_LOST_TIMEOUT: a flicker, held into the curve like in
        following, not the search turn away from the pass side (RECOV3)"""
        return self.recover_seen_at is not None and now - self.recover_seen_at <= config.LANE_LOST_TIMEOUT

    def lane_gone(self, now):
        """The lane is lost: find it again, or end the run"""
        self.enter(LINE_RECOVERY if self.line_recovery else HALT, now)

    def line_recovery_done(self, found, now):
        """Called by drive.py when the search has ended. The driving direction is kept"""
        self.enter(ROAD_FOLLOWING if found else HALT, now)
        self.lost_since, self.close_frames = None, 0

    def update(self, percept, now):
        """Returns the state for this frame"""
        if self.state == OBSTACLE_AVOIDANCE:
            self.update_avoidance(percept, now)
        elif self.state == ROAD_RECOVERY:
            self.update_recovery(percept, now)
        elif self.state not in (HALT, LINE_RECOVERY):  # those two: drive.py runs the search and reports back
            self.update_driving(percept, now)
        return self.state

    # --- ROAD_FOLLOWING, SLOW_DOWN, STOP ---

    def update_driving(self, percept, now):
        self.close_frames = count(self.close_frames, cup_close(percept))
        if self.stop_only:
            self.update_stop_only(percept, now)
            if self.state == STOP:
                return
        elif self.close_frames >= config.OBSTACLE_FRAMES:
            self.enter(OBSTACLE_AVOIDANCE, now)
            return
        p_sharp, near = percept['curve_probs'][2], cup_near(percept)
        if self.state == ROAD_FOLLOWING and (p_sharp > config.SLOW_DOWN_ENTER or near):
            self.enter(SLOW_DOWN, now)
        elif self.state == SLOW_DOWN and p_sharp < config.SLOW_DOWN_EXIT and not near:
            self.enter(ROAD_FOLLOWING, now)
        if self.direction is None:
            self.learn_direction(percept)
        # drive.py starts only with the lane in sight (FIX1: one weak first frame used to end the run here)
        if sees_lane(percept):
            self.lost_since = None
        elif self.lost_since is None:
            self.lost_since = now
        elif now - self.lost_since >= config.LANE_LOST_TIMEOUT:  # a short gap keeps the last steering
            self.lane_gone(now)

    def learn_direction(self, percept):
        """Sets the driving direction at the first sharp curve: on an oval all curves bend the same way, right = cw"""
        turn = percept['curve_dir']
        if percept['curve_probs'][2] < config.DIRECTION_SHARP or abs(turn) < config.DIRECTION_MIN_DIR:
            self.sharp_steps = 0
            return
        sign = 1 if turn > 0 else -1
        self.sharp_steps = self.sharp_steps + sign if self.sharp_steps * sign >= 0 else sign
        if abs(self.sharp_steps) >= config.DIRECTION_FRAMES:
            self.direction = 'cw' if sign > 0 else 'ccw'

    def update_stop_only(self, percept, now):
        """Stops for a close cup, drives on once it is gone and the lane is in sight (a hand can hide both)"""
        self.clear_frames = count(self.clear_frames, cup_gone(percept) and sees_lane(percept))
        if self.state == STOP and self.clear_frames >= config.OBSTACLE_CLEAR_FRAMES:
            self.enter(ROAD_FOLLOWING, now)
        elif self.state != STOP and self.close_frames >= config.OBSTACLE_FRAMES:
            self.enter(STOP, now)
        if self.state == STOP:
            self.update_stop(percept, now)
            self.lost_since = None  # standing still is not losing the lane

    def update_stop(self, percept, now):
        """Brake pulse, then wait; if the cup is closer than BACKUP_CM, back up once to BACKUP_TARGET_CM"""
        bands = percept['cup_bands']
        cm = band_cm(bands[0]) if bands else float('inf')
        elapsed = now - self.phase_since
        if self.stop_phase == 'brake' and elapsed >= config.BRAKE[1]:
            self.stop_phase, self.phase_since = 'wait', now
        elif self.stop_phase == 'wait' and not self.backed and cm <= config.BACKUP_CM:
            self.stop_phase, self.phase_since, self.backed = 'back', now, True
        elif self.stop_phase == 'back' and (cm > config.BACKUP_TARGET_CM or elapsed >= config.BACKUP_MAX):
            self.stop_phase, self.phase_since = 'wait', now

    # --- ROAD_RECOVERY ---

    def update_recovery(self, percept, now):
        self.close_frames = count(self.close_frames, cup_close(percept))
        if self.close_frames >= config.OBSTACLE_FRAMES:  # the swerve did not get past the cup: swerve again (RECOV2)
            self.enter(OBSTACLE_AVOIDANCE, now)
            return
        self.centered_frames = count(self.centered_frames, lane_found(percept))
        if sees_lane(percept):
            self.recover_seen_at = now
        if self.centered_frames >= config.RECOVER_FRAMES:
            self.lost_since, self.close_frames = None, 0
            self.enter(ROAD_FOLLOWING, now)
        elif now - self.state_since > config.RECOVER_TIMEOUT:
            self.lane_gone(now)

    # --- OBSTACLE_AVOIDANCE: each phase ends on a camera mark (no encoders), or after its time limit ---

    def update_avoidance(self, percept, now):
        """Passing on the left (right is mirrored): stand still; turn left about 90 degrees; curve right around the cup
        until about 90 degrees back and facing the lane; turn left until the lane is found, along it"""
        phase, elapsed = self.avoid_phase, now - self.phase_since
        toward = -1 if self.pass_side() == 'left' else 1  # turn direction toward the pass side
        done = {'brake': self.brake_done, 'turn_out': self.turn_out_done, 'arc': self.arc_done,
                'turn_in': self.turn_in_done, TURN_BACK: self.turn_back_done}[phase](percept, now, elapsed, toward)
        if self.state != OBSTACLE_AVOIDANCE or self.avoid_phase != phase:  # the phase itself switched (HALT, TURN_BACK)
            return
        if done and phase in ('turn_in', TURN_BACK):
            self.centered_frames = self.close_frames = 0  # the cup that started this swerve does not count again
            self.enter(ROAD_RECOVERY, now)
        elif done:
            if phase == 'brake':  # standing still before the turn: the curve model sees where the cup stands
                self.curve_side = curve_inside(percept)
                self.cup_in_curve = self.curve_side is not None and self.pass_side() == self.curve_side
            self.avoid_phase = AVOID_PHASES[AVOID_PHASES.index(phase) + 1]
            self.phase_since = self.arc_last = now
            self.arc_turned = 0.0
        elif elapsed >= PHASE_LIMITS[phase]:
            self.lane_gone(now)  # a stall, or the mark was not seen: do not drive on blind

    def brake_done(self, percept, now, elapsed, toward):
        return elapsed >= config.AVOID_BRAKE

    def turn_out_done(self, percept, now, elapsed, toward):
        """The cup has left the image sideways, or without a cup: the lane edge looks horizontal or has left the image"""
        angle, band = percept['tape_angle'], near_band(percept)
        done = cup_left_view(self.turn_cup_x, band, toward) or (band is None and (
            reached_horizontal(angle, toward, config.TURN_EARLY) or edge_left_view(self.edge_angle, angle, toward)))
        self.edge_angle = angle
        if band is not None:
            self.turn_cup_x = band[0]
        return done

    def arc_done(self, percept, now, elapsed, toward):
        """The lane's border was crossed, the lane is found, or the edge ahead looks horizontal or has left the image;
        then straight on until the far border comes as near as from the lane's middle (ARC7), at most ARC_PAST after the
        border crossing (ARC2, ARC4, ARC5; in a curve ARC_PAST_CURVE, and not at all with the far line ahead).
        On a straight only after about 90 degrees of curve (ARC1: before that a line ahead is another one) or once the
        crossing brought the far border that near (ARC7); with the cup in a curve bending toward the pass side the road
        comes back early, so the earlier marks count (ARC3)"""
        angle, band = percept['tape_angle'], near_band(percept)
        if cup_in_the_way(band):
            self.enter(HALT, now)
            return False
        past = config.ARC_PAST_CURVE if self.cup_in_curve else config.ARC_PAST
        under = percept['tape_row'] >= config.TAPE_UNDER_ROW
        self.tape_under = self.tape_under or (under and elapsed >= config.ARC_MIN)  # at the start it is the old lane
        crossed = self.tape_under and percept['tape_row'] < config.TAPE_PAST_ROW
        if crossed and self.crossed_at is None:
            self.crossed_at = now
        middle = self.crossed_at is not None and percept['tape_row'] >= config.TAPE_MIDDLE_ROW  # far border near (ARC7)
        if self.past_from is not None:
            return middle or now - self.past_from >= past
        if not self.go_straight:  # the wheels curved since the last step
            self.arc_turned += now - self.arc_last
        self.arc_last = now
        turned = self.arc_turned >= config.ARC_TURN_MIN
        self.go_straight = cup_beside_curve(band, toward) or (
            elapsed >= config.ARC_STRAIGHT_AFTER and (turned or self.cup_in_curve))
        lane = lane_found(percept, config.TURN_IN_CENTERED)
        facing = reached_horizontal(angle, -toward, config.ARC_EARLY) or edge_left_view(self.edge_angle, angle, -toward)
        self.edge_angle = angle
        if self.cup_in_curve:
            ended = crossed or (lane and elapsed >= config.ARC_LANE_MIN) or (facing and elapsed >= config.ARC_MIN)
        else:
            ended = middle or (turned and (crossed or lane or facing))  # crossed into the lane's middle: done (ARC7)
        if ended and facing and self.cup_in_curve:
            return True  # in a curve the far line is ahead: the robot is in the lane already (ARC4)
        if ended:
            self.past_from = now if self.crossed_at is None else self.crossed_at  # counted from the border (ARC4)
            self.go_straight = True
            return middle or now - self.past_from >= past
        return False

    def turn_in_done(self, percept, now, elapsed, toward):
        """The lane is found along it, or seen sure and bending our way (TURN2). Lost again after it was seen: the
        robot turned past it and turns the other way (TURN_BACK)"""
        if sees_lane(percept):
            self.turn_lane_at = now
        elif (self.turn_lane_at is not None and elapsed >= config.TURN_IN_MIN
              and now - self.turn_lane_at >= config.TURN_PAST):
            self.avoid_phase, self.phase_since = TURN_BACK, now
            return False
        return elapsed >= config.TURN_IN_MIN and (lane_found(percept, config.TURN_IN_CENTERED)
                                                  or (lane_near(percept) and bends_our_way(percept, self.direction)))

    def turn_back_done(self, percept, now, elapsed, toward):
        """The lane is just behind the turn, so the first lane near the middle is the right one"""
        return lane_near(percept)
