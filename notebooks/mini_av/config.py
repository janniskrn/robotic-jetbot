"""All tuning values of the driving program in one place. The history of each value is in DECISIONS.md (IDs)."""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(HERE, 'models')        # SD card
LOG_ROOT = '/workspace/usb/logs'                # USB stick (inside the Jupyter container)

# Perception
LANE_VISIBLE_THRESHOLD = 0.5  # lane model probability above which the lane counts as visible
CURVE_EVERY = 2               # run the curve model every Nth frame (the curvature changes slowly)
OBSTACLE_EVERY = 2            # run the obstacle model every Nth frame, between the curve frames (saves 12 ms per step)
CURVE_SMOOTHING = 0.3         # weight of a new curve prediction in the running average (single frames flickered)

# Steering (D4, D4c): PD on the lane center, lane_x -1 (left edge) .. 1 (right edge), plus a curve feedforward (D4f)
STEERING_KP = 0.15      # wheel speed difference per unit of lane_x (0.35 made the robot swing)
STEERING_KD = 0.06      # per unit of lane_x change per second (damping; 0.03 let the swing grow at 0.39)
D_SMOOTHING = 0.5       # weight of the new lane_x in the smoothed value the D term uses (P stays on the raw value)
FEEDFORWARD_GENTLE = 0.015  # base turn in a gentle curve (times the curve model's probability)
FEEDFORWARD_SHARP = 0.04    # base turn in a sharp curve (0.07 cut over the inner line)
FEEDFORWARD_MIN_DIR = 0.2   # |curve_dir| below which the curve's direction is unclear: no feedforward (DATA2)
FEEDFORWARD_MAX_INSIDE = 0.10  # lane_x toward the outside of the curve from which no feedforward is added (already inside)
STEERING_REF_SPEED = 0.32  # speed the gains were tuned at; at higher speeds they shrink by REF/speed
STEERING_RATE = 2.0     # maximum change of the steering command per second
MOTOR_TRIM = -0.01      # added to the left wheel, subtracted from the right: the robot drifts right

# Speed (D5): speed per curve class, blended by the curve model's probabilities
SPEED_STRAIGHT = 0.40
SPEED_GENTLE = 0.35
SPEED_SHARP = 0.31      # the robot does not move below about 0.27
TURN_SLOW_START = 0.10  # |lane_x| from which the robot counts as turning and slows down
TURN_SLOW_FULL = 0.30   # |lane_x| from which it drives at SPEED_SHARP
SPEED_UP_RATE = 0.10    # maximum speed increase per second
SPEED_DOWN_RATE = 0.40  # maximum speed decrease per second (brake faster than accelerate)
BASELINE_SPEED = 0.32   # comparison run: stock JetBot style, constant speed, plain P steering

# Decision
LANE_LOST_TIMEOUT = 0.5  # seconds without a visible lane before the lane counts as lost
SLOW_DOWN_ENTER = 0.5    # p_sharp above which the state machine enters SLOW_DOWN
SLOW_DOWN_EXIT = 0.3     # p_sharp below which it returns to ROAD_FOLLOWING (hysteresis)
# Driving direction (DIR1): set once at the first sharp curve; on the oval all curves bend the same way (right = cw)
DIRECTION_SHARP = 0.5    # p_sharp from which a step counts (a gentle curve once decided wrong)
DIRECTION_MIN_DIR = 0.5  # |curve_dir| from which the curve's direction is clear
DIRECTION_FRAMES = 5     # steps in a row with a sharp curve the same way

# Cups (OBST9, LEARN1): distance in cm = CUP_SIZE_CM / sqrt(red band pixels), from the cup mask
OBSTACLE_VISIBLE_THRESHOLD = 0.5  # obstacle model probability above which a cup counts as seen
CUP_SIZE_CM = 405.0
BAND_CUT_ROW = 222 / 224.0  # a band reaching this row is cut off by the image edge: right in front of the robot
APPROACH_CM = 65.0         # a cup in the lane this close slows the robot (SLOW_DOWN)
OBSTACLE_CM = 40.0         # a cup in the lane this close starts the swerve (the robot rolls on about 15 cm)
OBSTACLE_CLEAR_CM = 60.0   # the cup counts as gone when no band is this close (hysteresis)
OBSTACLE_FRAMES = 4        # steps in a row with a close cup before the robot counts as blocked
OBSTACLE_CLEAR_FRAMES = 5  # steps in a row with the cup gone before it drives on (stop_only)
CUP_IN_LANE = 0.4          # |band x - lane_x| below which a cup is in the lane
CUP_DEAD_AHEAD = 0.25      # |band x| below which a cup is straight ahead, whatever the lane model says (it hides the lane)

