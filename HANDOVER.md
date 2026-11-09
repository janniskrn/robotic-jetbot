# Handover (2026-11-09, end of session)

For the next Claude session. Read this, then `CLAUDE.md`, `DECISIONS.md` (newest: OBST8, OBST9, AVOID4, LEARN1, LINE1,
LINE2), `PLAN.md` section 6 step S1, `notebooks/mini_av/STATE_MACHINE.md`.

**The team wants fast progress and simple solutions. Do not start the next step without the user's go.**

## Where we are (commit `092b97d`, all pushed; only the widget ID in `04_drive.ipynb` is left uncommitted on purpose)

- **Cup distance:** from the red band's size, cm = 405 / sqrt(pixels) (`OBST9`), learned with `cup_learn.py` in 5 places.
  Approach 65, trigger 40, clear 60 cm. The row depends on place and camera tilt; a band cut off by the lower image
  edge counts as 0 cm.
- **Models on single frames** (`usb/logs/models_on_frames_2026-11-08.csv`): cup found in 96-99 % of the frames up to 50 cm,
  71 % at 60-73 cm, false alarms 0.4 %. The lane model loses the lane close to a cup (45 % at 18-25 cm).
- **Swerve (`AVOID4`):** brake, turn out until the cup leaves the image, curve (`ARC_WHEELS` 0.36 / 0.31) straight on
  while the cup is in view on its side, ends when the lane's border was crossed or the lane is found; straight on after
  3.5 s; turn back. Track, 3 cups: 11 of 12 swerves (runs `avoid4_7..9`, `line1_1`), 14 of 18 (`line2_1`, `_3`, `_4`, `_5`),
  then 2 of 3 with the crossing rule (`line3_1`, too few to judge). Whether cups were touched was not observed.
- **`LINE_RECOVERY` (`LINE1`, `LINE2`, `find_lane.py`):** undo (1.5 s of wheel commands backwards), sweep (about 100
  degrees each way), search (one turn, nearest tape, drive across it). Search stops with the Stop button and the time
  limit; no forward pulse without tape in view.
- **Offline test:** `usb/logs/test_avoid.py`, 82 checks (`python3 -B test_avoid.py ~/jetbot/notebooks/mini_av`), not in the repo.
  Test helpers of this session: `usb/logs/session_tools_2026-11-08/` (`go.sh`, `find.sh` have paths of the old scratchpad).

## Open problems, in the order to work on them

1. **Turn back fails at the border (proposed, no go yet):** when `turn_in` times out the robot often stands right at the
   lane (run `line3_1`: lane 0.49, aligned, tape under the nose), and the search then turns away and loses it. Proposal:
   a small forward nudge and a new look before the long search; test on the failed runs, then full laps with cups.
2. **Search from open floor is unreliable:** 2 of 3 standalone runs found the lane (22 and 113 stops); during `line3_1` it
   found nothing in 100 s and drove to the wall (the no-tape rule came after that; not re-tested). The camera does not
   see walls or chairs.
3. **Undo:** tested on purpose once (back at lane 0.63, then the sweep found it in 2.5 s; a 2.1 s drive-off needed the
   search). Relaxed afterwards (1.5 s, `UNDO_SURE` 0.6), not re-tested. No natural lane loss has reached it yet.
4. **Lane loss in curves** while following: 8 of 8 losses in curves (5 sharp, 3 gentle), about 15 cm after the last good reading.
5. **Cups just past a curve** count as in the lane late: triggers at 21-25 cm instead of about 37.
6. Recovery without following keeps no heading, so the robot can end up driving the lap the other way (the pass side is
   then measured anew; clockwise swerves worked in `line1_1`, `line2_1`).

## Practical notes

- Each new camera program needs `scripts/restart_camera.sh` first or Argus hangs (it restarts Jupyter too); once "camera frozen" at a start, a retry worked.
- Battery: 11.52 V at the end, charging. Check before driving; limit 11.4 V at rest.
- Tighten the camera mount: the tilt moved 2-4 rows since September.
- Do not match the 4 Hz frames to log times to judge the models: that gave a false "model blind beyond 40 cm". Run the models on the single frames.

