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
# Cup distance from the size of the red band (cup mask, OBST9): distance in cm = CUP_SIZE_CM / sqrt(band pixels). Learned
# 2026-11-08 by backing away from a cup in 5 places (cup_learn.py, LEARN1), scaled on the ruler photos of 2026-09-27.
# The size gives the straight-line distance in every place; the band's row moved 4-9 rows with the place (sharp curve,
# cup off to the side) and 2-4 rows with the camera tilt. Closer than about 8 cm the band is below the view; beyond
# about 70 cm it is smaller than the mask's minimum
CUP_SIZE_CM = 405.0
BAND_CUT_ROW = 222 / 224.0  # a band reaching this row is cut off by the image's lower edge, so its size says nothing: it is
                            # right in front of the robot (run avoid3_ccw_2: 36 pixels at row 223, about to hit the cup)
APPROACH_CM = 65.0         # a cup in the lane this close slows the robot (SLOW_DOWN): it rolls on less after the stop
OBSTACLE_CM = 40.0         # a cup in the lane this close is the trigger. At 0.31 and braked the robot still rolls on
                           # about 15 cm (camera delay, coasting), so it comes to rest at about 25 cm
OBSTACLE_CLEAR_CM = 60.0   # the cup only counts as gone when no band is this close (hysteresis: at the trigger distance
                           # a jittering reading released the robot early)
BRAKE = (0.31, 0.1)        # reverse wheel speed and seconds right after a stop: at 0 the motor board lets the wheels coast
BACKUP_CM = 20.0           # standing with the nearest band this close, the robot backs up
BACKUP_TARGET_CM = 26.0    # until the band is further than this (it rolls on a little backwards too)
BACKUP_SPEED = 0.31        # backwards, the slowest that moves the robot
BACKUP_MAX = 2.0           # seconds of backing up at most (a misread band must not drive it back far)
OBSTACLE_FRAMES = 4        # control steps in a row with a close cup before the robot counts as blocked (debounce;
                           # 2 fresh readings, the obstacle model runs every OBSTACLE_EVERY-th step)
OBSTACLE_CLEAR_FRAMES = 5  # control steps in a row with the cup gone before it drives on (stop-only mode)
CUP_IN_LANE = 0.4          # |band x - lane_x| below which a cup is in the lane (a cup beside it is not in the way)
CUP_DEAD_AHEAD = 0.25      # |band x| below which a cup is straight in front of the robot, whatever the lane model says: a
                           # close cup hides the lane (the lane model saw it in only 45 % of the frames at 18-25 cm, OBST8)

# Avoidance (AVOID3): swerve to the inside of the oval as turn 90 degrees toward the pass side in place, curve around
# the cup, turn back onto the lane. No encoders or gyro (MOVE2): every phase ends on a camera mark (HYBRID) and has a
# time limit. Turn rates in place, spin test 2026-10-29 at 12 V: wheel speed 0.35 about 305 deg/s, 0.30 about 200,
# 0.27 about 100, 0.26 did not start
AVOID_BRAKE = 0.3          # seconds standing still before the first turn: turning while still rolling carried the robot
                           # toward the lane edge, which then left the image before it looked horizontal (avoid3_ccw_1)
TURN_SPEED = 0.28          # slowest wheel speed that turns reliably, little overshoot from the camera delay: at 0.27 the
                           # turn back stalled for 1.2 s at 11.9 V (run avoid4_2)
TURN_KICK = (0.35, 0.1)    # wheel speed and seconds at the start of a turn (0.26 and below did not start on their own)
TURN_EARLY = 13.0          # tape angle (degrees) before horizontal at which a 90-degree turn stops: the robot turned
                           # on by 11-14 degrees of tape angle after a stop at horizontal (camera delay, braking)
TURN_LOST = 25.0           # tape angle (degrees) before horizontal from which the edge leaving the image also counts as
                           # 90 degrees: close to the edge it is horizontal below the camera's view (avoid3_ccw_1: last
                           # seen at 16 degrees, then gone)
TURN_JUMP = 10.0           # degrees the reading may jump back before it counts as another tape piece (the edge has left)
TURN_OUT_MAX = 2.5         # seconds the turn out may take before the robot stops: 90 degrees took 0.8 s at about
                           # 100 deg/s, but about 60 deg/s on the track (avoid3_ccw_1, the user saw 180 degrees in 3 s)
TURN_IN_MIN = 0.4          # seconds the turn back lasts at least: it starts with the lane found, crossing it at an angle
TURN_IN_MAX = 2.2          # seconds the turn back may take (it took up to 1.9 s): longer means the robot turned past the
                           # lane and would take it facing backwards (run 2026-11-03_04-52-58)
TURN_IN_CENTERED = 0.4     # |lane_x| below which the turn back ends on an aligned lane. The curve ends at the lane's
                           # edge, so 0.15 was never met and the robot spun on; ROAD_RECOVERY then centers it (AVOID4)
CUP_NEAR_CM = 50.0         # during a swerve only bands this close count: cups further back are
                           # not the one being passed
CUP_EDGE = 0.6             # image x (0..1 toward the edge) the cup must have reached before it counts as having left
                           # the image sideways: last seen at 0.71-0.96 in 5 swerves, about 70-85 degrees turned (AVOID4)
ARC_WHEELS = (0.36, 0.31)  # outer and inner wheel in the curve around the cup. A wheel moves only above about 0.24 and
                           # then about in proportion to (speed - 0.24) (spin test). 0.37 / 0.30 was a circle of about
                           # 25 cm radius, too small for a cup more than about 25 cm ahead; this is about 35 cm (AVOID4)
ARC_STRAIGHT = 0.335       # both wheels while the cup is in view during the curve: drive on past it (AVOID4)
ARC_STOP_CM = 16.0         # a band this close in the middle of the image during the curve: stop
ARC_STOP_X = 0.5           # |band x| below which that band counts as in the way
ARC_LANE_MIN = 2.5         # seconds of curve before the lane found ends it: it first appeared 3.4-3.5 s in, inside the
                           # lane and 0.8 s before the far border (runs avoid4_1, avoid4_2). Earlier it could be the lane
                           # seen from the side, before the cup is passed
ARC_MIN = 1.0              # seconds the curve lasts at least (it starts with the lane edge horizontal ahead)
ARC_EARLY = 5.0            # tape angle (degrees) before horizontal at which the curve ends (facing the lane again):
                           # it turns slower than a spin in place, so it overshoots less
ARC_LONGEST = 3.9          # seconds after which the curve ends even without a mark: the good curves took 2.3-3.7 s (run
                           # avoid4_7), longer it reached the far border of the lane (avoid4_2, avoid4_8)
RECOVER_SPEED = 0.31       # forward speed while looking for the lane (the slowest that moves the robot)
RECOVER_TURN = 0.04        # gentle turn toward the lane while it is not seen yet
RECOVER_CENTERED = 0.15    # |lane_x| below which the lane counts as found (and the lane mask must see the robot
                           # aligned: crosswise tape gave lane_x near 0, run avoid_ccw_1)
RECOVER_FRAMES = 5         # control steps in a row with the lane found before normal following resumes
RECOVER_TIMEOUT = 4.0      # seconds without finding the lane before the robot stops
