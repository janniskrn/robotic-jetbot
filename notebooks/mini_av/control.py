"""Control: lane position and curve class -> wheel speeds (D4 steering, D5 speed).

Our own control layer between the model output and the motors (Task 1).
"""

import config

SPEEDS = [config.SPEED_STRAIGHT, config.SPEED_GENTLE, config.SPEED_SHARP]  # same order as CURVE_CLASSES


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

    def feedforward(self, curve_probs, curve_dir):
        """Base turn from the curve model: a curve needs a sustained turn that P alone only gives with a
        large error. Size from how sharp the curve is, direction from which way it bends (both curve model)."""
        if abs(curve_dir) < config.FEEDFORWARD_MIN_DIR:
            return 0.0
        size = curve_probs[1] * config.FEEDFORWARD_GENTLE + curve_probs[2] * config.FEEDFORWARD_SHARP
        return size if curve_dir > 0 else -size

    def update(self, lane_x, curve_probs, curve_dir, dt):
        """Returns (left, right) wheel speeds"""
        if self.baseline:
            # stock JetBot style: raw model output, plain P steering, constant speed
            self.steering = config.STEERING_KP * lane_x
            self.speed = config.BASELINE_SPEED
        else:
            self.lane_x += config.LANE_SMOOTHING * (lane_x - self.lane_x)
            change = 0.0 if self.last_error is None else (self.lane_x - self.last_error) / dt
            self.last_error = self.lane_x
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
                self.speed = limit_change(self.target_speed(curve_probs, self.lane_x), self.speed,
                                          config.SPEED_UP_RATE, config.SPEED_DOWN_RATE, dt)
            else:
                self.speed = config.BASELINE_SPEED  # same speed as the baseline: the runs differ only in steering
        return self.wheels()

    def hold(self, curve_probs, curve_dir, dt):
        """Returns (left, right) for a short gap in which the lane is not visible (lane_x is not trained on
        such frames). In a curve the robot keeps turning into it, at least as hard as the feedforward: holding
        the last raw command held a turn out of the sharp ccw curve in both failed runs (DATA2). On a straight
        the last command is kept."""
        turn = self.feedforward(curve_probs, curve_dir)
        if turn != 0.0 and (self.steering * turn <= 0.0 or abs(self.steering) < abs(turn)):
            self.steering = limit_change(turn, self.steering, config.STEERING_RATE, config.STEERING_RATE, dt)
        return self.wheels()

    def wheels(self):
        """(left, right) wheel speeds from the current speed and steering"""
        left = self.speed + self.steering + config.MOTOR_TRIM
        right = self.speed - self.steering - config.MOTOR_TRIM
        return max(-1.0, min(1.0, left)), max(-1.0, min(1.0, right))
