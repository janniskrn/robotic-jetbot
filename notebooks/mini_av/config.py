"""All tuning values of the driving program in one place (Task 1: adaptive lane following)."""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(HERE, 'models')        # SD card
LOG_ROOT = '/workspace/usb/logs'                # USB stick (inside the Jupyter container)

# Perception
LANE_VISIBLE_THRESHOLD = 0.5  # probability above which the lane counts as visible
CURVE_EVERY = 2               # run the curve model every Nth frame: the curvature changes slowly, saves time
OBSTACLE_EVERY = 2            # run the obstacle model every Nth frame, on the frames without the curve model: a third
                              # model on every frame added 12 ms per step, and the robot swung after the cw sharp curve
CURVE_SMOOTHING = 0.3         # weight of a new curve prediction in the running average (single frames flickered)

# Steering (D4): smoothed PD on the lane center, lane_x -1 (left edge) .. 1 (right edge)
LANE_SMOOTHING = 1.0    # weight of the new lane_x in the running average (1 = none: any smoothing delay made the robot oversteer)
STEERING_KP = 0.15      # wheel speed difference per unit of lane_x (0.35 and a cubic term made the robot swing)
STEERING_KI = 0.0       # integral (off: 0.25 added delay and a growing swing on the track, 2026-09-20)
STEERING_I_LEAK = 1.5   # seconds: the integral fades after a curve instead of carrying over into the straight
STEERING_I_MAX = 0.12   # largest steering the integral may add (no wind-up)
STEERING_KD = 0.06      # wheel speed difference per unit of lane_x change per second (damping; 0.03 let the swing grow at 0.39)
D_SMOOTHING = 0.5       # weight of the new lane_x in the smoothed value the D term differentiates (P stays on the raw
                        # value): D on the raw value turned every frame-to-frame jump into a steering jerk (2026-10-01)
FEEDFORWARD_GENTLE = 0.015  # base turn added in a gentle curve (times the curve model's probability)
FEEDFORWARD_SHARP = 0.04    # base turn added in a sharp curve. With the direction from lane_x (on only part of the
                            # time) 0.04 ran wide; with the steady curve-model direction 0.07 turned in early and cut
                            # over the inner line (runs v3_ccw_1..3, seen by the user)
FEEDFORWARD_MIN_DIR = 0.2  # |curve_dir| (curve model: p_right - p_left) below which the direction is unclear and
                           # no feedforward is added. The direction used to come from lane_x, which stayed near 0
                           # and flipped sign in the sharp ccw curve (DATA2)
FEEDFORWARD_MAX_INSIDE = 0.10  # lane_x toward the outside of the curve (the robot is already inside it) from which
                               # no feedforward is added and P steers back (also during a short lane gap)
STEERING_REF_SPEED = 0.32  # speed the gains were tuned at; at other speeds they are scaled by REF/speed
                           # (at 0.40 the unscaled gains made the robot swing on the straight)
STEERING_RATE = 2.0     # maximum change of the steering command per second
MOTOR_TRIM = -0.01      # added to the left wheel, subtracted from the right; positive corrects a drift to the left.
                        # The robot drifts right: on straights the steering averaged -0.005..-0.013 and the robot sat
                        # right of center (mean lane_x -0.04..-0.11) in every run up to 2026-10-01

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
SLOW_DOWN_ENTER = 0.5    # p_sharp above which the state machine enters SLOW_DOWN (speed capped at SPEED_SHARP)
SLOW_DOWN_EXIT = 0.3     # p_sharp below which it returns to ROAD_FOLLOWING (hysteresis)
OBSTACLE_VISIBLE_THRESHOLD = 0.5  # obstacle model probability above which a cup counts as seen
OBSTACLE_ROW = 88 / 224.0  # cup_row (lower edge of the red band) from which the cup is close: about 45 cm as the model
                           # sees it. Triggered at row 98-112 the robot stood at row 134-138 (10-12 cm, run
                           # stop_cups_1): debounce, about 0.14 s camera lag and rolling on after the stop;
                           # this should stop it at about 25 cm
