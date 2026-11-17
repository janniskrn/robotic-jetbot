# Speaking notes, week 3

What to say on each slide of the **Week 3** page of `week3.html` (the second card on the roadmap), in the order
the slides come. Short sentences, meant to be read from a laptop while presenting. The slides carry the
evidence, this carries the story. For the Week 1 walkthrough behind the first card, `SPEAKING.md` still applies.

Numbers come from `DECISIONS.md` (SIT1 to SIT3) and the run logs. If a number here and a number on a slide
disagree, the slide is right and this file is out of date.

---

## The spine: say this once, at the start

Last week the robot could follow the lane and drive around a cup. When it lost the lane, it searched, and the
search often did not stop, even with the lane right in front of it.

The reason: the robot only knew one thing about the lane, where its center was in one row of the picture. It
did not know *where it was*: in the lane, on a line, beside the lane, or inside the oval.

So this week the robot estimates its own position relative to the lane, from the whole floor in the picture,
not from one line. That was your advice after the last demonstration, and it is the one idea of this week.

---

## Slide 1, where the project stands

Say: Same board as last week, with two changes. The circumvention is at 18 of 23 passes, adding the 10
November runs to the 14 of 18 from before. And there is a new amber row: lane-relative localization. It is
amber because it runs and is measured, but our own review gave 82 of 100 frames, and our pass mark is 90.

The grey rows are unchanged: we still need tape for an intersection and a parking box, and a second robot.

## Slide 2, what we did since the last demonstration

Say: Four entries, oldest first, failures included.

On 10 November we ran the full program from the notebook. Four of five swerves completed. But after losing the
lane in a curve, the robot searched for 25 to 40 seconds with the lane in view. The lane model was 0.90 and
0.94 sure, and our acceptance test still said no.

On 11 November we built the localization. On frames where the robot was clearly in the lane, it says "in
lane" 98 percent of the time.

The same day the team reviewed 100 frames by eye: 82 right. Most misses were faint far lines. We then tested
three camera resolutions and found that the problem was not the camera but the JPEG compression of our saved
pictures.

On 16 November we used the localization to decide when the recovery has found the lane. On 18 recorded
recoveries, it finds the lane in 13 instead of 6. That has not been driven yet.

## Slide 3, key capabilities implemented in git over the last week

Say: Ten commits since the week 2 deck: five in the code, the rest notes and the presentation. Three
capabilities.

First, the localization itself, in a new file, `situation.py`. Second, the recovery now uses it to decide that
it has found the lane. Third, tools to check it honestly: a live overlay in the camera notebook, and the
recovery saving its pictures without compression.

## Slide 4, changes against last week

Say: Two changes, one in the approach and one in the code. Each one: what it was, why it moved, what it is now.

**The approach.** Before, the lane state came from one image row and a test that needs both lines one lane
width apart. In a curve, that test fails. You told us to look at the broader picture. Now the robot traces both
lane borders over the whole floor, near and far, and decides which of six zones it is in.

**The code.** Before, the recovery accepted the lane only when that two-line test passed. Now it also accepts
it when the localization says "in lane" near the center. In the same replay that is 13 of 18 instead of 6.
This box is amber on purpose: it is tested on recordings, not yet on the track.

## Slide 5, situation.py, the localization

Say: One picture in, three answers out: which zone the robot is in, where the lane center is relative to its
nose, and which way the lane runs.

Walk down the notes:

- **Line 219.** We trace the tape near and far. Far tape looks pale, so it gets its own color threshold. Tape
  running across the picture is traced column by column; before, it was thrown away, and it is what the robot
  sees during most recovery steps.
- **Line 223.** Two traced lines become one lane. We take the nearest pair, because a far pair can match the
  lane width by chance: that is another part of the oval.
- **Line 224.** Tape under the robot's nose means "on a line". That is exactly the case where the old recovery
  turned away from a lane it was standing on.
- **Line 232.** The lane center, from minus 1 to plus 1. It tells the robot which side to go to, even from
  outside the lane.
