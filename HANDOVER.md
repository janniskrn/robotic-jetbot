# Handover (2026-09-27, end of session 2)

For the next Claude session. Read this, then `CLAUDE.md`, `DECISIONS.md` (newest entries: DATA2, CURVE3,
LANE2, FF2, OBST1), `WEEK1_PLAN.md`.

**Your first job: obstacle data for Task 2** (step 4b of the plan below). The team stopped the session before
recording; two small changes were proposed and not yet approved (see "Next steps").

## Where we are

- **Task 1 works in both directions.** Counterclockwise: 5 sharp curves in a row (run `v3_ccw_4`, 58 s, ended by
  a test cup the team put on the road). Clockwise: 60 s without a lane loss (`v3_cw_1`). Logs in `usb/logs/`.
- **What fixed the sharp ccw curve** (DATA2, CURVE3, FF2):
  1. The curve model has 5 classes (straight, gentle/sharp left/right); `perception.py` gives `curve_dir`
     (-1 left .. 1 right), and the feedforward takes its direction from it instead of from lane_x.
  2. `FEEDFORWARD_SHARP` 0.07 -> 0.04 (with the steady direction 0.07 turned in early and cut over the inner line).
  3. No feedforward once lane_x shows the robot more than 0.10 inside the curve (`FEEDFORWARD_MAX_INSIDE`).
  4. During the 0.5 s lane-lost grace time `Controller.hold` keeps turning into the curve (unless already inside).
- **Lane model unchanged** (2026-09-20). A retrain on all data had a constant offset (+0.025..+0.037) and is not
  used (LANE2, kept in `models/old/`). Old models are backed up in `notebooks/mini_av/models/old/`.
- **`replay.py`** measures models offline per section and direction (hard-case set: the unlabeled runs
  `drive_v2_adaptive_a/_b` plus `lap_ccw4`, `lap_cw3`). Use it before every driving test.

## Lessons from this session

- The single-row lane_x carries no heading: at the sharp curve's exit it reads slightly right both when the robot
  is inside and when it runs wide, and the mask labels say the same. More lane_x data cannot fix that.
- **Frames alone did not tell inside from wide; the person watching did.** Ask the team what they saw before
  tuning. Claude misread two runs from the images.
- Change one thing per driving test; each lane loss costs a human trip.

## Task 2: obstacle recognition (OBST1)

- Obstacles: white paper cups (about 8 cm) with a red tape band all around; all cups, also for the demo.
- `cup_mask.py` finds the band (hue 165-180 and 0-4; 0 false cups in 6298 recorded frames). Band lower edge:
  20 cm row 109, 30 cm row 98, 50 cm row 84 (snapshots in `usb/images/obstacle_survey/`).
- `auto_record.py --cup-stop` follows the lane with the blue mask, stops at a cup, turns around and drives to the
  next one. First session `2026-09-28_06-13-18_cups_a` (60 s): 4 approaches, all stopped, but at about 12 cm
  instead of 20 (camera lag), and only about 3 "blocked" frames per approach.

## Next steps (each needs the team's go)

1. **Proposed, not approved yet:** `CUP_STOP_ROW` 109 -> 104 (stop at about 20 cm) and record at 8 Hz in cup mode.
2. **Record** 6 x 90 s: cups centered on both straights (2 sessions), shifted left/right in the lane (2), one in the
   gentle curve (1), new positions (1). Target 300+ "blocked" frames. Team moves the cups between sessions.
3. **Labels (4c):** blocked from band row 98 (30 cm) with the cup in the lane, free above about row 90 or no cup,
   frames between left out; review sheets. Add an `obstacle` label to `02_auto_label.py`.
4. **Train the obstacle model (4d)**, check false alarms per lap with laps without cups, then Phase 5 (AVOID /
   RECOVER, `WEEK1_PLAN.md`, open items in `DECISIONS.md`).
5. **Known risk for RECOVER:** off the track the lane model reported "lane visible 0.99" on the distant tape and
   the robot drove on for about 4 s (run `v3_ccw_3`). Recovery must require the lane near the center, and the lane
   model needs negative frames (lane far away or sideways).
6. Later: repeat the Task 1 comparison (baseline, nocurve, adaptive, both directions) with `analyze_runs.py`.

## How to run things (on the robot, from `~/jetbot`)

| What | Command |
| :--- | :--- |
| Battery | `python3 notebooks/mini_av/battery.py` (valid with the charger unplugged; 11.90 V at the end of this session) |
| Emergency stop | `scripts/stop_robot.sh` |
| Camera broken ("(Argus) Error") | `scripts/restart_camera.sh` |
| Drive (in the container) | `echo 'jetbot' \| sudo -S -p '' docker exec -w /workspace/jetbot/notebooks/mini_av jetbot_jupyter python3 drive.py --name NAME --seconds 60` |
| Record cup approaches | same prefix, `python3 auto_record.py --name cups_b --seconds 90 --cup-stop` |
| Replay models offline | same prefix, `python3 replay.py v2_adaptive lap_ccw4 lap_cw3` (`--per-frame` for details) |
| Label | host: `cd notebooks/mini_av && python3 02_auto_label.py /home/jetbot/usb/images/datasets/<session>/` |
| Train | container, detached: `docker exec -d ... bash -c "python3 -u 03_train.py --task curve --val lap_ccw4 --val lap_cw3 --epochs 8 > /workspace/usb/logs/<name>.log 2>&1; echo FINISHED >> ..."` (`-u`, or the log stays empty until the end) |
| TensorRT (after every training) | container: `python3 03_convert_trt.py --task curve` |

- The models folder is owned by root: use sudo to copy or move model files.
- Scripts for the container cannot be read from the host's scratchpad: pipe them in with
  `echo 'jetbot' | sudo -S -p '' -v && sudo -n docker exec -i jetbot_jupyter python3 - < script.py`.
- Never train while the robot drives; check the battery before motor sessions (below 11.4 V charge).
