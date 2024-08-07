#Stores definitions and internal code of classes representing sequences

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


class Timeline():
    min_step = 0 #Minimum step (time it takes between actions), defined by maximum actions per second
    tmline: dict[int, str] = {}

    def __init__(self, max_aps):
        self.min_step = round(1/max_aps, 3) * 1000 #Adjust for miliseconds
        print(self.min_step)
    
    def snapNearest(self, value, less, more):
        less_dist = value - less
        more_dist = more - value
        
        if less_dist < more_dist:
            return less
        elif less_dist > more_dist:
            return more_dist

    def addAction(self, timestamp, action:str):
        if timestamp % self.min_step == 0: # This action fits perfectly on the timestamp
            tstmp = timestamp
        else:
            less = (timestamp // self.min_step) * self.min_step
            more = less + self.min_step
            tstmp = self.snapNearest(timestamp, less, more) # Snap to nearest timestamp
            print(f"less: {less}, more: {more}, tst: {tstmp}")
        self.tmline[tstmp] = action

