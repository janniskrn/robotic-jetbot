#!/bin/bash
# Repairs the camera after "(Argus) Error ..." messages: restarts the camera service, then the Jupyter
# container (it only reaches the camera service if it starts after it). Running notebook kernels stop.
# On the robot: jetbot/scripts/restart_camera.sh     From a PC: ssh jetbot@<robot-ip> jetbot/scripts/restart_camera.sh
echo 'jetbot' | sudo -S -p '' systemctl restart nvargus-daemon
sleep 3
echo 'jetbot' | sudo -S -p '' docker restart jetbot_jupyter >/dev/null
echo "camera service and Jupyter restarted"
