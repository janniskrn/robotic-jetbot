"""Trains one model from the labeled dataset sessions (D2: one model per task).

    python3 03_train.py --task lane  --val <session name part> [--val ...]
    python3 03_train.py --task curve --val <session name part>

lane:  outputs lane_visible (yes/no) and lane_x; lane_x only counts on frames where the lane is visible.
curve: straight / gentle / sharp, only frames that have a curve class.

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

from vision import CURVE_CLASSES, build_model, preprocess

DATASET_ROOT = '/workspace/usb/images/datasets'  # inside the Jupyter container
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')  # SD card, *.pth is not in git

EPOCHS = 15
BATCH_SIZE = 16
LEARNING_RATE = 1e-4   # small: the pretrained backbone only needs fine-tuning
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
            for row in csv.DictReader(f):
                if task == 'curve' and not row['curve_class']:
                    continue
                rows.append((os.path.join(session_dir, row['frame']), session, row))
    return rows


def target(task, row, flipped):
    """Label as a float vector: lane = [visible, x], curve = [class index]"""
    if task == 'lane':
        visible = float(row['lane_visible'])
        x = float(row['lane_x']) if row['lane_x'] != '' else 0.0
        return [visible, -x if flipped else x]  # a mirrored image mirrors the lane center
    return [float(CURVE_CLASSES.index(row['curve_class']))]  # a curve stays the same class when mirrored


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
    if task == 'lane':
        visible = y[:, 0]
        loss = F.binary_cross_entropy_with_logits(out[:, 0], visible)
        mask = visible > 0.5
        x_error = (out[:, 1] - y[:, 1]).abs()[mask]
        if mask.any():
            loss = loss + F.mse_loss(out[:, 1][mask], y[:, 1][mask])
        correct = ((out[:, 0] > 0).float() == visible).sum().item()
        return loss, {'correct': correct, 'x_error_sum': x_error.sum().item(), 'x_count': int(mask.sum().item())}
    labels = y[:, 0].long()
    loss = F.cross_entropy(out, labels)
    predicted = out.argmax(1)
    confusion = np.zeros((3, 3), dtype=int)
    for t, p in zip(labels.tolist(), predicted.tolist()):
        confusion[t][p] += 1
    return loss, {'correct': (predicted == labels).sum().item(), 'confusion': confusion}


def run_epoch(model, rows, task, dev, optimizer=None):
    """One pass over rows; trains if an optimizer is given. Returns the metrics."""
    model.train(optimizer is not None)
    total = {'loss': 0.0, 'correct': 0, 'x_error_sum': 0.0, 'x_count': 0, 'confusion': np.zeros((3, 3), dtype=int)}
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
    if task == 'lane':
        metrics['lane_x_mean_error'] = total['x_error_sum'] / max(total['x_count'], 1)
    else:
        metrics['confusion'] = total['confusion'].tolist()  # rows: true class, columns: predicted
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', choices=['lane', 'curve'], required=True)
    parser.add_argument('--val', action='append', required=True, help='part of a session name held out for validation')
    parser.add_argument('--epochs', type=int, default=EPOCHS)
    parser.add_argument('--root', default=DATASET_ROOT)
    args = parser.parse_args()

    rows = load_rows(args.root, args.task)
    val = [r for r in rows if any(v in r[1] for v in args.val)]
    train = [r for r in rows if not any(v in r[1] for v in args.val)]
    print('train %d frames from %d sessions, validation %d frames from %s' % (
        len(train), len(set(r[1] for r in train)), len(val), sorted(set(r[1] for r in val))))

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
            '  val lane_x error %.3f' % val_metrics['lane_x_mean_error'] if args.task == 'lane' else '',
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
