import network
import webrepl
from time import sleep
import esp_cfg as V
from machine import freq


freq(240000000) # Run at 240MHz, fastest you can go

def ConnectToWifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.ifconfig((V.ESP_Static_IP, V.WIFI_Subnet, V.WIFI_Gateway, V.WIFI_Gateway))
    for pair in V.WIFI_DICT:
        print("\nTrying to connect to: " + str(pair), end=" ")
        wlan.connect(*pair)
        for _ in range(V.TIMEOUT):
            if wlan.isconnected():
                print("\n Connected!")
                return 1

            print(".", end="")
            sleep(1)
        wlan.disconnect()
        

            
    #If the code reaches here it means we tried every combination and still couldn't connect to any wifi
    print("Couldn't connect to any given wifi configurations!")
    return 0
    
        

def Main():
    if ConnectToWifi():
        print("Starting webrepl...")
        webrepl.start()

Main()