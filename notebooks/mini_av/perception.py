"""Perception: camera frame -> what the models see (lane visible, lane position, curve class).

No decisions and no motor commands here.
"""

import os
import time

import torch

import config
from vision import CURVE_CLASSES, build_model, preprocess


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
        self.frame_count = 0
        self.curve_probs = [1.0, 0.0, 0.0]  # straight until the curve model says otherwise

    @torch.no_grad()
    def observe(self, frame):
        """Returns a dict: lane_visible (probability), lane_x (-1..1), curve_probs, inference_ms"""
        start = time.time()
        image = preprocess(frame).unsqueeze(0).cuda().half()
        lane = self.lane_model(image)[0].float()
        if self.curve_model is not None and self.frame_count % config.CURVE_EVERY == 0:
            new = torch.softmax(self.curve_model(image)[0].float(), 0).tolist()
            self.curve_probs = [old + config.CURVE_SMOOTHING * (n - old) for old, n in zip(self.curve_probs, new)]
        self.frame_count += 1
        return {
            'lane_visible': torch.sigmoid(lane[0]).item(),
            'lane_x': max(-1.0, min(1.0, lane[1].item())),
            'curve_probs': list(self.curve_probs),
            'curve_class': CURVE_CLASSES[max(range(3), key=lambda i: self.curve_probs[i])],
            'inference_ms': (time.time() - start) * 1000.0,
        }