- **Line 236.** The zone comes from where the nose lies between the two borders.
- **Line 181, below.** The gap between two lines is compared with the lane width we measured for each image row
  on 354 frames, and the lines must converge toward the horizon, as real lane borders do.

No learned model here: this is a measurement, like the cup distance last week. 24 milliseconds per picture on
the robot.

## Slide 6, find_lane.py, when the recovery stops

Say: This is where the localization changes behavior.

- **Line 84.** The lane model must first see a lane, at least 0.6. The model recognizes, the script measures.
- **Line 86.** The localization only runs when the robot stands still between search steps, so its 24
  milliseconds cost nothing.
- **Line 87.** "In lane" with the center within 0.7 of the nose. Further off, the robot was standing at an angle
  at the border, and we do not want to hand that to normal driving.
- **Line 166.** Old test or new test. We kept the old one: in the replay, one recovery was found only by it.
- **Line 172.** The answer must hold for three more pictures. One look alone was borderline.

## Slide 7, localization results

Say: Three of the robot's own pictures with what it understood drawn on them. Left: in the lane. Middle: on a
line. Right: outside the lane, and it knows the lane is to the left, because it found the faint far line.

Then the four numbers. 98 percent on frames that are clearly in the lane. 82 of 100 in our own review, below our
pass mark of 90. Three test spots showing that JPEG, not resolution, hides the far lines. And 13 of 18
recoveries in the replay.

The honest point: our review was done on compressed recordings, and the robot drives on uncompressed pictures.
So the real test is live, on the track, and that is the first step of the next plan.

## Slide 8, failures and causes

Say: Four rows. Two are new this week, two are carried over.

The first is the long search: the cause was the two-line test failing in curves, the fix is the localization,
and it is marked "not yet driven" because it is not.

The second is the missed far lines: the cause is JPEG, even at maximum quality. We now check on uncompressed
pictures, live.

The third is last week's recovery. One piece of good news: on 10 November the undo step, driving back along
the last second of wheel commands, found the lane twice in about 2 seconds. The search from open floor is
still unreliable.

The fourth, the swinging at the gentle curve, is still open and still our question to you.

## Slide 9, the next plan

Say: Five steps, each with its pass condition.

First, check the zones live: we place the robot by hand on the track, and it must be right 9 times of 10 in each
situation. Second, drive the new recovery: 8 of 10 lane losses recovered in under 10 seconds, without turning
around. Third, a short memory: the robot remembers where the lane was a moment ago from its wheel commands.
Fourth, a new state, REJOIN, that uses the zone and the memory to drive back to the center, replacing the
current recovery.

The last row is still the only one that blocks other tasks: tape for the intersection and the parking box.

---

## Questions we should expect

**"Why not a neural network for the zones?"** We will train one, and this script is how we get its labels. A
model needs thousands of labeled pictures; the script labels them, and the team corrects them. Same pattern as
the cup: the model recognizes, the script measures.

**"Why not a higher camera resolution?"** We tested 224, 448 and 616 pixels at three spots. Higher resolution
added little. The far lines were lost in the JPEG files, not in the camera.

**"Does the new recovery work?"** On recordings, 13 of 18 instead of 6. On the track, not yet: that is step two
of the plan. Say this plainly.

**"How does the robot know it is inside the oval?"** Only when it sees both borders, with the lane beyond the
near one. If it sees one line only, it cannot tell, and that is what the short memory is for.

**"Show me."** Open `05_camera_check.ipynb`, run the first cell, then "show what the robot understands", and
move the robot by hand: the zone is written on the live picture. Stop that camera before starting a drive.

---

## Before the demonstration

- Battery at rest at least 11.4 volts: `python3 notebooks/mini_av/battery.py`
- Only one program uses the camera: stop the camera in `05_camera_check.ipynb` before starting `04_drive.ipynb`
- `04_drive.ipynb`: mode **adaptive**, seconds 60 to 90, robot in the middle of the lane, counterclockwise
- One short test run before the professor watches: the new recovery acceptance has not been driven yet
- `scripts/stop_robot.sh` open in a terminal, and somebody with a hand near the robot
- Other robots off the track
