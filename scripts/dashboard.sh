#!/bin/bash
# Web cockpit (notebooks/mini_av/dashboard.py) on port 8080, inside the Jupyter container.
# Normally started by the service jetbot-cockpit (scripts/jetbot-cockpit.service): at boot, and again after any exit.
# By hand: sudo systemctl stop jetbot-cockpit, then run this script (only one program may own the camera).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CONTAINER=jetbot_jupyter
EXIT_CAMERA_DEAD=3   # dashboard.py's exit code when the camera sends no frames (cockpit.EXIT_CAMERA_DEAD)

as_root() {  # the service runs as root; by hand the robot's sudo password is used
    if [ "$(id -u)" = 0 ]; then "$@"; else echo 'jetbot' | sudo -S -p '' "$@"; fi
}

stop_motors() {
    as_root docker exec "$CONTAINER" python3 -c 'from jetbot import Robot; Robot().stop()' >/dev/null 2>&1
}

# 1. the container (restart policy "always") may still be starting after a boot
for _ in $(seq 1 60); do
    [ "$(as_root docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null)" = true ] && break
    sleep 2
done

# 2. an older cockpit still running would hold the camera: Ctrl-C, then kill if it hangs
as_root docker exec "$CONTAINER" pkill -INT -f 'python3 -u dashboard.py' 2>/dev/null
for _ in $(seq 1 20); do
    as_root docker exec "$CONTAINER" pgrep -f 'python3 -u dashboard.py' >/dev/null 2>&1 || break
    sleep 1
done
as_root docker exec "$CONTAINER" pkill -KILL -f 'python3 -u dashboard.py' 2>/dev/null

# 3. run it; the motors are stopped before and after
stop_motors
as_root docker exec "$CONTAINER" sh -c 'cd /workspace/jetbot/notebooks/mini_av && exec python3 -u dashboard.py'
code=$?
stop_motors
if [ "$code" = "$EXIT_CAMERA_DEAD" ]; then
    echo "camera dead: restarting the camera service and the container"
    "$HERE/restart_camera.sh"
fi
exit "$code"
