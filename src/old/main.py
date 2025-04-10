# Main script for aRGBeX


from sys import argv, exit
from pathlib import Path
import argbex_parser as parser
from sequence_definitions import Timeline
from struct import pack, unpack
from server_mgr import CurrentSong, ServerManager
from threading import Lock, Event
from time import sleep, time
import lzma

from globals_def import MAX_APS, LIGHTSTRIP_SIZE

DEFAULT_PRESET_PATH = "./presets/"
GENERATED_FILES_PATH = "generated" # Relative to default preset path

def Settings():
    try:
        presets_dir = argv.index("--presets_dir")
        presets_dir = argv[presets_dir + 1]
    except:
        presets_dir = DEFAULT_PRESET_PATH
    
    presets_dir = Path(presets_dir)
    print(f"Using preset path '{presets_dir}'")

    only_generate = "--only_compile" in argv
    only_server = "--only_server" in argv
    
    if only_generate and only_server:
        raise RuntimeError("Invalid arguments passed, --only_compile and --only_server cannot be specified together!")
    
    try:
        fl = argv.index("--play_id")
        fl = argv[fl + 1]
    except:
        fl = None

    return presets_dir, only_generate, only_server, fl


def main():
    presets_dir, only_generate, only_server, run_file = Settings()

    if not presets_dir.exists():
        raise RuntimeError(f"Specified presets_dir {presets_dir} does not exist!")

    if not only_server: # Compile .argbex files
        print("Compiling .argbex files!")
        CompileARGBEX(presets_dir)
    
    if not only_generate:
        print("Loading song animations...")
        cfg = LoadAllConfigs(presets_dir / "generated")
        print("Setting up server...")
        RunServer(cfg, run_file)


def LoadAllConfigs(dir: Path):
    files = list(dir.rglob("**/*.argbex_anim"))

    dick = {} #Hehe hihi haha
    dick["Generics"] = []

    for file in files:
        name = str(file.stem)
        cfg = LoadAnim(file)
        name = cfg["Song Name"]
        if name.lower() == "<generic>":
            dick["Generics"].append(cfg)
            continue
        
        dick[name] = cfg

    return dick



def RunServer(database, file_id:str = None):
    songdata = CurrentSong()
    song_changed_event = Event()

    if file_id:
        songdata.SetSong(file_id.lower())
        song_changed_event.set() # Register to notify the program that we've set a song/id to play
        songdata.latency = time()
    
    song_lock = Lock()

    server_mgr = ServerManager(database, song_lock, songdata, song_changed_event)
    
    if file_id:
        server_mgr.start() # Start everything up
        try:
            while True:
                sleep(10) #Lock itself, let other threads run
        except KeyboardInterrupt:
            print("Exiting")
            exit()
    else:
        from get_current_playing import GetCurrentlyPlaying

        started = False
        old_song = ""
        old_author = ""
        #sleeptime = 1/MAX_APS
        while True:

            try: # GetCurrentlyPlaying can sometimes fail when switching songs
                time_start = time()
                cur_song = GetCurrentlyPlaying()
                title, author = cur_song["title"].lower(), cur_song["author"].lower()
                #TODO: If possible find a better way to read currently playing media.
                #title, author = "360", "charli xcx"
                if old_song == title and old_author == author:
                    pass
                else: # Song changed
                    print(f"Trying to play: {title} by {author}")
                    with song_lock:
                        song_changed_event.set()
                        songdata.SetSong(title, author)
                        songdata.latency = time_start
                    old_song, old_author = title, author

                if not started:
                    server_mgr.start()
                    started = True
            except KeyboardInterrupt:
                exit()
            except:
                sleep(0.05) # Wait another frame to check the song
        




def CompileARGBEX(presets_dir: Path):
    all_src_files = list(presets_dir.rglob("**/*.argbex"))
    for i in range(len(all_src_files)):
        all_src_files[i] = all_src_files[i].resolve()
    
    generated_path = presets_dir.joinpath(GENERATED_FILES_PATH)
    
    for file in all_src_files:
        structure = GenerateStructure(file)
        new_path = generated_path.joinpath(str(file.stem) + ".argbex_anim")
        print(f"Saving {new_path}")
        SaveAnim(structure, new_path)




def GenerateStructure(filepath: Path):
    timeline = Timeline(MAX_APS)
    parser.ParseFile(filepath, timeline)
    parsed: dict[int, list[int, tuple[int, int, int]]] = timeline.GetFullTimeline()

    # Due to how the server works we have to send every led data every time, even if the color for that specific led hasn't changed

    parsed_timekeys = list(parsed.keys())
    previous_config = [(0, 0, 0)] * LIGHTSTRIP_SIZE  # By default, each led is turned off
    for key in parsed_timekeys:
        current_config = parsed[key]

        for i in range(1, LIGHTSTRIP_SIZE + 1):
            if not i in current_config.keys(): # Lightstrip config doesn't exist
                current_config[i] = previous_config[i - 1] # We can mis-match dict to list here
        
        current_config = dict(sorted(current_config.items())) #Since we're appending stuff here we have to sort

        current_config = [x[1] for x in current_config.items()] # Convert to list, we can omit the indexes here as they should be all filled in
        previous_config = current_config.copy() # Copy the list to previous config, just to be safe, and also store it so we can fill from that data now

        # Here we can also destroy the tuples and implement a filestructure ready to be sent over to the client via tcp_server.py
        temp_red, temp_green, temp_blue = [], [], []
        for item in current_config:
            temp_red.append(item[0])
            temp_green.append(item[1])
            temp_blue.append(item[2])
        
        temp_red.extend(temp_green)
        temp_red.extend(temp_blue)
        
        
        current_config = temp_red.copy() # Make sure to copy, temp red is going to be modified in the future
        parsed[key] = current_config

    d = {}
    n = timeline.name
    if "|" in n:
        name, artist = n.split("|")
    else:
        name, artist = n, ""

    d["Song Name"] = name
    if artist:
        d["Artist"] = artist
    
    d["Song Data"] = parsed

    return d

def SaveAnim(structure, filepath: Path):

    name = structure["Song Name"]
    artist = ""
    try:
        artist = structure["Artist"]
    except:
        pass

    

    songdata: dict[int, list[int]] = structure["Song Data"]


    with lzma.open(filepath, "wb") as file:
        file.write(pack("<B", len(name)))
        file.write(name.encode())

        file.write(pack("<B", len(artist)))
        if artist:
            file.write(artist.encode())

        for keyval in songdata.items():
            file.write(bytearray(pack("<I", int(keyval[0])))) # This is the timestamp
            file.write(bytearray(pack("<" + str(LIGHTSTRIP_SIZE * 3) + "B", *keyval[1]        ))) # This is the led configuration
            

def LoadAnim(filepath: Path):
    with lzma.open(filepath, "rb") as file:
        name = file.read(1)
        name = unpack("<B", name)[0]
        name = file.read(name) # Chars are 1 byte each
        name = name.decode()

        artist = file.read(1)
        artist = unpack("<B", artist)[0]
        if artist:
            artist = file.read(artist)
            artist = artist.decode()
        else:
            artist = ""

    d = {}
    d["Song Name"] = name
    d["Artist"] = artist
    d["Path"] = filepath
    return d


if __name__ == "__main__":
    main()