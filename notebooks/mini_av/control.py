"""Control: lane position and curve class -> wheel speeds (D4 steering, D5 speed).

Our own control layer between the model output and the motors (Task 1).
"""

import config

SPEEDS = [config.SPEED_STRAIGHT, config.SPEED_GENTLE, config.SPEED_SHARP]  # same order as CURVE_CLASSES


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
        self.baseline = baseline
        self.use_curve = use_curve
        self.lane_x = 0.0      # smoothed lane position
        self.d_lane_x = 0.0    # more strongly smoothed lane position, only for the D term
        self.integral = 0.0    # leaky sum of lane_x over time
        self.last_error = None
        self.steering = 0.0
        self.speed = config.SPEED_SHARP  # start at the slowest speed that moves the robot, then ramp up

    def reset(self):
        """Forget the past, for example after the robot stopped"""
        self.__init__(self.baseline, self.use_curve)

    def target_speed(self, curve_probs, lane_x):
        """Slower of two speeds: the curve model's (blended by its probabilities) and the steering's.

        The steering part keeps the robot slow while it is still turning, also when the curve model
        already sees the straight ahead.
        """
        model_speed = sum(p * v for p, v in zip(curve_probs, SPEEDS))
        turning = (abs(lane_x) - config.TURN_SLOW_START) / (config.TURN_SLOW_FULL - config.TURN_SLOW_START)
        turning = max(0.0, min(1.0, turning))
        steering_speed = config.SPEED_STRAIGHT - turning * (config.SPEED_STRAIGHT - config.SPEED_SHARP)
        return min(model_speed, steering_speed)

    def curve_turn(self, curve_probs, curve_dir):
        """Base turn for the curve the curve model sees: a curve needs a sustained turn that P alone only gives
        with a large error. Size from how sharp the curve is, direction from which way it bends (both curve model)"""
        if abs(curve_dir) < config.FEEDFORWARD_MIN_DIR:
            return 0.0
        size = curve_probs[1] * config.FEEDFORWARD_GENTLE + curve_probs[2] * config.FEEDFORWARD_SHARP
        return size if curve_dir > 0 else -size

    def feedforward(self, curve_probs, curve_dir):
        """The curve turn, or none when the robot is already inside the curve: then P steers it back to the center"""
        if self.lane_x * curve_dir < 0 and abs(self.lane_x) > config.FEEDFORWARD_MAX_INSIDE:
            return 0.0
        return self.curve_turn(curve_probs, curve_dir)

    def update(self, lane_x, curve_probs, curve_dir, dt, speed_limit=None):
        """Returns (left, right) wheel speeds; speed_limit caps the target speed (state SLOW_DOWN)"""
        if self.baseline:
            # stock JetBot style: raw model output, plain P steering, constant speed
            self.steering = config.STEERING_KP * lane_x
            self.speed = config.BASELINE_SPEED
        else:
            self.lane_x += config.LANE_SMOOTHING * (lane_x - self.lane_x)
            if self.last_error is None:
                self.d_lane_x = self.lane_x
            self.d_lane_x += config.D_SMOOTHING * (self.lane_x - self.d_lane_x)
            change = 0.0 if self.last_error is None else (self.d_lane_x - self.last_error) / dt
            self.last_error = self.d_lane_x
            # leaky integral: grows while the robot stays off-center in a curve, fades on the straight
            self.integral += self.lane_x * dt - self.integral * dt / config.STEERING_I_LEAK
            integral_part = max(-config.STEERING_I_MAX, min(config.STEERING_I_MAX, config.STEERING_KI * self.integral))
            # gain scheduling: the faster the robot, the more a correction moves it before the next frame,
            # so the gains shrink with speed and the steering has the same effect at every speed
            schedule = config.STEERING_REF_SPEED / max(self.speed, config.STEERING_REF_SPEED)
            wanted = (schedule * (config.STEERING_KP * self.lane_x + config.STEERING_KD * change) + integral_part
                      + self.feedforward(curve_probs, curve_dir))
            self.steering = limit_change(wanted, self.steering, config.STEERING_RATE, config.STEERING_RATE, dt)
            if self.use_curve:
                target = self.target_speed(curve_probs, self.lane_x)
                if speed_limit is not None:
                    target = min(target, speed_limit)
                self.speed = limit_change(target, self.speed, config.SPEED_UP_RATE, config.SPEED_DOWN_RATE, dt)
            else:
                self.speed = config.BASELINE_SPEED  # same speed as the baseline: the runs differ only in steering
        return self.wheels()

    def hold(self, curve_probs, curve_dir, dt):
        """Returns (left, right) for a short gap in which the lane is not visible (lane_x is not trained on
        such frames). In a curve the robot keeps turning into it, at least as hard as the curve turn: holding
        the last raw command held a turn out of the sharp ccw curve in both failed runs (DATA2). Without the
        inside rule: lane_x reached +0.10 just before the gap and the rule then held a turn out of the curve
        (S1d0, 2 runs on 2026-11-03). On a straight the last command is kept."""
        turn = self.curve_turn(curve_probs, curve_dir)
        if turn != 0.0 and (self.steering * turn <= 0.0 or abs(self.steering) < abs(turn)):
            self.steering = limit_change(turn, self.steering, config.STEERING_RATE, config.STEERING_RATE, dt)
        return self.wheels()

    def avoid(self, phase, side, elapsed):
        """Returns (left, right) for a swerve phase (decision.AVOID_PHASES; the decision layer picks and ends it).

        brake: stand still; turn_out, turn_in: turn in place toward the pass side; arc: curve away from it, around
        the cup; pass: straight on while the cup is in view during the curve (Decision.avoid_action).
        side: 'left' or 'right', the pass side; elapsed: seconds since the phase started (the kick).
        """
        if phase == 'brake':
            return self.stop(phase, elapsed)
        if phase == 'pass':
            return config.ARC_STRAIGHT, config.ARC_STRAIGHT
        toward = -1.0 if side == 'left' else 1.0  # sign of a turn toward the pass side (positive turns right)
        if phase == 'arc':
            outer, inner = config.ARC_WHEELS
            return (inner, outer) if toward > 0 else (outer, inner)
        spin = toward * turn_speed(elapsed)
        return spin, -spin

    def stop(self, phase, elapsed):
        """Returns (left, right) standing in front of a cup (decision.STOP_PHASES): brake = a short reverse pulse,
        because at 0 the motor board lets the wheels coast; back = slowly backwards; wait = off"""
        if phase == 'back':
            return -config.BACKUP_SPEED, -config.BACKUP_SPEED
        if phase == 'brake' and elapsed < config.BRAKE[1]:
            return -config.BRAKE[0], -config.BRAKE[0]
        return 0.0, 0.0

    def recover(self, side):
        """Returns (left, right) while the lane is not seen after the swerve: slowly forward, turning gently away
        from the pass side. The swerve ends with the lane found, so this only covers frames in which the lane model
        loses it again"""
        self.steering = (config.RECOVER_TURN if side == 'left' else -config.RECOVER_TURN)
        self.speed = config.RECOVER_SPEED
        return self.wheels()

    def wheels(self):
        """(left, right) wheel speeds from the current speed and steering"""
        left = self.speed + self.steering + config.MOTOR_TRIM
        right = self.speed - self.steering - config.MOTOR_TRIM
        return max(-1.0, min(1.0, left)), max(-1.0, min(1.0, right))
