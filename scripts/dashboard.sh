#!/bin/bash
# Web cockpit (notebooks/mini_av/dashboard.py) on port 8080: live camera, state, start/stop buttons.
# Close the 04_drive and 05_camera_check notebook kernels first: only one program may own the camera.
# Stop it with scripts/stop_robot.sh. The host /home/jetbot is /workspace inside the container.
echo 'jetbot' | sudo -S -p '' docker exec jetbot_jupyter sh -c 'cd /workspace/jetbot/notebooks/mini_av && exec python3 -u dashboard.py'
