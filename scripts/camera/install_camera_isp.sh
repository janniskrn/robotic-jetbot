#!/bin/bash
# Installs the Waveshare IMX219-160 ISP calibration (fixes the pink/red colour cast).
# nvargus-daemon loads this file at start, so the fix applies to every program
# that uses the camera (host and Docker) and survives reboots.
# Usage: sudo bash scripts/camera/install_camera_isp.sh
set -e

SRC="$(dirname "$0")/camera_overrides.isp"
DST=/var/nvidia/nvcam/settings/camera_overrides.isp
SHA=c6b8cafffa5f218a85f73d323e2a72b382194b84b39ff9a7804fffc1819638ec

echo "$SHA  $SRC" | sha256sum -c -
install -m 664 -o root -g root "$SRC" "$DST"
systemctl restart nvargus-daemon
docker restart jetbot_jupyter   # notebooks must reopen the camera after the daemon restart
echo "Installed $DST"
