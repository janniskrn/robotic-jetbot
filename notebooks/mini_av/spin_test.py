"""Measures how fast the robot turns in place at a few wheel speeds, from the camera (AVOID3: no encoders, no gyro).

    python3 spin_test.py                        # the speeds in SPEEDS
    python3 spin_test.py 0.28 0.27 --kick       # other speeds, each started with a short kick

The robot stands on the lane and spins left in place at each speed for SPIN_SECONDS, saving every frame with its
time. A full turn shows the start view again, so the frames give the turn rate (analyzed offline) and views at
known angles to test a "turned 90 degrees" check. Run inside the container.
"""

import csv
import os
import sys
import time

import cv2
from jetbot import Camera, Robot

from recorder import DATASET_ROOT
from safety import BatteryGuard, MotorWatchdog, wait_for_new_frame

SPEEDS = (0.35, 0.30, 0.25)  # wheel speeds to test (0.35 turned about 130 degrees in 0.36 s, run avoid_ccw_2)
SPIN_SECONDS = 4.0           # long enough for more than one full turn
KICK = (0.35, 0.1)           # wheel speed and seconds to break the robot free (0.25 did not start turning on its own)
PAUSE_SECONDS = 1.5          # standing still between the speeds (the camera view settles)


def main():
    kick = '--kick' in sys.argv
    speeds = [float(a) for a in sys.argv[1:] if a != '--kick'] or SPEEDS
    battery = BatteryGuard()
    if not battery.start_ok():
        raise SystemExit('battery %.2f V is too low: charge first' % battery.volts)
    robot = Robot()
    camera = Camera.instance()
    watchdog = MotorWatchdog(robot)
    out = os.path.join(DATASET_ROOT, time.strftime('%Y-%m-%d_%H-%M-%S') + '_spin_test')
    os.makedirs(out)
    shots = []  # (time, speed, frame), written after the motors are off
    try:
        frame = wait_for_new_frame(camera, camera.value, timeout=2.0)
        watchdog.start()
        start = time.time()
        for speed in speeds:
            for spinning, seconds in ((True, SPIN_SECONDS), (False, PAUSE_SECONDS)):
                since = time.time()
                while time.time() - since < seconds:
                    if not spinning:
                        left = 0.0
                    elif kick and time.time() - since < KICK[1]:
                        left = -KICK[0]
                    else:
                        left = -speed
                    battery.check()
                    with watchdog.lock:
                        robot.set_motors(left, -left)
                    watchdog.feed()
                    frame = wait_for_new_frame(camera, frame)
                    shots.append((time.time() - start, speed if spinning else 0.0, frame.copy()))
    except KeyboardInterrupt:
        print('stopped by hand')
    finally:
        watchdog.running = False
        with watchdog.lock:
            robot.stop()
        camera.stop()
    with open(os.path.join(out, 'frames.csv'), 'w') as f:
        rows = csv.writer(f)
        rows.writerow(['frame', 'time', 'speed'])
        for i, (t, speed, image) in enumerate(shots):
            cv2.imwrite(os.path.join(out, 'frame_%05d.jpg' % i), image)
            rows.writerow(['frame_%05d.jpg' % i, '%.3f' % t, speed])
    print('%d frames in %s, battery %.2f V, kick %s' % (len(shots), out, battery.volts, kick))


if __name__ == '__main__':
    main()
