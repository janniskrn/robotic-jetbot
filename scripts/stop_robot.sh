#!/bin/bash
# Emergency stop: ends our driving scripts and stops the motors (the cockpit service restarts the cockpit, idle).
# On the robot:  jetbot/scripts/stop_robot.sh      From a PC:  ssh jetbot@<robot-ip> jetbot/scripts/stop_robot.sh
# Ctrl-C (SIGINT), not a plain kill: a plain kill skips the script's clean-up and the motors keep turning.
echo 'jetbot' | sudo -S -p '' docker exec jetbot_jupyter pkill -INT -f '^python3 (-u )?(tools/)?(drive|dashboard|find_lane|motion_test|cup_learn)[.]py' 2>/dev/null
sleep 1
echo 'jetbot' | sudo -S -p '' docker exec jetbot_jupyter python3 -c 'from jetbot import Robot; Robot().stop()' >/dev/null 2>&1
echo "motors stopped"
# wait until the scripts have ended, so the camera is free (the cockpit service's ExecStop relies on this)
for _ in $(seq 1 25); do
    echo 'jetbot' | sudo -S -p '' docker exec jetbot_jupyter pgrep -f '^python3 (-u )?(tools/)?(drive|dashboard|find_lane|motion_test|cup_learn)[.]py' >/dev/null 2>&1 || exit 0
    sleep 1
done
echo "a script is still running after 25 s"
