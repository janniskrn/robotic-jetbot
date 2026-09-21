# Handover (2026-09-20, end of session 1)

For the next Claude session. Read this, then `CLAUDE.md`, `DECISIONS.md`, `WEEK1_PLAN.md`.

**Before starting anything: run a critical review.** Hand this file, `WEEK1_PLAN.md` (Phases 4-6),
`DECISIONS.md` and `notebooks/mini_av/` to a Sonnet subagent (high effort) and ask it to find gaps,
risks and bugs in the Task 2 plan and the current code. Fix what it finds, then start.

## Where we are

- **Task 1 (adaptive lane following) works** in both directions: 60 s runs without losing the lane,
  faster on straights (about 0.38), slower in curves (0.34-0.36). Results: `results/week1/task1_results.md`,
  graphs on the USB stick in `images/results/week1/`.
- **Weak spot:** the sharp curve at the couch counterclockwise (a left turn) is marginal (lane_x down to
  -0.48). The curve model rarely predicts "sharp" (recall 21/37, clockwise almost never).
- **Task 2 (obstacle avoidance) not started.** Decided: minimal modes FOLLOW / AVOID / RECOVER / STOP (D9b),
  pass on the inside of the oval, default left (PASS).

## Next steps, in order

1. **Critical review** (see above).
2. **More counterclockwise sharp-curve data (CCWGAP):** clean laps counterclockwise with `auto_record.py`,
   plus the frames every `drive.py` run records (`drive_*` sessions). Label with `02_auto_label.py`.
   Drive sessions where the robot swung must get `"curves_trusted": false` in their `session.json`.
3. **Retrain the curve model** (and consider the lane model) with the new data; always run
   `03_convert_trt.py` afterwards, otherwise the old TensorRT engine is used. Check sharp recall.
4. **Re-run the Task 1 comparison** with the final configuration (baseline, nocurve, adaptive, both directions)
   and regenerate the table with `analyze_runs.py`.
5. **Task 2**, `WEEK1_PLAN.md` Phases 4-5: obstacle (a box in a strong non-blue color, the human places it),
   obstacle data and labels, obstacle model (free/blocked, D6), trigger with debounce and hysteresis,
   AVOID on timers (D7), RECOVER with lane_visible + centered, pass side per PASS.

## How to run things (on the robot, from `~/jetbot`)

| What | Command |
| :--- | :--- |
| Battery | `python3 notebooks/mini_av/battery.py` (valid with the charger unplugged) |
| Emergency stop | `scripts/stop_robot.sh` |
| Camera broken ("(Argus) Error") | `scripts/restart_camera.sh` |
| Drive (in the container) | `echo 'jetbot' \| sudo -S -p '' docker exec -w /workspace/jetbot/notebooks/mini_av jetbot_jupyter python3 drive.py --name NAME --seconds 60` (add `--baseline` or `--no-curve`) |
| Record laps by color mask | same prefix, `python3 auto_record.py --name lap_ccw7 --seconds 60` (`--turn-around`, `--weave 25`, `--spin-every 6`) |
| Label | `cd notebooks/mini_av && python3 02_auto_label.py /home/jetbot/usb/images/datasets/<session>/` (host) |
| Train | container: `python3 03_train.py --task curve --val lap_ccw4 --val lap_cw3 --epochs 6` (15-20 min) |
| TensorRT | container: `python3 03_convert_trt.py --task curve` |
| Results | host: `python3 analyze_runs.py /home/jetbot/usb/logs/<run> ...` |

- **Heredoc + sudo:** `echo pw | sudo -S docker exec -i ... <<EOF` fails (the heredoc replaces the password
  input). Use `echo 'jetbot' | sudo -S -p '' -v && sudo -n docker exec -i ... <<'EOF'`.
- **Stopping a driving script:** only with Ctrl-C (`pkill -INT -f '^python3 drive[.]py'`), never a plain kill:
  that skips the clean-up and the motors keep running. `pkill -f` inside `bash -c` can match its own shell.
- **Robot off the lane:** `auto_record.py --turn-around --seconds 0.3` sometimes finds the lane again;
  often the human has to put the robot back.

## Rules learned the hard way (all in CLAUDE.md / DECISIONS.md)

- Never train while the robot drives: low memory froze the camera and the robot hit a chair.
- Check the battery before motor sessions; below 11.4 V charge. A brownout happened at 64 % after 4 min of turning.
- Every driving program: battery guard, camera watchdog, motor watchdog, Ctrl-C stop, motors off in `finally`.
- Steering tuning: any delay in the loop (smoothing, integral) caused oversteering; faster driving needed more
  damping and gain scheduling; the robot must not speed up while still turning (D4b-D4f, D5b).
- Session names can be wrong about direction: take it from the data (sign of curve_value or mean lane_x).

## Current state of the code and data

- Code: `notebooks/mini_av/` (see its README). Final steering: KP 0.15, KD 0.06, gain scheduling to 0.32,
  curvature feedforward 0.015 / 0.04, speeds 0.40 / 0.35 / 0.31, speed limited while turning (0.10-0.30).
- Models (`notebooks/mini_av/models/`, weights not in git): lane (visible 99.6 %, lane_x error 0.022),
  curve (86.6 %). Metrics in `lane.json`, `curve.json`.
- Data: USB stick `images/datasets/`, 2912 labeled training frames plus 14 `drive_*` sessions not yet used
  for training. Validation sessions: `lap_ccw4`, `lap_cw3`. Sessions with `test` in the name are never used.
- Logs of every drive: USB stick `logs/`.

## Human-only steps coming up

Charging and unplugging, putting the robot on the lane, providing and placing the obstacle box, checking
the free floor beside the lane, watching Task 2 trials, the week 1 demo.
