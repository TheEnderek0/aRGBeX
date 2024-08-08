from pathlib import Path
from enum import Enum
import sequence_definitions as SD

SEQUENCE_ALLOWED_CHARS = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890"


class ParsingMode(Enum):
    NONE = 1
    SEQUENCES = 2
    PLAYBACK = 3
    SEQ_FN = 4
    SEQ_AWAIT_BRACKET = 5
    SEQ_SCH_END = 6


def ParseFile(path: Path, timeline: SD.Timeline):
    with open(path, "r") as preset:
        lines = preset.read().splitlines()
    
    parsemode = ParsingMode.NONE
    current_sequence = None
    sequences_database = {}

    

    line_id = -1
    loop_recursion = 0
    for line_ in lines:
        line = line_

        # Process the line stripping the comments and whitespaces
        try:
            commentid = line.index("//") # Search for comments
            line = line[:commentid] # Strip comments
        except ValueError:
            pass # No comments
        
        line = line.strip()
        # Line processed, we can now proceed to parse
        line_id += 1

        if line == "": # Skip empty lines
            continue

        if line.lower() == "<sequences>":
            parsemode = ParsingMode.SEQUENCES
            continue

        if line.lower() == "<playback>":
            parsemode = ParsingMode.PLAYBACK
            continue
        

        #========================
        # SEQUENCE PARSING
        #========================
        if parsemode == ParsingMode.SEQUENCES: # This means a function declaration, since we are outside one (mode defines this)
            parsemode = ParsingMode.SEQ_AWAIT_BRACKET
            name, params, end = FnFormatParser(line, line_id)
            print(f"{name}, {str(params)}, {end}")
            current_sequence = name
            sequences_database[name] = SD.Sequence((name, params, end))

            if "{" in end:
                parsemode = ParsingMode.SEQ_FN
            
            continue
        
        if parsemode == ParsingMode.SEQ_AWAIT_BRACKET:
            try:
                br_ind = line.index("{")
                line = line[br_ind + 1:]
                parsemode = ParsingMode.SEQ_FN
            except ValueError:
                raise(RuntimeError(f"No opening bracket found for function {name}"))
            #No continue keyword! We are immediatelly processing the line
        
        if parsemode == ParsingMode.SEQ_FN:
            if "loop" in line:
                loop_recursion += 1
            if "}" in line:
                if loop_recursion == 0:
                    parsemode = ParsingMode.SEQUENCES
                else:
                    seq = ("endloop", [])
                    sequences_database[current_sequence].addActionLine(seq)
                    print(seq)
                    loop_recursion -= 1
            else:
                seq = FnFormatParser(line, line_id, True)
                print(seq)
                sequences_database[current_sequence].addActionLine(seq)
            
            continue

        #========================
        # PLAYBACK PARSING
        #========================
        
        if parsemode == ParsingMode.PLAYBACK:
            t, a = ParsePlayback(line, line_id)
            print(f"playback t: {t} | a: {a}")
            a = FnFormatParser(a, line_id, True)
            a = ParseAction(a, line_id)
            if a:
                timeline.addAction(t, a)
    
    #print(sequences_database)
        

    
def ParseAction(adef, lineidx):
    try:
        main_func = adef[0].lower()
        if main_func == "nothing":
            return None
        elif main_func in SD.BUILTIN_SEQUENCES: # Every class uses pretty much the same beginning syntax (except for user defined functions), that is class(selector color <somethingelsemaybe>)
            selector = ParseSelector(adef[1][0])
            color = ParseColor(adef[1][1], lineidx)
            print(main_func)
            print(selector)
            print(color)
            exit()
    except:
        raise RuntimeError(f"Invalid syntax at line {lineidx}!")

def ParseSelector(selectorHeader):
    selector = selectorHeader[0]
    s_params = list(map(int, selectorHeader[1]))

    selector = SD.SELECTORS[selector.lower()](s_params)
    
    return selector


def ParseColor(colorHeader, lineidx):
            #COLOR PROCESSING
            color = colorHeader
            color_type = color[0].lower()
            color_params = color[1]
            if color_type == "c":
                red, green, blue = list(map(int, color_params))
                color = SD.Color(red, green, blue)
            elif color_type == "colorshift":
                colorstart = color_params[0]
                colorend = color_params[1]
                time = color_params[2]
                if colorstart[0].lower() != "c" or colorend[0].lower() != "c":
                    raise RuntimeError(f"Invalid syntax at line {lineidx}, color definition inside ColorShift!")
                
                cs_c = list(map(int, colorstart[1]))
                colorstart_class = SD.ColorData(cs_c[0], cs_c[1], cs_c[2])
                cs_e = list(map(int, colorend[1]))
                colorend_class = SD.ColorData(cs_e[0], cs_e[1], cs_e[2])
                time = int(time)
                color = SD.ColorShift(colorstart_class, colorend_class, time)
            
            return color
        




def ParsePlayback(line_: str, lineidx):
    line = line_.strip()

    res = line.split(" ")
    if len(res) < 2:
        raise RuntimeError(f"Syntax error at line {lineidx}")
    elif len(res) > 2:
        timestamp = line[:len(res[0])]
        action = line[len(res[0]) + 1:]
    else:
        timestamp, action = res

    t_res = timestamp.split(":")
    if len(t_res) != 3:
        raise RuntimeError(f"Invalid timestamp syntax at line {lineidx}")

    minutes, seconds, cs = map(int, t_res) #technically centiseconds lol

    seconds += minutes * 60
    cs += seconds * 100
    ms = cs * 10
    #Achieved time in ms

    return ms, action




def FnFormatParser(line_: str, lineidx, omit_end = False):
    line = line_
    line = line.strip() # Just in case

    class FnParser(Enum):
        NAME = 1
        PARAM = 2
        END = 3
    
    fn_name = ""
    params = []
    parsermode = FnParser.NAME # First we're parsing the name
    
    pidx = None
    idx = -1
    r_index = 0
    param = ""
    p_helper_len = 0
    for char in line:
        idx += 1

        if parsermode == FnParser.NAME and not char == "(":
            if char in SEQUENCE_ALLOWED_CHARS:
                fn_name += char
                continue
            else:
                raise(RuntimeError(f"Error on line {lineidx}, {char} is not allowed!"))


        if char == "(":
            r_index += 1
            if parsermode == FnParser.NAME:
                parsermode = FnParser.PARAM
            
            if r_index == 2:
                p_helper_len = len(param)
                param = ""
                pidx = idx
                
            
            continue
        
        if char == ")":
            r_index -= 1
            if r_index == 0:
                if param != "":
                    params.append(param)
                parsermode = FnParser.END
                break

            elif r_index == 1: # Almost at the end, parse this function
                param = ""
                fn = line[pidx - p_helper_len: idx + 1]
                #print(fn)
                params.append(FnFormatParser(fn, lineidx, omit_end))
            
            continue
        
        if char == " " and not r_index != 1:
            if param != "":
                params.append(param)
            param = ""
            continue
            
        #print(f"Char {char}, param {param}")
        param += char

                
        
    if parsermode == FnParser.PARAM or parsermode == FnParser.NAME:
        raise(RuntimeError(f"Invalid sequence syntax at line {lineidx}"))
    
    
    if not omit_end:
        return fn_name, params, line[idx + 1:]
    else:
        return fn_name, params
        


timeline = SD.Timeline(100)
ParseFile(Path("presets/test.argbex"), timeline)

