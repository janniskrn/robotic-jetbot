"""Decision: what the robot should do now, from what perception sees.

Modes (D9b): FOLLOW the lane; BLOCKED, a cup is close ahead and the robot waits (step 5.2; AVOID and RECOVER
come next); STOP when the lane is lost. BLOCKED comes first: a close cup matters even while the lane is seen.
"""

import config

FOLLOW = 'FOLLOW'
BLOCKED = 'BLOCKED'
STOP = 'STOP'


def cup_close(percept):
    """True if the obstacle model sees a cup at or closer than the trigger distance"""
    return (percept['cup_visible'] >= config.OBSTACLE_VISIBLE_THRESHOLD
            and percept['cup_row'] >= config.OBSTACLE_ROW)


def cup_gone(percept):
    """True if no cup is seen, or only one clearly further away than the trigger distance"""
    return (percept['cup_visible'] < config.OBSTACLE_VISIBLE_THRESHOLD
            or percept['cup_row'] < config.OBSTACLE_CLEAR_ROW)


class Decision(object):
    def __init__(self):
        self.lost_since = None
        self.lane_seen = False
        self.blocked = False
        self.close_frames = 0  # control steps in a row with a close cup
        self.clear_frames = 0  # control steps in a row with the cup gone

    def update(self, percept, now):
        """Returns the mode for this frame"""
        self.close_frames = self.close_frames + 1 if cup_close(percept) else 0
        self.clear_frames = self.clear_frames + 1 if cup_gone(percept) else 0
        if self.blocked and self.clear_frames >= config.OBSTACLE_CLEAR_FRAMES:
            self.blocked = False
        elif not self.blocked and self.close_frames >= config.OBSTACLE_FRAMES:
            self.blocked = True
        if self.blocked:
            self.lost_since = None  # standing still is not losing the lane
            return BLOCKED
        if percept['lane_visible'] >= config.LANE_VISIBLE_THRESHOLD:
            self.lost_since = None
            self.lane_seen = True
            return FOLLOW
        if not self.lane_seen:
            return STOP  # never start without seeing the lane (the grace time is only for short gaps)
        if self.lost_since is None:
            self.lost_since = now
        # a short gap (one or two bad frames) keeps following on the last steering
        return FOLLOW if now - self.lost_since < config.LANE_LOST_TIMEOUT else STOP
