# Houses the main class of argbex animation file
from .base_defs import Selector, Color, Action, IndexedColorFrame, Frame, fitbest
from re import match

class Sequence():
    def __init__(self, led_amount: int, FPS: int):
        """Creates a new sequence. Add events to it by calling Sequence.add(event)"""
        self.size = led_amount
        self.fps = FPS

        self.timeline: dict[int : IndexedColorFrame] = {}


    def add(self, selector: Selector|Action, color=Color(0, 0, 0), timestamp:str|int = "00:00:00") -> None:
        """Add action to the animation. You can either pass selector and color, or pass an already created Action 
        (in which case the color optional parameter is ignored).
        Timestamp specifies when to play this action/animation, the format is either minutes:seconds:ms or integer in seconds."""

        if type(timestamp) == str:
            if match("[0-9]{2}:[0-9]{2}:[0-9]{2,3}", timestamp):
                timestamp = self._calc_timestamp(timestamp)
            else:
                raise ValueError("Timestamp value does not match neither pattern 00:00:00 nor 00:00:000")
        elif type(timestamp) == int:
            timestamp *= 1000
        else:
            raise ValueError("Unsupported value for timestamp!")
        

        timestamp = fitbest(timestamp, self.fps)

        if type(selector) == Selector:
            self._add_raw(selector, color, timestamp)
        elif type(selector) == Action:
            self._add_action(selector, timestamp)
        else:
            raise ValueError("Unsupported type passed into the selector argument!")
        
        
    
    def _calc_timestamp(self, ts: str) -> int:
        minutes, seconds, ms = ts.split(":")
        minutes, seconds, ms = int(minutes), int(seconds), int(ms)
        return (minutes * 60 + seconds) * 1000 + ms


    def _add_raw(self, sel: Selector, col: Color, ts):
        action = Action(sel, col)
        return self._add_action(action, ts)
        
    def _add_action(self, action: Action, ts):
        action.SetFPS(self.fps)
        action.SetLightstripSize(self.size)

        frames: dict[int: Frame] = action.GetTimeline()

        for ts2, frame in frames.items():
            ts += ts2

            if not ts in self.timeline.keys(): # New frame
                self.timeline[ts] = IndexedColorFrame()

            self.timeline[ts].AddFrame(frame)


    def GetTimeline(self):
        return self.timeline.copy()



