#Stores definitions and internal code of classes representing sequences
from globals_def import MAX_APS, LIGHTSTRIP_SIZE
from random import randint
class ARGBEX_BASE():
    construction_types = []

def snapNearest(value, less, more):
        less_dist = value - less
        more_dist = more - value
        
        if less_dist <= more_dist:
            return less
        elif less_dist > more_dist:
            return more_dist

def MergeTimelines(timeline_a, timeline_b, step = int(1000 / MAX_APS)):
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
        self.name = ""

    def addAction(self, timestamp: int, action: dict):
        #print(f"Adding {action.keys()}")
        unlocalized_action = {}
        for key in action.keys():
            unlocalized_action[int(key + timestamp)] = action[key] # Shift the actions to fit the timeline when we actually called it

        MergeTimelines(self.tmline, unlocalized_action, self.min_step)
    
    def GetFullTimeline(self):
        timeline_copy = self.tmline.copy()

        for key in timeline_copy.keys():
            timeline_copy[key] = timeline_copy[key].GetDict()
        
        timeline_copy = dict(sorted(timeline_copy.items())) #Sort the list by keys
        
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
        self.selection = list(range(1, LIGHTSTRIP_SIZE + 1))


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
            if start >= LIGHTSTRIP_SIZE:
                break
            if end >= LIGHTSTRIP_SIZE:
                end = LIGHTSTRIP_SIZE
                break
            self.selection.extend(list(range(start + 1,  end + 1)))
            i += 1
            start_from += led_selected

class ID(Selector):
    s_name = "ID"
    construction_types = ["int"]
    def __init__(self, id_):
        self.selection = []
        i = 0
        for _ in range(len(id_)):
            if id_[i] > LIGHTSTRIP_SIZE:
                del id_[i]
            else:
                i += 1

        self.selection = list(map(int, id_))

class Range(Selector):
    s_name = "Range"
    construction_types = ["int", "int"]
    def __init__(self, start:int, end:int):
        self.selection = []
        if end > LIGHTSTRIP_SIZE:
            end = LIGHTSTRIP_SIZE
        self.selection = list(range(start, end+1))

class Random(Selector):
    s_name = "Random"
    construction_types = ["int", "Tags"]
    def __init__(self, max_leds, tags):
        self.selection = []
        
        for i in range(max_leds):
            randitm = randint(1, LIGHTSTRIP_SIZE)
            if not randitm in self.selection:
                self.selection.append(randitm)
        
        if "Sorted" in tags:
            self.selection.sort()



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
 
    def __init__(self, red, green, blue):
        self.timeframe = {} # Specifies what color happens at what time, used for color shifting, here it's static so it'll be timeframe[0] and only thiss
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
        return self.timeframe.copy() #Return a copy to dissallow modification

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


class ColorRand(Color):
    construction_types = []

    def __init__(self):
        self.timeframe = {}
        self.red = 0
        self.green = 0
        self.blue = 0

    def ComputeTimeframe(self):
        self.red = randint(0, 255)
        self.blue = randint(0, 255)
        self.green = randint(0, 255)

        t = TimelineData()
        t.color = self
        self.timeframe[0] = t
        return  

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
        return self.led_dict.copy() #Dissallow modification

    
    def ComputeDict(self):
        #print(f"Computing dict for {self}")
        all_leds = self.selector.selection

        temp_dict = {}
        for led in all_leds:
            temp_dict[led] = (self.color.red, self.color.green, self.color.blue) # Make a tuple, saves us a hassle later on, we don't need the additional color wrapper after this function
        
        self.led_dict = temp_dict
            
    
    def MergeWith(self, tdata):
        self.GetDict() # Just to be sure we have generated one

        other_dict = tdata.GetDict()

        ot_keys = list(other_dict.keys())
        for key in ot_keys:
            #if int(key) in list(self.led_dict.keys()): #We have a duplicate
            #    self.led_dict[key] = other_dict[key] # We have priority (totally not egoistic behaviour)
            #else:
            
            #After consideration this code was scrapped and the priority was reversed, later defined actions override the ones in the background
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
            return self.timeline.copy()
        else:
            #print(f"Computing timeline for {self}")
            self.ComputeTimeline()
            #print(self.timeline)
            return self.timeline.copy()
        
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

