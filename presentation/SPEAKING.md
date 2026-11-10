# Speaking notes, week 2

What to say on each slide of `week2.html`, in the order the slides come. Short sentences, meant to be read
from a laptop while presenting. Nothing here is on the slides; the slides carry the evidence, this carries
the story.

Numbers come from `DECISIONS.md` and the run logs. If a number here and a number on a slide disagree, the
slide is right and this file is out of date.

---

## The spine: say this once, early, and everything else hangs off it

The robot does the same four things, about twenty times a second.

1. **The camera gives one picture.** 224 by 224 pixels.
2. **Perception turns the picture into numbers.** Where the lane is, how sharp the curve is, whether a cup is
   there and how far away.
3. **Decision turns the numbers into one word.** The active operational state (seven in total):
   following the lane, slowing down, obstacle circumvention, centering recovery, line search recovery,
   stopped, or terminal halt.
4. **Control turns that word into two numbers.** The speed of the left wheel and the speed of the right wheel.

One file does each job, and a fifth file, `drive.py`, is the loop that calls them in that order and writes the
two numbers to the motors. **Eyes, brain, hands, and the loop around them.** That is the whole program.

Why we separated it that way: the brain never touches a motor, and the eyes never make a decision. We can
test the brain on recorded runs with no robot and no camera, which is how most of our bugs were found.

---

## Slide 1, where the project stands

Say: Week 1 was two tasks, lane following and the obstacle. Both run on the track. The state machine is
written and seven states run, but task 6 is formally week 3, so it stays amber. The grey rows are not
code problems: we need tape on the floor for an intersection and a parking box, and a second robot for
cruise control.

If asked why the swerve is green now: the last session was 14 of 18 back on the road.

## Slide 2, what we did since the last demonstration

Say: Four days, in order. On 3 November the swerve worked only on the straight it was tuned on. We found out
why, changed how the distance is measured, and taught the robot the distances by letting it measure them
itself. On 9 November it was 14 of 18.

The honest part: the first day is a failure and it stays on the slide.

## Slide 3, code architecture

Say: This is the whole program in one picture. Three layers, left to right, and the arrows only go one way.
A camera frame goes into perception, a dictionary of numbers goes into decision, one state goes into control,
two wheel speeds come out.

The box around them is `drive.py`, the loop. It is the only file that writes to the motors.

**Offer the proof.** `decision.py` and `control.py` do not import the robot library at all, so they cannot
reach a motor even by mistake. One grep shows it, and it takes ten seconds at the keyboard.

Underneath everything is `config.py`: 128 numbers, every tuning value in the program, none of them hidden in
the logic.

## Slide 4, one camera frame

Say: The same thing again, but in time. One frame takes about 30 milliseconds for all three models, and we
run about 21 frames a second.

The lane model runs on every frame, because steering needs a fresh position every step. The curve model and
the cup model take turns on alternate frames. We tried all three on every frame: it cost 12 milliseconds more
per step, and the steering got visibly worse.

## Slide 5, drive.py, the loop

Say: Here is the loop itself. Read it as five steps.

Line 106 takes the newest camera frame. Line 109 asks perception for the numbers. Line 116 asks decision for
the state. Line 143 asks control for two wheel speeds. Line 148 writes them to the motors.

Two things worth pointing at. Line 117: one state, searching for a lost lane, takes many seconds, so the loop
hands over to `find_lane.py` and gets told whether it worked. And the end of the file: four different failures
all land in the same `finally`, which stops the motors. A frozen camera, a flat battery, the stop button, or
time running out.

If asked about line 147, the lock: motor commands go over I2C, and a watchdog thread can stop the motors at
the same moment, so they take turns.

## Slide 6, perception.py, the eyes

Say: One picture goes in, about ten numbers come out, and nothing is decided here.

Three neural networks: one finds the lane and where its center is, one classifies the curve, one finds the
cup. Then two color masks measure geometry: the angle of the tape ahead, and the exact size and position of
every red band.

**Why both.** Models are good at recognizing and bad at measuring. Our cup model's distance was wrong by up
to 28 image rows when people stood behind the cup, because it had learned the background too. The color mask
was right. So now the model says *a cup is there*, and the mask says *how far*.

The small block at the bottom: the curve model has five classes, left and right included, and this line
splits them into two separate signals. How sharp the curve is sets the speed. Which way it bends sets the
steering. If the model is not sure of the direction, no steering is added.

## Slide 7, the state machine

