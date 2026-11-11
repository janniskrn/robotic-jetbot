# Brief: what we did and what came out of it

The answer to give when the professor asks what the team has done. First person, out loud, in the order
below. The slides carry the evidence; this is the argument.

Numbers come from `DECISIONS.md`, `HANDOVER.md` and the run logs. If a number here disagrees with a slide,
the slide is right and this file is behind.

---

## 1. The 30-second answer

We finished week 1, both tasks. The robot follows the lane with our own control layer, and it handles a cup
in its way: it sees the cup, measures how far it is, drives around it, and gets back on the lane. Since the
last demonstration we rebuilt two things that were not reliable, and the maneuver went from 5 of 9 to 14 of
18 on the track. The state machine for task 6 already runs with seven states, ahead of its week.

What is not done is not code: we need tape on the floor for an intersection and a parking box, and a second
robot for cruise control.

## 2. What we built

Three layers, and each one has one job. **`perception.py` are the eyes:** three ResNet18 networks and two
color masks turn a camera frame into about ten numbers. **`decision.py` is the brain:** a state machine with
seven states that answers with one state per frame. **`control.py` are the hands:** it turns that state into
two wheel speeds. **`drive.py` is the loop** around them, and the only file that writes to the motors.

The separation is real, not a diagram: the brain and the hands do not import the robot library at all, so
they cannot reach a motor. That is why we can replay a recorded run through the decision layer with no robot
and no camera, which is how most of our bugs were found.

3301 lines in 26 Python files, all written by us. The stock NVIDIA notebooks are used as building blocks only.

## 3. Results

**Task 1, adaptive lane following.** Six runs of 60 seconds. The stock-style controller lost the lane after
about 20 seconds in both directions. Ours drove the full minute in both. Wobble went from 0.150 and 0.126
down to 0.087. Speed is not constant: 0.40 on the straight, 0.31 in a sharp curve, chosen by the curve model.

**Task 2, stopping at a cup.** Three runs, the robot stops at 35 to 40 centimetres. The distance comes from
the size of the red band in the image, and **the robot learned that itself**: it stood touching a cup, backed
away in small pulses, and saved a picture at every stop. 139 stops in 5 places. We never held a ruler.

**Task 2, driving around the cup.** 14 of 18 maneuvers came back onto the road in the last session, after
11 of 12 the session before. Each phase ends on something the camera sees, never on a timer.

**The models.** The lane model finds the lane in 99.6 percent of frames. The curve model is 88.6 percent over
five classes and never confused left with right in validation. The cup model finds the cup in 96 to 99
percent of frames up to half a metre, with 0.4 percent false alarms.

**Task 6, early.** Seven states run in one program, with an explicit priority order.

## 4. What failed, and what we learned

This is the part worth the most, so say it without softening.

**The model's distance was wrong, and we trusted it.** Our obstacle model reported how far the cup was. With
people standing behind the cup at the end of the straight, it was wrong by up to 28 image rows, and the robot
started the maneuver while the cup was still half a metre away. Four maneuvers failed that way. The cause is
that the model was trained on labels from a color mask, so it learned the background too.

What we changed: **the model says a cup is there, the mask measures how far.** Recognition is learned,
geometry is measured. That principle now holds everywhere in the program.

**The maneuver only worked where we tuned it.** Its marks were the angle of the lane tape, which is straight
only on one straight section. Away from it, the mark never came.

What we changed: **every mark now refers to the cup**, not to the lane. The turn ends when the cup has left
the picture. The cup is there in a curve too.

**Still open, and this is our question.** At speed 0.39, entering the gentle curve, the robot starts swinging
and the swing grows: the lane position went minus 0.11, plus 0.24, minus 0.40, plus 0.42 in one run. We ruled
out the third model, the loop timing and camera lag, which we measured at 115 to 160 milliseconds and
constant. All eight of our lane losses happened in curves, about 15 centimetres after the last good reading.
Our fallback is a lower speed limit in that curve, but we would rather know the cause.

## 5. The two changes since last week

**In the approach:** the cup's distance moved from the model's guess to the band's measured size, and the
robot measured the scale itself instead of us measuring with a ruler.

**In the code:** the marks that end each phase of the maneuver moved from the lane tape to the cup
(`decision.py`, `update_avoidance`). The same change also gave the curve a mark that exists in a curve: the
moment the lane's border passes under the robot.

**One more worth naming:** a lost lane used to end the run and somebody carried the robot back. Now
`LINE_RECOVERY` searches in three stages, undo, sweep and search. It is honest to say this one is not
finished: from the start of a run it found the lane 3 times out of 3, but after a failed maneuver 0 of 4.

## 6. What is next

1. Make the search work after a failed maneuver. It usually stops right next to the lane and then turns away
   from it; a short nudge forward and a second look should fix that.
2. Cups that enter the lane late, just after a curve: they trigger at 21 to 25 centimetres instead of 40.
3. Film the maneuver from the side, so we can say whether a cup was touched. We have not observed that yet.
4. Find the swing at the gentle curve entry, or cap the speed there.
5. The team tapes an intersection and a parking box, which unblocks tasks 3, 4 and 5.

---

## If he asks

**"Show me the code."** Press `d` on the deck: the document view has the full source of the seven driving
modules, with the same line numbers the slides cite.

**"How do you know the layers are separated?"** One grep: `decision.py` and `control.py` do not import the
robot library.

**"Why is this constant 0.15?"** Every one of the 128 tuning values is in `config.py` with the run that set
it written in the comment next to it.

**"Why not use the model for distance too?"** Because we measured that it was wrong by 28 rows when the
background changed. Models recognize, scripts measure.

**"How much machine learning is in it?"** Three networks today, trained on data the robot recorded of itself.
Whole recording sessions are held out of training, never single frames, because neighbouring frames look
almost the same and a random split would flatter the model.

**"What if the camera fails during the demo?"** The robot stops within half a second. The watchdog compares
frame objects, because the camera can keep returning the same old picture after it dies. It caught a real
freeze 46 seconds into one run.
