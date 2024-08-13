import socket
import struct
import select
import threading as T

# TCP SERVER CODE

class ColorFrameData():
    """Storage class that stores the pre-computed bytes of colors for each frame of led animation.

       WARNING: Use with Threading.Lock() when doing ColorData.bytes = something !
    """
    def __init__(self, color_bytes: bytes = None):
        if not color_bytes:
            arr = [0] * 900
            color_bytes = bytearray(struct.pack("BBB" * 300, *arr))
        self.bytes = color_bytes
    

class Server(T.Thread):
    '''
    A class that acts as a TCP server for the ESP32 to read from.

    It waits for a signal (a packet) from a client (esp32) containing at max 4 bytes of data (It doesn't actually read, it only waits for it).
    That packet is used to signalize that the esp32 is ready for another packet of data. 
    
    Then, the server sents the color data for every led.

    '''
    def __init__(self, color_data: ColorFrameData, color_data_lock: T.Lock, max_timeouts = 20, HOST = "", PORT = 1000):
        super().__init__()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((HOST, PORT))
        self.socket.listen(1)
        self.color_data = color_data
        self.color_data_lock = color_data_lock
        self.max_timeouts = max_timeouts



    def run(self):
        print("Starting TCP server...")
        while True: # If server exited we can restart it to wait for new client connection
            self.run_internal()

    
    def run_internal(self):
        try:
            client, cl_address = self.socket.accept()
            with client:
                print(f"Client connected: {cl_address}")
                timeouts = 0
                while True:
                    timeout = 2
                    ready_sockets, _, _ = select.select(
                        [client], [], [], timeout
                        )
                    if ready_sockets:
                        client.recv(4) # Receive the bytes, we don't do anything with them, treat them as a signal
                        #print("Data received!")
                        with self.color_data_lock: #Ensure thread safety
                            client.send(self.color_data.bytes)
                    else:
                        timeouts += 1
                        print("No response from client!")
                        if timeouts >= self.max_timeouts:
                            print("Restarting the server, no response from client!")
                            return
        except ConnectionAbortedError:
            return


if __name__ == "__main__": #Used for testing the speed and code and shit in general
    lock = T.Lock()
    arr = [255] * 300 + [255] * 300 + [255] * 300 
    data_transfer = ColorFrameData(bytearray(struct.pack("BBB" * 300, *arr)))

    server = Server(data_transfer, lock, max_timeouts=2)

    server.start()

            
            