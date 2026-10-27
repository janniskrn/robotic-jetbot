# Goal: what the slides ask for

Analysis of the three slide files in the repository root. The full text of Guide #1 is in `PROJECT_GUIDE_1.md`;
this file adds Guide #2 and the state machine example, and says what they mean for our code.
The working plan toward this goal is `PLAN.md`.

| Source | Content |
| :--- | :--- |
| `JetBot_Project_Guide_1 (Autonomous_Vehicle) (rev3).pdf` | Objective, coding policy, Tasks 1-8, schedule, deliverables |
| `JetBot_Project_Guide_2 (StateMachine PseudoCode).pdf` | System and state diagram, pseudo code of the main loop, `update_state`, the models and the behaviors |
| `State_Machine_Example.pdf` | How a state machine is written down: diagram plus present state / input / next state / output table |

## 1. Final goal

A JetBot starts in a parking space, drives a course it has never seen (curves, a sharp curve, a T or 4-way
intersection, a STOP sign, a LEFT/RIGHT sign, a pedestrian/obstacle, a section with a lead JetBot), and parks
completely inside the parking lines at the end. No human steering during the scored run. Obstacle and sign
positions, lighting or road appearance are changed for the final test.

## 2. Required architecture (Guide #2, state diagram)

```
Camera -> Perception (models)   -> State transition -> Behavior execution -> Motor control
           road / obstacle / sign    update_state(...)   <state>_step(...)     set_motor_commands(steering, speed)
                       ^                                                                      |
                       +-------------------- every camera frame ---------------------------- +
```

- **Several models**, each run on the frame, each returning a result object (not a motor command). The picture
  shows three as an **example** (user, 2026-10-26); which models we use is our design:

  | Model in the example | Output in the slides | Purpose |
  | :--- | :--- | :--- |
  | Road model | target point (x, y) | road following, road lost / reacquired |
  | Obstacle model | free / blocked score | obstacle confirmed |
  | Traffic sign model | STOP / LEFT / RIGHT (+ NONE), confidence | stop and turn decisions |

- **One state transition function** `update_state(current_state, road, obstacle, sign) -> next_state`. Only it
  changes the state.
- **Behavior execution:** only the behavior of the current state runs (`road_following_step`,
  `obstacle_avoidance_step`, `road_recovery_step`, `turn_left_step`, ...). Each returns `(steering, speed)`.
- **Centralized motor control:** one function `set_motor_commands(steering, speed)` clamps the values and is the
  only place that writes the motors. Perception never commands the motors.

## 3. State transitions (Guide #2)

Priority in `update_state`, highest first:

1. `EMERGENCY_STOP_REQUIRED` -> `STOP`
2. `OBSTACLE_CONFIRMED` -> `OBSTACLE_AVOIDANCE`
3. `STOP_SIGN_CONFIRMED` -> `STOP`
4. `TURN_SIGN_CONFIRMED` -> `TURN_LEFT` / `TURN_RIGHT`
5. `ROAD_LOST` -> `ROAD_RECOVERY`
6. otherwise -> `ROAD_FOLLOWING`

Transitions shown in the diagram:

| From | Condition | To |
| :--- | :--- | :--- |
| any | emergency stop required | `STOP` |
| `ROAD_FOLLOWING` | stop sign confirmed | `STOP` |
| `STOP` | condition not in STOP any more | `ROAD_FOLLOWING` |
| `ROAD_FOLLOWING` | obstacle confirmed | `OBSTACLE_AVOIDANCE` |
| `OBSTACLE_AVOIDANCE` | obstacle passed and road reacquired (`avoidance_phase = COMPLETE`) | `ROAD_FOLLOWING` |
| `ROAD_FOLLOWING` | turn sign confirmed (LEFT / RIGHT) | `TURN_LEFT` / `TURN_RIGHT` |
| `TURN_LEFT` / `TURN_RIGHT` | turn completed | `ROAD_FOLLOWING` |
| `ROAD_FOLLOWING` | road lost | `ROAD_RECOVERY` |
| `ROAD_RECOVERY` | road reacquired | `ROAD_FOLLOWING` |

`OBSTACLE_AVOIDANCE` has its own sub-phases (a nested state machine): `SLOW_DOWN -> TURNING -> PASSING ->
RECOVERY -> COMPLETE`, each with its own condition (`READY_TO_TURN`, `TURN_COMPLETED`, `OBSTACLE_PASSED`,
`ROAD_REACQUIRED`).

