# JetBot Mini Autonomous Vehicle

Our team's code for the Mini Autonomous Vehicle Challenge (6-week course project, `guide/PROJECT_GUIDE_1.md`),
built on the NVIDIA JetBot (Jetson Nano). The robot follows a taped lane with learned models, slows down in sharp
curves, swerves around cups and finds the lane again, all through one explicit state machine.

## Where things are

| Path | What |
| :--- | :--- |
| `notebooks/mini_av/` | Our driving program; `tools/` for labeling, training, tests and analysis (see its `README.md`) |
| `notebooks/mini_av/STATE_MACHINE.md` | States, transitions and the diagram, in step with `decision.py` |
| `PLAN.md` | Working plan and the current step |
| `DECISIONS.md` | Every decision with its ID (the IDs in code comments point here) |
| `HANDOVER.md` | Latest session handover |
| `STORAGE.md` | Images and datasets on the USB stick, models on the SD card |
| `guide/` | The course: project guides (PDF and Markdown), our analysis `GOAL.md`, weekly rhythm |
| `presentation/`, `diagrams/`, `design/`, `results/` | Weekly presentations, diagrams, the look, result tables |
| `scripts/` | `stop_robot.sh` (emergency stop), the cockpit service (`jetbot-cockpit.service`, `dashboard.sh`), `restart_camera.sh`, camera setup |
| `jetbot/`, `docker/`, `setup.py` | NVIDIA JetBot package and containers (upstream, used as is) |
| `notebooks/` (other folders) | NVIDIA example notebooks (upstream, building blocks only) |
| `archive/` | Old plans and notes |

## Quick start (on the robot)

```
python3 ~/jetbot/notebooks/mini_av/battery.py      # do not drive below 11.4 V
# web cockpit: always running at http://<robot-ip>:8080 (service jetbot-cockpit, starts at boot)
sudo systemctl stop jetbot-cockpit                 # free the camera for a notebook; start: systemctl start
~/jetbot/scripts/stop_robot.sh                     # emergency stop
```

Based on [NVIDIA-AI-IOT/jetbot](https://github.com/NVIDIA-AI-IOT/jetbot) (MIT license, `LICENSE.md`).
