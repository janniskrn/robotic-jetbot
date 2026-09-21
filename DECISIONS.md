# Decisions

Compact log of every project decision. Newest facts win. IDs match the planning discussion.
Status: **decided**, **open** (options proposed, waiting for the team), **revisit** (decided for now, check again later).

## Project facts

| Fact | Detail |
| :--- | :--- |
| Robot | Waveshare JetBot, Jetson Nano 4 GB, JetPack 4.5 (L4T 32.5.0), Docker Jupyter with PyTorch 1.7.0 / torchvision 0.8, TensorRT 7.1, torch2trt |
| Motors | Can drive backward (-1..1). No wheel encoders: maneuvers without the camera are time-based |
| Camera | IMX219-160 wide angle, fixed mount, cannot be adjusted |
| Road | Camera survey 2026-09-20 (`usb/images/track_survey/`): **two parallel blue tape lines forming a lane**, light speckled floor, sunlight from windows causes glare, tape wrinkled in the sharp curve. Shape: an oval, one lap is about 15 s at base speed 0.32: straight, long gentle curve, straight, sharp curve at the couch. Directions: **ccw** (counterclockwise seen from above, all curves turn left, negative `curve_value`) and **cw** (curves turn right, positive). Confirmed by the user watching the robot. Sessions were renamed after the fact by their measured direction (`session.json` keeps `renamed_from` and `direction`) |
| Old collision dataset | Unusable: all 200 images are the same frame, blocked and free identical. Recollect on the track |
| Our code location | Under `notebooks/` (mounted into Docker). The `jetbot/` package is baked into the image at build time, edits there are not seen |
| Battery | 3S lithium-ion pack, INA219 at I2C bus 1 address 0x41. Check with `python3 ~/jetbot/notebooks/mini_av/battery.py` (host, container, or over ssh). Percent is only valid at rest; under load the voltage sags, while charging it reads high |
| Motors (measured) | Robot does not move below about 0.27 wheel speed; 0.30 moves it. Driving straight open-loop drifts to the right, so a motor trim is needed (D4) |
| Training | Small trainings (under 40 min) run on the robot. Larger trainings run on the MacBook M4 24 GB; the robot is the fallback when the Mac is not available |

## Decided

