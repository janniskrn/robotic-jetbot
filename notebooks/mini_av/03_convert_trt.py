"""Converts a trained model to TensorRT for fast driving (run on the robot, after every training).

    python3 03_convert_trt.py --task lane

Measured on the robot: lane model 66 ms per frame in PyTorch, 10.6 ms in TensorRT, same outputs.
A TensorRT engine only runs on the GPU it was built on, so this step always runs on the robot.
Saves models/<task>_trt.pth; perception.py uses it when it is newer than models/<task>.pth.
"""

import argparse
import os

import torch
from torch2trt import torch2trt

from perception import load

MAX_DIFFERENCE = 0.05  # largest allowed output difference to PyTorch (measured: 0.002 and below)
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', choices=['lane', 'curve', 'obstacle'], required=True)
    args = parser.parse_args()
    model = load(args.task, allow_trt=False)
    example = torch.zeros((1, 3, 224, 224)).cuda().half()
    engine = torch2trt(model, [example], fp16_mode=True)
    with torch.no_grad():
        difference = (model(example).float() - engine(example).float()).abs().max().item()
    if difference > MAX_DIFFERENCE:
        raise SystemExit('conversion changed the outputs by %.4f: not saved' % difference)
    torch.save(engine.state_dict(), os.path.join(MODEL_DIR, args.task + '_trt.pth'))
    print('saved models/%s_trt.pth, largest output difference to PyTorch %.4f' % (args.task, difference))


if __name__ == '__main__':
    main()
