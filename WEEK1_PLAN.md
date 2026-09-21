# Week 1 plan: Task 1 and Task 2, fastest path

Goal (PROJECT_GUIDE_1.md): stable lane following with our own control layer, faster on straights and
slower in sharp curves (Task 1), and `ROAD_FOLLOWING -> AVOIDANCE -> ROAD_RECOVERY -> ROAD_FOLLOWING`
around an obstacle without manual steering (Task 2). Decisions behind this plan: `DECISIONS.md`.

**Rule of this plan:** Claude does every step that a program can do (recording, labeling, training,
coding, testing, graphs). Steps marked **HUMAN** need hands, eyes or a decision. Every step that drives
the motors starts with a battery check (CLAUDE.md section 9).

## State now (2026-09-20)

- Camera fix, battery check, self-driving recorder (`auto_record.py`), automatic labels (`02_auto_label.py`) done.
- 867 labeled frames, counterclockwise only; only 34 sharp-curve frames.
- The manual pipeline (gamepad recording, SSH copy, hand labeling) is ready for a test: `MANUAL_TEST.md`.

## Phase 1: Data for Task 1 (about 30 min, robot drives)

| Step | Who | What | Done when |
| :--- | :--- | :--- | :--- |
| 1.1 | HUMAN | Charge the battery, unplug it, wait 5 min, put the robot on a straight in the lane | `battery.py` shows at least 12.0 V |
| 1.2 | Claude | Record clockwise: turn around, 2 x 60 s clean laps, 60 s weave (25 px), 60 s spin | Sessions saved, stop reason "time up" |
| 1.3 | Claude | Record 2 x 60 s more clean counterclockwise laps (sharp-curve examples) | Sharp-curve frames above 100 |
| 1.4 | Claude | Label all new sessions, check every review sheet, fix label rules if needed | No wrong labels found on the sheets |
| 1.5 | HUMAN, optional | Rescue the robot if it stops off the lane (battery guard or lane lost) | Robot back on a straight |

Charge between blocks if the battery drops below 11.4 V at rest.

## Phase 2: Models for Task 1 (about 1 h, runs on the robot while it charges, never while it drives)

| Step | Who | What | Done when |
| :--- | :--- | :--- | :--- |
| 2.1 | Claude | `03_train.py --task lane`: ResNet18 with two outputs, `lane_x` (regression) and `lane_visible` (yes/no). Split by session: whole sessions held out for testing. Mirror augmentation with `lane_x -> -lane_x` | Test error of `lane_x` and accuracy of `lane_visible` on held-out sessions |
| 2.2 | Claude | `03_train.py --task curve`: ResNet18, 3 classes, only clean-lap frames | Confusion matrix on held-out sessions |
| 2.3 | Claude | Load both models in the container, measure frames per second | FPS number; TensorRT only if the control loop drops below about 15 Hz |

**Training time budget:** measured 88 s per epoch for about 700 frames on the robot. With about 2000 frames,
15 epochs take about 60 min, above the 40 min limit: then fewer epochs (about 8) on the robot, or the Mac.

Lane position and lane visible share one model (both describe "where is the lane"); curve and obstacle
get their own models (D2). Training under 40 min stays on the robot (DECISIONS.md, Training).

## Authorship of the control code (decided)

PROJECT_GUIDE_1.md asks for team-written steering, speed, avoidance and recovery logic. The team decided
that Claude writes all of it and accepts that risk (DECISIONS.md, AUTHOR). No human gold set (GOLD).

## Phase 3: Driving program for Task 1 (about 2 h)

| Step | Who | What | Done when |
| :--- | :--- | :--- | :--- |
| 3.1 | Claude | Modules: `config.py` (all constants), `perception.py` (models -> lane_x, lane_visible, curve probabilities), `control.py` (smoothed PD steering, motor trim, rate limit; speed from curve probabilities with a speed rate limit), `decision.py` (follow, or stop when the lane is lost), `logger.py` (CSV per step plus run metadata), `drive.py` (main loop, command line) and `04_drive.ipynb` (thin, with a stop button) | Runs a lap in a test at low speed |
| 3.2 | HUMAN | Watch the first runs, put the robot back if needed | - |
| 3.3 | Claude | Baseline run: constant speed, plain P steering, same logger | Baseline log saved |
| 3.4 | Claude | Tune PD and the speed map; runs in both directions | Wobble on straights smaller than baseline, no lane loss in 3 laps each way |
| 3.5 | Claude | Task 1 results: speed per curve class, wobble, lap time, lane losses; graphs and a table | Table and graphs in `results/week1/` |

