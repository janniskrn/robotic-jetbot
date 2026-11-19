"""Control: lane position and curve class -> wheel speeds (Task 1: D4 steering, D5 speed).

Our own control layer between the model output and the motors. Steering: PD on lane_x plus a curve feedforward.
"""

import config

SPEEDS = [config.SPEED_STRAIGHT, config.SPEED_GENTLE, config.SPEED_SHARP]  # same order as CURVE_CLASSES


def clamp(value, low, high):
    return max(low, min(high, value))


def turn_speed(elapsed):
    """Wheel speed of a turn in place: a short kick to break the robot free, then the slow speed (MOVE2)"""
    return config.TURN_KICK[0] if elapsed < config.TURN_KICK[1] else config.TURN_SPEED


def limit_change(target, current, up_rate, down_rate, dt):
    """Moves current toward target by at most up_rate (rising) or down_rate (falling) per second"""
    if target > current:
        return min(target, current + up_rate * dt)
    return max(target, current - down_rate * dt)


class Controller(object):
    def __init__(self, baseline=False, use_curve=True):
        self.baseline = baseline    # stock JetBot style for the comparison run: plain P, constant speed
        self.use_curve = use_curve  # False: our steering at the baseline speed
        self.lane_x = 0.0
        self.d_lane_x = None        # smoothed lane_x, only for the D term
        self.steering = 0.0
        self.speed = config.SPEED_SHARP  # start at the slowest speed that moves the robot, then ramp up

    def reset(self):
        """Forget the past, for example after the robot stopped"""
        self.__init__(self.baseline, self.use_curve)

    def target_speed(self, curve_probs, lane_x):
        """The slower of the curve model's speed (blended by its probabilities) and the steering's: the robot stays
        slow while it is still turning, also when the curve model already sees the straight ahead"""
        model_speed = sum(p * v for p, v in zip(curve_probs, SPEEDS))
        turning = clamp((abs(lane_x) - config.TURN_SLOW_START) / (config.TURN_SLOW_FULL - config.TURN_SLOW_START), 0, 1)
        steering_speed = config.SPEED_STRAIGHT - turning * (config.SPEED_STRAIGHT - config.SPEED_SHARP)
        return min(model_speed, steering_speed)

    def curve_turn(self, curve_probs, curve_dir):
        """Base turn for the curve ahead (curve model: size from how sharp, sign from which way it bends)"""
        if abs(curve_dir) < config.FEEDFORWARD_MIN_DIR:
            return 0.0
        size = curve_probs[1] * config.FEEDFORWARD_GENTLE + curve_probs[2] * config.FEEDFORWARD_SHARP
        return size if curve_dir > 0 else -size

    def feedforward(self, curve_probs, curve_dir):
        """The curve turn, or none when the robot is already inside the curve: then P steers it back"""
        if self.lane_x * curve_dir < 0 and abs(self.lane_x) > config.FEEDFORWARD_MAX_INSIDE:
            return 0.0
        return self.curve_turn(curve_probs, curve_dir)

    def update(self, lane_x, curve_probs, curve_dir, dt, speed_limit=None):
        """Returns (left, right) wheel speeds; speed_limit caps the target speed (state SLOW_DOWN)"""
        if self.baseline:
            self.steering = config.STEERING_KP * lane_x
            self.speed = config.BASELINE_SPEED
            return self.wheels()
        self.lane_x = lane_x
        # D on a smoothed lane_x: on the raw value every frame-to-frame jump was a steering jerk
        last = self.d_lane_x
        self.d_lane_x = lane_x if last is None else last + config.D_SMOOTHING * (lane_x - last)
        change = 0.0 if last is None else (self.d_lane_x - last) / dt
        # gain scheduling: the faster the robot, the more a correction moves it before the next frame
        schedule = config.STEERING_REF_SPEED / max(self.speed, config.STEERING_REF_SPEED)
        wanted = (schedule * (config.STEERING_KP * lane_x + config.STEERING_KD * change)
                  + self.feedforward(curve_probs, curve_dir))
        self.steering = limit_change(wanted, self.steering, config.STEERING_RATE, config.STEERING_RATE, dt)
        if self.use_curve:
            target = self.target_speed(curve_probs, lane_x)
            if speed_limit is not None:
                target = min(target, speed_limit)
            self.speed = limit_change(target, self.speed, config.SPEED_UP_RATE, config.SPEED_DOWN_RATE, dt)
        else:
            self.speed = config.BASELINE_SPEED  # the runs differ only in steering
        return self.wheels()

    def hold(self, curve_probs, curve_dir, dt):
        """Returns (left, right) for a short gap without the lane (lane_x is not trained on such frames). In a curve
        the robot keeps turning into it at least as hard as the curve turn (DATA2); on a straight it keeps the command"""
        turn = self.curve_turn(curve_probs, curve_dir)
        if turn != 0.0 and (self.steering * turn <= 0.0 or abs(self.steering) < abs(turn)):
            self.steering = limit_change(turn, self.steering, config.STEERING_RATE, config.STEERING_RATE, dt)
        return self.wheels()

    def avoid(self, phase, side, elapsed):
        """Returns (left, right) for a swerve phase (decision.avoid_action); side: the pass side; elapsed: seconds in
        the phase. brake: stand still; turn_out, turn_in: turn in place toward the pass side; arc: curve away from
        it around the cup; pass: straight on; turn_back: turn in place away from the pass side"""
        if phase == 'brake':
            return self.stop(phase, elapsed)
        if phase == 'pass':
            return config.ARC_STRAIGHT, config.ARC_STRAIGHT
        toward = -1.0 if side == 'left' else 1.0  # positive turns right
        if phase == 'arc':
            outer, inner = config.ARC_WHEELS
            return (inner, outer) if toward > 0 else (outer, inner)
        spin = toward * turn_speed(elapsed)
        if phase == 'turn_back':
            spin = -spin
        return spin, -spin

    def stop(self, phase, elapsed):
        """Returns (left, right) in front of a cup (decision.STOP_PHASES): brake = a short reverse pulse (at 0 the
        motor board lets the wheels coast); back = slowly backwards; wait = off"""
        if phase == 'back':
            return -config.BACKUP_SPEED, -config.BACKUP_SPEED
        if phase == 'brake' and elapsed < config.BRAKE[1]:
            return -config.BRAKE[0], -config.BRAKE[0]
        return 0.0, 0.0

    def recover(self, side):
        """Returns (left, right) while the lane is not seen in ROAD_RECOVERY: slowly forward, gently away from the
        pass side"""
        self.steering = config.RECOVER_TURN if side == 'left' else -config.RECOVER_TURN
        self.speed = config.RECOVER_SPEED
        return self.wheels()

    def wheels(self):
        """(left, right) wheel speeds from the current speed and steering"""
        left = self.speed + self.steering + config.MOTOR_TRIM
        right = self.speed - self.steering - config.MOTOR_TRIM
        return clamp(left, -1.0, 1.0), clamp(right, -1.0, 1.0)
