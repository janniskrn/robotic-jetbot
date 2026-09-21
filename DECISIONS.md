# Decisions

Compact log of every project decision. Newest facts win. IDs match the planning discussion.
Status: **decided**, **open** (options proposed, waiting for the team), **revisit** (decided for now, check again later).

## Project facts

| Fact | Detail |
| :--- | :--- |
| Robot | Waveshare JetBot, Jetson Nano 4 GB, JetPack 4.5 (L4T 32.5.0), Docker Jupyter with PyTorch 1.6, TensorRT 7.1, torch2trt |
| Motors | Can drive backward (-1..1). No wheel encoders: maneuvers without the camera are time-based |
| Camera | IMX219-160 wide angle, fixed mount, cannot be adjusted |
| Road | Camera survey 2026-09-20 (`usb/images/track_survey/`): **two parallel blue tape lines forming a lane**, light speckled floor, sunlight from windows causes glare, tape wrinkled in the sharp curve. Track is built and drivable |
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
| SUDO | 2026-09-17 | Sudo on the robot is pre-approved; the password lives in Claude's local memory, not in the repo | The repo is pushed to GitHub |
| STEP1 | 2026-09-17 | Datasets are recorded as sessions: `usb/images/datasets/<date>_<name>/` with frames at 4 Hz plus a `session.json` (tape color, lighting, section, obstacle, notes, frame size, max speed). Tool: `notebooks/mini_av/01_record_dataset.ipynb` with `recorder.py` | Labeling happens later on the Mac (D10) |
| STRUCT | 2026-09-17 | Our code lives in `notebooks/mini_av/`, files numbered in pipeline order (01 record, 02 label, 03 train, 04 drive). No week folders | The same files are reused in later weeks; a week is a deadline, not a component |
| LANE | 2026-09-20 | The robot drives in the lane center between the two blue lines. Target point = lane center where it crosses the lookahead circle; "line visible" (D8) means "lane visible"; avoidance (D7) leaves the lane to the fixed side and returns into it | Confirmed by the user after the camera survey; replaces the earlier single-line note |
| AUTOREC | 2026-09-20 | The robot records clean laps itself: `auto_record.py` drives with the classical blue-tape mask (`lane_mask.py`) and writes `auto_labels.csv` (lines seen, lane center) per frame as pre-labels | User choice; faster than gamepad driving, labels come for free. Data tool only, not the final controller |
| POWER | 2026-09-20 | Motor sessions only with enough battery: `auto_record.py` refuses to start below 11.4 V at rest (about 50 %) and stops when the voltage stays below 10.8 V for 2 s under load; the voltage is logged in `trace.csv` and log files are line-buffered | Incident below |
| D12 | 2026-09-16 | Logging: one CSV row per control step per run (time, dt, mode, model outputs, steering, speed, FPS) plus a run metadata file (config constants, model version), on the USB stick. Every experiment recorded as problem -> hypothesis -> change -> test -> result | Graphs and tables are required deliverables |

## Incidents

**2026-09-20, robot lost power while recording.**
- **What happened:** the battery started at 11.66 V (about 68 %). After about 4 minutes of continuous driving and turning in place (sessions `lap_b`, `weave_b`, `spin_b`), the WiFi firmware crashed during a turn in place (kernel log 19:49:42, "Hardware restart was requested"). About a minute later, 5 seconds into `weave_b2`, the Jetson lost power without shutting down; the session was never closed and its trace was lost.
- **Most likely cause:** the battery voltage sagged under motor load (turning in place and starting from standstill draw the most current), and the Jetson browned out. The WiFi crash is a typical early sign of supply dips. Not proven: the voltage was not logged during the run.
- **Fix:** battery guard, voltage logging and line-buffered files in `auto_record.py` (POWER). Start motor sessions with a charged battery, and check it between sessions.
- **Still to verify:** the thresholds are first guesses; the new voltage log will show the real sag. If it happens with a full battery, check the cells and consider the Jetson 5 W power mode.

## Risks to measure

- `auto_record.py` drives full laps stably since the damping fix (2026-09-20). A weave of 40 px left the lane in the couch curve; 25 px is the next test.
- D2 with one model per task means one network pass per model per frame. Measure the frame rate in phase 2 and convert to TensorRT if it is too low.
- Recording at the camera's 224x224 keeps training and driving identical, but throws away detail. Revisit before Task 3, where signs are small and far away.
- If the kernel dies mid-session, `session.json` keeps the frame count from the last write. The labeling tool counts the files on disk instead.

## Open

Nothing blocking. Still needed from the team: tape width, lane width, radius of the sharpest curve, number of JetBots and batteries, team roles for the slides.
