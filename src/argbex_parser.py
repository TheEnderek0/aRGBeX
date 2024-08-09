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
            #print(f"{name}, {str(params)}, {end}")
            current_sequence = name
            sequences_database[name] = SD.UserDefinedSequence(name, params, sequences_database)

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
            if "loop" in line: # LOOPS ARE NOT CURRENTLY SUPPORTED!
                loop_recursion += 1
            if "}" in line:
                if loop_recursion == 0:
                    parsemode = ParsingMode.SEQUENCES
                else:
                    seq = ("endloop", [])
                    sequences_database[current_sequence].addAction(seq)
                    #print(seq)
                    loop_recursion -= 1
            else:
                seq = FnFormatParser(line, line_id, True)
                sequences_database[current_sequence].addActionRaw(seq)
            
            continue
        

        #========================
        # PLAYBACK PARSING
        #========================
        
        if parsemode == ParsingMode.PLAYBACK:
            t, a = ParsePlayback(line, line_id)
            #print(f"playback t: {t} | a: {a}")
            a = FnFormatParser(a, line_id, True)
            if a[0] == "nothing":
                continue
            a, params = Objectify(a, sequences_database)
            #print(a)
            if a:
                if params: #If true we have a user defined sequence
                    a = a.GetTimeline(params) # Generate the dict of timeline

                timeline.addAction(t, a.GetTimeline()) # Add to timeline whatever we have
    
    #print(sequences_database)
    #print("SEQUENCES============")
    #print(sequences_database["s1"].actions_raw)
    #print(sequences_database["s1"].GetTimeline(["20"]))

    return timeline
        
def Objectify(line, user_defined_dict):
    try: # Errors can occur if somehow the data structure is wrong
        if type(line) == tuple: #We're processing a function declaration
            decl = line[0]
            params = line[1] # Line can have a third parameter but we're omitting that

            for i in range(len(params)):
                parameter = params[i]
                if type(parameter) == tuple: # Another function in this function
                    tempobj, _ = Objectify(parameter, user_defined_dict) # Replace with a processed object
                    if type(tempobj) == SD.UserDefinedSequence:
                        raise RuntimeError(f"Userdefined Sequences cannot be put inside other functions! Line: {line}")
                    params[i] = tempobj
            
            if not decl in SD.getglobals().keys():
                print(f"Decl {decl} not found!")
                return None

            # No more functions inside, process this one
            if decl in SD.getglobals().keys():
                user_seq = False
                decl_object = getattr(SD, decl)
                param_types:list = decl_object.construction_types

                process_tags = "Tags" in param_types
            elif decl in user_defined_dict.keys():
                user_seq = True
                process_tags = False
                decl_object: SD.UserDefinedSequence = user_defined_dict[decl]
                param_types = [None] * len(decl_object.ud_parameters) # This ensures the parameter amount checking still works correctly

            if process_tags:
                a_req_param = len(param_types) - 1
            else:
                a_req_param = len(param_types)
            a_given_param = len(params)
            
            if (a_req_param < a_given_param and not process_tags) or a_req_param > a_given_param: # Second one is not enough parameters, first one is no tags accepted but something specified
                
                raise RuntimeError(f"Wrong number of parameters passed to {line}: {len(param_types)} | {len(params)} | {process_tags}")

                
            if param_types.count(SD.Tags) > 0 and (param_types.count(SD.Tags) > 1 or param_types[-1] != SD.Tags):
                raise RuntimeError(f"Internal Error, class {decl} has wrongly defined construction_types (Tags)")
            
            parameters_to_pass = []
            #print(params)

            for i in range(a_req_param):
                
                temp = params[i]
                if not user_seq: # If we're working with user defined sequences, we're not converting datatypes
                    if not type(temp) == param_types[i] and not issubclass(type(temp), getattr(SD, param_types[i])): # Also check if the type is not a child of the thing we want to convert, 
                        temp = getattr(SD, param_types[i])(temp) #Convert type, at least try to                # because in that case it's pointless and problematic to do so
                    
                parameters_to_pass.append(temp)

                if process_tags and i == a_req_param - 1: #Ensure we are at the end, last param
                    tags = []
                    #print("Processing tags!")
                    if len(params) > a_req_param: # Ensure we actually have anything to be tagged
                        for j in range(len(params) - len(param_types) + 1):
                            tags.append(str(params[j+i + 1]))
                    parameters_to_pass.append(tags)
                #print(param_types[i])

            #After all this shit, return the object with proper parameters
            #print(f"Creating object {decl_object}")
            #print(parameters_to_pass)
            if not user_seq:
                obj = decl_object(*parameters_to_pass)
                parameters_to_pass = []

            return obj, parameters_to_pass
            

                


    except:
        raise RuntimeError(f"Data structure {line} is invalid!")
        





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
        

if __name__ == "__main__":
    timeline = SD.Timeline(100)
    ParseFile(Path("presets/test.argbex"), timeline)
    #print(timeline.tmline)
    for keyval in timeline.GetFullTimeline().items():
        print(keyval)

