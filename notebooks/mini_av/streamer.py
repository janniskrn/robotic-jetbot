"""Video for the cockpit (MJPEG): each picture is encoded once, in one thread, and sent to every viewer.

raw: read straight from the camera, so it runs at the camera rate whatever the driving loop does.
overlay: situation.picture of the latest camera frame (about 13 ms of CPU with the encoding, SPEED1).
Nothing is encoded while nobody watches.
"""

import threading
import time
import traceback

import cv2

import situation
from safety import CameraFrozen, wait_for_new_frame

JPEG_QUALITY = 85
OVERLAY_HZ = {'IDLE': 30, 'DRIVING': 10}  # overlay pictures per second: less while driving, the loop needs the CPU
WAIT = 1.0         # seconds a thread or a viewer waits for a new picture before it checks again
NO_VIEWER = 0.05   # seconds between checks whether someone watches


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


class Streamer(object):
    def __init__(self, camera, mode):
        """mode() returns 'IDLE' or 'DRIVING' (the overlay rate)"""
        self.camera, self.mode = camera, mode
        self.raw, self.overlay = Feed(), Feed()
        self.stop_event = threading.Event()
        self.threads = [threading.Thread(target=self._run, args=(self.raw, encode, None), daemon=True),
                        threading.Thread(target=self._run, args=(self.overlay, self._overlay_picture, self._overlay_hz),
                                         daemon=True)]

    def start(self):
        for thread in self.threads:
            thread.start()

    def stop(self):
        self.stop_event.set()
        for thread in self.threads:
            if thread.is_alive():
                thread.join()

    def feed(self, overlay):
        return self.overlay if overlay else self.raw

    def _run(self, feed, picture, hz):
        """Encodes new camera frames into feed while someone watches; hz() limits the rate (None: every frame)"""
        frame = None
        while not self.stop_event.is_set():
            if not feed.watched():
                time.sleep(NO_VIEWER)
                continue
            try:
                started = time.time()
                frame = wait_for_new_frame(self.camera, frame, timeout=WAIT)
                feed.put(picture(frame))
                if hz is not None:
                    time.sleep(max(0.0, 1.0 / hz() - (time.time() - started)))
            except CameraFrozen:
                pass  # the cockpit notices a dead camera and restarts
            except Exception:  # one bad frame must not end the stream
                traceback.print_exc()

    def _overlay_picture(self, frame):
        return encode(situation.picture(frame))

    def _overlay_hz(self):
        return OVERLAY_HZ.get(self.mode(), OVERLAY_HZ['DRIVING'])
