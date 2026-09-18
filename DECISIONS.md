# Decisions

Compact log of every project decision. Newest facts win. IDs match the planning discussion.
Status: **decided**, **open** (options proposed, waiting for the team), **revisit** (decided for now, check again later).

## Project facts

| Fact | Detail |
| :--- | :--- |
| Robot | Waveshare JetBot, Jetson Nano 4 GB, JetPack 4.5 (L4T 32.5.0), Docker Jupyter with PyTorch 1.6, TensorRT 7.1, torch2trt |
| Motors | Can drive backward (-1..1). No wheel encoders: maneuvers without the camera are time-based |
| Camera | IMX219-160 wide angle, fixed mount, cannot be adjusted |
| Road | One colored tape line on the floor; the robot drives along the line. Track is built and drivable |
| Old collision dataset | Unusable: all 200 images are the same frame, blocked and free identical. Recollect on the track |
| Our code location | Under `notebooks/` (mounted into Docker). The `jetbot/` package is baked into the image at build time, edits there are not seen |
| Training | Small trainings (under 40 min) run on the robot. Larger trainings run on the MacBook M4 24 GB; the robot is the fallback when the Mac is not available |

## Decided

| ID | Date | Decision | Why |
| :--- | :--- | :--- | :--- |
| CAM | 2026-09-16 | Waveshare ISP calibration installed system-wide via `scripts/camera/install_camera_isp.sh` (run once with sudo; verify with a before/after photo in light) | Removes the pink cast for every program, permanently. Must be in place before any data collection |
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
| STEP1 | 2026-09-17 | Datasets are recorded as sessions: `usb/images/datasets/<date>_<name>/` with frames at 4 Hz plus a `session.json` (tape color, lighting, section, obstacle, notes). Tool: `notebooks/mini_av/record_dataset.ipynb` with `recorder.py` | Labeling happens later on the Mac (D10) |
| D12 | 2026-09-16 | Logging: one CSV row per control step per run (time, dt, mode, model outputs, steering, speed, FPS) plus a run metadata file (config constants, model version), on the USB stick. Every experiment recorded as problem -> hypothesis -> change -> test -> result | Graphs and tables are required deliverables |

## Open

Nothing blocking. Still needed from the team: tape color and width, curve radii of the built track, number of JetBots and batteries, team roles for the slides.
