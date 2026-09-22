"""Computes the labels for recorded dataset sessions with the color mask (D10 stage 3).

For every frame of a session it writes labels.csv:
    frame          image file name
    tape_visible   1 if blue tape is visible on the floor at all
    lines_seen     lane lines crossing the lookahead row (0, 1 or 2)
    lane_visible   1 if the lane is seen properly: both lines leaning the right way, or one line
                   shortly after such a frame (sharp curve); 0 otherwise (for example turned sideways)
    lane_x         lane center at the lookahead row, -1 (left edge) .. 1 (right edge); empty if lane_visible is 0
    curve_value    bend of the lane center path over three rows ahead (signed, 0 = straight); empty if not measurable
    curve_class    straight / gentle / sharp from curve_value; empty if curve_value is empty
                   Curve labels only come from sessions driven on the lane center: in weave and spin
                   sessions the robot is at an angle, and lens distortion then fakes a bend.
    label_source   color_mask
    reviewed       0 until a person has checked the frame

It also draws review sheets (labels drawn on the frames) into usb/images/review/<session>/.

Run from this folder, on the robot or on the workstation:
    python3 02_auto_label.py /home/jetbot/usb/images/datasets/<session> [more sessions...]
"""

import csv
import glob
import json
import os
import sys

import cv2
import numpy as np

from lane_mask import LOOKAHEAD_ROW, LaneTracker, blue_mask, is_left_line, line_centers

MIN_TAPE_PIXELS = 150   # tape pixels on the floor (224x224 image) that count as "tape visible"
# Rows (fraction of image height) where the lane center is measured for the bend, equally spaced,
# with the lane width in pixels measured there on a straight.
CURVE_ROWS = [(0.55, 123), (0.675, 172), (0.80, 208)]
GENTLE_CURVE = 0.02     # |curve_value| from here on is a gentle curve (from 3 labeled laps, tune_b)
SHARP_CURVE = 0.045     # |curve_value| from here on is a sharp curve (couch curve: 0.05-0.10)
LANE_WIDTH_RANGE = (100, 215)  # pixels two lines at the lookahead row may be apart to be this lane (162 on a straight)
MAX_SINGLE_LINE_RUN = 4  # frames (1 s at 4 Hz) a single line is trusted after a frame with both lines
MAX_SINGLE_LINE_JUMP = 40  # pixels the lane center may move between frames when only one line is seen
SHEET_COLUMNS = 6
SHEET_ROWS = 5
REVIEW_ROOT = '/home/jetbot/usb/images/review'


def curve_value(centers, width):
    """Bend of the lane center path: second difference of the centers at far, middle and near row.

    A straight lane gives about 0 even when the robot is off-center or at an angle, because then the
    center path is a straight (tilted) line. Divided by the image width; the sign says left or right.
    """
    if None in centers:
        return None
    far, middle, near = centers
    return (far - 2.0 * middle + near) / width


def both_lines_proper(mask, lines):
    """True if exactly two lines are seen, about one lane width apart, and at least one leans the right way.

    In curves both lines lean the same way, so one correct lean is enough; the lean is unknown (None)
    when a line leaves the image in the closer row, which also counts as fine.
    """
    if len(lines) != 2 or not LANE_WIDTH_RANGE[0] <= lines[1] - lines[0] <= LANE_WIDTH_RANGE[1]:
        return False
    return is_left_line(mask, lines[0]) is not False or is_left_line(mask, lines[1]) is not True


def curve_class(value):
    if value is None:
        return ''
    if abs(value) >= SHARP_CURVE:
        return 'sharp'
    return 'gentle' if abs(value) >= GENTLE_CURVE else 'straight'


def centered_driving(session_dir):
    """True if the session was driven on the lane center (no weaving, no turns in place while driving)"""
    with open(os.path.join(session_dir, 'session.json')) as f:
        session = json.load(f)
    if 'curves_trusted' in session:  # driving runs: False by default, set True by hand after checking the log
        return bool(session['curves_trusted'])
    return not session.get('weave') and not session.get('spin_every')


def turn_around_frames(session_dir):
    """Names of the frames saved while the robot turned around at the start (no lane center in auto_labels.csv)"""
    path = os.path.join(session_dir, 'auto_labels.csv')
    with open(os.path.join(session_dir, 'session.json')) as f:
        if not json.load(f).get('turn_around') or not os.path.exists(path):
            return set()
    names = set()
    with open(path) as f:
        for row in csv.DictReader(f):
            if row['lane_center_x'] != '':
                break
            names.add(row['frame'])
    return names


