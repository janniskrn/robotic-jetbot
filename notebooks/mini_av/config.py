"""All tuning values of the driving program in one place (Task 1: adaptive lane following)."""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(HERE, 'models')        # SD card
LOG_ROOT = '/workspace/usb/logs'                # USB stick (inside the Jupyter container)

# Perception
LANE_VISIBLE_THRESHOLD = 0.5  # probability above which the lane counts as visible
CURVE_EVERY = 2               # run the curve model every Nth frame: the curvature changes slowly, saves time
CURVE_SMOOTHING = 0.3         # weight of a new curve prediction in the running average (single frames flickered)

# Steering (D4): smoothed PD on the lane center, lane_x -1 (left edge) .. 1 (right edge)
LANE_SMOOTHING = 1.0    # weight of the new lane_x in the running average (1 = none: any smoothing delay made the robot oversteer)
STEERING_KP = 0.15      # wheel speed difference per unit of lane_x (0.35 and a cubic term made the robot swing)
STEERING_KI = 0.0       # integral (off: 0.25 added delay and a growing swing on the track, 2026-09-20)
STEERING_I_LEAK = 1.5   # seconds: the integral fades after a curve instead of carrying over into the straight
STEERING_I_MAX = 0.12   # largest steering the integral may add (no wind-up)
STEERING_KD = 0.06      # wheel speed difference per unit of lane_x change per second (damping; 0.03 let the swing grow at 0.39)
FEEDFORWARD_GENTLE = 0.015  # base turn added in a gentle curve (times the curve model's probability)
FEEDFORWARD_SHARP = 0.04    # base turn added in a sharp curve: P alone gave only about 0.036 there, the curve needs about 0.08
FEEDFORWARD_MIN_X = 0.05    # |lane_x| below which the curve direction is unclear and no feedforward is added
STEERING_REF_SPEED = 0.32  # speed the gains were tuned at; at other speeds they are scaled by REF/speed
                           # (at 0.40 the unscaled gains made the robot swing on the straight)
STEERING_RATE = 2.0     # maximum change of the steering command per second
MOTOR_TRIM = 0.0        # added to the left wheel, subtracted from the right; positive corrects a drift to the left

# Speed (D5): speed per curve class, blended by the curve model's probabilities
SPEED_STRAIGHT = 0.40
SPEED_GENTLE = 0.35
SPEED_SHARP = 0.31      # the robot does not move below about 0.27
TURN_SLOW_START = 0.10  # |lane_x| from which the robot counts as turning and slows down
TURN_SLOW_FULL = 0.30   # |lane_x| from which it drives at SPEED_SHARP (it sped up while still turning out of the sharp curve)
SPEED_UP_RATE = 0.10    # maximum speed increase per second (smooth acceleration)
SPEED_DOWN_RATE = 0.40  # maximum speed decrease per second (brake faster than accelerate)

# Baseline for the comparison (stock JetBot behaviour: constant speed, plain P steering, no smoothing)
BASELINE_SPEED = 0.32

# Decision
LANE_LOST_TIMEOUT = 0.5  # seconds without a visible lane before the robot stops
