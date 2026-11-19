"""The cockpit's robot side: one camera and one Perception, used by the idle loop or by a run of drive.py.

Idle: the perception runs with the motors off, so the cockpit shows what the robot sees.
Driving: drive.run owns the camera and the motors and reports every step through publish().
"""

import os
import threading
import time
import traceback

from jetbot import Camera

import drive
from battery import charge_percent, read_voltage
from decision import band_cm, cup_ahead
from perception import Perception
from safety import CameraFrozen, wait_for_new_frame
from streamer import Streamer

BATTERY_PERIOD = 2.0      # seconds between battery readings in idle
CAMERA_DEAD = 10.0        # seconds without a new frame in idle before the cockpit gives up (the service restarts it)
EXIT_CAMERA_DEAD = 3      # exit code for a dead camera: scripts/dashboard.sh then resets the camera service
MAX_SECONDS = 600.0       # longest run the cockpit starts
MODES = ('adaptive',)     # the shared Perception has the curve model loaded, as the adaptive mode needs


class Shared(object):
    """The latest values for the web page. publish() is called by the idle loop or the driving loop (keep it cheap)."""

    def __init__(self):
        self.cond = threading.Condition()  # woken by each publish
        self.seq = 0
        self.values = {}
        self.mode = 'IDLE'
        self.last_reason = None
        self.fps = 0.0
        self._count, self._since = 0, time.time()

    def publish(self, frame, values):
        """on_step of drive.run: the frame is not needed, the video comes straight from the camera"""
        with self.cond:
            self.values, self.seq = values, self.seq + 1
            self.cond.notify_all()
            self._count += 1
            now = time.time()
            if now - self._since >= 1.0:
                self.fps, self._count, self._since = self._count / (now - self._since), 0, now

    def set_mode(self, mode, reason=None):
        with self.cond:
            self.mode = mode
            if reason is not None:
                self.last_reason = reason
            self.seq += 1
            self.cond.notify_all()

    def wait_newer(self, seen, timeout):
        """The sequence number once it is above seen, or after timeout"""
        with self.cond:
            self.cond.wait_for(lambda: self.seq > seen, timeout=timeout)
            return self.seq


def idle_values(percept, volts):
    ahead = cup_ahead(percept)
    return {'mode': 'IDLE', 'lane_visible': percept['lane_visible'], 'lane_x': percept['lane_x'],
            'curve_class': percept['curve_class'], 'curve_dir': percept['curve_dir'],
            'p_straight': percept['curve_probs'][0], 'p_gentle': percept['curve_probs'][1],
            'p_sharp': percept['curve_probs'][2], 'lane_aligned': int(percept['lane_aligned']),
            'cup_visible': percept['cup_visible'], 'band_cm': band_cm(ahead) if ahead else None,
            'battery_v': volts, 'inference_ms': percept['inference_ms']}


def idle_loop(shared, perception, camera, stop):
    """Runs the perception with the motors off. A camera without frames for CAMERA_DEAD ends the process"""
    frame = camera.value
    volts, read_at = read_voltage(), time.time()
    seen_at = time.time()
    while not stop.is_set():
        try:
            frame = wait_for_new_frame(camera, frame)
        except CameraFrozen:
            if time.time() - seen_at > CAMERA_DEAD:
                print('camera sends no frames: exit for a restart', flush=True)
                os._exit(EXIT_CAMERA_DEAD)  # the motors are off in idle; the service resets the camera
            continue
        seen_at = time.time()
        if seen_at - read_at >= BATTERY_PERIOD:
            volts, read_at = read_voltage(), seen_at
        shared.publish(frame, idle_values(perception.observe(frame), volts))


def parse_start(body):
    """(mode, seconds) from the start request's JSON object, or ValueError"""
    if not isinstance(body, dict):
        raise ValueError('expected a JSON object')
    mode, seconds = body.get('mode'), body.get('seconds')
    if mode not in MODES:
        raise ValueError('mode must be one of %s' % ', '.join(MODES))
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not 0 < seconds <= MAX_SECONDS:
        raise ValueError('seconds must be a number from 0 to %d' % MAX_SECONDS)
    return mode, float(seconds)


class Cockpit(object):
    """Owns the idle loop and the driving thread: only one of them uses the camera's frames for the models"""

    def __init__(self):
        self.shared = Shared()
        self.perception = Perception(use_curve=True)  # loaded once: two copies of the models do not fit in memory
        self.camera = Camera.instance()  # opened once (Argus cannot reopen it); after the models, which can fail
        self.streamer = Streamer(self.camera, lambda: self.shared.mode)
        self.lock = threading.Lock()
        self.idle, self.idle_stop = None, None
        self.drive_thread, self.drive_stop = None, None

    def start(self):
        self.streamer.start()
        self.start_idle()

    def start_idle(self):
        self.idle_stop = threading.Event()
        self.idle = threading.Thread(target=idle_loop, args=(self.shared, self.perception, self.camera,
                                                             self.idle_stop), daemon=True)
        self.idle.start()

    def stop_idle(self):
        if self.idle is not None:
            self.idle_stop.set()
            self.idle.join()
            self.idle = None

    def start_drive(self, mode, seconds):
        """False if a run is already going"""
        with self.lock:
            if self.shared.mode == 'DRIVING':
                return False
            self.shared.set_mode('DRIVING')
            self.drive_stop = threading.Event()
            self.drive_thread = threading.Thread(target=self._drive, args=(mode, seconds, self.drive_stop),
                                                 daemon=True)
        self.stop_idle()
        self.drive_thread.start()
        return True

    def _drive(self, mode, seconds, stop_event):
        reason = 'drive crashed: see the cockpit log (journalctl -u jetbot-cockpit)'
        try:
            reason, _ = drive.run(mode, seconds, stop_event=stop_event, on_step=self.shared.publish,
                                  perception=self.perception, camera=self.camera)
        except Exception:
            traceback.print_exc()
        finally:
            self.shared.set_mode('IDLE', reason)
            self.start_idle()

    def stop_drive(self):
        if self.drive_stop is not None:
            self.drive_stop.set()

    def state(self):
        """Everything the web page shows, as one JSON-ready dict"""
        shared = self.shared
        with shared.cond:
            values, mode, reason, fps, seq = dict(shared.values), shared.mode, shared.last_reason, shared.fps, shared.seq
        volts = values.get('battery_v')
        return {'seq': seq, 'mode': mode, 'last_reason': reason, 'fps': fps,
                'stream_fps': self.streamer.raw.fps, 'overlay_fps': self.streamer.overlay.fps,
                'battery_pct': charge_percent(volts) if volts else None, 'values': values}

    def shutdown(self):
        self.stop_drive()
        if self.drive_thread is not None:
            self.drive_thread.join()  # drive.run stops the motors in its finally
        self.stop_idle()
        self.streamer.stop()
        self.camera.stop()