## Where we are

- Task 1 works; a lane-gap fix for the sharp ccw curve (`GAP2`) is in, not yet confirmed on the track.
- Task 2: the cup's distance comes from the cup mask (`OBST6`). Stop-only mode with slow approach, brake pulse and one
  backup (`OBST7`) stops in front of the cup at about 35-40 cm (3 runs, `stop_s1d2_1..3`). Driving on after the cup is
  lifted (needs the lane in sight) is coded but not yet seen on the track.
- The swerve (`AVOID3`: brake, turn 90 degrees, curve, turn back) works on the straight it was tuned on and fails
  elsewhere: its camera marks need a straight lane edge.
- Offline test (34 checks): `/home/jetbot/usb/logs/test_avoid.py` (USB stick, not in the repo; run with `python3 -B test_avoid.py ~/jetbot/notebooks/mini_av`).

## Next steps (agreed with the user 2026-11-05)

1. Teach the distances: the user places the robot 20, 30, 40, 50, 60 cm before a cup on the straight and 30, 40 cm in
   the gentle curve; `notebooks/mini_av/cup_distance.py <cm> [label]` takes the picture (motors off); build a cm table.
2. Simpler, wider swerve: stop at the fixed distance, turn 90 degrees, a wider curve (about 1.4 times) until
   `lane_found`, then lane following (no turn back on the spot); offline tests, then the track: straight, then curve.
3. Open: the growing swing at the gentle-curve entry (run 2026-11-03_04-51-54); the clockwise lap (pass right).

## Session 3 (2026-10-01) in short

- **Obstacle model done (OBST2, OBST3):** outputs `cup_visible`, `cup_row`, `cup_x`; 7 cup sessions (396 frames
  with a cup); 0 false alarms on laps without cups; near the trigger it reads 3-13 rows too close.
- **Step 5.2 (stop at a cup) built:** mode BLOCKED in `decision.py` (trigger band row 88, clear below row 80,
  debounce 4 steps, obstacle model alternating with the curve model). Only one stop run so far (`stop_cups_1`,
  with the older trigger row 98: stopped at 10-12 cm, released once too early; both fixed, not yet re-tested).
- **Steering swung more than in session 2, with the same code** (A/B test with the old code, AB1). Not the third
  model, not loop timing, not camera lag (measured 115-160 ms, constant). Speed 0.37 and KP 0.12 did not help and
  were reverted. Committed under test (STEER2): motor trim -0.01 and a smoothed D term: calmer steering and less
  offset, but the swing after the sharp curve still grows during a run. Verify in both directions first.
- `auto_record.py` now waits for the lane before moving (a forgotten lens cap gave pure noise, and the cup mask saw
  cups in it). Noise session renamed to `test_lenscap`.
- Diagnostic scripts on the USB stick: `usb/logs/lag_test.py` (camera lag under model load),
  `usb/logs/compare_runs.py <run names>` (direction, offset, jerkiness, swing after the sharp curve).

## Next steps (each needs the team's go)

1. Camera check (above). Then 60 s cw and 60 s ccw without cups with STEER2; compare with
   `python3 /home/jetbot/usb/logs/compare_runs.py v3_cw_1 v5_trim_dsmooth_1 <new runs>`.
   Keep STEER2 if the steering is calmer and no lane is lost; the team's eyes decide.
2. Stop test 5.2: cups in the middle of both straights, 10 approaches, the team lifts each cup away; then 3 laps
   without cups (no false stop). Measure the stop distance (settled cup row).
3. 5.3 AVOID / RECOVER: mode table first (open items in `DECISIONS.md`); the cup must be in the lane
   (compare `cup_x` with the lane), RECOVER must not accept a distant lane (false "lane visible", session 2).
4. Later: obstacle model retrained with a right-shifted cup session in training; Task 1 comparison table.

## State from session 2 (still valid unless noted above)

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
