"""Network and image preprocessing shared by training (03_train.py) and driving.

One place for both, so the robot feeds the model exactly what it was trained on.
"""

import numpy as np
import torch
import torchvision

MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)  # ImageNet statistics, the backbone was pretrained on them
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

# Outputs per task: lane = (lane_visible logit, lane_x); curve = CURVE_MODEL_CLASSES; obstacle = free/blocked
TASK_OUTPUTS = {'lane': 2, 'curve': 5, 'obstacle': 2}
CURVE_CLASSES = ['straight', 'gentle', 'sharp']  # how sharp: what speed and feedforward size use
# The curve model also says which way the curve bends (DATA2): the sign of lane_x was near 0 and flipped
# in the sharp curve. Left = negative curve_value, the same sign convention as lane_x.
CURVE_MODEL_CLASSES = ['straight', 'gentle_left', 'sharp_left', 'gentle_right', 'sharp_right']


def curve_model_class(curve_class, curve_value):
    """Label (curve_class and signed curve_value from labels.csv) -> one of CURVE_MODEL_CLASSES"""
    if curve_class == 'straight':
        return 'straight'
    return curve_class + ('_left' if curve_value < 0 else '_right')


def split_curve_probs(probs):
    """Curve model probabilities -> ([p_straight, p_gentle, p_sharp], curve_dir).

    curve_dir = p_right - p_left, from -1 (surely a left curve) to 1 (surely a right curve).
    """
    straight, gentle_left, sharp_left, gentle_right, sharp_right = probs
    return [straight, gentle_left + gentle_right, sharp_left + sharp_right], gentle_right + sharp_right - gentle_left - sharp_left


def build_model(task, pretrained=False):
    """ResNet18 with a new last layer for the task"""
    model = torchvision.models.resnet18(pretrained=pretrained)
    model.fc = torch.nn.Linear(512, TASK_OUTPUTS[task])
    return model


def preprocess(bgr):
    """Camera or file image (224x224 BGR uint8, as OpenCV gives it) -> normalized 3x224x224 float tensor"""
    rgb = bgr[:, :, ::-1].astype(np.float32) / 255.0
    return torch.from_numpy(((rgb - MEAN) / STD).transpose(2, 0, 1).copy())
