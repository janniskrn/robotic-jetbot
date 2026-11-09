# Weekly rhythm

How the course runs from now on (professor, 2026-11-02). The goal itself is in `GOAL.md` and
`PROJECT_GUIDE_1.md`; the order of the technical work stays in `PLAN.md`. This file only says what has to
exist by which day of the week, and what the Tuesday presentation must contain.

## 1. The rules

| When | What |
| :--- | :--- |
| Every class | Work on the JetBot project. Nothing else |
| Every Thursday | Work on your own (programming, experiments). Upload the **latest source code** and a **summary of results** to the course system. Any format, text is fine |
| Every Tuesday | **Team presentation with a live demonstration** (points below). Then a discussion of the failures with the professor |

The Tuesday presentation must cover four points:

| # | Required | Where it comes from |
| :--- | :--- | :--- |
| 1 | What the team did during the last week | commits and new `DECISIONS.md` entries since the last Tuesday |
| 2 | Our ideas, and an explanation of the code we wrote | architecture (perception / decision / control), `STATE_MACHINE.md`, one code walkthrough |
| 3 | Accomplishments **and** failures, with our own analysis of why a task did not succeed | run logs, `results/`, model metrics, the failure table of the week |
| 4 | The next plan to turn the failure into a success | the next open steps in `PLAN.md` section 6 |

The professor's guidance is based on what we actually did, and the discussion is about the failures. So an
honest failure with a measured cause is worth more than a vague success.

## 2. What this changes for us

- **A demo must exist every week, not only code.** A step counts as done for Tuesday only if it ran on the
  track. `AVOID1` was coded for two weeks before its first track run, and the first run then failed.
- **Failures are part of the deliverable.** Keep the experiment record (`D12`: problem -> hypothesis -> change
  -> test -> result) and state the *cause*, not the symptom. "The robot left the lane" is a symptom; "each timed
  turn was about 130 degrees instead of 90, so the turn-in pointed back at the cup (`MOVE2`)" is a cause.
- **Film every run** (`PLAN.md` section 6). If the live demo fails on Tuesday, the video still shows the work.
- **Thursday is a fixed bundle**, not a scramble: code is already pushed, so the upload is the repository plus
  one results file.

No task deadlines are written down here (decision `ORDER`): this is the course's fixed weekly rhythm, while what
we build in which order stays in `PLAN.md`.

## 3. Thursday: work and upload

| Step | What | Done when |
| :--- | :--- | :--- |
| 1 | `git pull`, read `HANDOVER.md` and the "Now" marker in `PLAN.md` | clear which step is next |
| 2 | Battery check before any motor session (`battery.py`, at least 11.4 V at rest) | voltage noted |
| 3 | Run the planned step: code, offline test, then the track test, filmed | pass criterion of the step met or failed with logs |
| 4 | Write the result into `DECISIONS.md` (decision or incident) and tick the step in `PLAN.md` | both files updated |
| 5 | Commit and push every working step separately | `git status` clean, nothing unpushed |
| 6 | Write `results/week<N>/summary.md` from the template below | file exists, numbers filled in |
| 7 | Upload to the course system: repository link or ZIP of the source, plus `summary.md` | upload confirmed |

### Template for `results/week<N>/summary.md`

```markdown
# Week <N> summary

## Planned
<the steps from PLAN.md we aimed at>

## Done
<what ran, with numbers: runs, durations, pass criteria met>

## Results
| Metric | Value | Source |

## Failures and causes
| What failed | Evidence (run, log, frames) | Cause | Fix we chose |

## Next
<next steps from PLAN.md>
```

## 4. Tuesday: presentation and demonstration

Keep it to the four required points, in that order. One slide per point is enough; the demo carries the rest.

| Slide | Content | Material in the repository |
| :--- | :--- | :--- |
| 1 | Where we are against the eight milestones | `PLAN.md` section 1 |
| 2 | How the system works: camera -> models -> state machine -> control -> motors | `GOAL.md` section 2, `STATE_MACHINE.md` diagram |
| 3 | The code we wrote this week, and why | the week's commits, `DECISIONS.md` |
| 4 | Accomplishments with numbers | `results/`, `models/*.json`, run logs |
| 5 | Failures, causes, and what we changed | the failure table of `summary.md` |
| 6 | Next plan | `PLAN.md` section 6 |

**The slides are a file in the repository:** `presentation/index_v3.html`, opened from disk, no link and no
internet needed. It starts on a roadmap of the six weeks and leads into the slides of the week being
presented, in the order of the professor's presentation guideline (architecture, source code, explanation,
results, next plan). What to change each week, where every number comes from, and the checks to run first are in
[`presentation/README.md`](presentation/README.md); `python presentation/check.py index_v3.html` runs the static half in a
second, including a check that every line of code on a slide is still in its source file.

**Demonstration:** live run on the track. Before it: battery charged, lane clear of cups unless the cup is part
of the demo, other robots off the track, `scripts/stop_robot.sh` ready in a terminal. Fallback: the filmed run
from Thursday.

**Presenters:** Task 8 requires every member to present an own slide, so the slides rotate. Fill this in as a
team (`PLAN.md` S0):

| Slide topic | Owner |
| :--- | :--- |
| System architecture and state machine | |
| Perception and models (data, training, metrics) | |
| Control (steering, speed) and results | |
| Avoidance, recovery and failure analysis | |

## 5. Weekly log

One row per week, filled on Thursday and used on Tuesday.

| Week | Step worked on | Demo shown | Accomplishment | Failure and cause | Next plan |
| :--- | :--- | :--- | :--- | :--- | :--- |
| current | S1c3 / S1c4 swerve phases and track runs (`AVOID3`) | | | | |
