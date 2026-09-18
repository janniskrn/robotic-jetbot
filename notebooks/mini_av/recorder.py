"""Recording of camera frames into dataset sessions.

One session = one folder with JPEG frames and a session.json describing how and
where they were recorded. Labels are added later on the workstation.

Images always go to the USB stick, never to the SD card (see STORAGE.md).
"""

import json
import os
import time

# Path inside the Jupyter container. On the robot itself this is /home/jetbot/usb/images/datasets.
DATASET_ROOT = '/workspace/usb/images/datasets'


class Recorder(object):
    """Saves at most one frame per period into the session folder"""

    def __init__(self, period, root=DATASET_ROOT):
        self.period = period
        self.root = root
        self.session_dir = None
        self.count = 0
        self._metadata = None
        self._last_save = 0.0

    @property
    def recording(self):
        return self.session_dir is not None

    def start(self, name, metadata):
        """Creates the session folder. Fails if the USB stick is not mounted."""
        started = time.strftime('%Y-%m-%d_%H-%M-%S')
        self.session_dir = os.path.join(self.root, '%s_%s' % (started, name))
        os.makedirs(self.session_dir)
        self._metadata = dict(metadata, name=name, started=started, period=self.period)
        self.count = 0
        self._last_save = 0.0
        self._write_metadata()
        return self.session_dir

    def offer(self, jpeg_bytes):
        """Saves the frame if a session is running and the period has passed"""
        if not self.recording:
            return False
        now = time.time()
        if now - self._last_save < self.period:
            return False
        path = os.path.join(self.session_dir, 'frame_%05d.jpg' % self.count)
        with open(path, 'wb') as f:
            f.write(jpeg_bytes)
        self._last_save = now
        self.count += 1
        return True

    def stop(self):
        """Writes the final frame count and closes the session"""
        if not self.recording:
            return None
        self._write_metadata()
        session_dir = self.session_dir
        self.session_dir = None
        return session_dir

    def _write_metadata(self):
        self._metadata['frames'] = self.count
        with open(os.path.join(self.session_dir, 'session.json'), 'w') as f:
            json.dump(self._metadata, f, indent=2, sort_keys=True)
