"""Web cockpit: live camera with the overlay, the robot's state, and start/stop buttons. Serves on port 8080.

    scripts/dashboard.sh          (close the 04/05 notebook kernels first: one program owns the camera)
    open http://<robot-ip>:8080/  stop with scripts/stop_robot.sh

Idle: the camera and the perception run with the motors off. Driving: drive.run owns camera and motors.
"""

import http.server
import json
import os
import signal
import socket
import socketserver
import threading
import time
import traceback
import urllib.parse

import cv2

from jetbot import Camera

import drive
import situation
from battery import charge_percent, read_voltage
from decision import cup_ahead, band_cm
from perception import Perception
from safety import CameraFrozen, wait_for_new_frame, STALE_TIMEOUT

PORT = 8080
JPEG_QUALITY = 90
# the overlay costs about 31 ms of CPU in the driving process, so it is drawn less often while driving
OVERLAY_HZ_IDLE = 15    # overlay pictures per second when idle
OVERLAY_HZ_DRIVING = 5  # overlay pictures per second while driving
OVERLAY_POLL = 0.01     # seconds between checks whether an overlay picture is due
STREAMER_WAIT = 1.0     # seconds the streamer waits for a camera frame before it checks for stop
CLIENT_WAIT = 2.0       # seconds a stream waits for a new picture before it checks again
BATTERY_PERIOD = 2.0    # seconds between battery readings in idle
MAX_SECONDS = 600.0     # longest run the cockpit starts
MODES = ('adaptive',)  # the shared Perception has the curve model loaded, as the adaptive mode needs
HERE = os.path.dirname(os.path.abspath(__file__))


class Shared(object):
    """Latest camera frame and values, read by the web handlers. Stores references only (cheap for the driving loop)."""

    def __init__(self):
        self.lock = threading.Lock()
        self.cond = threading.Condition(self.lock)  # woken by each publish
        self.frame = None
        self.seq = 0  # counts the published frames
        self.values = {}
        self.mode = 'IDLE'
        self.last_reason = None
        self.fps = 0.0
        self.stream_fps = 0.0   # raw pictures encoded per second (set by the Streamer)
        self.overlay_fps = 0.0  # overlay pictures encoded per second (set by the Streamer)
        self._count, self._since = 0, time.time()

    def publish(self, frame, values):
        with self.lock:
            self.frame, self.values = frame, values
            self.seq += 1
            self.cond.notify_all()
            self._count += 1
            now = time.time()
            if now - self._since >= 1.0:
                self.fps, self._count, self._since = self._count / (now - self._since), 0, now

    def set_mode(self, mode, reason=None):
        with self.lock:
            self.mode = mode
            if reason is not None:
                self.last_reason = reason

    def snapshot(self):
        with self.lock:
            volts = self.values.get('battery_v')
            return {'mode': self.mode, 'last_reason': self.last_reason, 'fps': self.fps, 'stream_fps': self.stream_fps,
                    'overlay_fps': self.overlay_fps, 'battery_pct': charge_percent(volts) if volts else None,
                    'values': dict(self.values)}


def idle_values(percept, volts):
    ahead = cup_ahead(percept)
    return {'mode': 'IDLE', 'lane_visible': percept['lane_visible'], 'lane_x': percept['lane_x'],
            'curve_class': percept['curve_class'], 'cup_visible': percept['cup_visible'],
            'band_cm': band_cm(ahead) if ahead else None, 'battery_v': volts,
            'inference_ms': percept['inference_ms']}


def idle_loop(shared, perception, camera, stop):
    """Looks at the camera with the motors off, so the cockpit shows what the robot sees."""
    frame = camera.value
    volts, read_at = read_voltage(), time.time()
    while not stop.is_set():
        try:
            frame = wait_for_new_frame(camera, frame)
        except CameraFrozen:
            continue
        if time.time() - read_at >= BATTERY_PERIOD:
            volts, read_at = read_voltage(), time.time()
        shared.publish(frame, idle_values(perception.observe(frame), volts))