OBSTACLE_CLEAR_ROW = 80 / 224.0  # the cup only counts as gone when unseen or above this row (hysteresis: at the same row
                                 # as the trigger, a reading jittering around it released the robot in front of the cup)
OBSTACLE_FRAMES = 4        # control steps in a row with a close cup before the robot counts as blocked (debounce;
                           # 2 fresh readings, the obstacle model runs every OBSTACLE_EVERY-th step)
OBSTACLE_CLEAR_FRAMES = 5  # control steps in a row with the cup gone before it drives on (stop-only mode)
CUP_IN_LANE = 0.4          # |cup_x - lane_x| below which a close cup is in the lane and gets avoided

# Avoidance (D7, AVOID1, AVOID2): swerve to the inside of the oval, from the measured motion (MOVE1: at wheel speed
# 0.35 about 25 cm/s straight and about 125 deg/s turning in place). Symmetric: the way back mirrors the way out,
# so a slower pivot (low battery) changes both turns alike. Only the pass uses the camera (cup mask, HYBRID)
AVOID_SPEED = 0.35
AVOID_STEPS = [            # (name, seconds, turn): turn +1 toward the pass side in place, -1 away from it, 0 straight
    ('turn_out', 0.36, 1),        # about 45 degrees toward the pass side
    ('out', 0.8, 0),              # about 20 cm diagonally: about 14 cm sideways, out of the lane
    ('turn_parallel', 0.36, -1),  # back parallel to the lane
    ('pass', 1.4, 0),             # at least this long (about 35 cm), then until the cup is behind (AVOID_PASS_CLEAR)
    ('turn_in', 0.36, -1),        # about 45 degrees toward the lane
    ('in', 0.8, 0),               # the same 14 cm sideways back to the lane center
    ('turn_straight', 0.36, 1),   # parallel to the lane again: without it recovery turned the robot crosswise
]
AVOID_PASS_CLEAR = 1.0     # seconds the pass goes on after the cup mask last saw the cup on its side: the cup leaves
                           # the wide-angle image while still beside the robot's front (run avoid_ccw_1)
AVOID_PASS_MAX = 4.0       # seconds after which a cup still beside the robot stops the run (HALT)
AVOID_BESIDE_PIXELS = 80   # smallest red band (pixels) that counts as the cup being passed: in avoid_ccw_1 it had
                           # 93-168, the next cup further along the track 34-68 (it must not stretch the pass)
# Turns in place ended by the camera (AVOID3, under test with turn_test.py): spin test 2026-10-29 at 12 V, wheel
# speed 0.35 turned about 305 deg/s, 0.30 about 200, 0.27 about 100, 0.26 did not start
TURN_SPEED = 0.27          # slowest wheel speed that turns reliably: little overshoot from the camera delay
TURN_KICK = (0.35, 0.1)    # wheel speed and seconds at the start of a turn (0.26 and below did not start on their own)
TURN_EARLY = 13.0          # tape angle (degrees) before horizontal at which a 90-degree turn stops: the robot turned
                           # on by 11-14 degrees of tape angle after a stop at horizontal (camera delay, braking)
TURN_MAX = 3.0             # seconds a turn may take before the robot stops (a stall or the tape not found)
RECOVER_SPEED = 0.31      # forward speed while looking for the lane (the slowest that moves the robot)
RECOVER_TURN = 0.04        # gentle turn toward the lane while it is not seen yet
RECOVER_CENTERED = 0.15    # |lane_x| below which the lane counts as found (and the lane mask must see the robot
                           # aligned: crosswise tape gave lane_x near 0, run avoid_ccw_1)
RECOVER_FRAMES = 5         # control steps in a row with the lane found before normal following resumes
RECOVER_TIMEOUT = 4.0      # seconds without finding the lane before the robot stops
