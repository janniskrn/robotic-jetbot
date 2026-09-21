"""Network and image preprocessing shared by training (03_train.py) and driving.

One place for both, so the robot feeds the model exactly what it was trained on.
"""

import numpy as np
import torch
import torchvision

MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)  # ImageNet statistics, the backbone was pretrained on them
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

# Outputs per task: lane = (lane_visible logit, lane_x); curve = straight/gentle/sharp; obstacle = free/blocked
TASK_OUTPUTS = {'lane': 2, 'curve': 3, 'obstacle': 2}
CURVE_CLASSES = ['straight', 'gentle', 'sharp']


def build_model(task, pretrained=False):
    """ResNet18 with a new last layer for the task"""
    model = torchvision.models.resnet18(pretrained=pretrained)
    model.fc = torch.nn.Linear(512, TASK_OUTPUTS[task])
    return model


def preprocess(bgr):
    """Camera or file image (224x224 BGR uint8, as OpenCV gives it) -> normalized 3x224x224 float tensor"""
    rgb = bgr[:, :, ::-1].astype(np.float32) / 255.0
    return torch.from_numpy(((rgb - MEAN) / STD).transpose(2, 0, 1).copy())
