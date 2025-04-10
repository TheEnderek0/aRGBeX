# Library to acquire current song data
from sys import platform


api_mic = None
api_mic_stream = None


if platform == "linux":
    import get_song_playerctl as api
elif platform == "win32":
    import get_song_winrt as api

def EnableMic(LISTENING_DEVICE_NAME:str=None):
    """Enables the microphone api, that uses shazam, which (greatly) help to identify songs."""
    global api_mic, api_mic_stream
    import get_song_microphone as api_mic
    


def SongData() -> dict:
    """Retrieve song data in a form of dictionary"""
    data = {}
    if not ENABLE_MIC_MODE:
        raw_data = api.GetCurrentlyPlaying()
        data['title'] = raw_data['title']
        data['author'] = raw_data['author']
        data['timestamp'] = -1 # Not supported via this method

    return data


if __name__ == "__main__":
    ENABLE_MIC_MODE = False
    while True:
        input()
        print(SongData())