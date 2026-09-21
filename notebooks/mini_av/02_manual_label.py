"""Manual labeling of a recorded session, on a computer with a screen (for example the Mac).

The same labels as 02_auto_label.py, set by hand, saved to labels_manual.csv in the session folder.
When labels.csv (the automatic labels) exists too, it prints how well both agree at the end.

    python3 02_manual_label.py <session folder> [--step N]

--step N shows every Nth frame only (default 5), enough for a check.

Controls in the image window:
    mouse click   lane center on the green line: sets lane_x and "lane visible"
    n             no lane visible (clears lane_x)
    1 / 2 / 3     curve class straight / gentle / sharp
    0             no curve class
    space         save this frame and go to the next one
    b             back to the previous frame
    q             save everything and quit
"""

import argparse
import csv
import glob
import os

import cv2

LOOKAHEAD_ROW = 0.65  # same row as lane_mask.py, where the lane center is measured
SCALE = 3             # window zoom, 224 px frames become 672 px
FIELDS = ['frame', 'lane_visible', 'lane_x', 'curve_class', 'label_source', 'reviewed']
CLASS_KEYS = {ord('1'): 'straight', ord('2'): 'gentle', ord('3'): 'sharp', ord('0'): ''}
WINDOW = 'manual label'


def load(path):
    """Existing labels by frame name, or an empty dict"""
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return {row['frame']: row for row in csv.DictReader(f)}


def save(path, labels):
    with open(path, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for name in sorted(labels):
            writer.writerow(labels[name])


def show(image, label):
    """Draws the frame, the lookahead row and the current label"""
    view = cv2.resize(image, None, fx=SCALE, fy=SCALE, interpolation=cv2.INTER_NEAREST)
    h, w = view.shape[:2]
    y = int(LOOKAHEAD_ROW * h)
    cv2.line(view, (0, y), (w - 1, y), (0, 255, 0), 1)
    if label['lane_x'] != '':
        x = int((float(label['lane_x']) + 1.0) / 2.0 * w)
        cv2.circle(view, (x, y), 10, (0, 255, 255), 2)
    text = '%s  visible %s  curve %s' % (label['frame'], label['lane_visible'], label['curve_class'] or '-')
    cv2.putText(view, text, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
    cv2.putText(view, text, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
    cv2.imshow(WINDOW, view)


def compare(manual, auto):
    """Prints how well the manual labels agree with the automatic ones"""
    both = [name for name in manual if name in auto]
    if not both:
        return
    visible_same = sum(manual[n]['lane_visible'] == str(auto[n]['lane_visible']) for n in both)
    x_pairs = [(float(manual[n]['lane_x']), float(auto[n]['lane_x'])) for n in both
               if manual[n]['lane_x'] != '' and auto[n]['lane_x'] != '']
    class_pairs = [(manual[n]['curve_class'], auto[n]['curve_class']) for n in both
                   if manual[n]['curve_class'] and auto[n]['curve_class']]
    print('compared with labels.csv on %d frames:' % len(both))
    print('  lane visible agrees on %d of %d' % (visible_same, len(both)))
    if x_pairs:
        error = sum(abs(m - a) for m, a in x_pairs) / len(x_pairs)
        print('  lane_x mean difference %.3f (1.0 = half the image width) on %d frames' % (error, len(x_pairs)))
    if class_pairs:
        print('  curve class agrees on %d of %d' % (sum(m == a for m, a in class_pairs), len(class_pairs)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('session')
    parser.add_argument('--step', type=int, default=5)
    args = parser.parse_args()

    frames = sorted(glob.glob(os.path.join(args.session, 'frame_*.jpg')))[::args.step]
    out_path = os.path.join(args.session, 'labels_manual.csv')
    labels = load(out_path)
    current = {}
    frame_width = {'pixels': 224}  # updated for every frame, read by the click handler

    def on_click(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            current['lane_x'] = '%.4f' % (2.0 * x / (frame_width['pixels'] * SCALE) - 1.0)
            current['lane_visible'] = '1'

    cv2.namedWindow(WINDOW)
    cv2.setMouseCallback(WINDOW, on_click)
    i = 0
    while 0 <= i < len(frames):
        name = os.path.basename(frames[i])
        current.clear()
        current.update(labels.get(name, {'frame': name, 'lane_visible': '0', 'lane_x': '', 'curve_class': '',
                                          'label_source': 'human', 'reviewed': '1'}))
        image = cv2.imread(frames[i])
        frame_width['pixels'] = image.shape[1]
        key = -1
        while key not in (ord(' '), ord('b'), ord('q')):
            show(image, current)
            key = cv2.waitKey(50) & 0xFF
            if key == ord('n'):
                current['lane_visible'], current['lane_x'] = '0', ''
            elif key in CLASS_KEYS:
                current['curve_class'] = CLASS_KEYS[key]
        labels[name] = dict(current)
        if key == ord('q'):
            break
        i += 1 if key == ord(' ') else -1
        i = max(i, 0)
    cv2.destroyAllWindows()
    save(out_path, labels)
    print('saved %d labels to %s' % (len(labels), out_path))
    compare(labels, load(os.path.join(args.session, 'labels.csv')))


if __name__ == '__main__':
    main()
