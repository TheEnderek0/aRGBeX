# Since os environ doesn't actually exist (or at least not properly) we can use this approach for variables

# Replace these with proper values

# Connect to wifi, used by boot.py
ESP_Static_IP   = "192.168.0.32" # IP the esp32 will get when connecting to the router
WIFI_Gateway    = "192.168.0.1" # Gateway, you can check that using ipconfig in Windows' CMD (same goes for WIFI_Subnet)
WIFI_Subnet     = "255.255.255.0"
WIFI_DICT       = {     # A dictionary of wifi SSID's and their passwords, will go in order
    "MyWifi": "MyPassword",
    "MySecondaryWifi": "Amogus"
}
TIMEOUT = 10 # In seconds, what time can we wait for a connection
# Connect to TCP server hosted on the end user's personal computer or such (I highly recommend setting a static ip for that computer/device)
SERVER_IP       = ["192.168.0.20"] #You can specify multiple, will try to connect by order
SERVER_PORT     = 1000

# Once you are done with the values, change the name to esp_cfg.py and upload it to the esp32