# Stop in front of a cup (stop_only)
BRAKE = (0.31, 0.1)        # reverse wheel speed and seconds right after a stop (at 0 the wheels coast)
BACKUP_CM = 20.0           # standing with the nearest band this close, the robot backs up
BACKUP_TARGET_CM = 26.0    # until the band is further than this
BACKUP_SPEED = 0.31        # backwards, the slowest that moves the robot
BACKUP_MAX = 2.0           # seconds of backing up at most

# Swerve (AVOID3, AVOID4): turn 90 degrees toward the pass side, curve around the cup, turn back onto the lane.
# No encoders or gyro (MOVE2): every phase ends on a camera mark (HYBRID) and has a time limit
AVOID_BRAKE = 0.3          # seconds standing still before the first turn (turning while rolling overshot)
TURN_SPEED = 0.28          # slowest wheel speed that turns reliably in place (0.27 stalled)
TURN_KICK = (0.35, 0.1)    # wheel speed and seconds at the start of a turn, to break the robot free
TURN_EARLY = 13.0          # tape angle (degrees) before horizontal at which a turn stops (it turns on 11-14 degrees)
TURN_LOST = 25.0           # within this many degrees of horizontal, the edge leaving the image also ends the turn
TURN_JUMP = 10.0           # degrees the angle may jump back before it counts as another tape piece
TURN_OUT_MAX = 2.5         # seconds the turn out may take
TURN_IN_MIN = 0.4          # seconds the turn back lasts at least (it starts on the lane, crossing it at an angle)
TURN_IN_MAX = 2.2          # seconds the turn back may take (longer: it turned past the lane)
TURN_IN_CENTERED = 0.4     # |lane_x| below which the turn back ends; ROAD_RECOVERY then centers the robot
TURN_PAST = 0.5            # seconds without the lane after it was seen in the turn back: turned past it (TURN1)
TURN_BACK_MAX = 1.5        # seconds the turn the other way may take
TURN_BACK_SURE = 0.6       # lane model value that ends a turn back without the two-line check (TURN1, TURN2)
CUP_NEAR_CM = 50.0         # during a swerve only bands this close count (cups further back are not this one)
CUP_EDGE = 0.6             # image x (0..1 toward the edge) from which a cup that is gone counts as left sideways
ARC_WHEELS = (0.36, 0.31)  # outer and inner wheel in the curve around the cup: a circle of about 35 cm radius
ARC_STRAIGHT = 0.335       # both wheels while the cup is in view during the curve: drive on past it
ARC_STOP_CM = 16.0         # a band this close in the middle of the image during the curve: stop
ARC_STOP_X = 0.5           # |band x| below which that band counts as in the middle
ARC_TURN_MIN = 3.0         # seconds of curving before the curve may end: about 90 degrees (ARC1, estimate; measure with
                           # `tools/motion_test.py arc`)
ARC_MIN = 1.0              # seconds of curve before tape under the nose counts (at the start it is the old lane)
ARC_EARLY = 5.0            # tape angle (degrees) before horizontal at which the curve ends
TAPE_UNDER_ROW = 215 / 224.0  # lowest tape at this row: the lane's border is under the robot's nose
TAPE_PAST_ROW = 175 / 224.0   # lowest tape back above this row: the border is crossed
ARC_STRAIGHT_AFTER = 3.5   # seconds after which the curve goes straight (after ARC_TURN_MIN): no circling on the floor
ARC_MAX = 8.0              # seconds the curve may take in all

# Road recovery
RECOVER_SPEED = 0.31       # forward speed while the lane is not seen (the slowest that moves the robot)
RECOVER_TURN = 0.04        # gentle turn while the lane is not seen
RECOVER_CENTERED = 0.15    # |lane_x| below which the lane counts as found (and the lane mask sees the robot aligned)
RECOVER_FRAMES = 5         # steps in a row with the lane found before normal following resumes
RECOVER_TIMEOUT = 4.0      # seconds without finding the lane before LINE_RECOVERY