## Phase 4: Obstacle perception for Task 2 (about 1.5 h)

| Step | Who | What | Done when |
| :--- | :--- | :--- | :--- |
| 4.1 | HUMAN | Choose the obstacle: a box about 10-15 cm, in a strong color that is not blue (red, orange or yellow), and put it on the lane | Box on the lane |
| 4.2 | HUMAN | Confirm there is free floor (about 30-40 cm) beside the lane on the passing side, and decide the side (left or right) | Side written into `DECISIONS.md` |
| 4.3 | Claude | Measure the box color; recorder mode that follows the lane, stops before the box (color mask) and turns around, so it approaches from both sides lap after lap | Sessions with many approaches |
| 4.4 | HUMAN | Move the box 2-3 times (straight, curve) between sessions | - |
| 4.5 | Claude | Labels: `blocked` when the box is closer than the trigger distance (its lower edge below a set row), `free` otherwise, frames near the threshold left out; review sheets | Sheets checked |
| 4.6 | Claude | `03_train.py --task obstacle`; test on held-out sessions, including false alarms in curves | Accuracy and false alarms per lap |

## Phase 5: Avoidance and recovery for Task 2 (about 2 h)

| Step | Who | What | Done when |
| :--- | :--- | :--- | :--- |
| 5.1 | HUMAN | Decide: Task 2 needs modes FOLLOW / AVOID / RECOVER / STOP. D9 said "no state machine for now". OK to add this minimal mode variable now (the full state machine stays week 3)? | Yes or no |
| 5.2 | Claude | Obstacle trigger with debounce and hysteresis (P(blocked) above 0.8 for 5 frames, clear below 0.3). First only stop | 10 approaches: stops each time, no false stop in 3 laps |
| 5.3 | Claude | AVOID (D7): turn out to the fixed side and pass on timers; RECOVER: turn back until `lane_visible` and lane centered for N frames; timeout -> STOP | 10 trials |
| 5.4 | HUMAN | Watch the trials, reset the robot after a failure | - |
| 5.5 | Claude | Task 2 results: success rate, false triggers, recovery time; graphs and table | In `results/week1/` |

## Phase 6: Demo preparation (about 1 h)

| Step | Who | What |
| :--- | :--- | :--- |
| 6.1 | Claude | Mode diagram (FOLLOW / AVOID / RECOVER / STOP) matching the code, flow diagram camera -> perception -> decision -> control, experiment records (problem -> hypothesis -> change -> test -> result) |
| 6.3 | HUMAN | Rehearse the demo once with a full battery |

## Manual way (test only)

`MANUAL_TEST.md`: record with the gamepad, copy to the Mac over SSH, label by hand with `02_manual_label.py`,
copy the labels back. The team only tests that it works; Claude does the real labeling.

## Risks

- **Battery brownout:** guard in `auto_record.py`; the same guard goes into `04_drive.py`.
- **Few sharp-curve frames:** Phase 1 records more; the curve model also learns from mirrored frames.
- **Frame rate with three models:** the curve and obstacle models can run every 2nd-3rd frame; TensorRT if needed.
- **Labels come from the blue color mask:** a model trained on them can at best be as accurate as the mask and
  the review sheets. What it adds: it runs without hand-tuned color thresholds, can be retrained on new
  conditions (lighting, tape) with more data, and gives a confidence. A different tape color later needs new data.
- **Time:** charging between data blocks can take longer than the phase estimates; the phases are working time.
- **Lighting:** sunlight changes during the day; recording at two times of day makes the models more robust.
- **Motor dead zone (below about 0.27 nothing moves):** the speed range is narrow (about 0.30-0.45); the controller keeps both wheels above the dead zone or compensates for it.
