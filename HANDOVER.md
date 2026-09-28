# Handover (2026-09-27, end of session 1)

For the next Claude session. Read this, then `CLAUDE.md`, `DECISIONS.md`, `WEEK1_PLAN.md`.

**Your first job: decide, plan and execute a data strategy** (details in "The open question" below).
Before starting, run a critical review (Sonnet subagent, high effort) of this plan and the code in
`notebooks/mini_av/`, as the last session did (DECISIONS.md: REVIEW2, PASS2).

## Where we are

- **Task 1 works in principle**: with the models and our control layer the robot drove 60 s laps in both
  directions (results: `results/week1/task1_results.md`, graphs on the USB stick in `images/results/week1/`).
  The stock-style baseline loses the lane after about 20 s.
- **The sharp curve at the couch, counterclockwise, is still the weak point.** Latest runs (2026-09-27, with
  the new curve model): 16.8 s and 28.6 s, both ended there.
- **Models:** lane (lane visible 99.6 %, lane_x error 0.022 on held-out sessions) and curve (85.9 %, sharp
  recall 34/37 after class weighting, `DECISIONS.md` CURVE2). Both converted to TensorRT.
- **Task 2 (obstacle avoidance) has not started.** Decisions ready: modes FOLLOW / AVOID / RECOVER / STOP
  (D9b), passing on the inside of the oval with left as fallback (PASS, PASS2).

## The open question: more data, and which data

The evidence says the remaining failure is **perception, not control**:

- In the sharp counterclockwise curve only the outer line is visible and the robot is at an angle. There the
  lane model reports too small a lane position, and in the last run it even **flipped sign for a few frames**
  (log `2026-09-28_03-45-05_v2_adaptive_b`, 27.9 s: +0.11 instead of negative), so the robot briefly steered
  out of the curve. The control now smooths the curve direction over about a second (committed), but that
  treats the symptom.
- The lane model has never seen such frames with correct labels: the color mask that produces the labels is
  itself unreliable exactly there (one line, sideways tape), so those frames were labeled "lane not visible"
  and dropped from the lane_x loss.

**Plan this properly, then execute it:**

1. **Measure first, offline.** Build a replay check: run the current models over the frames of the failed runs
   (`usb/images/datasets/*drive_v2_adaptive_*`) and compare with the mask labels, split by section
   (straight / gentle / sharp) and by direction. That gives a hard number for "how bad is the model in the
   sharp curve" and lets every later change be judged without driving. This is the cheapest and most useful
   next step.
2. **Decide what data is missing**, at least:
   - **Hard cases:** the sharp curve counterclockwise, from many starting positions and angles, including
     views with only one line, entering too wide, and the curve exit.
   - **Negative and false-positive material:** frames with no lane at all, the lane far away sideways, other
     blue objects (the couch), strong glare, other lighting (day, evening, lamp), motion blur. These teach
     "lane not visible" and stop false confidence.
   - **Balance:** currently about 3300 labeled frames, mostly straights. Count per section and direction, and
     record a target ("at least N frames per section and direction, at least M with the lane not visible").
   - **Label quality where it matters most:** the mask is weakest in the sharp curve, which is where the model
     needs the best labels. Options: hand-label a few hundred frames there with `02_manual_label.py`
     (it exists and is tested), or improve the mask for one-line situations, or both. The decision GOLD said
     "no human gold set"; propose revisiting it for the sharp curve only, and ask the user.
3. **Then retrain and measure again with the replay check**, not by driving first.

## Other levers for quality (evaluate, don't apply blindly)

- **Model output:** instead of one lane position, predict the two line positions separately (left and right
  line, each with "visible"), and compute the lane center in code. In the sharp curve a single line is then a
  first-class case instead of a missing label.
- **Auxiliary output "curve direction"** (left / right / none) trained on the signed curve value; would fix the
  sign flip in perception rather than in control.
- **More input:** the models see 224x224. Recording at a higher resolution and downscaling later keeps detail
  for small or distant tape (also needed for traffic signs in week 2).
- **Time context:** the model sees single frames. Feeding two frames (now and 0.15 s ago) or smoothing the
  model output would stabilize exactly the flickering frames.
- **Augmentation:** currently mirror, brightness, contrast. Motion blur and small rotations match the real
  failure cases; hue must stay untouched (the blue tape color is the signal).