| ID | Date | Decision | Why |
| :--- | :--- | :--- | :--- |
| CAM | 2026-09-16 | Waveshare ISP calibration installed system-wide via `scripts/camera/install_camera_isp.sh` (installed and verified 2026-09-20: colors natural, photo `usb/images/camera_calibration/after_isp_fix_lit.jpg`) | Removes the pink cast for every program, permanently. Must be in place before any data collection |
| ML | 2026-09-16 | ML levels A + B + C, no D. ML measures the world, team code decides and controls. Start easy, build on top | Guide requires own control layer and explicit states; D breaks both |
| STYLE | 2026-09-16 | Never use emoji (chat, docs, code, commits) | Team rule |
| D1 | 2026-09-16 | Python modules (`config`, `perception`, `decision`, `control`, `logger`) plus one thin run notebook; own control loop thread with measured dt | Matches the required perception/decision/control separation |
| D3 | 2026-09-16 | Curvature from an ML classifier (C3): straight / gentle / sharp | More ML, robust; class thresholds must be defined objectively on the track |
| D4 | 2026-09-16 | Steering: smoothed PD (S1): filter on model output, D-term with dt, motor trim, rate limit | Fixes the stock demo's wobble and frame-rate dependence |
| D5 | 2026-09-16 | Speed: continuous map from curvature to speed, plus a speed rate limit | Smooth; same shape as week 4 `min(curve_speed, safe_following_speed)` |
| D6 | 2026-09-16 | Obstacles: free/blocked classifier retrained on the track (O1), with debounce and hysteresis | Guide allows reuse as perception; old data unusable |
| D9 | 2026-09-16 | No state machine for now | Keep Task 1 simple. **Revisit** before Task 2, which needs the FOLLOW -> AVOID -> RECOVER sequence |
| D2 | 2026-09-17 | One model per task (N3): line model, obstacle model, curve model. One shared dataset and one label schema for all of them | Easier to debug and retrain separately; costs frames per second, fix with TensorRT if needed |
| D7 | 2026-09-17 | Avoidance V2: leave the line and pass on timers, return guided by the camera until the line is found; timeout stops the robot. Pass side is a fixed constant | Only the blind part is timed; no encoders |
| D8 | 2026-09-17 | Line visible: learned signal (R3), labels pre-computed by a color mask and human-reviewed. Recovery ends only when the line is visible AND near the center for N frames | Generalizes to changed lighting; a sideways line must not end recovery |
| D10 | 2026-09-17 | Record while driving on the robot, label later on the Mac; hand-label about 300 images as a gold test set, automate labeling afterwards against that set | Fast collection, human-checked ground truth |
| D11 | 2026-09-17 | Mac and robot are on the same WiFi: transfer data and models with rsync. USB stick only as backup | No mount and Jupyter restart per round trip |
| SUDO | 2026-09-17 | Sudo on the robot is pre-approved; the password is in CLAUDE.md at the user's request, although the repo is public | The user does not want to run system commands by hand |
| STEP1 | 2026-09-17 | Datasets are recorded as sessions: `usb/images/datasets/<date>_<name>/` with frames at 4 Hz plus a `session.json` (tape color, lighting, section, obstacle, notes, frame size, max speed). Tool: `notebooks/mini_av/01_record_dataset.ipynb` with `recorder.py` | Labeling happens later on the Mac (D10) |
| STRUCT | 2026-09-17 | Our code lives in `notebooks/mini_av/`, files numbered in pipeline order (01 record, 02 label, 03 train, 04 drive). No week folders | The same files are reused in later weeks; a week is a deadline, not a component |
| LANE | 2026-09-20 | The robot drives in the lane center between the two blue lines. Target point = lane center at a fixed lookahead row (65 % of the image height; replaces the earlier lookahead-circle idea, simpler and enough for a lane); "line visible" (D8) means "lane visible"; avoidance (D7) leaves the lane to the fixed side and returns into it | Confirmed by the user after the camera survey; replaces the earlier single-line note |
| AUTOREC | 2026-09-20 | The robot records clean laps itself: `auto_record.py` drives with the classical blue-tape mask (`lane_mask.py`) and writes `auto_labels.csv` (lines seen, lane center) per frame as pre-labels | User choice; faster than gamepad driving, labels come for free. Data tool only, not the final controller |
| POWER | 2026-09-20 | Motor sessions only with enough battery: `auto_record.py` refuses to start below 11.4 V at rest (about 50 %) and stops when the voltage stays below 10.8 V for 2 s under load; the voltage is logged in `trace.csv` and log files are line-buffered | Incident below |
| LABELS | 2026-09-20 | `02_auto_label.py` labels every frame from the color mask: `lane_visible`, `lane_x` (-1..1 at the lookahead row), `curve_value`/`curve_class`, plus review sheets in `usb/images/review/`. Lane only counts as visible with two lines about one lane width apart (one line only briefly after that, with a small jump). Curve = bend of the lane center over three rows ahead; thresholds 0.02 (gentle) and 0.045 (sharp) from 3 labeled laps. Curve labels only from sessions driven on the center (no weave or spin), because at an angle the lens fakes a bend. Claude reviewed the sheets; a team member still spot-checks about 50 frames | Automatic, consistent labels; the rules were tuned on the review sheets |
| LANEMODEL | 2026-09-20 | The lane model has two outputs, `lane_x` and `lane_visible`; curve and obstacle get their own models. Training and driving share `vision.py` (network and preprocessing). Torch in the container is 1.7.0 (not 1.6) | Both lane outputs describe "where is the lane" (reading of D2); one preprocessing source prevents train/drive mismatch |
| AUTHOR | 2026-09-20 | Claude writes all code, including steering, speed, avoidance and recovery logic. The reviewer pointed out that PROJECT_GUIDE_1.md asks for team-written control logic; the user decided this knowingly and accepts that risk | User decision |
| GOLD | 2026-09-20 | No human-labeled gold set: Claude labels automatically and checks the review sheets. The manual labeling tool exists for testing only. Replaces the gold-set part of D10 | User decision, fastest path |
| SAFETY | 2026-09-20 | Every program that drives the motors has: battery guard, camera watchdog (stop after 0.5 s without a new frame), stop on Ctrl-C, motors stopped in `finally`. No training or other heavy job runs while the robot drives. Emergency stop: `scripts/stop_robot.sh` | Chair incident below |
| DATA1 | 2026-09-20 | Phase 1 data: 2912 training frames in 17 sessions (ccw and cw clean laps, weaving at 40 and 25 px, spins), 200 with the lane not visible, curve classes 1462 straight / 573 gentle / 171 sharp. Validation sessions: `lap_ccw4` and `lap_cw3` | Enough for the first lane and curve models |
| TURN | 2026-09-20 | `--turn-around` only stops where the view clearly differs from the start (`SAME_VIEW_DIFF`), because the lane looks aligned after a half and after a full turn; before this fix two "clockwise" sessions were counterclockwise | Found by the user watching the robot |
| TRT | 2026-09-20 | Driving uses TensorRT engines (`03_convert_trt.py`, run on the robot after every training); `perception.py` takes `<task>_trt.pth` only when it is newer than `<task>.pth`, else PyTorch with cuDNN benchmark | Lane model: 66 ms PyTorch fp16, 41 ms with cuDNN benchmark, 10.6 ms TensorRT; same outputs (max difference below 0.001) |
| LANE1 | 2026-09-20 | First lane model: 2458 training frames, held-out sessions `lap_ccw4` + `lap_cw3` (454 frames): lane visible 99.6 % correct, mean lane_x error 0.022 (about 2.5 px); 6 epochs, 20 min on the robot | Good enough to start driving tests |
| D4b | 2026-09-20 | Steering extended from PD to PID with a leaky, capped integral (KP 0.15, KI 0.25, leak 1.5 s, cap 0.12, KD 0.03, smoothing 0.7). Tried first on the track: KP 0.15 ran wide out of the sharp curve (a curve needs a sustained turn, P alone only gives it with a sustained error), KP 0.35 swung on the straight, a cubic term overshot after the curve exit | Integral supplies the sustained turn without a high gain; it fades after the curve and cannot wind up |
| D4c | 2026-09-20 | Steering back to the settings proven over 15+ laps by the color-mask driver: KP 0.15, KD 0.03 on the raw lane_x, no smoothing, integral off. The PID run (D4b) swung with growing amplitude; the color mask on the same frames saw the same swing, so the model measured correctly and the delay from smoothing and the integral caused the oversteering (the user saw it too) | Delay in the loop causes oversteering; the proven settings have none |
| T1RUNS | 2026-09-20 | First Task 1 results: our steering (D4c) drove 60 s (about 4 laps) without losing the lane, lane_x -0.12..+0.32, spread 0.087; the stock-style baseline (plain P, same KP, no damping) lost the lane after 20.5 s and 20.4 s | Steering comparison for the Task 1 table |
| CURVE1 | 2026-09-20 | First curve model: 1758 training frames, held out `lap_ccw4` + `lap_cw3` (448 frames): accuracy 86.6 %; confusion straight/gentle/sharp rows true: [253 11 1], [30 114 2], [0 16 21]. Errors are between neighboring classes, a sharp curve was never called straight; 14.5 min on the robot | Speed blends the class probabilities, so neighbor errors only change the speed a little |
| D4d | 2026-09-20 | Steering gains scaled by 0.32 / speed (gain scheduling). The first adaptive-speed run drove 42.5 s, then swung out of the lane on the straight at speed 0.40 with the gains tuned at 0.32 | At higher speed a correction moves the robot further before the next frame; scaling keeps the same effect at every speed |
| D4e | 2026-09-20 | Damping KD 0.03 -> 0.06. With adaptive speed (straights at about 0.39) the swing grew a little every lap (seen by the user, lane lost after 42.5 s and 33.3 s) although loop timing stayed constant (about 46 ms, no heating); at 0.32 the same gains were stable for 60 s | Growing oscillation = too little damping at the higher speed; the model output is smooth, so more D is possible |
| D5b | 2026-09-20 | Speed = min(curve model speed, steering speed): the robot slows from lane_x 0.10 and drives at SPEED_SHARP from 0.30; curve probabilities are smoothed over time (weight 0.3 per prediction). Log of the 33 s run: the robot sped up to 0.39 while still turning out of the sharp curve (lane_x +0.25..+0.30) and the swing started right after; the curve prediction flickered in the gentle curve (p_gentle 0.90 -> 0.04 -> 0.93), pumping the speed | User's hypothesis (turning at high speed) confirmed by the log; steering magnitude as a curvature indicator is the guide's own suggestion, combined with the ML curve class |
| D12 | 2026-09-16 | Logging: one CSV row per control step per run (time, dt, mode, model outputs, steering, speed, FPS) plus a run metadata file (config constants, model version), on the USB stick. Every experiment recorded as problem -> hypothesis -> change -> test -> result | Graphs and tables are required deliverables |