Say: Seven states. Across the top is normal driving: following the lane, driving around a cup, and getting
back on the lane afterwards. Below are the ways out of trouble.

The one to point at is `LINE_RECOVERY`, which is new. Before it, a lost lane ended the run and somebody had to
carry the robot back. Now the robot searches: it undoes its last second of driving, sweeps about 100 degrees
to each side, and if that fails it does a full turn looking for tape.

The four boxes at the bottom are the phases of driving around a cup. Every phase ends on something the camera
sees, never on a timer, and every phase has a time limit. We learned that the hard way: our first version
timed the turns, and a turn we had calculated as 45 degrees came out as about 130.

## Slide 8, decision.py, transitions

Say: This is how a state actually changes.

The four phases are a tuple on line 32, and line 232 walks through it by index, so adding a phase means
adding a name in one place.

Every transition in the program goes through `enter()` on line 155. It writes down the new state and the time
it started, and that timestamp is what every time limit measures from.

Lines 202 to 226 are the marks that end each phase. The turn out ends when the cup has left the picture
sideways. The curve ends when the lane tape has passed under the robot. The turn back ends when the lane is
in front of the robot and the robot is pointing along it.

The last line is the important one. If a mark never comes, the robot does not drive on blind: it goes to the
lane search.

## Slide 9, decision.py, the priority order

Say: Same file, the other half, and this is the part the professor asked about.

Every frame, the same questions in the same order. Is the run over? Are we in the middle of a maneuver? Are
we recovering? Is there a cup close enough? Is the curve sharp? Has the lane been gone too long?

**Priority is not a comment in our code. It is the order of the questions, and the first yes wins.** That is
why a cup can never be overruled by a curve: the cup is asked first.

Two details if asked. The cup needs four frames in a row before we believe it, because the cup model only
runs on every second frame. And slowing down enters at one threshold and leaves at a lower one, so it cannot
flicker on and off at the boundary.

## Slide 10, control.py, the steering

Say: This is our own control layer, which is what task 1 asked for. The stock example multiplies the error by
a constant. Ours has eight pieces, and every one of them came from a run that failed.

Walk four of them: P on the raw position, D on a smoothed copy because differentiating the raw value turned
every pixel of noise into a jerk, gains that shrink as the robot speeds up, and a feedforward that holds a
steady turn through a curve.

The feedforward is the interesting one. In the sharp curve the lane position reads near zero and flips sign,
so steering by position alone fails there. The direction now comes from the curve model instead, and that is
what fixed the curve that kept throwing us off the track.

## Slide 11, control.py, what each state commands

Say: The brain picks a state; this file says what the wheels do in it.

Four functions. Following the lane uses the steering we just saw. The swerve has one branch per phase. The
stop is a short reverse pulse, because at zero the motor board lets the wheels coast and the robot rolls on.
The recovery creeps forward and turns gently.

**Point at `target_speed`.** The speed is the smaller of two limits: the curve limit and the steering limit.
That is already the shape task 7 asks for. Adding a following distance means adding a third argument to the
same minimum, and nothing else in the program changes.

## Slide 12, config.py and safety.py

Say: Two rules we hold ourselves to.

First, no magic numbers. All 128 tuning values are in one file, and each one carries the run that set it, in
the comment. That is how we can defend a value or roll it back.

Second, four guards, in `safety.py`, in every program that drives. Battery before the start and under load. A
new camera frame within half a second. A motor update within a quarter second. And motors stopped in
`finally`.

**Tell the story.** On 20 September we ran a training job while the robot drove. Memory ran out, the camera
froze, and the camera object kept returning the same old picture, so the robot drove blind into a chair. The
watchdog compares frame objects now, and it caught a real freeze 46 seconds into a later run.

## Slide 13, the learning pipeline

Say: How a model is made here, and how it earns the right to drive.

The robot records itself driving on a color mask, so nobody steers for the dataset. The masks write the
labels. We train one ResNet18 per task, a pretrained network with a new last layer. Then TensorRT, which took
one lane pass from 41 to 10.6 milliseconds; without it, three models do not fit in one 30 millisecond step.

The line on the slide is the honest part: **whole recording sessions are held out, never single frames.**
Neighbouring frames look almost the same, so a random split would report a model that is better than it is.

If asked about accuracy: the labels come from the color masks, so the percentages are agreement with the
mask, not ground truth. We say that on the next slide too.

## Slide 14, the three models

Say: What they get right, and where each one is weak. The weak line is why the decision layer never takes a
model number on its own.

