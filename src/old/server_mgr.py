# Manages the tcp server and animations
import threading as T
import tcp_server as ServerModule
from time import sleep, time
import lzma
from struct import unpack
from random import randint
from globals_def import GLOBAL_LATENCY, MAX_APS
import bisect

SLEEP_TIME = 1/MAX_APS

class CurrentSong():
    def SetSong(self, song, author = ""):
        self.song = song
        self.author = author
        self.latency = 0

class ServerManager(T.Thread):
    """ Manages the Server, reads current song playing from currentsong with song_playing_lock (When song_changed_event event is set).
    
    Generic scripts are keys of database that point to animations that aren't bound to specific songs and these play if the user plays a song that is not in the database (or the song ends)

    """
    def __init__(self, database: dict[str, dict[int, bytes]], song_playing_lock, currentsong: CurrentSong, song_changed_event, generic_scripts = []):
        super().__init__(daemon=True)
        self.database = database
        self.song_lock = song_playing_lock
        self.current_song_object = currentsong
        self.song_changed_event: T.Event = song_changed_event

        self.color_frame_lock = T.Lock()
        self.colordata = ServerModule.ColorFrameData()
        self.cur_song = ""
        self.cur_song_author = ""
        
        self.cur_song_playback = None
        self.cur_song_playback_keys = None
        self.cur_time = 0

    def GetPlayback(self, filep):
        with lzma.open(filep) as file:
            name = file.read(1)
            name = unpack("<B", name)[0]
            file.read(name) # Chars are 1 byte each
            artist = file.read(1)
            artist = unpack("<B", artist)[0] # We don't actually need this data, but we just need to set the cursor properly
            if artist:
                file.read(artist)
            
            # Now we can parse the timeframes
            dictus = {}
            while True:

                key = file.read(4)
                if key == b"":
                    break # We hit a stop, with a proper filestructure the key will be empty
                key = unpack("<I", key)[0]

                data = file.read(900) #We don't need to unpack anything here, because this will get sent straight to the server!
                dictus[key] = data
            
        return dictus
            

    def PlayGeneric(self):
        with self.song_lock:
            self.current_song_object.latency = time()
        self.song_changed_event.set()
        print("Song not found, animating generic")
        generics = self.database["Generics"]
        randm = randint(0, len(generics) - 1)

        selected = generics[randm]
        print(f"Playing {selected["Path"].stem}")

        pback = self.GetPlayback(selected["Path"])
        self.cur_song_playback = pback
        self.cur_song_playback_keys = list(pback.keys())


    
    def UpdateSongPlayback(self):
        name = self.cur_song
        author = self.cur_song_author
        #print(f"Trying to find {name} in {self.database.keys()}")
        try:
            playback = self.GetPlayback(self.database[name]["Path"])
            if "Artist" in playback.keys():
                if not author in self.database[name]:
                    self.PlayGeneric()
                    return
            
            print(f"Animating {name}")
            self.cur_song_playback = playback
            self.cur_song_playback_keys = list(playback.keys())
        

        except KeyError: # Song not found
            self.PlayGeneric()
        

    def UpdateSong(self):
        if self.song_changed_event.is_set():
            with self.song_lock:
                self.cur_song = self.current_song_object.song
                self.cur_song_author = self.current_song_object.author
            self.UpdateSongPlayback()
    
    def run(self):
        
        server = ServerModule.Server(self.colordata, self.color_frame_lock, 5)
        server.start() # Start the server

        lag = 0
        self.cur_time = 0
        while True:
            self.UpdateSong()
            if self.song_changed_event.is_set():
                with self.song_lock:
                    lag = self.current_song_object.latency * 1000
                    
                lag += GLOBAL_LATENCY
                self.song_changed_event.clear()


            try:
                self.cur_time = time() * 1000 - lag
                #print(f"Cur time: {self.cur_time}")
                ind = bisect.bisect_left(self.cur_song_playback_keys, self.cur_time) - 1 # Find nearest frame
                self.cur_song_playback_keys[ind + 1] # Try to check if we haven't ended the animation
                #print(ind)
                #print(f"Found nearest frame: {self.cur_song_playback_keys[ind]}, our time: {self.cur_time}")
                frame = self.cur_song_playback[     self.cur_song_playback_keys[ind]     ]
                #print("Frame!")
                with self.color_frame_lock:
                    self.colordata.bytes = frame # We are on the correct frame, set the color and let the server handle the rest
                sleep(SLEEP_TIME)

            except IndexError: # We are done with this animation, clear
                with self.song_lock:
                    self.current_song_object.SetSong("SongEnded")
                self.song_changed_event.set()
                sleep(1) # Let it rest for a bit, it is eepy, no but seriously this is just a delay between playing the generic animation, nothing else


