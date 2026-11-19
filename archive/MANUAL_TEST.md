# Manual pipeline test

Checks that the manual way works end to end: record with the gamepad, copy to the Mac over SSH,
label by hand, copy the labels back. Only a test: Claude does the real recording and labeling.
Takes about 20 minutes.

Everything below runs in the **Mac terminal** unless it says otherwise.
Robot address `192.168.0.174`, user `jetbot`, password `jetbot`. If the address changed, run `hostname -I` on the robot.

## 0. Once: shortcuts and tools

```bash
export JB=jetbot@192.168.0.174                  # robot login, used by all commands below
ssh-copy-id $JB                                  # optional: no password prompts from now on
git clone https://github.com/janniskrn/robotic-jetbot.git ~/robotic-jetbot   # our code
python3 -m venv ~/jetbot-venv                    # separate Python environment for the tools
source ~/jetbot-venv/bin/activate
pip install opencv-python numpy                  # image window and math for the labeling tool
mkdir -p ~/jetbot-data                           # where copied sessions go
```

`export JB=...` only lasts for this terminal window. In a new window, run it again, and
`source ~/jetbot-venv/bin/activate` too.

## 1. Update the code on the robot

```bash
ssh $JB "cd ~/jetbot && git pull"                # the robot must have the same tool versions as the Mac
```

The first `ssh` asks "Are you sure you want to continue connecting?": type `yes`.

## 1b. Battery

```bash
ssh $JB python3 jetbot/notebooks/mini_av/battery.py
```

Needs at least 11.4 V with the charger unplugged for 5 minutes (CLAUDE.md, section 9).

## 2. Record a short session with the gamepad

1. Put the robot on a straight, in the lane. Plug the gamepad into the Mac.
2. Open `http://192.168.0.174:8888` in the browser (password `jetbot`).
3. Open `jetbot/notebooks/mini_av/01_record_dataset.ipynb` and run the cells from top to bottom.
4. Press a gamepad button so the browser sees it. In the session fields, set **name** to `manual_test`
   and **tape** to `blue`.
5. Click **DISARMED** to arm, click **record**, drive about 30 seconds along the lane, then click **record** again.
6. Run the last cell (**Finish**). This frees the camera.

## 3. Find the session and label it automatically on the robot

```bash
ssh $JB 'ls ~/usb/images/datasets | grep manual_test'      # prints the folder name
export S=2026-09-21_10-15-00_manual_test                  # REPLACE with the exact folder name printed above
ssh $JB "cd ~/jetbot/notebooks/mini_av && python3 02_auto_label.py ~/usb/images/datasets/$S"
```

The last command writes `labels.csv` (automatic labels), so step 5 can compare against it.

## 4. Copy the session to the Mac

```bash
rsync -av $JB:usb/images/datasets/$S ~/jetbot-data/
ls ~/jetbot-data/$S | head                                 # frames, session.json, labels.csv
```

## 5. Label by hand

```bash
cd ~/robotic-jetbot && git pull                            # latest version of the tools
cd notebooks/mini_av
python3 02_manual_label.py ~/jetbot-data/$S --step 5       # every 5th frame
```

In the image window:

| Input | Meaning |
| :--- | :--- |
| mouse click on the green line | lane center there (sets "lane visible") |
| `n` | no lane visible |
| `1` / `2` / `3` | curve straight / gentle / sharp |
| `0` | no curve class |
| space | next frame |
| `b` | previous frame |
| `q` | save and quit |

Check once that the yellow circle appears exactly where you click (on Retina screens OpenCV windows
sometimes scale clicks; if it is off, report it). At the end it prints how well your labels agree with the automatic ones. Labels are saved in
`labels_manual.csv`; running the command again resumes where you stopped.

## 6. Copy the labels back to the robot

```bash
rsync -av ~/jetbot-data/$S/labels_manual.csv $JB:usb/images/datasets/$S/
ssh $JB "ls ~/usb/images/datasets/$S/labels_manual.csv"    # check it arrived
```

## 7. What to report back

- Did every step work? Copy any error message.
- The agreement numbers from step 5.

The test session can stay on the robot. Sessions with `test` in the name are never used for training.
