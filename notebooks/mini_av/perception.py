"""Perception: camera frame -> what the models see (lane visible, lane position, curve class).

No decisions and no motor commands here.
"""

import math
import os
import time

import torch

import config
from vision import CURVE_CLASSES, build_model, preprocess, split_curve_probs


def load(task, allow_trt=True):
    """Trained model for the task on the GPU in half precision, or None if it was not trained yet.

    Uses the TensorRT version (03_convert_trt.py, about 6x faster) when it is newer than the trained
    weights; an older one belongs to a previous training and is ignored.
    """
    path = os.path.join(config.MODEL_DIR, task + '.pth')
    if not os.path.exists(path):
        return None
    trt_path = os.path.join(config.MODEL_DIR, task + '_trt.pth')
    if allow_trt and os.path.exists(trt_path) and os.path.getmtime(trt_path) > os.path.getmtime(path):
        from torch2trt import TRTModule
        engine = TRTModule()
        engine.load_state_dict(torch.load(trt_path))
        return engine
    torch.backends.cudnn.benchmark = True  # PyTorch fallback: lets cuDNN pick the fastest kernels (66 -> 41 ms)
    model = build_model(task)
    model.load_state_dict(torch.load(path, map_location='cpu'))
    return model.cuda().eval().half()


class Perception(object):
    def __init__(self, use_curve=True):
        self.lane_model = load('lane')
        if self.lane_model is None:
            raise RuntimeError('no lane model: train it first with 03_train.py --task lane')
        self.curve_model = load('curve') if use_curve else None
        self.obstacle_model = load('obstacle')  # None until trained: then no cup is ever seen
        self.frame_count = 0
        self.curve_model_probs = [1.0, 0.0, 0.0, 0.0, 0.0]  # straight until the curve model says otherwise
        self.cup = [-10.0, 0.0, 0.0]  # obstacle model output (visible logit, row, x): no cup until it says otherwise

    @torch.no_grad()
    def observe(self, frame):
        """Returns a dict: lane_visible (probability), lane_x (-1..1), curve_probs (straight, gentle, sharp),
        curve_dir (-1 left .. 1 right), curve_class, cup_visible (probability), cup_row (lower edge of the cup's
        band, 0 top .. 1 bottom), cup_x (-1..1), inference_ms"""
        start = time.time()
        image = preprocess(frame).unsqueeze(0).cuda().half()
        lane = self.lane_model(image)[0].float()
        if self.curve_model is not None and self.frame_count % config.CURVE_EVERY == 0:
            new = torch.softmax(self.curve_model(image)[0].float(), 0).tolist()
            self.curve_model_probs = [old + config.CURVE_SMOOTHING * (n - old)
                                      for old, n in zip(self.curve_model_probs, new)]
        if self.obstacle_model is not None and self.frame_count % config.OBSTACLE_EVERY == 1:  # between curve frames
            self.cup = self.obstacle_model(image)[0].float().tolist()
        self.frame_count += 1
        curve_probs, curve_dir = split_curve_probs(self.curve_model_probs)
        cup = self.cup
        return {
            'lane_visible': torch.sigmoid(lane[0]).item(),
            'lane_x': max(-1.0, min(1.0, lane[1].item())),
            'curve_probs': curve_probs,
            'curve_dir': curve_dir,
            'curve_class': CURVE_CLASSES[max(range(3), key=lambda i: curve_probs[i])],
            'cup_visible': 1.0 / (1.0 + math.exp(-cup[0])),
            'cup_row': cup[1],
            'cup_x': cup[2],
            'inference_ms': (time.time() - start) * 1000.0,
        }
