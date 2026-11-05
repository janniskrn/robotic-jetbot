# State machine (Task 6)

The code is `decision.py` (when to switch) and `control.py` (what each state does). This file and the code
change together: every version of `decision.py` must match this table and diagram. Constants are in `config.py`.

Version: 2026-11-04 (S1d1: the cup mask measures how far the nearest cup in the lane is; AVOID3: swerve as stop,
turn 90 degrees, curve around the cup, turn back, each turn and the curve ended by a camera mark; recovery needs an
aligned lane; turns, STOP sign and parking planned).

## States

Priority 1 is the highest: when several conditions hold at once, the state with the higher priority wins.

| State | Priority | Entry condition | Action / control | Exit condition |
| :--- | :--- | :--- | :--- | :--- |
| `HALT` | 1 | lane not seen for 0.5 s (`LANE_LOST_TIMEOUT`) while following; recovery timeout; a swerve phase without its camera mark in time (`TURN_OUT_MAX`, `ARC_MAX`, `TURN_IN_MAX`); no lane at the start; battery low, camera frozen or Ctrl-C (in `drive.py`) | motors off, run ends, reason logged | none (end of run) |
| `OBSTACLE_AVOIDANCE` | 2 | the obstacle model sees a cup **and** the cup mask's nearest red band in the lane (abs(band x - lane_x) < `CUP_IN_LANE`) has its lower edge at or below `OBSTACLE_ROW` (about 35 cm) for `OBSTACLE_FRAMES` steps (HYBRID: the model's own distance was wrong with people behind the cup) | swerve to the inside of the oval in phases (`AVOID_PHASES`), the turns and the curve each ended by a camera mark (HYBRID): `brake` reverse pulse `BRAKE`, then standing still, `AVOID_BRAKE` in all; `turn_out` turns in place toward the pass side (kick, then `TURN_SPEED`) until the lane edge is `TURN_EARLY` before horizontal, or leaves the image after being within `TURN_LOST` of horizontal (90 degrees); `arc` curves around the cup (`ARC_WHEELS`) for at least `ARC_MIN` until the edge ahead is `ARC_EARLY` before horizontal (facing the lane); `turn_in` turns toward the pass side until the lane is found (aligned and centered). Lane-lost rule ignored | `turn_in` done -> `ROAD_RECOVERY`; a phase longer than `TURN_OUT_MAX`, `ARC_MAX` or `TURN_IN_MAX` -> `HALT` |
| `ROAD_RECOVERY` | 2 | swerve done | lane seen: normal steering, which brings the robot back to the center (the swerve can end off-center); lane not seen: slowly forward, turning gently away from the pass side (`RECOVER_SPEED`, `RECOVER_TURN`) | lane seen, aligned (lane mask: two lines about one lane width apart) and abs(lane_x) < `RECOVER_CENTERED` for `RECOVER_FRAMES` steps -> `ROAD_FOLLOWING` (a distant or crosswise lane does not count); `RECOVER_TIMEOUT` (4 s) -> `HALT` |
| `STOP` | 3 | required stop. Now: `--stop-only` and a close cup in the lane (as above) for `OBSTACLE_FRAMES` steps. Planned: STOP sign | `STOP_PHASES`: `brake` reverse pulse `BRAKE` (the motors coast at 0); `wait` motors off; once per stop `back`: slowly backwards (`BACKUP_SPEED`) while the nearest band is at or below `BACKUP_ROW` (20 cm), until above `BACKUP_TARGET_ROW` or `BACKUP_MAX` | no red band at or below `OBSTACLE_CLEAR_ROW` anywhere (the cup can hide the lane) **and** the lane visible (a hand in front of the camera hides both) for `OBSTACLE_CLEAR_FRAMES` steps -> `ROAD_FOLLOWING` |
| `SLOW_DOWN` | 4 | sharp curve ahead: p_sharp > `SLOW_DOWN_ENTER`; or a cup in the lane at or below `APPROACH_ROW` (about 60 cm), so the robot rolls on less after a stop. Planned: intersection ahead | lane following, speed capped at `SPEED_SHARP` | p_sharp < `SLOW_DOWN_EXIT` and no cup within the approach distance -> `ROAD_FOLLOWING` |
| `ROAD_FOLLOWING` | 5 | start (lane seen), recovery done, stop over, curve over | lane following: PD steering with curve feedforward, speed from the curve model (Task 1) | see the entry conditions of the other states |
| `TURN_LEFT` / `TURN_RIGHT` | 3 | planned: intersection detected and LEFT / RIGHT sign seen before it | planned: slow down, enter the turn, reacquire the road | planned: lane found -> `ROAD_FOLLOWING` |
| `PARKING` | 3 | planned: parking lot reached at the end of the route | planned: approach, align, stop inside the lines, retry if outside | planned: stopped inside the lines -> `HALT` |

Rules that hold in every state:
- The pass side is the inside of the oval, measured from the curve direction during the run (left until the
  first curve), or fixed with `--pass-side`.
- A short lane gap (under 0.5 s) while following keeps steering without lane_x (`Controller.hold`).
- Entering `OBSTACLE_AVOIDANCE` or `STOP` resets the controller, so the robot starts slowly afterwards.

## Diagram

```mermaid
stateDiagram-v2
    [*] --> ROAD_FOLLOWING: lane seen at start
    ROAD_FOLLOWING --> SLOW_DOWN: sharp curve (p_sharp > 0.5) or cup in the lane within 60 cm
    SLOW_DOWN --> ROAD_FOLLOWING: curve over (p_sharp < 0.3) and no cup near
    ROAD_FOLLOWING --> OBSTACLE_AVOIDANCE: cup close and in the lane
    SLOW_DOWN --> OBSTACLE_AVOIDANCE: cup close and in the lane
    state OBSTACLE_AVOIDANCE {
        [*] --> brake
        brake --> turn_out: 0.3 s
        turn_out --> arc: lane edge horizontal or out of view (90 degrees)
        arc --> turn_in: lane edge ahead horizontal again
        turn_in --> [*]: lane found
    }
    OBSTACLE_AVOIDANCE --> ROAD_RECOVERY: turn_in found the lane
    OBSTACLE_AVOIDANCE --> HALT: a phase misses its camera mark in time
    ROAD_RECOVERY --> ROAD_FOLLOWING: lane centered and aligned for 5 steps
    ROAD_RECOVERY --> HALT: 4 s without the lane
    ROAD_FOLLOWING --> STOP: cup close (--stop-only)
    SLOW_DOWN --> STOP: cup close (--stop-only)
    STOP --> ROAD_FOLLOWING: cup gone
    ROAD_FOLLOWING --> HALT: lane lost 0.5 s
    SLOW_DOWN --> HALT: lane lost 0.5 s
    HALT --> [*]
```

Planned states (`TURN_LEFT`, `TURN_RIGHT`, `PARKING`, `STOP` for a sign) are added to the diagram when they are
coded.
