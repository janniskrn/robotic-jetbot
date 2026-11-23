"""The cockpit's overlay picture in its own process (SPEED2): reads camera frames on stdin, writes situation.picture
JPEGs on stdout. Its pure Python runs on another core here and no longer slows the driving loop.

Each frame: height and width (two little-endian uint32), then height * width * 3 bytes BGR. Each answer: the JPEG's
length (uint32), then the JPEG. Ends when stdin closes. Started by streamer.OverlayWorker.
"""

import struct
import sys

import numpy as np

import situation
from streamer import encode

HEADER = struct.Struct('<II')  # height, width


def main():
    source, sink = sys.stdin.buffer, sys.stdout.buffer
    while True:
        header = source.read(HEADER.size)
        if len(header) < HEADER.size:
            return  # the cockpit closed the pipe
        height, width = HEADER.unpack(header)
        data = source.read(height * width * 3)
        if len(data) < height * width * 3:
            return
        jpeg = encode(situation.picture(np.frombuffer(data, np.uint8).reshape(height, width, 3)))
        sink.write(struct.pack('<I', len(jpeg)) + jpeg)
        sink.flush()


if __name__ == '__main__':
    main()