class Cockpit(object):
    """Owns the idle loop and the driving thread: only one of them uses the camera at a time."""

    def __init__(self):
        self.shared = Shared()
        self.streamer = Streamer(self.shared)
        self.camera = Camera.instance()  # opened once: Argus cannot reopen it in the same process
        self.perception = Perception(use_curve=True)  # loaded once: two copies of the models do not fit in memory
        self.lock = threading.Lock()
        self.idle, self.idle_stop = None, None
        self.drive_thread, self.drive_stop = None, None

    def start_idle(self):
        self.idle_stop = threading.Event()
        self.idle = threading.Thread(target=idle_loop, args=(self.shared, self.perception, self.camera, self.idle_stop), daemon=True)
        self.idle.start()

    def stop_idle(self):
        if self.idle is not None:
            self.idle_stop.set()
            self.idle.join()
            self.idle = None

    def start_drive(self, mode, seconds):
        with self.lock:
            if self.shared.mode == 'DRIVING':
                return False
            self.shared.set_mode('DRIVING')
            self.drive_stop = threading.Event()
            self.drive_thread = threading.Thread(target=self._drive, args=(mode, seconds, self.drive_stop), daemon=True)
        self.stop_idle()
        self.drive_thread.start()
        return True

    def _drive(self, mode, seconds, stop_event):
        reason = 'drive crashed: see the dashboard terminal'
        try:
            reason, _ = drive.run(mode, seconds, stop_event=stop_event, on_step=self.shared.publish,
                                  perception=self.perception, camera=self.camera)
        finally:
            self.shared.set_mode('IDLE', reason)
            self.start_idle()

    def stop_drive(self):
        if self.drive_stop is not None:
            self.drive_stop.set()

    def shutdown(self):
        self.stop_drive()
        if self.drive_thread is not None:
            self.drive_thread.join()  # drive.run stops the motors in its finally
        self.stop_idle()
        self.streamer.stop()
        self.camera.stop()


def encode(image):
    return cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])[1].tobytes()


class Streamer(object):
    """Encodes each new camera frame once, in one thread. The clients send these buffers, so none encodes its own copy."""

    def __init__(self, shared):
        self.shared = shared
        self.cond = threading.Condition()  # guards the buffers and the overlay viewer count
        self.raw_seq, self.raw_jpeg = 0, None
        self.overlay_seq, self.overlay_jpeg = 0, None
        self.overlay_viewers = 0
        self.overlay_at = 0.0  # when the last overlay picture was made
        self.rate_since, self.raw_count, self.overlay_count = time.time(), 0, 0
        self.stop_event = threading.Event()
        self.threads = [threading.Thread(target=self._run, daemon=True),
                        threading.Thread(target=self._run_overlay, daemon=True)]

    def start(self):
        for thread in self.threads:
            thread.start()

    def stop(self):
        self.stop_event.set()
        for thread in self.threads:
            thread.join()

    def count_overlay_viewer(self, delta):
        with self.cond:
            self.overlay_viewers += delta

    def wait_for_new(self, overlay, seen):
        """Waits until the buffer's sequence number is above seen, or CLIENT_WAIT seconds pass. Returns (seq, jpeg)."""
        with self.cond:
            self.cond.wait_for(lambda: self._buffer(overlay)[0] > seen, timeout=CLIENT_WAIT)
            return self._buffer(overlay)

    def _buffer(self, overlay):
        return (self.overlay_seq, self.overlay_jpeg) if overlay else (self.raw_seq, self.raw_jpeg)

    def _run(self):
        seen = 0
        while not self.stop_event.is_set():
            with self.shared.cond:
                self.shared.cond.wait_for(lambda: self.shared.seq != seen, timeout=STREAMER_WAIT)
                seq, frame = self.shared.seq, self.shared.frame
            if seq != seen:
                seen = seq
                try:
                    self._encode(frame)
                except Exception:  # one bad frame must not freeze every stream
                    traceback.print_exc()

    def _encode(self, frame):
        """The raw picture for every new frame: cheap (about 1 ms), so the raw stream runs at the camera rate."""
        raw = encode(frame)
        with self.cond:
            self.raw_seq, self.raw_jpeg = self.raw_seq + 1, raw
            self.cond.notify_all()
        self._count_rates(time.time(), False)

    def _run_overlay(self):
        """The overlay in its own thread: it costs about 31 ms, so the raw stream never waits for it."""
        drawn = 0
        while not self.stop_event.is_set():
            now = time.time()
            seq, frame = self.shared.seq, self.shared.frame
            if seq == drawn or frame is None or not self._overlay_due(now):
                time.sleep(OVERLAY_POLL)
                continue
            drawn, self.overlay_at = seq, now
            try:
                overlay = encode(situation.picture(frame))
            except Exception:  # one bad frame must not freeze the overlay stream
                traceback.print_exc()
                continue
            with self.cond:
                self.overlay_seq, self.overlay_jpeg = self.overlay_seq + 1, overlay
                self.cond.notify_all()
            self._count_rates(now, True)

    def _overlay_due(self, now):
        with self.cond:
            watched = self.overlay_viewers > 0
        hz = OVERLAY_HZ_DRIVING if self.shared.mode == 'DRIVING' else OVERLAY_HZ_IDLE
        return watched and now - self.overlay_at >= 1.0 / hz

    def _count_rates(self, now, overlay):
        with self.cond:  # called from both threads
            if overlay:
                self.overlay_count += 1
            else:
                self.raw_count += 1
            span = now - self.rate_since
            if span >= 1.0:
                self.shared.stream_fps = self.raw_count / span
                self.shared.overlay_fps = self.overlay_count / span
                self.raw_count, self.overlay_count, self.rate_since = 0, 0, now