class Slide(Action):
    act_name = "SLIDE"
    construction_types = ["Selector", "Color", "float", "Tags"]

    def __init__(self, selector, color, time, tags):
        self.tags = tags
        self.selector = selector
        self.color = color
        self.timeline = {}
        self.time = time

        #Enums
        self.single = 0
        self.multi = 1


    def ComputeTimeline(self):
        color_timeline: dict[int, TimelineData] = self.color.GetTimeframe()

        mode = -1 #Unset

        if "Single" in self.tags:
            mode = self.single
        
        if "Multi" in self.tags:
            if mode != -1:
                raise RuntimeError("Only Multi *or* Single tags can be specified at once!")
            else:
                mode = self.multi
        
        if mode == self.single:

            selection_leds = len(self.selector.selection)

            operations = int(self.time * MAX_APS)  #This will give us how many operations do we need to perform
            shiftTime = 1000 / MAX_APS
            leds_per_step = selection_leds / operations
            old_timeline_keys = list(color_timeline.keys())
            old_color = None

            selection:list = self.selector.selection.copy()

            if "Reversed" in self.tags:
                selection.reverse()

            selector = None

            last_ind = 0
            for step in range(operations + 1):
                timekey = int(round(step * shiftTime))
                if timekey == 0 and timekey not in old_timeline_keys:
                    raise RuntimeError("Internal error in Slideaction, timekey = 0 but  no key found!")
                
                if timekey in old_timeline_keys: # If we have a color on that timeframe we can copy it to be compatible with ColorShift
                    old_color = color_timeline[timekey].color
                
                selected_leds = int(round(leds_per_step * step))
                
                selector = Selector()
                selector.selection = selection[0:selected_leds + 1]

                color_timeline[timekey] = TimelineData(old_color, selector)

                loop_until = 0
                for tmframe in old_timeline_keys:
                    if tmframe < timekey:
                        loop_until = old_timeline_keys.index(tmframe)
                        break
                
                for j in range(last_ind, loop_until): # Append this selector to frames that happened between our animation frames
                    k = old_timeline_keys[j]
                    if color_timeline[k].selector == None:
                        color_timeline[k].selector = selector

                
                last_ind = loop_until
            
            # Append last selector to remaining frames
            loop_from = 0
            for tmframe in old_timeline_keys:
                    if tmframe == timekey: # Timekey is last timekey, when we exited the loop
                        loop_from = old_timeline_keys.index(tmframe)
            
            for key in old_timeline_keys[loop_from + 1:]:
                if color_timeline[key].selector == None:
                    color_timeline[key].selector = selector 





            self.timeline = color_timeline




class UserDefinedSequence():

    def __init__(self, name, parameters, sequences):
        self.name = name
        self.ud_parameters = [str(x) for x in parameters]
        self.all_sequence_definitions = sequences
        self.actions_raw = []

    def addActionRaw(self, action: list):
        self.actions_raw.append(action)

    def ReplaceVarsInActionRaw(self, action, values, previous_uds: set[str] = set()): # action argument is mutable, but it may contain immutable tuples, which is a problem. We need to re-construct it from scratch :sob:
        name, params = action # Unpack
        #print(f"Replace {action}, {self.ud_parameters} -> {values}")
        previous_uds |= set([self.name]) # Have to make it a list so the set() doesn't split it into separate letters
        #Dissallow self-reference
        #if name in previous_uds: #TODO: check why this errors out even when not referencing
        #    raise RuntimeError(f"Self reference inside of user defined sequences is not allowed! Sequence {self.name}")
        #This is because there's no actual way for us to exit this recursing loop, sequences are basic pre-defined actions, they don't have any real logic like variables inside

        for i in range(len(params)):

            if type(params[i]) == tuple: # Function in function type scenario, similar to what happens in Objectify()
                self.ReplaceVarsInActionRaw(params[i], values)
            else:
                for j in range(len(self.ud_parameters)):
                    if params[i] == self.ud_parameters[j]:
                        #print(f"Replacing {params[i]} with {values[j]}")
                        params[i] = values[j] # Replace the var

        return name, params

    
    def GetTimeline(self, parameters, previous_uds: set[str] = set()): # This is always computed at runtime, since we can use different variables
        if len(parameters) != len(self.ud_parameters):
            raise RuntimeError(f"Wrong amount of numbers passed {parameters}, {self.ud_parameters}, {self}")
        
        actions = self.actions_raw.copy() # Important that we don't touch the list in this class

        from argbex_parser import Objectify as Obj

        #if len(self.ud_parameters): # Unfortunately we have to check for parameters every time, since that function also checks for self-references and looping references
        for i in range(len(actions)):
            actions[i] = self.ReplaceVarsInActionRaw(actions[i], parameters, previous_uds)

        for i in range(len(actions)):
                actions[i], inside_params = Obj(actions[i], self.all_sequence_definitions) #This will turn it into ready to process objects :) [hopefully, the bugs are killing me]  
        
        timeline_final = None
        time_offset = 0
        this_timeline = None
        for i in range(len(actions)):
            #print(f'{self.name} = {time_offset}')
            if type(actions[i]) == Wait: # Handle specially
                time_offset += int(actions[i].wait) # Add offset and skip element
                continue
            
            if type(actions[i]) == UserDefinedSequence:
                this_timeline = actions[i]
                this_timeline = this_timeline.GetTimeline(inside_params, previous_uds).copy() # Convert sequences to timelines
            else:
                this_timeline = actions[i].GetTimeline().copy()

            #print(this_timeline.keys())


            
            if time_offset: #Minor optimization, don't do this if offset == 0
                this_timeline_keys = list(this_timeline.keys())
                timeline_copy = {}
                for key in this_timeline_keys:
                    temp_tmline = this_timeline[key] # Store the led data
                    timeline_copy[int(key + time_offset)] = temp_tmline
                
                this_timeline = timeline_copy


            if not timeline_final: #First timeline will be the base one
                timeline_final = this_timeline.copy() #Appearently python stores some shit as reference here and when the second last line of code in the loop above
                continue                              # gets called it also deletes the same key from timeline_final. Fuck you python

            MergeTimelines(timeline_final, this_timeline)
            
        #print(timeline_final)
        return timeline_final


class Wait(ARGBEX_BASE):
    construction_types = ["float"]
    wait = 0
    def __init__(self, time):
        self.wait = time * 1000 #Adjust for miliseconds

    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return f"ACTION<WAIT {self.wait} ms>"


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