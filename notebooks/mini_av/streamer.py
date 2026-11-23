"""Video for the cockpit (MJPEG): each picture is encoded once, in one thread, and sent to every viewer.

raw: read straight from the camera, so it runs at the camera rate whatever the driving loop does.
overlay: situation.picture of every new camera frame, drawn in its own process (overlay_worker.py, SPEED2): in this
process its pure Python held the interpreter lock and slowed the driving loop (30 Hz overlay: loop 29.6 -> 25.2 Hz).
Nothing is encoded while nobody watches.
"""

import os
import struct
import subprocess
import sys
import threading
import time
import traceback

import cv2

from safety import CameraFrozen, wait_for_new_frame

JPEG_QUALITY = 85
WAIT = 1.0          # seconds a thread or a viewer waits for a new picture before it checks again
NO_VIEWER = 0.05    # seconds between checks whether someone watches
WORKER_RETRY = 1.0  # seconds to wait after the overlay process failed, before it is started again
WORKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'overlay_worker.py')


def encode(image):
    return cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])[1].tobytes()


class Feed(object):
    """The latest encoded picture of one stream, its viewers and its rate"""

    def __init__(self):
        self.cond = threading.Condition()
        self.seq, self.jpeg = 0, None
        self.viewers = 0
        self.fps = 0.0
        self._count, self._since = 0, time.time()

    def put(self, jpeg):
        with self.cond:
            self.seq, self.jpeg = self.seq + 1, jpeg
            self.cond.notify_all()
            self._count += 1
            now = time.time()
            if now - self._since >= 1.0:
                self.fps, self._count, self._since = self._count / (now - self._since), 0, now

    def wait_newer(self, seen):
        """(seq, jpeg) once a picture newer than seen exists, or after WAIT seconds"""
        with self.cond:
            self.cond.wait_for(lambda: self.seq > seen, timeout=WAIT)
            return self.seq, self.jpeg

    def watch(self, delta):
        with self.cond:
            self.viewers += delta
            if self.viewers == 0:
                self.fps = 0.0

    def watched(self):
        return self.viewers > 0


class OverlayWorker(object):
    """overlay_worker.py as a child process, started on first use and again after it failed"""

    def __init__(self):
        self.process = None
        self.lock = threading.Lock()  # stop() comes from the overlay thread or from the cockpit's shutdown

    def picture(self, frame):
        """The overlay JPEG of one frame"""
        if self.process is None:
            self.process = subprocess.Popen([sys.executable, '-B', WORKER], stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE)
        try:
            height, width = frame.shape[:2]
            self.process.stdin.write(struct.pack('<II', height, width) + frame.tobytes())
            self.process.stdin.flush()
            size, = struct.unpack('<I', self.process.stdout.read(4))  # struct.error: the process ended
            return self.process.stdout.read(size)
        except (OSError, struct.error):
            self.stop()
            time.sleep(WORKER_RETRY)  # a process that fails at once must not be restarted for every frame
            raise

    def stop(self):
        with self.lock:
            if self.process is not None:
                self.process.kill()  # it holds no state: nothing to finish
                self.process.wait()
                self.process = None


class Streamer(object):
    def __init__(self, camera):
        self.camera = camera
        self.raw, self.overlay = Feed(), Feed()
        self.worker = OverlayWorker()
        self.stop_event = threading.Event()
        self.threads = [threading.Thread(target=self._run, args=(self.raw, encode), daemon=True),
                        threading.Thread(target=self._run, args=(self.overlay, self.worker.picture), daemon=True)]

    def start(self):
        for thread in self.threads:
            thread.start()

    def stop(self):
        self.stop_event.set()
        self.worker.stop()  # ends a read the overlay thread may be waiting in
        for thread in self.threads:
            if thread.is_alive():
                thread.join()

    def feed(self, overlay):
        return self.overlay if overlay else self.raw

    def _run(self, feed, picture):
        """Encodes every new camera frame into feed while someone watches"""
        frame = None
        while not self.stop_event.is_set():
            if not feed.watched():
                time.sleep(NO_VIEWER)
                continue
            try:
                frame = wait_for_new_frame(self.camera, frame, timeout=WAIT)
                feed.put(picture(frame))
            except CameraFrozen:
                pass  # the cockpit notices a dead camera and restarts
            except Exception:  # one bad frame must not end the stream
                traceback.print_exc()