def parse_start(body):
    """Returns (mode, seconds) from the POST body, or raises ValueError"""
    mode, seconds = body.get('mode'), body.get('seconds')
    if mode not in MODES:
        raise ValueError('mode must be one of %s' % ', '.join(MODES))
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not 0 < seconds <= MAX_SECONDS:
        raise ValueError('seconds must be a number from 0 to %d' % MAX_SECONDS)
    return mode, float(seconds)


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # no per-request lines in the terminal

    def send_bytes(self, data, content_type, code=200):
        try:
            self.send_response(code)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass  # the browser closed the request before the answer

    def send_json(self, obj, code=200):
        self.send_bytes(json.dumps(obj, default=float).encode(), 'application/json', code)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path == '/':
            with open(os.path.join(HERE, 'web', 'index.html'), 'rb') as page:
                self.send_bytes(page.read(), 'text/html; charset=utf-8')
        elif url.path == '/state.json':
            self.send_json(self.server.cockpit.shared.snapshot())
        elif url.path == '/stream.mjpg':
            overlay = urllib.parse.parse_qs(url.query).get('overlay', ['1'])[0] != '0'
            self.stream(overlay)
        else:
            self.send_bytes(b'not found', 'text/plain', 404)

    def stream(self, overlay):
        streamer = self.server.cockpit.streamer
        self.send_response(200)
        self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
        self.end_headers()
        if overlay:
            streamer.count_overlay_viewer(1)
        sent = 0
        try:
            self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # send each picture at once
            while True:
                seq, data = streamer.wait_for_new(overlay, sent)
                if seq > sent:
                    self.wfile.write(b'--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n' % len(data)
                                     + data + b'\r\n')
                    self.wfile.flush()
                    sent = seq
        except (BrokenPipeError, ConnectionResetError):
            pass  # the browser closed the picture
        finally:
            if overlay:
                streamer.count_overlay_viewer(-1)

    def do_POST(self):
        cockpit = self.server.cockpit
        if self.path == '/stop':
            cockpit.stop_drive()
            self.send_json({'ok': True})
        elif self.path == '/start':
            try:
                length = int(self.headers.get('Content-Length', 0))
                mode, seconds = parse_start(json.loads(self.rfile.read(length).decode()))
            except (ValueError, AttributeError) as error:  # bad JSON, or not an object
                self.send_json({'error': str(error)}, 400)
                return
            if cockpit.start_drive(mode, seconds):
                self.send_json({'ok': True})
            else:
                self.send_json({'error': 'already driving'}, 409)
        else:
            self.send_bytes(b'not found', 'text/plain', 404)


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


def raise_interrupt(signum, frame):
    raise KeyboardInterrupt  # SIGTERM gets the same clean stop as Ctrl-C


def main():
    signal.signal(signal.SIGTERM, raise_interrupt)
    server = Server(('0.0.0.0', PORT), Handler)
    server.cockpit = Cockpit()
    server.cockpit.start_idle()
    server.cockpit.streamer.start()
    print('dashboard on port %d: open http://<robot-ip>:%d/' % (PORT, PORT), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.cockpit.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
