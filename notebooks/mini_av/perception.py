"""Perception: camera frame -> what the models see (lane visible, lane position, curve class, cup) plus script
measurements from the color masks (HYBRID): lane aligned, the angle of the lane edge ahead, and where the cup bands are.

No decisions and no motor commands here.
"""

import math
import os
import time

import torch

import config
import cup_mask
import lane_mask
from safety import wait_for_new_frame
from vision import CURVE_CLASSES, build_model, preprocess, split_curve_probs

WARMUP_FRAMES = 5  # model calls with the motors off before driving: the first call is slow


def load(task, allow_trt=True):
    """Trained model for the task on the GPU in half precision, or None if it was not trained yet.
    Uses the TensorRT version (tools/convert_trt.py) when it is newer than the trained weights."""
    path = os.path.join(config.MODEL_DIR, task + '.pth')
    if not os.path.exists(path):
        return None
    trt_path = os.path.join(config.MODEL_DIR, task + '_trt.pth')
    if allow_trt and os.path.exists(trt_path) and os.path.getmtime(trt_path) > os.path.getmtime(path):
        from torch2trt import TRTModule
        engine = TRTModule()
        engine.load_state_dict(torch.load(trt_path))
        return engine
    torch.backends.cudnn.benchmark = True  # PyTorch fallback: lets cuDNN pick the fastest kernels
    model = build_model(task)
    model.load_state_dict(torch.load(path, map_location='cpu'))
    return model.cuda().eval().half()


class Perception(object):
    def __init__(self, use_curve=True):
        self.lane_model = load('lane')
        if self.lane_model is None:
            raise RuntimeError('no lane model: train it first with tools/train.py --task lane')
        self.curve_model = load('curve') if use_curve else None
        self.curve_on = self.curve_model is not None
        self.obstacle_model = load('obstacle')  # None until trained: then no cup is ever seen
        self.frame_count = 0
        self.curve_model_probs = [1.0, 0.0, 0.0, 0.0, 0.0]  # straight until the curve model says otherwise
        self.cup = [-10.0, 0.0, 0.0]  # obstacle model output (visible logit, row, x): no cup until it says otherwise

    def use_curve_model(self, on):
        """Switches a loaded curve model on or off: a shared Perception (cockpit) runs baseline and no-curve runs
        without it, like their own. Off, the curve reads straight"""
        on = on and self.curve_model is not None
        if on != self.curve_on:
            self.curve_on = on
            self.curve_model_probs = [1.0, 0.0, 0.0, 0.0, 0.0]

    def warm_up(self, camera):
        """Runs the models on a few frames with the motors off. Returns the last frame"""
        frame = wait_for_new_frame(camera, camera.value, timeout=2.0)  # is the camera alive at all?
        for _ in range(WARMUP_FRAMES):
            frame = wait_for_new_frame(camera, frame)
            self.observe(frame)
        return frame

    @torch.no_grad()
    def observe(self, frame):
        """Returns a dict with the model outputs (lane_*, curve_*, cup_*, inference_ms) and the color-mask
        measurements (lane_aligned, tape_angle, tape_row, cup_bands: (x -1..1, lower edge row 0..1, pixels))"""
        start = time.time()
        image = preprocess(frame).unsqueeze(0).cuda().half()
        lane = self.lane_model(image)[0].float()
        if self.curve_on and self.frame_count % config.CURVE_EVERY == 0:
            new = torch.softmax(self.curve_model(image)[0].float(), 0).tolist()
            self.curve_model_probs = [old + config.CURVE_SMOOTHING * (n - old)
                                      for old, n in zip(self.curve_model_probs, new)]
        if self.obstacle_model is not None and self.frame_count % config.OBSTACLE_EVERY == 1:  # between curve frames
            self.cup = self.obstacle_model(image)[0].float().tolist()
        self.frame_count += 1
        curve_probs, curve_dir = split_curve_probs(self.curve_model_probs)
        height, width = frame.shape[:2]
        mask = lane_mask.blue_mask(frame)
        return {
            'lane_visible': torch.sigmoid(lane[0]).item(),
            'lane_x': max(-1.0, min(1.0, lane[1].item())),
            'curve_probs': curve_probs,
            'curve_dir': curve_dir,
            'curve_class': CURVE_CLASSES[max(range(3), key=lambda i: curve_probs[i])],
            'cup_visible': 1.0 / (1.0 + math.exp(-self.cup[0])),
            'cup_row': self.cup[1],
            'cup_x': self.cup[2],
            'lane_aligned': lane_mask.lane_aligned(frame, mask),
            'tape_angle': lane_mask.tape_angle(frame, mask),
            'tape_row': lane_mask.tape_row(frame, mask) / float(height),
            'cup_bands': [(x / (width / 2.0) - 1.0, row / float(height), pixels)
                          for x, row, pixels in cup_mask.find_cups(frame)],
            'inference_ms': (time.time() - start) * 1000.0,
        }
