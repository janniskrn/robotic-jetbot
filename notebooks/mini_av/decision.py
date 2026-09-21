"""Decision: what the robot should do now, from what perception sees (Task 1).

D9: no state machine yet. Task 1 has two modes only: FOLLOW the lane, or STOP when it is lost.
Task 2 will add AVOID and RECOVER here.
"""

import config

FOLLOW = 'FOLLOW'
STOP = 'STOP'


class Decision(object):
    def __init__(self):
        self.lost_since = None
        self.lane_seen = False

    def update(self, percept, now):
        """Returns the mode for this frame"""
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
