# Decisions

Compact log of every project decision. Newest facts win. IDs match the planning discussion.
Status: **decided**, **open** (options proposed, waiting for the team), **revisit** (decided for now, check again later).

## Project facts

| Fact | Detail |
| :--- | :--- |
| Robot | Waveshare JetBot, Jetson Nano 4 GB, JetPack 4.5 (L4T 32.5.0), Docker Jupyter with PyTorch 1.6, TensorRT 7.1, torch2trt |
| Motors | Can drive backward (-1..1). No wheel encoders: maneuvers without the camera are time-based |
| Camera | IMX219-160 wide angle, fixed mount, cannot be adjusted |
| Road | One colored tape line on the floor; the robot drives along the line |
| Old collision dataset | Unusable: all 200 images are the same frame, blocked and free identical. Recollect on the track |
| Our code location | Under `notebooks/` (mounted into Docker). The `jetbot/` package is baked into the image at build time, edits there are not seen |
| Training | MacBook M4 24 GB (primary). Robot is the fallback; trainings under 40 min may run on the robot |

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
| D12 | 2026-09-16 | Logging: one CSV row per control step per run (time, dt, mode, model outputs, steering, speed, FPS) plus a run metadata file (config constants, model version), on the USB stick. Every experiment recorded as problem -> hypothesis -> change -> test -> result | Graphs and tables are required deliverables |

## Open

| ID | Question | Options (details in the planning chat) |
| :--- | :--- | :--- |
| D2 | Perception architecture and label schema | Multi-task net / multi-task net + detector / one model per task |
| D7 | Avoidance maneuver around an obstacle on the tape line | Timed bypass / timed out + sensed return / offset line tracking / obstacle-guided |
| D8 | "Line visible" signal for recovery | Learned head / classical color mask / learned head with auto labels |
| D10 | Data collection and labeling workflow | Manual snapshots / record then label / auto-label + review / model-assisted from failures |
| D11 | Mac training details and transfer to the robot | Transfer path, weight format, shared preprocessing |
