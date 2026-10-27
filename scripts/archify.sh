#!/bin/bash
# Runs the Archify diagram skill (.claude/skills/diagrams-archify, needs Node >= 18) in a Node container:
# the robot's Ubuntu 18.04 (glibc 2.27) cannot run Node 18. Paths are relative to the repository root.
# Example: scripts/archify.sh finalize lifecycle docs/diagrams/state_machine.json docs/diagrams/state_machine.html --quality showcase
# Never run it while the robot drives (memory, see CLAUDE.md 9b).
REPO="$(cd "$(dirname "$0")/.." && pwd)"
echo 'jetbot' | sudo -S -p '' docker run --rm -u "$(id -u):$(id -g)" -e ARCHIFY_UPDATE_CHECK_DISABLED=1 \
    -v "$REPO":/repo -w /repo node:20-bookworm-slim node .claude/skills/diagrams-archify/bin/archify.mjs "$@"