## Incidents

**2026-09-20, robot lost power while recording.**
- **What happened:** the battery started at 11.66 V (about 68 %). After about 4 minutes of continuous driving and turning in place (sessions `lap_b`, `weave_b`, `spin_b`), the WiFi firmware crashed during a turn in place (kernel log 19:49:42, "Hardware restart was requested"). About a minute later, 5 seconds into `weave_b2`, the Jetson lost power without shutting down; the session was never closed and its trace was lost.
- **Most likely cause:** the battery voltage sagged under motor load (turning in place and starting from standstill draw the most current), and the Jetson browned out. The WiFi crash is a typical early sign of supply dips. Not proven: the voltage was not logged during the run.
- **Fix:** battery guard, voltage logging and line-buffered files in `auto_record.py` (POWER). Start motor sessions with a charged battery, and check it between sessions.
- **Still to verify:** the thresholds are first guesses; the new voltage log will show the real sag. If it happens with a full battery, check the cells and consider the Jetson 5 W power mode.

**2026-09-20, robot drove into a chair.**
- **What happened:** a lane training ran on the robot while `auto_record.py` drove (session `lap_cw`, deleted). Free memory fell to about 120 MB, and the camera delivered one frame at the start and then none. The JetBot camera thread ends silently on a read error, so `camera.value` kept returning that one image. The robot turned around and drove 47 s on the frozen image with a constant steering command, into a chair. The first emergency stop (`pkill -f auto_record.py` inside `bash -c`) killed its own shell, so the motors stopped only with the second command.
- **Fixes:** (1) never train or run other heavy jobs while the robot drives; (2) `auto_record.py` stops when no new camera frame arrives for 0.5 s (`wait_for_new_frame`), and checks the camera before moving; (3) `scripts/stop_robot.sh` sends Ctrl-C (SIGINT) so the script's clean-up stops the motors, then stops them directly as a backup. A plain kill (SIGTERM) skips the clean-up and leaves the motors running.

## Risks to measure

- `auto_record.py` drives full laps stably since the damping fix (2026-09-20). A weave of 40 px left the lane in the couch curve; 25 px is the next test.
- Label noise: while turning in place, one curved line can cross the measuring row twice and pass as two lines, giving a wrong lane label on a few percent of the turning frames. Driving frames are clean.
- The battery percent is only meaningful at rest: while charging the voltage reads high (64 % before the run, a false 95 % on the charger).
- D2 with one model per task means one network pass per model per frame. Measure the frame rate in phase 2 and convert to TensorRT if it is too low.
- Recording at the camera's 224x224 keeps training and driving identical, but throws away detail. Revisit before Task 3, where signs are small and far away.
- If the kernel dies mid-session, `session.json` keeps the frame count from the last write. The labeling tool counts the files on disk instead.

## Open

Nothing blocking. Still needed from the team: tape width, lane width, radius of the sharpest curve, number of JetBots and batteries, team roles for the slides.
