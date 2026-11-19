# Mini Autonomous Vehicle (our code)

Everything the team writes for the challenge lives here. The stock NVIDIA notebooks in the other `notebooks/`
folders stay untouched and are used as building blocks only. Run everything inside the Jupyter container from this
folder (`docker exec -w /workspace/jetbot/notebooks/mini_av jetbot_jupyter python3 ...`). The cockpit service owns
the camera and about 2 GB of memory: `sudo systemctl stop jetbot-cockpit` before a notebook or script uses the camera,
and before a training or TensorRT conversion; `start` afterwards. In idle it runs the models only while a page is open.

## Driving program (this folder)

One loop: camera -> `perception` -> `decision` -> `control` -> motors. Perception, decision and control stay
separate.

| File | Purpose |
| :--- | :--- |
| `drive.py` | Main loop with logging and safety (`--baseline`, `--no-curve`, `--stop-only`, `--pass-side`) |
| `config.py` | All tuning values of the driving program |
| `perception.py` | Camera frame -> what the models see, plus the color-mask measurements (HYBRID) |
| `lane_mask.py`, `cup_mask.py` | Color masks: blue lane tape and the cups' red band |
| `situation.py` | Where the robot stands relative to the lane (zone, center, heading), from the tape |
| `vision.py` | Network and preprocessing shared by training and driving |
| `decision.py` | The state machine (Task 6); table and diagram in `STATE_MACHINE.md` |
| `find_lane.py` | LINE_RECOVERY: finds a lost lane again (undo, sweep, search) |
| `control.py` | PD steering with curve feedforward, curve-based speed, the swerve's wheel commands |
| `safety.py`, `battery.py` | Camera watchdog, motor watchdog, battery guard; `battery.py` alone prints the charge |
| `logger.py`, `recorder.py` | Run logs (`usb/logs/`) and camera frames (`usb/images/datasets/`) |
| `dashboard.py` | Web cockpit on port 8080: page, live state (Server-Sent Events), video, start and stop |
| `cockpit.py`, `streamer.py` | The cockpit's robot side (idle loop, runs of `drive.py`) and its MJPEG video |
| `web/` | The cockpit page (`index.html`, `style.css`, `app.js`) |
| `01_record_dataset.ipynb` | Drive with the gamepad and record a session |
| `04_drive.ipynb` | Start and stop buttons for `drive.py` |
| `05_camera_check.ipynb` | Live view: place the robot, check `situation.py` |

## Tools (`tools/`)

Run from this folder, for example `python3 tools/train.py --task lane --val <session>`.

| File | Purpose |
| :--- | :--- |
| `auto_label.py` | Labels recorded sessions with the color masks (`labels.csv`) and draws review sheets |
| `train.py` | Trains one model (`--task lane`, `curve` or `obstacle`) with whole sessions held out |
| `convert_trt.py` | Converts a trained model to TensorRT (about 6x faster); run on the robot after every training |
| `replay.py` | Runs the models over recorded sessions offline and compares them with the color mask (DATA2) |
| `analyze_runs.py` | Task 1 table (`results/week1/`) and graphs from run logs (on the host: needs matplotlib) |
| `motion_test.py` | Swerve moves without a cup: `turn`, `swerve`, `arc` (the curve should turn about 90 degrees) |
| `cup_learn.py` | Learns the cup distance from the red band's size by backing away from a cup (LEARN1) |

## Rules

- Images and datasets only on the USB stick: `/workspace/usb/images/datasets/` (see `STORAGE.md`).
- Model weights (`*.pth`) stay on the SD card in `models/`.
- Offline checks of the decision and recovery logic: `python3 -B /home/jetbot/usb/logs/test_avoid.py <this folder>`
  on the host.
