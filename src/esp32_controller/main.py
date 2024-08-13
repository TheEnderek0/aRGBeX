# Boot.py handles connecting to the internet

from socket import socket
from struct import pack, unpack
from time import sleep_ms, time_ns
from select import select
import esp_cfg as V
from machine import Pin
import neopixel
from micropython import mem_info

OUTPUT_PIN = 27
LIGHTSTRIP_SIZE = 300

s = socket()
print("Trying to connect...")
try:
    s.connect((V.SERVER_IP, V.SERVER_PORT))
except:
    raise RuntimeError("Error when trying to connect to the server!")

print("Connected!")
# Fire up them leds, but not yet, for now only use the internal led to singalize that esp32 has successfully connected to the server
p_int_led = Pin(2, Pin.OUT)
p_int_led.value(1)

np = neopixel.NeoPixel(Pin(OUTPUT_PIN), 300)

def RunClient():
    while True:
        t_start = time_ns()
        s.send(bytearray(pack("B", 20))) # Send a signal that we're ready to receive the next data packet
        #print("Sent packet!")
        timeout = 2  # in seconds
        ready_sockets, _, _ = select(
            [s], [], [], timeout
        )
        if ready_sockets:
            data = s.recv(3 * LIGHTSTRIP_SIZE) # 3 bytes of color for each of lightstrip_size leds
            data = unpack("BBB" * LIGHTSTRIP_SIZE, data)
            for i in range(300):
                np[i] = (data[i], data[i + LIGHTSTRIP_SIZE], data[i + 2 * LIGHTSTRIP_SIZE])
            np.write()
            #mem_info()
            print(f"Received data, latency {(time_ns() - t_start) / 1000000}")
        else:
            print('No data')

        #sleep_ms(9) #Honestly run as fast as you can

RunClient()