- **Training:** longer training with early stopping, and a learning-rate schedule; the curve model was still
  improving when it stopped.
- **Evaluation:** keep a fixed hard-case test set (sharp curve, both directions, mixed lighting) and report
  the numbers for every model version in `DECISIONS.md`, the way CURVE1 and CURVE2 are recorded.

## After that

1. Repeat the Task 1 comparison with the final configuration (baseline, nocurve, adaptive, both directions)
   and regenerate the table with `analyze_runs.py`.
2. Task 2 per `WEEK1_PLAN.md` Phases 4-5, with the open items in `DECISIONS.md` (motor trim, numeric
   "centered" for RECOVER, avoidance timing across the battery range, mode table).

## How to run things (on the robot, from `~/jetbot`)

| What | Command |
| :--- | :--- |
| Battery | `python3 notebooks/mini_av/battery.py` (valid with the charger unplugged) |
| Emergency stop | `scripts/stop_robot.sh` |
| Camera broken ("(Argus) Error") | `scripts/restart_camera.sh` (happened twice; always works) |
| Drive (in the container) | `echo 'jetbot' \| sudo -S -p '' docker exec -w /workspace/jetbot/notebooks/mini_av jetbot_jupyter python3 drive.py --name NAME --seconds 60` (add `--baseline` or `--no-curve`) |
| Record laps by color mask | same prefix, `python3 auto_record.py --name lap_ccw10 --seconds 60` (`--turn-around`, `--weave 25`, `--spin-every 6`) |
| Label | host: `cd notebooks/mini_av && python3 02_auto_label.py /home/jetbot/usb/images/datasets/<session>/` |
| Train | container: `python3 03_train.py --task curve --val lap_ccw4 --val lap_cw3 --epochs 6` (15-25 min) |
| TensorRT (after every training) | container: `python3 03_convert_trt.py --task curve` |
| Results | host: `python3 analyze_runs.py /home/jetbot/usb/logs/<run> ...` |
| Long job without a session | `docker exec -d ... bash -c "python3 ... > /workspace/usb/logs/<name>.log 2>&1; echo FINISHED >> ..."` |

- **Heredoc + sudo:** `echo pw | sudo -S docker exec -i ... <<EOF` fails (the heredoc replaces the password
  input). Use `echo 'jetbot' | sudo -S -p '' -v && sudo -n docker exec -i ... <<'EOF'`.
- **Stopping a driving script:** only with Ctrl-C (`pkill -INT -f '^python3 drive[.]py'`), never a plain kill.
- **Robot off the lane:** `auto_record.py --turn-around --seconds 0.3` sometimes finds the lane again; usually
  the human has to put the robot back. Every lane loss costs a human trip, so plan runs in batches.

## Rules learned the hard way (all in CLAUDE.md / DECISIONS.md)

- Never train while the robot drives: low memory froze the camera and the robot hit a chair.
- Check the battery before motor sessions; below 11.4 V charge.
- Every driving program: battery guard, camera watchdog, motor watchdog, Ctrl-C stop, motors off in `finally`,
  and waiting for the lane before the first movement (a forgotten lens cap cost one run).
- Steering: delay in the loop causes oversteering (D4b-D4f); higher speed needs more damping and gain
  scheduling; the robot must not speed up while still turning (D5b).
- Session names can be wrong about direction: take it from the data (sign of curve_value or mean lane_x).
- Curve labels only from runs that did not swing: driving runs are `"curves_trusted": false` until checked.

## State of code and data

- Code: `notebooks/mini_av/` (see its README). Steering: KP 0.15, KD 0.06, gain scheduling to 0.32,
  feedforward 0.015 gentle / 0.07 sharp with a smoothed direction, speeds 0.40 / 0.35 / 0.31, speed limited
  while turning, startup waits for the lane.
- Models in `notebooks/mini_av/models/` (weights not in git), metrics in `lane.json` / `curve.json`.
- Data on the USB stick in `images/datasets/`: about 3300 labeled training frames plus the `drive_*` runs;
  validation sessions `lap_ccw4` and `lap_cw3`; sessions with `test` in the name are never used.
- Logs of every drive: USB stick `logs/`.

## Human-only steps

Charging and unplugging, putting the robot on the lane (also after every lane loss), providing and placing
the obstacle box, checking the free floor beside the lane, watching Task 2 trials, the week 1 demo.
