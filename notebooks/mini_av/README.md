# Mini Autonomous Vehicle (our code)

Everything the team writes for the challenge lives here. The stock NVIDIA notebooks in the
other `notebooks/` folders stay untouched and are used as building blocks only.

## Layout

Files are numbered in the order of the pipeline, not by week. A week is a deadline, not a
component: the same recorder, model and control code is used again in later weeks, so week
folders would mean moving or copying files every week.

| File | Purpose | Runs on |
| :--- | :--- | :--- |
| `recorder.py` | Saves camera frames into dataset sessions | Robot |
| `01_record_dataset.ipynb` | Drive with the gamepad and record a session | Robot |
| `lane_mask.py` | Classical blue-tape lane detection (color mask); data tool and pre-labels only | Robot, workstation |
| `02_auto_label.py` | Labels recorded sessions with the color mask (`labels.csv`) and draws review sheets | Robot or workstation |
| `vision.py` | Network and preprocessing shared by training and driving | Robot, workstation |
| `03_train.py` | Trains one model (`--task lane` or `curve`) with whole sessions held out | Robot (never while driving) or Mac |
| `03_convert_trt.py` | Converts a trained model to TensorRT (about 6x faster); run on the robot after every training | Robot (container) |
| `02_manual_label.py` | Manual labeling on a computer with a screen (test only, see `MANUAL_TEST.md`) | Mac |
| `config.py` | All tuning values of the driving program | Robot |
| `safety.py` | Camera watchdog and battery guard, shared by every program that drives | Robot |
| `perception.py` | Camera frame -> lane visible, lane position, curve probabilities (models) | Robot |
| `decision.py` | FOLLOW or STOP (Task 1); AVOID and RECOVER come with Task 2 | Robot |
| `control.py` | Smoothed PD steering, curve-based speed, rate limits, motor trim | Robot |
| `logger.py` | One CSV row per control step plus run.json, in `usb/logs/` | Robot |
| `drive.py` | Main loop: perception -> decision -> control -> motors (`--baseline`, `--no-curve`) | Robot (container) |
| `04_drive.ipynb` | Start and stop buttons for `drive.py` | Robot (browser) |
| `analyze_runs.py` | Task 1 table (`results/week1/`) and graphs (`usb/images/results/week1/`) from run logs | Robot host |
| `battery.py` | Battery voltage and charge estimate; run it before any motor session | Robot host, container, or `ssh` from a PC |
| `auto_record.py` | Robot drives the lane itself with `lane_mask` and records a session plus `auto_labels.csv` | Robot (`python3 auto_record.py --name lap --seconds 60` in the container) |

Planned next, same numbering: `02_label_dataset` (workstation), `03_train_*` (workstation or
robot), `04_drive` plus the driving modules `config.py`, `perception.py`, `decision.py`,
`control.py`, `logger.py`.

## Which task uses what

| Week | Task | Files |
| :--- | :--- | :--- |
| 1 | Task 1 adaptive lane following | `01_record_dataset`, `02_label_dataset`, `03_train_lane`, `04_drive` |
| 1 | Task 2 obstacle avoidance and recovery | same files, plus the obstacle model and the avoidance logic |

## Rules

- Images and datasets only on the USB stick: `/workspace/usb/images/datasets/` (see `STORAGE.md`).
- Model weights (`*.pth`) stay on the SD card.
- Decisions behind this structure are in `DECISIONS.md`.
