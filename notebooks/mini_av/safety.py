"""Safety checks shared by every program that drives the motors (DECISIONS.md, SAFETY)."""

import threading
import time

from battery import read_voltage

MOTOR_TIMEOUT = 0.25  # seconds without a motor update before the watchdog stops the motors (the loop stalled up to 1.1 s)
STALE_TIMEOUT = 0.5  # seconds without a new camera frame before the robot stops (the camera froze on 2026-09-20)

# On 2026-09-20 the Jetson lost power mid-session (voltage sag under motor load).
MIN_START_VOLTAGE = 11.4  # volts at rest (about 50 %) needed to start driving
MIN_RUN_VOLTAGE = 10.8    # volts under load; staying below this stops the run before the Jetson browns out
LOW_VOLTAGE_TIME = 2.0    # seconds below MIN_RUN_VOLTAGE before stopping (short dips at start-up are normal)
VOLTAGE_PERIOD = 0.5      # seconds between battery readings


class CameraFrozen(Exception):
    """The camera stopped delivering new frames: the robot must not drive on an old image"""


class BatteryLow(Exception):
    """The battery voltage stayed too low under load"""


def wait_for_new_frame(camera, old, timeout=STALE_TIMEOUT):
    """Returns a frame newer than old; raises CameraFrozen if none arrives in time.

    The JetBot camera thread ends silently on a read error and camera.value then keeps the last
    image forever, so every new frame is a new array object: the same object means no new frame.
    """
    start = time.time()
    while camera.value is old:
        if time.time() - start > timeout:
            raise CameraFrozen()
        time.sleep(0.005)
    return camera.value


class BatteryGuard(object):
    """Reads the battery every VOLTAGE_PERIOD seconds and raises BatteryLow if it stays too low"""

    def __init__(self):
        self.volts = read_voltage()
        self._last_read = time.time()
        self._low_since = None

    def start_ok(self):
        return self.volts >= MIN_START_VOLTAGE

    def check(self):
        now = time.time()
        if now - self._last_read < VOLTAGE_PERIOD:
            return self.volts
        self.volts, self._last_read = read_voltage(), now
        if self.volts >= MIN_RUN_VOLTAGE:
            self._low_since = None
        elif self._low_since is None:
            self._low_since = now
        elif now - self._low_since > LOW_VOLTAGE_TIME:
            raise BatteryLow('battery low (%.2f V)' % self.volts)
        return self.volts


class MotorWatchdog(threading.Thread):
    """Stops the motors when the control loop has not updated them for MOTOR_TIMEOUT seconds.

    The loop can stall (first model call, a slow write): then the robot must wait, not drive blind.
    """

    def __init__(self, robot, timeout=MOTOR_TIMEOUT):
        threading.Thread.__init__(self, daemon=True)
        self.robot = robot
        self.timeout = timeout
        self.last_feed = time.time()
        self.running = True
        self.lock = threading.Lock()  # the control loop holds it too: no interleaved I2C motor writes

    def feed(self):
        """Called by the control loop every time it sets the motors"""
        self.last_feed = time.time()

    def run(self):
        while self.running:
            if time.time() - self.last_feed > self.timeout:
                try:
                    with self.lock:
                        self.robot.stop()
                except Exception as error:  # a transient I2C error must not end the watchdog
                    print('motor watchdog: %s' % error)
            time.sleep(0.05)
