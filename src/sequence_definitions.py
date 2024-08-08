#Stores definitions and internal code of classes representing sequences
from enum import Enum

MAX_LED = 300
MAX_APS = 100
BUILTIN_SEQUENCES = ["static"]
class Sequence():
    name = ""
    parameters = []
    actions = {}
    act_ind = 0

    def __init__(self, decl: tuple[str, list[str]]):
        self.name = decl[0]
        self.parameters = decl[1]

    def addActionLine(self, line):
        self.actions[self.act_ind] = line
        self.act_ind += 1


class Action():
    led_ids = []
    colors = []

    def __init__(self, leds: list, color: list):
        if len(leds) != len(color):
            raise RuntimeError(f"Error in object Action, LED: {str(leds)}, \n Color: {str(color)}")
        
        self.led_ids = leds
        self.colors = color

class Timeline():
    min_step = 0 #Minimum step (time it takes between actions), defined by maximum actions per second
    tmline: dict[int, str] = {}

    def __init__(self, max_aps):
        self.min_step = round(1/max_aps, 3) * 1000 #Adjust for miliseconds
    
    def snapNearest(self, value, less, more):
        less_dist = value - less
        more_dist = more - value
        
        if less_dist <= more_dist:
            return less
        elif less_dist > more_dist:
            return more_dist

    def addAction(self, timestamp, action:  Action):
        if timestamp % self.min_step == 0: # This action fits perfectly on the timestamp
            tstmp = timestamp
        else:
            less = (timestamp // self.min_step) * self.min_step
            more = less + self.min_step
            tstmp = self.snapNearest(timestamp, less, more) # Snap to nearest timestamp
        self.tmline[tstmp] = action

class OperandType(Enum):
    SELECTOR = 1

# SELECTORS
class Selector():
    op_type = OperandType.SELECTOR
    selection = []
    valid = True
    s_name = ""

    def __str__(self) -> str:
        return self.__repr__()
    
    def __repr__(self) -> str:
        return f"SELECTOR<{self.s_name}>"



class All(Selector):
    s_name = "All"
    def __init__(self, *args):
        self.selection = list(range(1, MAX_LED + 1))

class Checker(Selector):
    s_name = "Checker"
    def __init__(self, *args):
        if len(args) != 3:
            self.valid = False
            return None
        start_from, led_selected, led_distance = args[0], args[1], args[2]
        i = 0
        while(True):
            start = start_from + led_distance * i
            end = start_from + led_selected + led_distance * i
            print(end)
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
    def __init__(self, *args):
        if len(args) != 1:
            self.valid = False
            return None
        id_ = args[0]
        i = 0
        for _ in range(len(id_)):
            if id_[i] > MAX_LED:
                del id_[i]
            else:
                i += 1

        self.selection = list(map(int, id_))

class Range(Selector):
    s_name = "Range"
    def __init__(self, *args):
        if len(args) != 2:
            self.valid = False
            return None
        
        start, end = args[0], args[1]
        if end > MAX_LED:
            end = MAX_LED
        self.selection = list(range(start, end+1))
    

class ColorData():
    red, green, blue = 0, 0, 0
    def __init__(self, red: int, green: int, blue: int):
        if red > 255:
            self.red = 255
        if green > 255:
            self.green = green % 255
        if blue > 255:
            self.blue = blue % 255
        
        self.red = red
        self.green = green
        self.blue = blue
    
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return f"<R: {self.red}, G: {self.green}, B: {self.blue}>"

class Color(ColorData):
    timeframe = {} # Specifies what color happens at what time, used for color shifting, here it's static so it'll be timeframe[0] and only this

    def ComputeTimeframe(self): #Overriden in ColorShift
        self.timeframe[0] = self
        return

    def GetTimeframe(self):
        if not self.timeframe:
            self.ComputeTimeframe()
        return self.timeframe

class ColorShift(Color):
    colorStart: ColorData = None
    colorEnd: ColorData = None
    operations: int = None
    shiftTime: int = None

    def __init__(self, colorStart: ColorData, colorEnd: ColorData, time):
        self.colorStart = colorStart
        self.colorEnd = colorEnd
        self.operations = time * MAX_APS  #This will give us how many operations do we need to perform
        self.shiftTime = 1000 / MAX_APS
        print(f"Operations: {self.operations}")
    
    def __repr__(self):
        return f"<ColorShift R: {self.colorStart.red} -> {self.colorEnd.red}, G: {self.colorStart.green} -> {self.colorEnd.green}, B: {self.colorStart.blue} -> {self.colorEnd.blue} | Time: {self.operations / MAX_APS}>"
    
    def ComputeTimeframe(self):
        self.timeframe[0] = self.colorStart # Always start at the starting color

        st_red, st_green, st_blue = self.colorStart.red, self.colorStart.green, self.colorStart.blue
        end_red, end_green, end_blue = self.colorEnd.red, self.colorEnd.green, self.colorEnd.blue

        step_red = (end_red - st_red) / self.operations
        step_green = (end_green - st_green) / self.operations
        step_blue = (end_blue - st_blue) / self.operations

        print(f"Steps {step_red}, {step_green}, {step_blue}")

        t_red, t_green, t_blue = st_red, st_green, st_blue

        red_values = []
        green_values = []
        blue_values = []

        while(abs(t_red - end_red) > step_red): # While the distance between start and end is greater than step, means we can still add to it and won't go above/below end value
            t_red += step_red
            red_values.append(round(t_red)) # We are rounding, because the color value is an integer. We're losing smoothness but nothing we can do about it

        while(abs(t_green - end_green) > step_green):
            t_green += step_green
            green_values.append(round(t_green)) 

        while(abs(t_blue - end_blue) > step_blue):
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
            self.timeframe[last_time + self.shiftTime] = ColorData(red, green, blue)

        


# Static led change without any animations performed
class Static():
    selector = None
    color = None


    def __init__(self, selector, color, params: list):
        
        selector = selector.lower()

        if selector == "all":
            self.selector = All()
        
        elif selector == "checker":
            self.selector = Checker(params[0], params[1], params[2])
        
        elif selector == "id":
            self.selector = ID(params[0])


SELECTORS = {
    "all": All,
    "checker": Checker,
    "range": Range,
    "id": ID,

}

#a = Color(2, 10, 0)
#print(a.GetTimeframe()[0].green)

#p = ColorShift(ColorData(0, 0, 0), ColorData(255, 10, 255), 2)
#print(p.GetTimeframe())
#print(p.GetTimeframe()[0])