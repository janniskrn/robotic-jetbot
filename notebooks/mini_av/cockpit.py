"""The cockpit's robot side: one camera and one Perception, used by the idle loop or by one job (COCK1).

Idle: the perception runs with the motors off, so the cockpit shows what the robot sees.
A job (a drive.py run, a motion test, the cup distance survey) owns the camera and the motors while it runs and
reports every step through publish(). The page shows the mode 'DRIVING' for all of them.
"""

import collections
import json
import os
import re
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
from tools import cup_learn, motion_test

BATTERY_PERIOD = 2.0      # seconds between battery readings in idle
CAMERA_DEAD = 10.0        # seconds without a new frame in idle before the cockpit gives up (the service restarts it)
EXIT_CAMERA_DEAD = 3      # exit code for a dead camera: scripts/dashboard.sh then resets the camera service
MAX_SECONDS = 600.0       # longest run the cockpit starts
MAX_REPEATS = 10          # most repeats of a motion test
RECENT_RUNS = 10          # jobs listed in the page's history
NAME = re.compile(r'[A-Za-z0-9_-]{1,40}')  # run names and cup labels become folder names
DRIVE_MODES = {'adaptive': {}, 'baseline': {'baseline': True}, 'nocurve': {'use_curve': False}}  # drive.py's flags
PASS_SIDES = {'auto': None, 'left': 'left', 'right': 'right'}  # auto: the inside of the oval
JOBS = {'drive': drive.run, 'motion_test': motion_test.run, 'cup_learn': cup_learn.run}


class Shared(object):
    """The latest values for the web page. publish() is called by the idle loop or the driving loop (keep it cheap)."""

    def __init__(self):
        self.cond = threading.Condition()  # woken by each publish
        self.seq = 0
        self.values = {}
        self.mode = 'IDLE'
        self.last_reason = None
        self.fps = 0.0
        self.viewers = 0  # open event streams: the idle loop runs the models only while someone watches
        self._count, self._since = 0, time.time()

    def watch(self, delta):
        with self.cond:
            self.viewers += delta

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
    """Runs the perception with the motors off while someone watches. A camera without frames for CAMERA_DEAD,
    or any error, ends the process: the service starts it again"""
    try:
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
            if shared.viewers == 0:
                continue  # nobody watches: no models, only the camera check (saves CPU and GPU)
            if seen_at - read_at >= BATTERY_PERIOD:
                volts, read_at = read_voltage(), seen_at
            shared.publish(frame, idle_values(perception.observe(frame), volts))
    except Exception:
        traceback.print_exc()
        os._exit(1)


def number(body, key, low, high, default=None, whole=False):
    """body[key] (or default) as a number from low to high, or ValueError"""
    value = body.get(key, default)
    if (isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high
            or (whole and value != int(value))):
        raise ValueError('%s must be a %s from %g to %g' % (key, 'whole number' if whole else 'number', low, high))
    return int(value) if whole else float(value)


def name(body, key, default=None):
    """body[key] (or default) as a name for a folder, or ValueError"""
    value = body.get(key, default)
    if not isinstance(value, str) or not NAME.fullmatch(value):
        raise ValueError('%s must be 1 to 40 letters, digits, - or _' % key)
    return value


def choice(body, key, options, default=None):
    """body[key] (or default) if it is one of options, or ValueError"""
    value = body.get(key, default)
    if isinstance(value, (dict, list)) or value not in options:
        raise ValueError('%s must be one of %s' % (key, ', '.join(json.dumps(option) for option in options)))
    return value


