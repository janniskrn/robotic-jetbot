#!/bin/bash
# Installs and starts the cockpit service (scripts/jetbot-cockpit.service): starts at boot, restarts after a failure.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
echo 'jetbot' | sudo -S -p '' cp "$HERE/jetbot-cockpit.service" /etc/systemd/system/jetbot-cockpit.service
echo 'jetbot' | sudo -S -p '' systemctl daemon-reload
echo 'jetbot' | sudo -S -p '' systemctl enable --now jetbot-cockpit
systemctl --no-pager status jetbot-cockpit | head -5
