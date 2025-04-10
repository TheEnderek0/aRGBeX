# Used when you don't have access to a lightstrip or just want to quickly test the animation
from socket import socket
from struct import pack, unpack
import pyglet
from select import select

MAX_APS = 50
LIGHTSTRIP_SIZE = 300
SERVER_IP = "192.168.0.31"
PORT = 1000
WINDOW_SIZE_HORIZONTAL = 2560 # Change this if you have a smaller monitor!
WINDOW_SIZE_VERTICAL = 200


s = socket()
print("Trying to connect...")
try:
    s.connect((SERVER_IP, PORT))
except:
    raise RuntimeError("Error when trying to connect to the server!")

print("Connected!")

window = pyglet.window.Window(WINDOW_SIZE_HORIZONTAL, WINDOW_SIZE_VERTICAL)

class Pixels():
    def __init__(self, size):
        self.size = size
        self.shapes: list[pyglet.shapes.Rectangle] = []
        self.batch = pyglet.graphics.Batch()

        max_pix_size = WINDOW_SIZE_HORIZONTAL // size
        for i in range(size):
            shape = pyglet.shapes.Rectangle(max_pix_size * i + max_pix_size // 2, max_pix_size, max_pix_size - 1, max_pix_size, color=(0, 0, 0), batch=self.batch)
            self.shapes.append(shape)
    
pixs = Pixels(LIGHTSTRIP_SIZE)


def RunClient():
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
            pixs.shapes[i].color = (data[i], data[i + LIGHTSTRIP_SIZE], data[i + 2 * LIGHTSTRIP_SIZE])
    else:
        print('No data')
    #sleep_ms(9) #Honestly run as fast as you can

@window.event
def on_draw():
    RunClient()
    window.clear()
    pixs.batch.draw()

pyglet.app.run()