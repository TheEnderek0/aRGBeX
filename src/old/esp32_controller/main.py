# Boot.py handles connecting to the internet

from socket import socket, SOCK_STREAM, getaddrinfo
from struct import pack, unpack
from time import time_ns
from select import select
import esp_cfg as V
from time import sleep
from machine import Pin
import neopixel
from gc import collect

OUTPUT_PIN = 27
LIGHTSTRIP_SIZE = const(300)
np = neopixel.NeoPixel(Pin(OUTPUT_PIN), 300)
p_int_led = Pin(2, Pin.OUT)

SOCKET_TIMEOUT = 2
MAX_TIMEOUTS = 3


s: socket = None


def ConnectToServer():
    for ip in V.SERVER_IP:
        print(f"Trying to connect to: {ip}")
        a_info = getaddrinfo(ip, V.SERVER_PORT, 0, SOCK_STREAM)[0][-1]

        soc = socket()
        soc.settimeout(SOCKET_TIMEOUT)
        try:
            soc.connect(a_info)
            print("Connection established.")
            global s
            s = soc
            return
        except:
            soc.close() # Close the socket
            continue # Try to connect to other server
    raise RuntimeError("Error when trying to connect to the server!")

@micropython.native
def RunClient():
    timeouts: int = 0
    while True:
        try:
            t_start: int = time_ns()
            s.send(bytearray(pack("B", 20))) # Send a signal that we're ready to receive the next data packet
            #print("Sent packet!")
            ready_sockets, _, _ = select(
                [s], [], [], SOCKET_TIMEOUT
            )
            if ready_sockets:

                #data: bytes = s.recv(3 * LIGHTSTRIP_SIZE) # 3 bytes of color for each of lightstrip_size leds
                data = unpack("BBB" * LIGHTSTRIP_SIZE, s.recv(3 * LIGHTSTRIP_SIZE)) # do this here to save on memory
                #print(f"Received data, latency WIFI {(time_ns() - t_start) / 1000000}")
                for i in range(300):
                    np[i] = (data[i], data[i + LIGHTSTRIP_SIZE], data[i + 2 * LIGHTSTRIP_SIZE])
                np.write()
                #print(f"Received data, latency SET {(time_ns() - t_start) / 1000000}")


            else:
                timeouts += 1
                if timeouts >= MAX_TIMEOUTS:
                    print("Server has timed out!")
                    BlinkLED()
        except OSError:
            print("Server has timed out!")
            BlinkLED()


def BlinkLED():
    while True:
        p_int_led.value(0)
        sleep(1)
        p_int_led.value(1)
        sleep(1)

def Main():
    ConnectToServer()
    collect() # Run garbage collection, makes sure we have as much memory as we can before we attempt server <-> esp comms
    # Fire up them leds, but not yet, for now only use the internal led to singalize that esp32 has successfully connected to the server
    p_int_led.value(1)
    RunClient()



Main()