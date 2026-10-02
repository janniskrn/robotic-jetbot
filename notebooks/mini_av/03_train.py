"""Trains one model from the labeled dataset sessions (D2: one model per task).

    python3 03_train.py --task lane  --val <session name part> [--val ...]
    python3 03_train.py --task curve --val <session name part>
    python3 03_train.py --task obstacle --val <session name part>

lane:  outputs lane_visible (yes/no) and lane_x; lane_x only counts on frames where the lane is visible.
curve: straight / gentle / sharp, and left or right for a curve (vision.CURVE_MODEL_CLASSES); only frames
       that have a curve class. A mirrored image swaps left and right.
obstacle: outputs cup_visible (yes/no), cup_row and cup_x; row and x only count on frames with a cup (OBST2).
       Frames of the cup sessions plus every OBSTACLE_OTHER_EVERY-th frame of the other sessions (no cups there).

Whole sessions are held out for validation (--val), never single frames: neighboring frames look
almost the same, so a random split would make the result look better than it is.
Sessions with "test" in the name are never used. Runs on the robot (CUDA), a Mac (MPS) or a CPU.
Saves the best model to models/<task>.pth and its metrics to models/<task>.json.
"""

import argparse
import csv
import glob
import json
import os
import random
import time

import cv2
import numpy as np
import torch
import torch.nn.functional as F

from vision import CURVE_MODEL_CLASSES, build_model, curve_model_class, preprocess

DATASET_ROOT = '/workspace/usb/images/datasets'  # inside the Jupyter container
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')  # SD card, *.pth is not in git

EPOCHS = 15
BATCH_SIZE = 16
LEARNING_RATE = 1e-4   # small: the pretrained backbone only needs fine-tuning
CLASS_WEIGHTS = None   # curve task: set in main() to the inverse class frequency, so sharp curves count as much
CLASSES = len(CURVE_MODEL_CLASSES)
MIRRORED = {'straight': 'straight', 'gentle_left': 'gentle_right', 'sharp_left': 'sharp_right',
            'gentle_right': 'gentle_left', 'sharp_right': 'sharp_left'}  # a mirrored curve bends the other way
OBSTACLE_OTHER_EVERY = 4  # obstacle task: share of frames from sessions without cups (about 6000, all "no cup")
BRIGHTNESS = 0.25      # random brightness change of up to +-25 %, for changing daylight
CONTRAST = 0.25        # random contrast change of up to +-25 %


def device():
    if torch.cuda.is_available():
        return torch.device('cuda')
    if getattr(torch.backends, 'mps', None) is not None and torch.backends.mps.is_available():
        return torch.device('mps')
    return torch.device('cpu')


def load_rows(root, task):
    """(image path, session name, label row) for every usable frame, by session"""
    rows = []
    for labels_path in sorted(glob.glob(os.path.join(root, '*', 'labels.csv'))):
        session_dir = os.path.dirname(labels_path)
        session = os.path.basename(session_dir)
        if 'test' in session:
            continue
        with open(labels_path) as f:
            for i, row in enumerate(csv.DictReader(f)):
                if task == 'curve' and not row['curve_class']:
                    continue
                if task == 'obstacle' and '_cups_' not in session and i % OBSTACLE_OTHER_EVERY:
                    continue
                rows.append((os.path.join(session_dir, row['frame']), session, row))
    return rows


def target(task, row, flipped):
    """Label as a float vector: lane = [visible, x], obstacle = [visible, row, x], curve = [class index]"""
    if task == 'obstacle':
        visible = float(row['cup_visible'])
        cup_row = float(row['cup_row']) if visible else 0.0
        x = float(row['cup_x']) if visible else 0.0
        return [visible, cup_row, -x if flipped else x]  # mirroring moves the cup to the other side, not up or down
    if task == 'lane':
        visible = float(row['lane_visible'])
        x = float(row['lane_x']) if row['lane_x'] != '' else 0.0
        return [visible, -x if flipped else x]  # a mirrored image mirrors the lane center
    name = curve_model_class(row['curve_class'], float(row['curve_value']))
    if flipped:
        name = MIRRORED[name]
    return [float(CURVE_MODEL_CLASSES.index(name))]


def augment(bgr):
    """Random mirror, brightness and contrast. Hue stays untouched: the blue tape color matters."""
    flipped = random.random() < 0.5
    if flipped:
        bgr = bgr[:, ::-1]
    gain = 1.0 + random.uniform(-CONTRAST, CONTRAST)
    shift = 255.0 * random.uniform(-BRIGHTNESS, BRIGHTNESS) / 2.0
    bgr = np.clip((bgr.astype(np.float32) - 128.0) * gain + 128.0 + shift, 0, 255).astype(np.uint8)
    return bgr, flipped


def batches(rows, task, train):
    """Yields (images, targets) tensors"""
    order = list(range(len(rows)))
    if train:
        random.shuffle(order)
    for start in range(0, len(order), BATCH_SIZE):
        images, targets = [], []
        for i in order[start:start + BATCH_SIZE]:
            bgr = cv2.imread(rows[i][0])
            flipped = False
            if train:
                bgr, flipped = augment(bgr)
            images.append(preprocess(bgr))
            targets.append(target(task, rows[i][2], flipped))
        yield torch.stack(images), torch.tensor(targets)


