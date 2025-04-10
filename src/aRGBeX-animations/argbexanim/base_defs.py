# Houses events that do stuff on the led strip
from typing import Literal



def fitbest(timestamp:float, FPS:int):
    """Fits the given timestamp in ms best it can to the FPS"""
    step = 1000 / FPS
    best_fit = round(timestamp / step)
    best_fit *= step
    return int(round(best_fit, 3)) #3 digits of accuracy gives us time up to 1 ms



class Frame():
    def __init__(self):
        self.color: tuple[int] = (0, 0, 0)
        self.selection: list[int] = []
        
    def __repr__(self):
        return f"<Frame | Selection: {self.selection} | Color: {self.color}>"
    
    def __str__(self):
        return self.__repr__()

class IndexedColorFrame():
    def __init__(self):
        self._id_color_dict: dict[int: tuple[int, int, int]] = {}

    def AddFrame(self, _frame: Frame):
        for sel in _frame.selection:
            self._id_color_dict[sel] = _frame.color
            #Override previous values, last added frame has the top priority

    def GetFrame(self):
        return self._id_color_dict.copy()
    
    def __repr__(self):
        s = f"<IndexedColorFrame | \n"
        for i, c in self._id_color_dict.items():
            s += f"{i}: {c}\n"

        return s + ">"
    
    def __str__(self):
        return f"<IndexedColorFrame: {len(self._id_color_dict)} LEDs>"
    

class Color():
    def __init__(self, red:int, green:int, blue:int):
        """Represents a specific color"""
        #Clamp the colors
        if type(red) != int or type(green) != int or type(blue) != int:
            raise ValueError("Colors passed are of invalid type!")
        
        self.red =      red     if red <= 255   else 255
        self.green =    green   if green <= 255 else 255
        self.blue =     blue    if blue <= 255  else 255

        

    def _computetimeline(self, FPS:int) -> dict[int:Frame]:
        # Only one frame here
        frame = Frame()
        frame.color = (self.red, self.green, self.blue)
        return {0: frame}
        
    def __repr__(self):
        return f"<Color R: {self.red}, G: {self.green}, B: {self.blue}>"
    
    def __str__(self):
        return self.__repr__()

class Selector():
    def __init__(self, selection: list[int] | Literal["All"]):
        """Base selector. Selects LEDs passed in the list (by their indexes)"""
        
        if type(selection) == str:
            if not selection.casefold() in ("all"): # In case we have other types too
                raise ValueError(f"Unsupported selection '{selection}'!")
            self.selection = selection.casefold()
        else:
            self.selection = list(set(selection)) #Hack: remove duplicates

            for item in self.selection:
                if type(item) != int:
                    raise ValueError(f"Item '{item}' in selection is not of type int!")

        self.timeline = None

    def _computetimeline(self, FPS:int, size:int) -> dict[int: Frame]:
        frame = Frame()
        selection = []

        if type(self.selection) == list:
            selection:list = self.selection.copy()

            for idx in self.selection:
                if idx < 1 or idx > size + 1:
                    del selection[selection.index(idx)] # Here we delete by searching the index, because indexes will change if stuff gets deleted

        elif type(self.selection) == str:
            if self.selection == "all":
                selection = list(range(1, size+1))

        frame.selection = selection

        return {0: frame}


    def _getselection(self):
        """Returns the selection"""
        return self.selection.copy()

    def __str__(self) -> str:
        return self.__repr__()
    
    def __repr__(self) -> str:
        return f"<Selector {self.s_name}>"
    

class Action(): # Base class for every predefined action or user-defined sequences
    def __init__(self, selector:Selector, color:Color):
        """Merges a selector and color into one action"""
        
        if not issubclass(type(selector), Selector) or not issubclass(type(color), Color):
            raise ValueError("Passed objects are not of (sub)type Selector or Color!")
        
        self.selector = selector
        self.color = color
        self.fps = 0
        self.size = 0
        self.fps_changed = False
        self.size_changed = False
        self.timeline = {}
    
    def GetTimeline(self) -> dict[int: Frame]:
        if self.fps_changed or self.size_changed: # Something changed, re-compute
            self._ComputeTimeline()
            
        return self.timeline.copy()


    def _ComputeTimeline(self):
        selection_timeline = self.selector._computetimeline(self.fps, self.size)
        color_timeline = self.color._computetimeline(self.fps) # Color can't even use size, no need to pass it here

        timestamps: set[int] = set(selection_timeline.keys())
        timestamps |= set(color_timeline.keys())


        self.timeline = {}
        last_color_data = (0, 0, 0)
        last_selection = []

        for ts in timestamps:
            try:
                last_selection = selection_timeline[ts].selection
            except KeyError:
                pass

            try:
                last_color_data = selection_timeline[ts].color
            except KeyError:
                pass

            newFrame = Frame()
            newFrame.color = last_color_data
            newFrame.selection = last_selection

            self.timeline.update({fitbest(ts, self.fps) : newFrame})
    
    def SetLightstripSize(self, x:int):
        """Sets the size of the lightstrip, before calling _GetTimeline"""
        self.size = x
        self.size_changed = True

    def SetFPS(self, x:int):
        """Sets FPS before calling _GetTimeline"""
        self.fps = x
        self.fps_changed = True

    def _GetTimeline(self):
        if not self.fps:
            raise RuntimeError("Set FPS first before calling _GetTimeline()!")

        if self.timeline:
            return self.timeline.copy()
        else:
            self._ComputeTimeline()
            return self.timeline.copy()
        
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return f"<ACTION {self.act_name} {self.selector} -> {self.color} , TAGS: {self.tags}>"