The lane model finds the lane in 99.6 percent of frames, but only 45 percent when a cup is 20 centimetres
away, because the cup hides it. That is why a cup straight ahead counts as being in the way even with no lane
in sight.

The curve model is 88.6 percent over five classes, and it never confused left with right in the validation
set. Every error is curve versus straight, which costs some speed but never steers the wrong way.

The cup model finds the cup in 98.1 percent of frames up to half a metre (96 to 99 percent across individual
recording sets), with 0.4 percent false alarms. Its distance we do not use at all.

## Slide 15, task 1 results

Say: Six runs of 60 seconds. The stock-style controller lost the lane after about 20 seconds in both
directions. Ours drove the full minute.

Be precise about what the curve model bought: it did not make the steering smoother. It got us through the
sharp curve. Tracking error standard deviation (lateral oscillation amplitude) went from 0.150 down to
0.087, and the adaptive run is 0.099 because it drives faster on the straights.

These runs are from September and should be repeated with today's code. That is on the next-plan slide.

## Slide 16, stopping at a cup

Say: The distance comes from the size of the red band, not from where it sits in the picture. Centimetres
equal 405 divided by the square root of the band's area in pixels.

**The robot learned that constant itself.** It started touching a cup and backed away in small pulses, saving
a picture at every stop. 139 stops in 5 places. We never held a ruler.

Three distances: slow down at 65 centimetres, stop at 40, and only drive on when nothing is closer than 60.
Then the code: the model has to see a cup, the band has to be in the lane or straight ahead, and it has to be
close enough. Three conditions, all three required.

Result: three runs, stops at 35 to 40 centimetres. Before the slow approach and the brake pulse, a stop
commanded at 27 centimetres left the robot at 10.

## Slide 17, driving around the cup

Say: The path. Turn until the cup leaves the picture, drive straight while the cup is beside the robot, then
curve, then turn back onto the lane.

**Why it changed.** The old version ended its turns on the angle of the lane tape, and that only works where
the tape is straight. Every mark now refers to the cup, which is there in a curve too.

Result: 14 of 18 on 9 November, after 11 of 12 the day before. Three of the four failures hit the curve's time
limit without finding their mark, and we have not yet watched whether a cup was touched. Both are on the next
plan.

## Slide 18, failures and causes

Say: Four failures, with the cause and what we changed. This is the slide to go slowly on, because the
professor asks about the failures.

For each one: what we saw, why it happened, what we changed, and whether it held. Two are fixed and held, one
is fixed and still rough, and one we do not understand yet.

**The open one is our question for today.** At speed 0.39, entering the gentle curve, the robot starts
swinging and the swing grows: positions went minus 0.11, plus 0.24, minus 0.40, plus 0.42 in one run. We
ruled out the third model, the loop timing, and camera lag, which we measured at 115 to 160 milliseconds and
constant. The fallback is a lower speed limit in that curve, but we would rather know why.

## Slide 19, the next plan

Say: Five steps, each with the condition that decides whether it worked.

The first two come straight from the failures on the previous slide: make the lane search work after a failed
swerve, and give the curve a mark it can always find.

The last row is the only one that blocks other tasks, and it is not a code problem. We need tape on the floor
for an intersection and a parking box. Signs, intersection and parking all reuse the pipeline that already
works.

---

## Questions we should expect

**"Show me the code."** Press `d`. The document view carries the whole deck plus the complete source of the
seven driving modules, with the same line numbers the slides cite.

**"Did you write this yourselves?"** The stock NVIDIA notebooks are used as building blocks only, untouched.
Steering, speed, avoidance, recovery, the state machine and the parking logic are ours: 3301 lines in 26 files.

**"Why is this number 0.15?"** Every constant in `config.py` carries the run that set it in its comment. Read
the comment out loud; that is what it is for.

**"Why not more machine learning?"** We use three networks and a fourth pipeline for signs is next. Where we
do not use a model is measurement, and we have the failure that forced that choice: the model's distance was
wrong by up to 28 rows with people behind the cup.

**"What happens if the camera fails during the demo?"** The robot stops within half a second. We can show the
guard in `safety.py`.

---

## Before the demonstration

- Battery at rest at least 11.4 volts: `python3 notebooks/mini_av/battery.py`
- `scripts/stop_robot.sh` open in a terminal, and somebody with a hand near the robot
- Cups on the track only if the cup is part of what we are showing
- Other robots off the track: a run once ended by driving into a second JetBot
- The filmed run from the last session open in a tab, as the fallback if the live run fails
