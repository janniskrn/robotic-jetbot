"""Measures the open-loop motion primitives for the timed avoidance maneuver (D7: no wheel encoders).

    python3 calibrate_motion.py straight   # 1.0 s straight at SPEED
    python3 calibrate_motion.py pivot_left  # 0.5 s turn in place to the left
    python3 calibrate_motion.py pivot_right
    python3 calibrate_motion.py arc_left    # 1.0 s curve to the left (outer wheel faster)
    python3 calibrate_motion.py arc_right

A person measures the distance (cm) or angle (degrees) after each move. Run inside the container, robot on the floor.
"""

import sys
import time

from jetbot import Robot

from safety import BatteryGuard

SPEED = 0.35        # wheel speed of the moves (driving speeds are 0.31-0.40)
ARC_DIFF = 0.10     # wheel speed difference for the arcs
MOVES = {           # name: (left wheel, right wheel, seconds)
    'straight': (SPEED, SPEED, 1.0),
    'pivot_left': (-SPEED, SPEED, 0.5),
    'pivot_right': (SPEED, -SPEED, 0.5),
    'arc_left': (SPEED - ARC_DIFF, SPEED + ARC_DIFF, 1.0),
    'arc_right': (SPEED + ARC_DIFF, SPEED - ARC_DIFF, 1.0),
}


def main():
    move = sys.argv[1] if len(sys.argv) > 1 else ''
    if move not in MOVES:
        raise SystemExit('move must be one of: %s' % ', '.join(MOVES))
    battery = BatteryGuard()
    if not battery.start_ok():
        raise SystemExit('battery %.2f V is too low: charge first' % battery.volts)
    left, right, seconds = MOVES[move]
    robot = Robot()
    try:
        robot.set_motors(left, right)
        time.sleep(seconds)
    except KeyboardInterrupt:
        pass
    finally:
        robot.stop()
    print('%s: left %.2f right %.2f for %.1f s at %.2f V' % (move, left, right, seconds, battery.volts))


if __name__ == '__main__':
    main()
