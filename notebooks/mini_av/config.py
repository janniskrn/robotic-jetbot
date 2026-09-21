"""All tuning values of the driving program in one place (Task 1: adaptive lane following)."""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(HERE, 'models')        # SD card
LOG_ROOT = '/workspace/usb/logs'                # USB stick (inside the Jupyter container)

# Perception
LANE_VISIBLE_THRESHOLD = 0.5  # probability above which the lane counts as visible
CURVE_EVERY = 2               # run the curve model every Nth frame: the curvature changes slowly, saves time

# Steering (D4): smoothed PD on the lane center, lane_x -1 (left edge) .. 1 (right edge)
LANE_SMOOTHING = 0.5    # weight of the new lane_x in the running average (1 = no smoothing)
STEERING_KP = 0.15      # wheel speed difference per unit of lane_x
STEERING_KD = 0.03      # wheel speed difference per unit of lane_x change per second (damping)
STEERING_RATE = 2.0     # maximum change of the steering command per second
MOTOR_TRIM = 0.0        # added to the left wheel, subtracted from the right; positive corrects a drift to the left

# Speed (D5): speed per curve class, blended by the curve model's probabilities
SPEED_STRAIGHT = 0.40
SPEED_GENTLE = 0.35
SPEED_SHARP = 0.31      # the robot does not move below about 0.27
SPEED_UP_RATE = 0.10    # maximum speed increase per second (smooth acceleration)
SPEED_DOWN_RATE = 0.40  # maximum speed decrease per second (brake faster than accelerate)

# Baseline for the comparison (stock JetBot behaviour: constant speed, plain P steering, no smoothing)
BASELINE_SPEED = 0.32

# Decision
LANE_LOST_TIMEOUT = 0.5  # seconds without a visible lane before the robot stops
