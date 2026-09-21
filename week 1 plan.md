Phase A: Setup (about 20 minutes)

A1. Light in the room, then camera check

You: put the robot on the track with normal lighting.
Me: take a photo and compare it with the "before" photo.
Check: colours look natural, no pink cast. If it still looks pink, I investigate before any data is recorded.

A2. Track facts

You: tell me tape colour, tape width, radius of the sharpest curve, and roughly the total length of the track.
Me: write them into DECISIONS.md and set the thresholds for straight, gentle and sharp from them.
Check: the numbers are in the decision log.

A3. Battery and safety

You: fully charge the battery, have the second one ready if you own one.
You: clear about half a metre of space around the track.
Check: robot drives freely, nothing to fall off or hit.
Phase B: First data (about 45 minutes)

B1. Test session

You: open notebooks/mini_av/01_record_dataset.ipynb, run all cells, fill in the fields, arm, record about 30 seconds of driving, stop.
Me: look at the saved frames and session.json.
Check: the images are sharp, the line is visible, the count matches, everything landed on the USB stick.

B2. Main recording
Record several short sessions instead of one long one, because we split train and test by session. Fill in the section field per session.

Session	What to drive	Roughly
1 and 2	Whole track, normal driving, one lap per direction	2 x 1 min
3	Straight sections only	30 s
4	Gentle curves only	30 s
5	Sharp curves only	30 s
6	Deliberately bad driving: cross the line, drive at an angle to it, approach it from the side, weave	1 min
7	Line at the edge of view and just out of view, set section to off_line	30 s
Sessions 6 and 7 matter most. Without them the model only knows perfect driving and can never recover.
Check: about 1500 to 2000 frames in total, several sessions, all metadata filled in.

B3. Transfer to the Mac

Me: copy the sessions over WiFi with rsync, and tell you the command so you can do it yourself later.
Check: the same number of files on both sides.
Phase C: First model (about 45 minutes)

C1. Labeling tool

Me: build 02_label_dataset for the Mac: image on screen, one click marks the point where the line crosses the lookahead circle, keys set "line visible" and the curve class.
Check: you label 10 images and the marks are drawn back correctly.

C2. Label the gold set

You: label about 300 images, mixed across all sessions. Takes roughly 20 to 30 minutes.
Check: every session is represented; the off-line images are labeled as "no line".

C3. Train the line model

Me: 03_train_line on the Mac, plus the training curve and the error on the held-out session.
Check: the model's predicted point lands on the tape in test images it never saw.

C4. Put the model on the robot

Me: copy the weights, load them on the robot, measure how many frames per second we get.
Check: the same image gives the same prediction on Mac and robot. If the frame rate is below about 20, I convert to TensorRT.
Phase D: Driving, Task 1 (about 2 hours, mostly tuning)

D1. Skeleton and baseline

Me: config.py, perception.py, control.py, logger.py, and 04_drive with a stop button.
You: first run at low speed, hand on the stop button.
Check: the robot follows the line at constant speed, and a log file is written. This is our baseline for the comparison table.

D2. Steering control

Me: smoothing, PD with real time steps, motor trim, steering rate limit.
You: drive straight, gentle and sharp sections; we tune two or three constants together.
Check: measurably less wobble on the straight than the baseline, no departures in the sharp curve.

D3. Curve class and speed

Me: train the curve classifier from the labels of C2, add the curvature-to-speed map and the acceleration limit.
You: one lap.
Check: visibly faster on straights, slower in sharp curves, no jerking. Table of average speed per section, baseline against ours.

Task 1 is done when the robot drives the whole track alone, faster on straights and slower in curves, and the table and graphs exist.

Phase E: Obstacles, Task 2 (about 2 hours)

E1. Obstacle data

You: place the obstacle on the line, record short sessions from several distances and angles, with obstacle set to on_line. Then record "free" sessions that include sharp curves and the track edges.
Check: roughly 300 frames per class, both classes recorded at several places on the track.

E2. Obstacle model

Me: train the classifier, report accuracy and the confusion matrix.
Check: no false alarms on the curve images in the test set.

E3. Stop only

Me: wire in detection with debounce and hysteresis; the robot only stops for now.
You: ten approaches at driving speed.
Check: stops every time at a sensible distance, no false stops during a lap.

E4. Passing maneuver

Me: leave the line to the fixed side, pass on a timer, then curve back until the camera finds the line again; a timeout stops the robot.
You: ten trials; we tune the two timing constants.
Check: it passes without touching the obstacle.

E5. Finding the line again

Me: recovery ends only when the line is visible and near the centre for several frames.
You: ten full trials, drive, avoid, recover, drive on.
Check: at least 8 of 10 without touching the robot; a failure ends in a clean stop, not a crash.

Task 2 is done when that sequence runs repeatedly without you steering.

Phase F: Demo preparation (about 1 hour)

F1. Measurement runs

You: three clean laps with logging on, one with an obstacle.
Me: graphs from the logs (speed against curvature, steering over time, the avoidance sequence) and the results tables.

F2. Documentation

Me: one page of flow diagram plus the experiment record, problem, hypothesis, change, test, result, for each of D2, D3 and E4.
Check: every number on a slide can be traced to a log file.

F3. Rehearsal

You: run the demo once end to end, with a fresh battery.
Check: it also works with the battery half empty. If the timed part drifts, we scale it by battery voltage.
Rules during all of this
One step at a time: I propose, you say go, I implement, we test, you approve, I commit and push.
Every tuning value is a named constant at the top of config.py, never buried in the code.
Images only on the USB stick, model weights on the SD card.
Every decision goes into DECISIONS.md.