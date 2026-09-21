"""Task 1 results from driving logs: a markdown table plus graphs for the slides.

    python3 analyze_runs.py <log folder> [<log folder> ...]

Run on the robot host (needs matplotlib). The table goes to results/week1/task1_results.md in the repo,
the graphs to the USB stick (usb/images/results/week1/), because images never go on the SD card.
"""

import csv
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')  # no screen on the robot
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
TABLE_PATH = os.path.join(HERE, '..', '..', 'results', 'week1', 'task1_results.md')
GRAPH_DIR = '/home/jetbot/usb/images/results/week1'
COLORS = {'baseline': '#eb6834', 'nocurve': '#1baf7a', 'adaptive': '#2a78d6'}  # validated default categorical slots
INK, MUTED, GRID = '#1f1f1e', '#6b6a64', '#e4e3dc'


def load(log_dir):
    with open(os.path.join(log_dir, 'run.json')) as f:
        info = json.load(f)
    with open(os.path.join(log_dir, 'steps.csv')) as f:
        steps = [{k: (v if k in ('mode', 'curve_class') else float(v)) for k, v in row.items()} for row in csv.DictReader(f)]
    kind = 'baseline' if info['baseline'] else ('adaptive' if info['use_curve'] else 'nocurve')
    return info, steps, kind


def mean(values):
    return sum(values) / len(values) if values else float('nan')


def std(values):
    m = mean(values)
    return (sum((v - m) ** 2 for v in values) / len(values)) ** 0.5 if values else float('nan')


def metrics(steps):
    """Numbers for the table; wobble = spread of the lane position, jitter = mean steering change per step"""
    duration = steps[-1]['time'] if steps else 0.0
    lane_x = [s['lane_x'] for s in steps]
    steering = [s['steering'] for s in steps]
    result = {
        'duration_s': duration,
        'loop_hz': len(steps) / duration if duration else float('nan'),
        'inference_ms': mean([s['inference_ms'] for s in steps]),
        'lane_x_std': std(lane_x),
        'lane_x_mean_abs': mean([abs(v) for v in lane_x]),
        'steering_jitter': mean([abs(b - a) for a, b in zip(steering, steering[1:])]),
        'lane_lost_steps': sum(1 for s in steps if s['lane_visible'] < 0.5),
        'mean_speed': mean([s['speed'] for s in steps]),
    }
    for cls in ('straight', 'gentle', 'sharp'):
        result['speed_' + cls] = mean([s['speed'] for s in steps if s['curve_class'] == cls])
    return result


def style(ax, title, ylabel):
    ax.set_title(title, loc='left', color=INK, fontsize=11)
    ax.set_ylabel(ylabel, color=MUTED)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED)


def plot_run(name, steps, kind):
    """Lane position and speed over time: two panels on a shared time axis (never two y-scales in one panel)"""
    t = [s['time'] for s in steps]
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
    top.plot(t, [s['lane_x'] for s in steps], color=COLORS[kind], linewidth=2)
    top.axhline(0, color=MUTED, linewidth=0.8)
    style(top, '%s: lane position (0 = lane center)' % name, 'lane_x')
    bottom.plot(t, [s['speed'] for s in steps], color=COLORS[kind], linewidth=2)
    style(bottom, 'wheel speed command', 'speed')
    bottom.set_xlabel('time (s)', color=MUTED)
    fig.tight_layout()
    fig.savefig(os.path.join(GRAPH_DIR, name + '_timeline.png'), dpi=150)
    plt.close(fig)


def plot_comparison(rows):
    """One small panel per metric, one bar per run (metrics have different scales)"""
    panels = [('lane_x_std', 'wobble: spread of lane position'), ('steering_jitter', 'steering change per step'),
              ('mean_speed', 'mean speed')]
    fig, axes = plt.subplots(1, len(panels), figsize=(11, 3.6))
    for ax, (key, title) in zip(axes, panels):
        names = [r[0] for r in rows]
        values = [r[2][key] for r in rows]
        bars = ax.bar(range(len(rows)), values, color=[COLORS[r[1]] for r in rows], width=0.6,
                      edgecolor='white', linewidth=2)
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), '%.3f' % value,
                    ha='center', va='bottom', color=INK, fontsize=9)
        ax.set_xticks(range(len(rows)))
        ax.set_xticklabels(names, rotation=20, ha='right', color=MUTED, fontsize=9)
        style(ax, title, '')
        ax.xaxis.grid(False)  # bars only need horizontal guides
    fig.tight_layout()
    fig.savefig(os.path.join(GRAPH_DIR, 'comparison.png'), dpi=150)
    plt.close(fig)


def main():
    if not os.path.isdir(GRAPH_DIR):
        os.makedirs(GRAPH_DIR)
    if not os.path.isdir(os.path.dirname(TABLE_PATH)):
        os.makedirs(os.path.dirname(TABLE_PATH))
    rows = []
    for log_dir in sys.argv[1:]:
        info, steps, kind = load(log_dir.rstrip('/'))
        name = os.path.basename(log_dir.rstrip('/'))[20:]  # drop the date prefix
        rows.append((name, kind, metrics(steps), info.get('stop_reason', '')))
        plot_run(name, steps, kind)
    plot_comparison(rows)
    header = ['run', 'mode', 'duration s', 'loop Hz', 'inference ms', 'wobble (lane_x std)', 'mean abs lane_x',
              'steering jitter', 'lane lost steps', 'mean speed', 'speed straight', 'speed gentle', 'speed sharp', 'stop']
    lines = ['| ' + ' | '.join(header) + ' |', '|' + ' :--- |' * len(header)]
    for name, kind, m, reason in rows:
        cells = [name, kind] + ['%.3f' % m[k] if k != 'lane_lost_steps' else str(m[k]) for k in
                                ('duration_s', 'loop_hz', 'inference_ms', 'lane_x_std', 'lane_x_mean_abs',
                                 'steering_jitter', 'lane_lost_steps', 'mean_speed', 'speed_straight',
                                 'speed_gentle', 'speed_sharp')] + [reason]
        lines.append('| ' + ' | '.join(cells) + ' |')
    table = '\n'.join(lines)
    with open(TABLE_PATH, 'w') as f:
        f.write('# Task 1 results\n\nGenerated by `notebooks/mini_av/analyze_runs.py`; graphs in `usb/images/results/week1/`.\n\n'
                + table + '\n')
    print(table)


if __name__ == '__main__':
    main()
