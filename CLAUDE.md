# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Git Workflow

**Commit, pull, and push on your own. No need to ask.**

- Always work on `master` (the main branch). No feature branches.
- Run `git pull` before starting any work.
- Commit whenever it makes sense for the project: small, logical, self-contained steps.
- Push immediately after every commit. Never leave a commit unpushed.

## 6. Current Assignment: Mini Autonomous Vehicle Challenge

**Never implement anything without explicit permission.**

- The assignment is described in `PROJECT_GUIDE_1.md` (JetBot Project Guide #1, a 6-week project).
- Analysis, explanations, plans, and suggestions are fine. Writing or changing code or notebooks for a task needs the user's approval first.
- Propose the approach, wait for a clear "go", then implement only what was approved.
- Coding policy from the guide: reuse existing notebooks as building blocks only. Steering, speed control, avoidance, recovery, intersection, state machine, cruise control, and parking logic must be team-written.
- **All decisions are logged in `DECISIONS.md`.** Read it before proposing anything. Add every new decision there (keep it compact) and never contradict a decided entry without asking.

### 6.1 How We Work: Step by Step

We build the robot in small steps. Each step must be tested and approved before the next one starts.

1. **Propose** one small step: what it does, why, and how we will test it.
2. **Wait** for the user's "go".
3. **Implement** only that step, with minimal and easy code.
4. **Test** it on the robot (or explain exactly how the user can test it).
5. **Wait** for the user to approve the result. Never continue to the next step or task without approval.
6. **Commit and push** the approved step.

Code style:
- Minimal, simple code that is easy to read and easy to explain in the presentation.
- Short functions, clear names, a short comment where the "why" is not obvious. No clever tricks.
- Follow best practices (clean structure, no magic numbers hidden in code: put tuning values as named constants at the top).
- Keep perception, decision, and control clearly separated (required for the final program).
- For every change, be ready to explain: problem → design → code change → test → result.

### 6.2 The Plan (Follow Strictly, in This Order)

Full details are in `PROJECT_GUIDE_1.md`. Do not skip ahead or mix tasks from later weeks.

| Week | Task | Done when |
| :--- | :--- | :--- |
| 1 | **Task 1:** Adaptive Road Following | Stable steering via our own control layer; faster on straights, slower on sharp curves; tested on straight, gentle, and sharp curves |
| 1 | **Task 2:** Road Following + Collision Avoidance | `ROAD_FOLLOWING → AVOIDANCE → ROAD_RECOVERY → ROAD_FOLLOWING` without manual steering |
| 2 | **Task 3:** Traffic Sign Recognition | `STOP` / `LEFT` / `RIGHT` / `NONE` classifier; output goes to the decision layer, never directly to the motors |
| 2 | **Task 4:** Intersection Navigation | Slow down → enter turn → reacquire road → resume road following, based on the sign |
| 2 | **Task 5:** Parking | Starts in and returns to the parking space; stops fully inside the lines; has a retry behavior |
| 3 | **Task 6:** State Machine / Integration | One program, explicit state machine with the required states; each state has entry condition, action, exit condition, priority |
| 4 | **Task 7:** Adaptive Speed + ACC | `target_speed = min(curve_speed, safe_following_speed)`; smooth following, stopping, and restarting behind a lead JetBot |
| 5–6 | **Task 8:** Final Challenge + Presentation | Full autonomous run on the unknown course from parking to parking; slides, graphs, tables, ZIP submission |

Every week ends with a demonstration of that week's tasks.

### 6.3 Professor's Advice (Not Mandatory, Keep in Mind)

- **Use a lot of machine learning** in the project (e.g. learned perception for road, obstacles, signs, intersections, parking, the lead JetBot) where it makes sense.
- **Use a state machine.** Keep each version of the code together with its matching state machine (a diagram or table of states and transitions), so code and state machine always fit together.

## 7. Storage: Images Only on the USB Stick

- All images and image datasets must be saved on the USB stick, never on the SD card. See `STORAGE.md`.
- Host path `/home/jetbot/usb/images/`, which Jupyter sees as `/workspace/usb/images/`.
- Any new image folder is a symlink into `usb/images/` (or an absolute `/workspace/usb/images/...` path).
- Model weights (`*.pth`) stay on the SD card.

## 8. Sudo

- Running `sudo` on the robot is pre-approved: do it without asking.
- User `jetbot`, password `jetbot` (the JetBot image default). Use it as `echo 'jetbot' | sudo -S -p '' <command>`.
- Note: this repository is public on GitHub, so the password is public too. Do not reuse it anywhere else, and keep the robot off untrusted networks.

## 9. Battery

- Before any session that drives the motors, check the battery: `python3 ~/jetbot/notebooks/mini_av/battery.py`. Do not start below 11.4 V at rest (about 50 %), and check again between sessions.
- The robot browned out on 2026-09-20 after about 4 minutes of driving from 68 %. See the incident in `DECISIONS.md`.

## 9b. Driving Safety

- Never run a training or any other heavy job while the robot drives: low memory froze the camera and the robot drove blind into a chair (2026-09-20, `DECISIONS.md`).
- Every program that drives the motors needs: battery guard, camera watchdog (stop after 0.5 s without a new frame), stop on Ctrl-C, motors stopped in `finally`.
- Emergency stop: `~/jetbot/scripts/stop_robot.sh`. Stop driving scripts with Ctrl-C (`pkill -INT`), never with a plain kill.

## 10. Never Use Emoji

- Never use emoji anywhere: chat responses, documentation, code, comments, notebooks, commit messages.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
