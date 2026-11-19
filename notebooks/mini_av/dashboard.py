"""Web cockpit: live camera with the overlay, the robot's state, and start/stop buttons. Serves on port 8080.

    scripts/dashboard.sh          (close the 04/05 notebook kernels first: one program owns the camera)
    open http://<robot-ip>:8080/  stop with scripts/stop_robot.sh

Idle: the camera and the perception run with the motors off. Driving: drive.run owns camera and motors.
"""

import http.server
import json
import os
import signal
import socketserver
import threading
import time
import urllib.parse

import cv2

from jetbot import Camera

import drive
import situation
from battery import read_voltage
from decision import cup_ahead, band_cm
from perception import Perception
from safety import CameraFrozen, wait_for_new_frame, STALE_TIMEOUT

PORT = 8080
STREAM_HZ = 5           # camera pictures per second sent to the browser
JPEG_QUALITY = 80
BATTERY_PERIOD = 2.0    # seconds between battery readings in idle
MAX_SECONDS = 600.0     # longest run the cockpit starts
MODES = ('adaptive',)  # the shared Perception has the curve model loaded, as the adaptive mode needs
HERE = os.path.dirname(os.path.abspath(__file__))


class Shared(object):
    """Latest camera frame and values, read by the web handlers. Stores references only (cheap for the driving loop)."""

    def __init__(self):
        self.lock = threading.Lock()
        self.frame = None
        self.values = {}
        self.mode = 'IDLE'
        self.last_reason = None
        self.fps = 0.0
        self._count, self._since = 0, time.time()

    def publish(self, frame, values):
        with self.lock:
            self.frame, self.values = frame, values
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
            return {'mode': self.mode, 'last_reason': self.last_reason, 'fps': self.fps, 'values': dict(self.values)}


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
        self.camera.stop()


def jpeg(frame, overlay):
    image = situation.picture(frame) if overlay else cv2.resize(frame, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
    return cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])[1].tobytes()


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
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

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
        self.send_response(200)
        self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
        self.end_headers()
        shared = self.server.cockpit.shared
        try:
            while True:
                frame = shared.frame
                if frame is not None:
                    data = jpeg(frame, overlay)
                    self.wfile.write(b'--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n' % len(data)
                                     + data + b'\r\n')
                time.sleep(1.0 / STREAM_HZ)
        except (BrokenPipeError, ConnectionResetError):
            pass  # the browser closed the picture

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
