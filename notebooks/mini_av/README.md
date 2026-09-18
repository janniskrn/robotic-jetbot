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

Planned next, same numbering: `02_label_dataset` (workstation), `03_train_*` (workstation or
robot), `04_drive` plus the driving modules `config.py`, `perception.py`, `decision.py`,
`control.py`, `logger.py`.

## Which task uses what

| Week | Task | Files |
| :--- | :--- | :--- |
| 1 | Task 1 adaptive line following | `01_record_dataset`, `02_label_dataset`, `03_train_line`, `04_drive` |
| 1 | Task 2 obstacle avoidance and recovery | same files, plus the obstacle model and the avoidance logic |

## Rules

- Images and datasets only on the USB stick: `/workspace/usb/images/datasets/` (see `STORAGE.md`).
- Model weights (`*.pth`) stay on the SD card.
- Decisions behind this structure are in `DECISIONS.md`.
