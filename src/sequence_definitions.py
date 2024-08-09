#Stores definitions and internal code of classes representing sequences
from enum import Enum
from dataclasses import dataclass
MAX_LED = 300
MAX_APS = 100
class ARGBEX_BASE():
    construction_types = []

def snapNearest(self, value, less, more):
        less_dist = value - less
        more_dist = more - value
        
        if less_dist <= more_dist:
            return less
        elif less_dist > more_dist:
            return more_dist

def MergeTimelines(timeline_a, timeline_b, step = 0):
    # We expect that timeline_a is properly fit into the step system
    for key in timeline_b.keys():
        val_copy = timeline_b[key]
        key = int(key) # Ensure we're working with ints

        if key % step != 0: #We need to snap to nearest
            less = (key // step) * step
            more = less + step
            key = snapNearest(key, less, more) # Snap to nearest timestamp
        
        try:
            led_setup: TimelineData = timeline_a[key]
            # If this hasn't failed this means that something is already there, we need to merge by TimelineData, which happens in that class
            
            led_setup.MergeWith(timeline_b[key]) #Merge the two TimelineDatas
        except KeyError:
            timeline_a[key] = val_copy
    


class Timeline():
    min_step = 0 #Minimum step (time it takes between actions), defined by maximum actions per second
    tmline: dict[int, str] = {}

    def __init__(self, max_aps):
        self.min_step = round(1/max_aps, 3) * 1000 #Adjust for miliseconds
        self.tmline = {}

    def addAction(self, timestamp: int, action: dict):
        #print(f"Adding {action}")
        unlocalized_action = {}
        for key in action.keys():
            unlocalized_action[int(key + timestamp)] = action[key] # Shift the actions to fit the timeline when we actually called it

        MergeTimelines(self.tmline, unlocalized_action, self.min_step)
    
    def GetFullTimeline(self):
        timeline_copy = self.tmline.copy()

        for key in timeline_copy.keys():
            timeline_copy[key] = timeline_copy[key].GetDict()
        
        return timeline_copy


# SELECTORS
class Selector(ARGBEX_BASE):
    selection = None
    s_name = ""

    def __str__(self) -> str:
        return self.__repr__()
    
    def __repr__(self) -> str:
        return f"SELECTOR<{self.s_name}>"



class All(Selector):
    s_name = "All"
    def __init__(self):
        self.selection = list(range(1, MAX_LED + 1))


class Checker(Selector):
    s_name = "Checker"
    construction_types = ["int", "int", "int"]

    def __init__(self, start_from, led_selected, led_distance):
        self.selection = []
        i = 0
        while(True):

            start = start_from + led_distance * i
            end = start_from + led_selected + led_distance * i
            #print(end)
            if start >= MAX_LED:
                break
            if end >= MAX_LED:
                end = MAX_LED
                break
            self.selection.extend(list(range(start,  end)))
            i += 1
            start_from = end

class ID(Selector):
    s_name = "ID"
    construction_types = ["int"]
    def __init__(self, id_):
        self.selection = []
        i = 0
        for _ in range(len(id_)):
            if id_[i] > MAX_LED:
                del id_[i]
            else:
                i += 1

        self.selection = list(map(int, id_))

class Range(Selector):
    s_name = "Range"
    construction_types = ["int", "int"]
    def __init__(self, start:int, end:int):
        self.selection = []
        if end > MAX_LED:
            end = MAX_LED
        self.selection = list(range(start, end+1))


#COLOR SPECIFIERS
class ColorData(ARGBEX_BASE):
    red, green, blue = 0, 0, 0
    construction_types = ["int", "int", "int"]

    def __init__(self, red: int, green: int, blue: int):
        self.red = red
        self.green = green
        self.blue = blue

        self.ClampColors()
    
    def ClampColors(self):
        if self.red > 255:
            self.red = 255
        if self.green > 255:
            self.green = 255
        if self.blue > 255:
            self.blue = 255
    
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return f"<R: {self.red}, G: {self.green}, B: {self.blue}>"

class Color(ColorData):
    timeframe = {} # Specifies what color happens at what time, used for color shifting, here it's static so it'll be timeframe[0] and only thiss
    
    def __init__(self, red, green, blue):
        timeframe = {}
        self.red = red
        self.green = green
        self.blue = blue

        self.ClampColors()
    
    
    def ComputeTimeframe(self): #Overriden in ColorShift
        t = TimelineData()
        t.color = self
        self.timeframe[0] = t
        return

    def GetTimeframe(self):
        if not self.timeframe:
            self.ComputeTimeframe()
        return self.timeframe

class ColorShift(Color):
    colorStart: ColorData = None
    colorEnd: ColorData = None
    time = None
    operations: int = None
    shiftTime: int = None
    construction_types = ["ColorData", "ColorData", "float"] # We can also create it with Color, makes us able to use the same syntax as regular color definition, we're not doing anything with the object either way
    def __init__(self, colorStart: ColorData, colorEnd: ColorData, time):
        self.timeframe = {}
        self.colorStart = colorStart
        self.colorEnd = colorEnd
        self.operations = time * MAX_APS  #This will give us how many operations do we need to perform
        self.shiftTime = 1000 / MAX_APS
        #print(f"Operations: {self.operations}")
    
    def __repr__(self):
        return f"<ColorShift R: {self.colorStart.red} -> {self.colorEnd.red}, G: {self.colorStart.green} -> {self.colorEnd.green}, B: {self.colorStart.blue} -> {self.colorEnd.blue} | Time: {self.operations / MAX_APS}>"
    
    def ComputeTimeframe(self):
        self.timeframe[0] = TimelineData(color=self.colorStart)

        st_red, st_green, st_blue = self.colorStart.red, self.colorStart.green, self.colorStart.blue
        end_red, end_green, end_blue = self.colorEnd.red, self.colorEnd.green, self.colorEnd.blue

        step_red = (end_red - st_red) / self.operations
        step_green = (end_green - st_green) / self.operations
        step_blue = (end_blue - st_blue) / self.operations

        #print(f"Steps {step_red}, {step_green}, {step_blue}")

        t_red, t_green, t_blue = st_red, st_green, st_blue

        red_values = []
        green_values = []
        blue_values = []

        while(abs(t_red - end_red) > abs(step_red)): # While the distance between start and end is greater than step, means we can still add to it and won't go above/below end value
            t_red += step_red
            red_values.append(round(t_red)) # We are rounding, because the color value is an integer. We're losing smoothness but nothing we can do about it

        while(abs(t_green - end_green) > abs(step_green)):
            t_green += step_green
            green_values.append(round(t_green)) 

        while(abs(t_blue - end_blue) > abs(step_blue)):
            t_blue += step_blue
            blue_values.append(round(t_blue))

        for i in range(max(len(red_values), len(green_values), len(blue_values))):
            try:
                red = red_values[i] # If we cannot get the value it means that we stopped tweening this color, so set this to end value
            except:                 # This only happens if precision errors caused the lists to be uneven, fear not as this is not a problem
                red = end_red
            
            try:
                green = green_values[i]
            except:
                green = end_green
            
            try:
                blue = blue_values[i]
            except:
                blue = end_blue
            
            

            last_time = list(self.timeframe.keys())[-1] # Keys represent the time (local time, it gets shifted when computed by other classes)
            #print(int(last_time + self.shiftTime))

            to_append = TimelineData(color=ColorData(red, green, blue))
            self.timeframe[int(last_time + self.shiftTime)] = to_append
    
        self.timeframe[int(self.operations * self.shiftTime)] = TimelineData(color=self.colorEnd)


class Tags(ARGBEX_BASE):
    construction_types = ["list"]
    tags = []
    def __init__(self, tags: list[str]):
        self.tags = [str(x).strip() for x in tags] #Ensure tags are in str, also strip


class TimelineData():
    selector: Selector = None
    color: ColorData = None
    
    led_dict = None
    def __init__(self, color = None, selector = None):
        self.color = color
        self.selector = selector
        self.led_dict = []

    def GetDict(self):
        #print(f'Getting dict for {self.selector} : {self.color}')
        if not self.led_dict:
            self.ComputeDict()
        return self.led_dict

    
    def ComputeDict(self):
        #print(f"Computing dict for {self}")
        all_leds = self.selector.selection

        temp_dict = {}
        for led in all_leds:
            temp_dict[led] = self.color
        
        self.led_dict = temp_dict
            
    
    def MergeWith(self, tdata):
        self.GetDict() # Just to be sure we have generated one

        other_dict = tdata.GetDict()

        ot_keys = list(other_dict.keys())
        for key in ot_keys:
            if int(key) in list(self.led_dict.keys()): #We have a duplicate
                del other_dict[key] # We have priority (totally not egoistic behaviour)
            else:
                self.led_dict[key] = other_dict[key] # If that doesn't exist copy
    
    def __repr__(self):
        return f"<TD [{self.selector}] -> [{self.color}]>"
    
    def __str__(self):
        return self.__repr__()



#ACTIONS
class Action(ARGBEX_BASE): # Base class for every predefined action or user-defined sequences
    selector: Selector = None
    color: Color = None
    tags = None

    timeline = None
    construction_types = ["Selector", "Color", "Tags"]
    act_name = ""

    def __init__(self, selector, color, tags):
        self.tags = tags
        self.selector = selector
        self.color = color
        self.timeline = {}


    def GetTimeline(self):
        if self.timeline:
            return self.timeline
        else:
            print(f"Computing timeline for {self}")
            self.ComputeTimeline()
            #print(self.timeline)
            return self.timeline
        
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return f"ACTION<{self.act_name} {self.selector} -> {self.color} , TAGS: {self.tags}>"


# Static led change without any animations performed
class Static(Action):
    act_name = "STATIC"
    def ComputeTimeline(self):
        color_timeline = self.color.GetTimeframe()
        #No movement timeline, this is static
        for key in color_timeline.keys():
            old = color_timeline[key]
            color_timeline[key] = TimelineData(old.color, self.selector) #Now we're filling the TimelineData objects at every frame with our selection, again, this is static

        #for key in color_timeline.keys(): #Convert to simple dictionaries of {ledID : ColorData}
        #    color_timeline[key] = color_timeline[key].GetDict()
        #Don't convert now, do it later
        
        self.timeline = color_timeline
        #print(self.timeline[10])
        #print("Timelinetest")
        #print(self.timeline)

class UserDefinedSequence():
    name = ""
    ud_parameters = None
    actions_raw: list = None
    all_sequence_definitions: dict = None


    def __init__(self, name, parameters, sequences):
        self.name = name
        self.ud_parameters = [str(x) for x in parameters]
        self.all_sequence_definitions = sequences
        self.actions_raw = []

    def addActionRaw(self, action: list):
        self.actions_raw.append(action)

    def ReplaceVarsInActionRaw(self, action, values): # action argument is mutable, but it may contain immutable tuples, which is a problem. We need to re-construct it from scratch :sob:
        name, params = action # Unpack
        #print(f"Replace {action}, {self.ud_parameters} -> {values}")
        
        for i in range(len(params)):

            if type(params[i]) == tuple: # Function in function type scenario, similar to what happens in Objectify()
                self.ReplaceVarsInActionRaw(params[i], values)
            else:
                for j in range(len(self.ud_parameters)):
                    if params[i] == self.ud_parameters[j]:
                        #print(f"Replacing {params[i]} with {values[j]}")
                        params[i] = values[j] # Replace the var

        return name, params

    
    def GetTimeline(self, parameters): # This is always computed at runtime, since we can use different variables
        if len(parameters) != len(self.ud_parameters):
            raise RuntimeError(f"Wrong amount of numbers passed {parameters}, {self.ud_parameters}")
        
        actions = self.actions_raw.copy() # Important that we don't touch the list in this class

        from argbex_parser import Objectify as Obj

        if len(self.ud_parameters):
            for i in range(len(actions)):
                actions[i] = self.ReplaceVarsInActionRaw(actions[i], parameters) #This will turn it into ready to process objects :) [hopefully, the bugs are killing me]

        for i in range(len(actions)):
                actions[i] = Obj(actions[i], self.all_sequence_definitions) #This will turn it into ready to process objects :) [hopefully, the bugs are killing me]  
        
        #TODO: Process the objects and return a timeline, and this should be it!

        return actions


class Wait(ARGBEX_BASE):
    construction_types = ["float"]
    wait = 0
    def __init__(self, time):
        self.wait = time

    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return f"ACTION<WAIT {self.wait}>"


def getglobals():
    return globals()

#Need this for Objectify
int = int
float = float
#a = Color(2, 10, 0)
#print(a.GetTimeframe()[0].green)

#p = ColorShift(ColorData(0, 0, 0), ColorData(255, 10, 255), 2)
#print(p.GetTimeframe())
#print(p.GetTimeframe()[0])