def loss_and_stats(task, out, y):
    """Loss plus counts for the metrics"""
    if task in ('lane', 'obstacle'):
        # first output: visible (yes/no); the others are positions that only count where something is visible
        visible = y[:, 0]
        loss = F.binary_cross_entropy_with_logits(out[:, 0], visible)
        mask = visible > 0.5
        errors = (out[:, 1:] - y[:, 1:]).abs()[mask]
        if mask.any():
            loss = loss + F.mse_loss(out[:, 1:][mask], y[:, 1:][mask])
        predicted = (out[:, 0] > 0).float()
        return loss, {'correct': (predicted == visible).sum().item(), 'x_count': int(mask.sum().item()),
                      'false_visible': int(((predicted == 1) & (visible == 0)).sum().item()),
                      'missed_visible': int(((predicted == 0) & (visible == 1)).sum().item()),
                      'error_sums': errors.sum(0).cpu().numpy() if mask.any() else 0.0}
    labels = y[:, 0].long()
    weight = None if CLASS_WEIGHTS is None else CLASS_WEIGHTS.to(out.device)
    loss = F.cross_entropy(out, labels, weight=weight)
    predicted = out.argmax(1)
    confusion = np.zeros((CLASSES, CLASSES), dtype=int)
    for t, p in zip(labels.tolist(), predicted.tolist()):
        confusion[t][p] += 1
    return loss, {'correct': (predicted == labels).sum().item(), 'confusion': confusion}


def run_epoch(model, rows, task, dev, optimizer=None):
    """One pass over rows; trains if an optimizer is given. Returns the metrics."""
    model.train(optimizer is not None)
    total = {'loss': 0.0, 'correct': 0, 'x_count': 0, 'false_visible': 0, 'missed_visible': 0, 'error_sums': 0.0,
             'confusion': np.zeros((CLASSES, CLASSES), dtype=int)}
    with torch.set_grad_enabled(optimizer is not None):
        for images, y in batches(rows, task, train=optimizer is not None):
            images, y = images.to(dev), y.to(dev)
            loss, stats = loss_and_stats(task, model(images), y)
            if optimizer is not None:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            total['loss'] += loss.item() * len(images)
            for key, value in stats.items():
                total[key] = total[key] + value
    n = max(len(rows), 1)
    metrics = {'loss': total['loss'] / n, 'accuracy': total['correct'] / n}
    if task in ('lane', 'obstacle'):
        means = np.atleast_1d(total['error_sums']) / max(total['x_count'], 1)
        names = ['lane_x'] if task == 'lane' else ['cup_row', 'cup_x']
        for name, value in zip(names, means):
            metrics[name + '_mean_error'] = float(value)
        metrics['false_visible'] = total['false_visible']
        metrics['missed_visible'] = total['missed_visible']
        metrics['visible_frames'] = total['x_count']
    else:
        metrics['confusion'] = total['confusion'].tolist()  # rows: true class, columns: predicted
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', choices=['lane', 'curve', 'obstacle'], required=True)
    parser.add_argument('--val', action='append', required=True, help='part of a session name held out for validation')
    parser.add_argument('--epochs', type=int, default=EPOCHS)
    parser.add_argument('--root', default=DATASET_ROOT)
    args = parser.parse_args()

    rows = load_rows(args.root, args.task)
    val = [r for r in rows if any(v in r[1] for v in args.val)]
    train = [r for r in rows if not any(v in r[1] for v in args.val)]
    print('train %d frames from %d sessions, validation %d frames from %s' % (
        len(train), len(set(r[1] for r in train)), len(val), sorted(set(r[1] for r in val))))

    if args.task == 'curve':
        global CLASS_WEIGHTS
        names = [curve_model_class(r[2]['curve_class'], float(r[2]['curve_value'])) for r in train]
        counts = [names.count(c) for c in CURVE_MODEL_CLASSES]
        # mirroring makes left and right equally frequent on average, so both sides get the same weight
        pairs = [counts[0], (counts[1] + counts[3]) / 2.0, (counts[2] + counts[4]) / 2.0]
        CLASS_WEIGHTS = torch.tensor([len(train) / (CLASSES * max(pairs[i], 1)) for i in [0, 1, 2, 1, 2]])
        print('class counts %s, weights %s' % (counts, [round(w, 2) for w in CLASS_WEIGHTS.tolist()]))
    dev = device()
    model = build_model(args.task, pretrained=True).to(dev)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    if not os.path.isdir(MODEL_DIR):
        os.makedirs(MODEL_DIR)
    best, history, start = None, [], time.time()
    for epoch in range(args.epochs):
        train_metrics = run_epoch(model, train, args.task, dev, optimizer)
        val_metrics = run_epoch(model, val, args.task, dev)
        history.append({'epoch': epoch, 'train': train_metrics, 'val': val_metrics})
        print('epoch %2d  train loss %.4f  val loss %.4f  val accuracy %.3f%s  (%.0f s)' % (
            epoch, train_metrics['loss'], val_metrics['loss'], val_metrics['accuracy'],
            ''.join('  val %s %.3f' % (k, v) for k, v in val_metrics.items() if k.endswith('_mean_error')),
            time.time() - start))
        if best is None or val_metrics['loss'] < best['val']['loss']:
            best = history[-1]
            # legacy format so older PyTorch versions can load it as well
            torch.save(model.state_dict(), os.path.join(MODEL_DIR, args.task + '.pth'),
                       _use_new_zipfile_serialization=False)
    report = {'task': args.task, 'best_epoch': best['epoch'], 'best': best, 'history': history,
              'train_sessions': sorted(set(r[1] for r in train)), 'val_sessions': sorted(set(r[1] for r in val)),
              'train_frames': len(train), 'val_frames': len(val), 'minutes': (time.time() - start) / 60.0,
              'device': str(dev), 'epochs': args.epochs, 'batch_size': BATCH_SIZE, 'learning_rate': LEARNING_RATE}
    with open(os.path.join(MODEL_DIR, args.task + '.json'), 'w') as f:
        json.dump(report, f, indent=2)
    print('best epoch %d: %s' % (best['epoch'], json.dumps(best['val'])))


if __name__ == '__main__':
    main()