def parse_start(body):
    """(job, options, title) from the start request's JSON object, or ValueError. job: a key of JOBS; options: the
    keyword arguments of its run(); title: the job in words, for the page"""
    if not isinstance(body, dict):
        raise ValueError('expected a JSON object')
    job = choice(body, 'job', JOBS, 'drive')
    if job == 'drive':
        mode, side = choice(body, 'mode', DRIVE_MODES), choice(body, 'pass_side', PASS_SIDES, 'auto')
        stop_only, seconds = choice(body, 'stop_only', (False, True), False), number(body, 'seconds', 1, MAX_SECONDS)
        options = dict(DRIVE_MODES[mode], name=name(body, 'name', mode), seconds=seconds, stop_only=stop_only,
                       pass_side=PASS_SIDES[side])
        return job, options, 'drive %s%s, %.0f s, cups: %s, pass %s' % (
            mode, '' if options['name'] == mode else ' "%s"' % options['name'], seconds,
            'stop' if stop_only else 'avoid', side)
    if job == 'motion_test':
        test, repeats = choice(body, 'test', motion_test.TESTS), number(body, 'repeats', 1, MAX_REPEATS, 1, True)
        return job, dict(test=test, repeats=repeats), 'motion test %s x%d' % (test, repeats)
    label = name(body, 'label')
    pulses = number(body, 'pulses', 0, cup_learn.MAX_PULSES, cup_learn.MAX_PULSES, True)
    return job, dict(label=label, pulses=pulses), 'cup distance %s, %d pulses' % (label, pulses)


class Cockpit(object):
    """Owns the idle loop and the job thread: only one of them uses the camera's frames for the models"""

    def __init__(self):
        self.shared = Shared()
        self.perception = Perception(use_curve=True)  # loaded once: two copies of the models do not fit in memory
        try:
            self.camera = Camera.instance()  # opened once (Argus cannot reopen it); after the models, which can fail
        except Exception:
            traceback.print_exc()
            print('camera does not open: exit for a restart', flush=True)
            os._exit(EXIT_CAMERA_DEAD)
        self.streamer = Streamer(self.camera)
        self.lock = threading.Lock()
        self.idle, self.idle_stop = None, None
        self.job_thread, self.job_stop, self.job_title = None, None, None
        self.runs = collections.deque(maxlen=RECENT_RUNS)  # the finished jobs, newest first

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

    def start_job(self, job, options, title):
        """Starts JOBS[job](**options); False if a job is already running"""
        with self.lock:
            if self.shared.mode == 'DRIVING':
                return False
            self.shared.set_mode('DRIVING')
            self.job_stop, self.job_title = threading.Event(), title
            self.job_thread = threading.Thread(target=self._run_job, args=(job, options, title, self.job_stop),
                                               daemon=True)
        self.stop_idle()
        self.job_thread.start()
        return True

    def _run_job(self, job, options, title, stop_event):
        reason, folder = '%s crashed: see the cockpit log (journalctl -u jetbot-cockpit)' % job, None
        started = time.time()
        try:
            reason, folder = JOBS[job](stop_event=stop_event, on_step=self.shared.publish, perception=self.perception,
                                       camera=self.camera, **options)
        except Exception:
            traceback.print_exc()
        finally:
            self.perception.use_curve_model(True)  # idle shows the curve model again
            with self.lock:  # idle first: a start right after must find the idle loop to stop it
                self.runs.appendleft({'started': time.strftime('%H:%M:%S', time.localtime(started)), 'job': title,
                                      'seconds': round(time.time() - started, 1), 'result': reason, 'folder': folder})
                self.start_idle()
                self.shared.set_mode('IDLE', reason)

    def stop_job(self):
        if self.job_stop is not None:
            self.job_stop.set()

    def state(self):
        """Everything the web page shows, as one JSON-ready dict"""
        shared = self.shared
        with shared.cond:
            values, mode, reason, fps, seq = dict(shared.values), shared.mode, shared.last_reason, shared.fps, shared.seq
        with self.lock:
            runs, title = list(self.runs), self.job_title
        volts = values.get('battery_v')
        return {'seq': seq, 'mode': mode, 'last_reason': reason, 'fps': fps, 'runs': runs,
                'job': title if mode == 'DRIVING' else None,
                'stream_fps': self.streamer.raw.fps, 'overlay_fps': self.streamer.overlay.fps,
                'battery_pct': charge_percent(volts) if volts else None, 'values': values}

    def shutdown(self):
        self.stop_job()
        if self.job_thread is not None:
            self.job_thread.join()  # every job stops the motors in its finally
        self.stop_idle()
        self.streamer.stop()
        self.camera.stop()
