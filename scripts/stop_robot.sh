#!/bin/bash
# Emergency stop: ends our driving scripts and stops the motors.
# On the robot:  jetbot/scripts/stop_robot.sh      From a PC:  ssh jetbot@<robot-ip> jetbot/scripts/stop_robot.sh
# Ctrl-C (SIGINT), not a plain kill: a plain kill skips the script's clean-up and the motors keep turning.
echo 'jetbot' | sudo -S -p '' docker exec jetbot_jupyter pkill -INT -f '^python3 (auto_record|drive)[.]py' 2>/dev/null
sleep 1
echo 'jetbot' | sudo -S -p '' docker exec jetbot_jupyter python3 -c 'from jetbot import Robot; Robot().stop()' >/dev/null 2>&1
echo "motors stopped"
