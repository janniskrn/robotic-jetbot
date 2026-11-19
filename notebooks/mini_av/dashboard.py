"""Web cockpit on port 8080: live camera, the robot's state as it happens, start and stop.

Runs as the service jetbot-cockpit (scripts/jetbot-cockpit.service): starts at boot, restarts after a failure.
    sudo systemctl stop jetbot-cockpit     # free the camera for the 04/05 notebooks
    journalctl -u jetbot-cockpit -f        # its log

Endpoints:
    /               the page (web/)
    /events         the state as Server-Sent Events, one per driving step (at most EVENT_HZ)
    /state.json     the state once
    /stream.mjpg    the camera as MJPEG, ?overlay=1 with the situation overlay
    POST /start     {"mode": "adaptive", "seconds": 30};  POST /stop
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

from cockpit import Cockpit, parse_start

PORT = 8080
EVENT_HZ = 30          # most state events per second and viewer (the driving loop runs at about 20 Hz)
KEEPALIVE = 5.0        # seconds without a new state before an event stream sends a comment line
WRITE_TIMEOUT = 5.0    # seconds a write to a viewer may block: a viewer gone without a word is dropped
MAX_BODY = 4096        # bytes of a POST body
SHUTDOWN_MAX = 20.0    # seconds the clean stop may take before the process exits anyway
HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = {'/': ('index.html', 'text/html; charset=utf-8'),
          '/app.js': ('app.js', 'application/javascript; charset=utf-8'),
          '/style.css': ('style.css', 'text/css; charset=utf-8')}


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # no line per request in the log

    def send_bytes(self, data, content_type, code=200):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, obj, code=200):
        self.send_bytes(json.dumps(obj, default=float).encode(), 'application/json', code)

    def start_stream(self, content_type):
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # send each piece at once
        self.connection.settimeout(WRITE_TIMEOUT)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        try:
            if url.path in STATIC:
                name, content_type = STATIC[url.path]
                with open(os.path.join(HERE, 'web', name), 'rb') as f:
                    self.send_bytes(f.read(), content_type)
            elif url.path == '/state.json':
                self.send_json(self.server.cockpit.state())
            elif url.path == '/events':
                self.events()
            elif url.path == '/stream.mjpg':
                self.video(urllib.parse.parse_qs(url.query).get('overlay', ['0'])[0] == '1')
            else:
                self.send_bytes(b'not found', 'text/plain', 404)
        except OSError:
            pass  # the browser went away, or stopped reading (timeout)

    def events(self):
        """One event with the full state after each new state, at most EVENT_HZ per second"""
        cockpit = self.server.cockpit
        self.start_stream('text/event-stream')
        cockpit.shared.watch(1)
        try:
            seen = -1
            while True:
                started = time.time()
                seq = cockpit.shared.wait_newer(seen, KEEPALIVE)
                if seq == seen:
                    self.wfile.write(b': keepalive\n\n')
                else:
                    self.wfile.write(b'data: ' + json.dumps(cockpit.state(), default=float).encode() + b'\n\n')
                    seen = seq
                self.wfile.flush()
                time.sleep(max(0.0, 1.0 / EVENT_HZ - (time.time() - started)))
        finally:
            cockpit.shared.watch(-1)

    def video(self, overlay):
        """MJPEG: every new picture of the feed, as soon as it is encoded"""
        feed = self.server.cockpit.streamer.feed(overlay)
        self.start_stream('multipart/x-mixed-replace; boundary=frame')
        feed.watch(1)
        try:
            sent = 0
            while True:
                seq, jpeg = feed.wait_newer(sent)
                if seq > sent:
                    self.wfile.write(b'--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n' % len(jpeg)
                                     + jpeg + b'\r\n')
                    self.wfile.flush()
                    sent = seq
        finally:
            feed.watch(-1)

    def do_POST(self):
        cockpit = self.server.cockpit
        try:
            if self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/json':
                # a page from elsewhere cannot send this without asking first (CORS), so it cannot start the robot
                self.send_json({'error': 'Content-Type must be application/json'}, 415)
                return
            if self.path == '/stop':
                cockpit.stop_drive()
                self.send_json({'ok': True})
            elif self.path == '/start':
                try:
                    length = int(self.headers.get('Content-Length', 0))
                    if not 0 <= length <= MAX_BODY:
                        raise ValueError('body too large')
                    mode, seconds = parse_start(json.loads(self.rfile.read(length).decode() or 'null'))
                except ValueError as error:  # bad JSON or bad values
                    self.send_json({'error': str(error)}, 400)
                    return
                if cockpit.start_drive(mode, seconds):
                    self.send_json({'ok': True})
                else:
                    self.send_json({'error': 'already driving'}, 409)
            else:
                self.send_bytes(b'not found', 'text/plain', 404)
        except OSError:
            pass


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True       # open streams do not keep the process alive
    allow_reuse_address = True  # a restart can bind the port again at once


def raise_interrupt(signum, frame):
    raise KeyboardInterrupt  # SIGTERM gets the same clean stop as Ctrl-C


def main():
    signal.signal(signal.SIGTERM, raise_interrupt)
    cockpit = Cockpit()
    code = 0
    try:
        server = Server(('0.0.0.0', PORT), Handler)
        server.cockpit = cockpit
        cockpit.start()
        print('cockpit on port %d: open http://<robot-ip>:%d/' % (PORT, PORT), flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    except Exception:  # for example the port is taken: exit, the service starts it again
        traceback.print_exc()
        code = 1
    finally:
        signal.signal(signal.SIGINT, signal.SIG_IGN)  # a second Ctrl-C must not cut the clean stop short
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        stopper = threading.Thread(target=cockpit.shutdown, daemon=True)  # a dead camera can hang its stop
        stopper.start()
        stopper.join(SHUTDOWN_MAX)
    os._exit(code)  # the camera's capture thread must not keep the process alive


if __name__ == '__main__':
    main()