**State machine example slide:** a state continues while its STAY condition is true; a TRANSITION happens only
when its condition is met. A state machine is written as a diagram **and** a table (present state, input, next
state, output). For our code this means: states are explicit names, transitions are explicit conditions, and a
transition table in the docs matches the code one to one.

## 4. Required states (Guide #1, Task 6)

Each state needs an entry condition, an action, an exit condition and a priority.

| State | Meaning |
| :--- | :--- |
| `ROAD_FOLLOWING` | normal road tracking |
| `SLOW_DOWN` | reduce speed for a curve or an intersection |
| `OBSTACLE_AVOIDANCE` | avoid an obstacle or pedestrian |
| `ROAD_RECOVERY` | reacquire the road |
| `TURN_LEFT` / `TURN_RIGHT` | execute an instructed turn |
| `STOP` | STOP sign or required stop |
| `PARKING` | approach, align, stop inside the lines |

The state machine must be implemented by the team, not a dispatcher that calls the old notebooks.

## 5. Milestones (the slides' task numbers)

| Milestone | Task | Done when | Needs |
| :--- | :--- | :--- | :--- |
| M1 | Adaptive road following | own control layer, stable steering, faster on straights, slower on sharp curves; tested on straight, gentle, sharp | single lane |
| M2 | Road following + collision avoidance | `ROAD_FOLLOWING -> AVOIDANCE -> ROAD_RECOVERY -> ROAD_FOLLOWING` without manual steering; student-written avoidance and recovery | obstacle prop, recovery space |
| M3 | Traffic sign recognition | STOP / LEFT / RIGHT / NONE from own data; solves a shown problem (distance, position or lighting); output goes to the decision layer only | miniature signs (being bought) |
| M4 | Intersection navigation | detect the intersection, combine with the sign: slow down -> enter turn -> reacquire road -> resume following | T or 4-way intersection |
| M5 | Parking | starts in the space, returns, stops completely inside the lines; approach, alignment, stop condition, retry | marked parking space |
| M6 | State machine / integration | Tasks 1-5 in one program with an explicit state machine (states of section 4) | combined course |
| M7 | Adaptive speed + ACC | `target_speed = min(curve_speed, safe_following_speed)`; keeps the gap, stops behind a stopped lead, restarts smoothly, no oscillation, straight and curved | 2+ JetBots |
| M8 | Final challenge + presentation | full run parking to parking on the unknown course; deliverables below | full course |

Every week ends with a demonstration of that week's tasks.

## 6. Deliverables (Task 8)

- Final autonomous demonstration including complete parking at the end.
- Slides: every team member presents an own slide (job partition).
- One integrated Python program with separate perception, decision and control modules.
- System / state diagram with information flow and state transitions; purpose and procedure of the code.
- Experiment record per change: problem -> hypothesis/design -> code change -> test -> result.
- Training and test data summary: why data was added and what problem it solved.
- Graphs and tables for the results.
- One ZIP: source code, report, video, optional data. Name `StudentID_Name_mmddyyyy_DataMining.zip`. Late: -10 % per day.

## 7. Coding policy

- Reuse as building blocks: camera setup, motor API, model loading, dataset utilities.
- Team-written: steering, speed control, avoidance, recovery, intersection decisions, state transitions, cruise
  control, parking (see `AUTHOR` in `DECISIONS.md` for how we handle this).
- More images or a retrained model alone earn no credit: every change must change the system's behavior and be
  explainable.

## 8. What this means for us

- **Several models, combined by the state machine.** The road / obstacle / sign set in Guide #2 is an example
  (user, 2026-10-26), not a fixed list. We have lane, curve and obstacle models today; signs (and later the
  intersection, the parking lines and the lead JetBot) still need perception. Which models we end up with is a
  planning decision (`PLAN.md`).
- **Models measure, scripts decide.** Model outputs go into `update_state`; the behaviors and motor control are
  plain team-written code. This keeps the system consistent and explainable.
- **The state machine is code, not a comment:** one transition function with the priority order of section 3,
  one `<state>_step` per state, one motor function, and a table plus diagram that match the code.
- Simple and efficient code: the minimum that meets each milestone's "done when".
- Physical facts from the team: miniature street signs are being bought (2026-10-26); intersection, parking space
  and a second JetBot do not exist yet (`MOVE1`).
