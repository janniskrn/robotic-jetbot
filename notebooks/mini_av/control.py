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
        self.last_error = None
        self.steering = 0.0
        self.speed = config.SPEED_SHARP  # start at the slowest speed that moves the robot, then ramp up

    def reset(self):
        """Forget the past, for example after the robot stopped"""
        self.__init__(self.baseline, self.use_curve)

    def target_speed(self, curve_probs):
        """Speed blended by the curve probabilities: sure straight -> fast, sure sharp -> slow"""
        return sum(p * v for p, v in zip(curve_probs, SPEEDS))

    def update(self, lane_x, curve_probs, dt):
        """Returns (left, right) wheel speeds"""
        if self.baseline:
            # stock JetBot style: raw model output, plain P steering, constant speed
            self.steering = config.STEERING_KP * lane_x
            self.speed = config.BASELINE_SPEED
        else:
            self.lane_x += config.LANE_SMOOTHING * (lane_x - self.lane_x)
            change = 0.0 if self.last_error is None else (self.lane_x - self.last_error) / dt
            self.last_error = self.lane_x
            # progressive: linear for small deviations, the cubic term adds strength only for large ones
            wanted = (config.STEERING_KP * self.lane_x + config.STEERING_K3 * self.lane_x ** 3
                      + config.STEERING_KD * change)
            self.steering = limit_change(wanted, self.steering, config.STEERING_RATE, config.STEERING_RATE, dt)
            if self.use_curve:
                self.speed = limit_change(self.target_speed(curve_probs), self.speed,
                                          config.SPEED_UP_RATE, config.SPEED_DOWN_RATE, dt)
            else:
                self.speed = config.BASELINE_SPEED  # same speed as the baseline: the runs differ only in steering
        left = self.speed + self.steering + config.MOTOR_TRIM
        right = self.speed - self.steering - config.MOTOR_TRIM
        return max(-1.0, min(1.0, left)), max(-1.0, min(1.0, right))
