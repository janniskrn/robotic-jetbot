"""Run logging (D12): one CSV row per control step plus run.json with the settings, on the USB stick."""

import csv
import json
import os
import time

import config

COLUMNS = ['time', 'dt', 'mode', 'lane_visible', 'lane_x', 'p_straight', 'p_gentle', 'p_sharp',
           'curve_class', 'steering', 'speed', 'left', 'right', 'battery_v', 'inference_ms']


class RunLogger(object):
    def __init__(self, name, settings):
        self.dir = os.path.join(config.LOG_ROOT, '%s_%s' % (time.strftime('%Y-%m-%d_%H-%M-%S'), name))
        os.makedirs(self.dir)
        constants = {k: v for k, v in vars(config).items() if k.isupper()}
        with open(os.path.join(self.dir, 'run.json'), 'w') as f:
            json.dump(dict(settings, name=name, config=constants), f, indent=2, sort_keys=True)
        self._file = open(os.path.join(self.dir, 'steps.csv'), 'w', buffering=1)  # line-buffered: survives a power loss
        self._writer = csv.DictWriter(self._file, fieldnames=COLUMNS)
        self._writer.writeheader()

    def step(self, **values):
        self._writer.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in values.items()})

    def close(self, reason):
        self._file.close()
        with open(os.path.join(self.dir, 'run.json')) as f:
            info = json.load(f)
        info['stop_reason'] = reason
        with open(os.path.join(self.dir, 'run.json'), 'w') as f:
            json.dump(info, f, indent=2, sort_keys=True)