def label_session(session_dir):
    """Writes labels.csv for one session and returns its rows"""
    frames = sorted(glob.glob(os.path.join(session_dir, 'frame_*.jpg')))
    curves_trusted = centered_driving(session_dir)
    turning = turn_around_frames(session_dir)
    width = cv2.imread(frames[0]).shape[1]
    tracker = LaneTracker(width)
    curve_trackers = [LaneTracker(width, row, lane_width) for row, lane_width in CURVE_ROWS]
    rows = []
    single_line_run = MAX_SINGLE_LINE_RUN  # no trusted frame yet
    last_center = None
    for path in frames:
        image = cv2.imread(path)
        mask = blue_mask(image)
        lines = line_centers(mask)
        center = tracker.update(mask)
        bend = curve_value([t.update(mask) for t in curve_trackers], width)
        if both_lines_proper(mask, lines):
            single_line_run = 0
        elif (len(lines) == 1 and single_line_run < MAX_SINGLE_LINE_RUN and center is not None
              and abs(center - last_center) <= MAX_SINGLE_LINE_JUMP):
            single_line_run += 1
        else:
            single_line_run = MAX_SINGLE_LINE_RUN
        visible = center is not None and single_line_run < MAX_SINGLE_LINE_RUN
        if not visible or not curves_trusted or os.path.basename(path) in turning:
            bend = None
        if not visible:
            center = None
        last_center = center
        rows.append({
            'frame': os.path.basename(path),
            'tape_visible': int(np.count_nonzero(mask) >= MIN_TAPE_PIXELS),
            'lines_seen': len(lines),
            'lane_visible': int(visible),
            'lane_x': '' if center is None else round(2.0 * center / width - 1.0, 4),
            'curve_value': '' if bend is None else round(bend, 4),
            'curve_class': curve_class(bend),
            'label_source': 'color_mask',
            'reviewed': 0,
        })
    with open(os.path.join(session_dir, 'labels.csv'), 'w') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def draw(image, row):
    """Draws the labels onto a copy of the frame"""
    out = image.copy()
    h, w = out.shape[:2]
    out[blue_mask(image) > 0] = (0, 0, 255)
    y = int(LOOKAHEAD_ROW * h)
    cv2.line(out, (0, y), (w - 1, y), (0, 255, 0), 1)
    if row['lane_x'] != '':
        x = int((row['lane_x'] + 1.0) / 2.0 * w)
        cv2.circle(out, (x, y), 6, (0, 255, 255), 2)
    text = '%s L%d %s' % (row['frame'][6:11], row['lane_visible'], row['curve_class'] or '-')
    cv2.putText(out, text, (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 3)
    cv2.putText(out, text, (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    return out


def write_review_sheets(session_dir, rows):
    """Saves every frame with its labels, 30 per sheet, for the visual check"""
    out_dir = os.path.join(REVIEW_ROOT, os.path.basename(session_dir.rstrip('/')))
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    per_sheet = SHEET_COLUMNS * SHEET_ROWS
    for start in range(0, len(rows), per_sheet):
        tiles = [draw(cv2.imread(os.path.join(session_dir, r['frame'])), r) for r in rows[start:start + per_sheet]]
        tiles += [np.zeros_like(tiles[0])] * (per_sheet - len(tiles))
        grid = [np.hstack(tiles[i:i + SHEET_COLUMNS]) for i in range(0, per_sheet, SHEET_COLUMNS)]
        cv2.imwrite(os.path.join(out_dir, 'sheet_%03d.jpg' % (start // per_sheet)), np.vstack(grid))


if __name__ == '__main__':
    for session in sys.argv[1:]:
        labeled = label_session(session)
        write_review_sheets(session, labeled)
        classes = [r['curve_class'] for r in labeled]
        print('%s: %d frames, tape visible %d, lane visible %d, straight %d, gentle %d, sharp %d' % (
            os.path.basename(session.rstrip('/')), len(labeled), sum(r['tape_visible'] for r in labeled),
            sum(r['lane_visible'] for r in labeled), classes.count('straight'), classes.count('gentle'),
            classes.count('sharp')))
