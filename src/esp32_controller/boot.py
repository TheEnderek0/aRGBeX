import network
import webrepl
from time import sleep
import esp_cfg as V
from machine import freq

wifi = (V.WIFI_SSID, V.WIFI_PASSWORD)

freq(240000000) # Run at 240MHz, fastest you can go

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.ifconfig((V.ESP_Static_IP, V.WIFI_Subnet, V.WIFI_Gateway, V.WIFI_Gateway))
print("Connecting to " + str(wifi), end=" ")
wlan.connect(*wifi)

while not wlan.isconnected():
    print(".", end="")
    sleep(1)

print("\nStarting webrepl...")
webrepl.start()