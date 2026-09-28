"""Offline replay: runs the trained models over the frames of recorded sessions and compares them with
the color mask, per section (straight / gentle / sharp / no lane) and per driving direction (DATA2).
No motors, no training: judge a model change here before driving.

    python3 replay.py <session name part> [...] [--per-frame]     # in the container

Main number: in curve frames, does the direction signal point to the inside of the oval? Its ground truth
needs no hand labels: counterclockwise every curve turns left, clockwise every curve turns right. The
driving direction is measured from the mask (sign of the bend over all curve frames), not the session name.
Direction signals: the sign of lane_x (the old feedforward) and, for a 5-class curve model, its left/right.
"""

import argparse
import glob
import importlib
import os

import cv2
import torch

from perception import load
from vision import preprocess

DATASET_ROOT = '/workspace/usb/images/datasets'
MIN_LANE_X = 0.05     # |lane_x| below which lane_x gives no direction (the old FEEDFORWARD_MIN_X)
MIN_CURVE_DIR = 0.2   # |p_right - p_left| below which the curve model gives no direction
SECTIONS = ['straight', 'gentle', 'sharp', 'no lane']

auto_label = importlib.import_module('02_auto_label')


@torch.no_grad()
def model_outputs(lane_model, curve_model, bgr):
    """Raw per-frame outputs (no smoothing): lane_visible, lane_x, curve magnitude class, curve_dir"""
    image = preprocess(bgr).unsqueeze(0).cuda().half()
    lane = lane_model(image)[0].float()
    probs = torch.softmax(curve_model(image)[0].float(), 0).tolist()
    if len(probs) == 5:  # straight, gentle_left, sharp_left, gentle_right, sharp_right
        magnitude = [probs[0], probs[1] + probs[3], probs[2] + probs[4]]
        curve_dir = probs[3] + probs[4] - probs[1] - probs[2]
    else:  # old 3-class model: straight, gentle, sharp, no direction
        magnitude, curve_dir = probs, None
    return {'lane_visible': torch.sigmoid(lane[0]).item(), 'lane_x': lane[1].item(),
            'curve_class': ['straight', 'gentle', 'sharp'][magnitude.index(max(magnitude))], 'curve_dir': curve_dir}


def direction_verdict(value, minimum, inside):
    """'right' if the signal points to the inside of the oval, 'wrong' if outward, 'none' if too small"""
    if value is None or abs(value) < minimum:
        return 'none'
    return 'right' if (value > 0) == (inside > 0) else 'wrong'


def replay_session(session_dir, lane_model, curve_model, per_frame):
    """Returns (inside, list of per-frame result dicts); inside is -1 for ccw (left curves), +1 for cw"""
    labels = auto_label.compute_labels(session_dir, curves_trusted=True)
    bend = sum(float(r['curve_value']) for r in labels if r['curve_class'] in ('gentle', 'sharp'))
    inside = -1 if bend < 0 else 1
    results = []
    for label in labels:
        out = model_outputs(lane_model, curve_model, cv2.imread(os.path.join(session_dir, label['frame'])))
        mask_visible = label['lane_visible'] == 1
        result = {
            'frame': label['frame'],
            'section': label['curve_class'] if mask_visible and label['curve_class'] else 'no lane' if not mask_visible else '',
            'visible_agree': (out['lane_visible'] >= 0.5) == mask_visible,
            'x_error': abs(out['lane_x'] - label['lane_x']) if mask_visible else None,
            'class_right': out['curve_class'] == label['curve_class'] if label['curve_class'] else None,
            'dir_lane_x': direction_verdict(out['lane_x'], MIN_LANE_X, inside),
            'dir_curve': direction_verdict(out['curve_dir'], MIN_CURVE_DIR, inside) if out['curve_dir'] is not None else '-',
        }
        results.append(result)
        if per_frame:
            print('%s %-8s mask x %6s  model vis %.2f x %+.3f %-8s dir %s  | lane_x dir %-5s curve dir %s' % (
                label['frame'][6:11], result['section'], label['lane_x'], out['lane_visible'], out['lane_x'],
                out['curve_class'], '-' if out['curve_dir'] is None else '%+.2f' % out['curve_dir'],
                result['dir_lane_x'], result['dir_curve']))
    return inside, results


def percent(part, whole):
    return '%5.1f' % (100.0 * part / whole) if whole else '    -'


def print_table(title, results):
    """One row per section: frames, agreement with the mask, and the direction verdicts in curve sections"""
    print(title)
    print('  %-9s %6s %8s %8s %8s | %-23s | %-23s' % ('section', 'frames', 'vis ok %', 'x error', 'class %',
                                                      'lane_x dir right/wrong %', 'curve dir right/wrong %'))
    for section in SECTIONS:
        rows = [r for r in results if r['section'] == section]
        if not rows:
            continue
        errors = [r['x_error'] for r in rows if r['x_error'] is not None]
        classes = [r['class_right'] for r in rows if r['class_right'] is not None]
        dirs = ''
        for key in ('dir_lane_x', 'dir_curve'):
            if section == 'straight' or rows[0][key] == '-':
                dirs += ' | %-23s' % '-'
            else:
                dirs += ' | %-23s' % ('%s / %s' % (percent(sum(r[key] == 'right' for r in rows), len(rows)),
                                                   percent(sum(r[key] == 'wrong' for r in rows), len(rows))))
        print('  %-9s %6d %8s %8s %8s%s' % (
            section, len(rows), percent(sum(r['visible_agree'] for r in rows), len(rows)),
            '%.3f' % (sum(errors) / len(errors)) if errors else '-', percent(sum(classes), len(classes)), dirs))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('sessions', nargs='+', help='parts of session names')
    parser.add_argument('--per-frame', action='store_true', help='print every frame')
    parser.add_argument('--root', default=DATASET_ROOT)
    args = parser.parse_args()
    lane_model, curve_model = load('lane'), load('curve')
    by_direction = {'ccw': [], 'cw': []}
    for part in args.sessions:
        for session_dir in sorted(d for d in glob.glob(os.path.join(args.root, '*' + part + '*')) if os.path.isdir(d)):
            if not glob.glob(os.path.join(session_dir, 'frame_*.jpg')):
                continue  # a run that stopped before its first frame
            inside, results = replay_session(session_dir, lane_model, curve_model, args.per_frame)
            direction = 'ccw' if inside < 0 else 'cw'
            by_direction[direction] += results
            print_table('%s (measured %s)' % (os.path.basename(session_dir), direction), results)
    for direction, results in by_direction.items():
        if results:
            print_table('ALL %s' % direction, results)


if __name__ == '__main__':
    main()
