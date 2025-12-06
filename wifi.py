# wifi.py
import network
import time
import config

def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not config.WIFI_SSID:
        print("No WiFi config, skipping connect")
        return

    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

        for _ in range(20):
            if wlan.isconnected():
                break
            time.sleep(0.5)

    if wlan.isconnected():
        print("Connected:", wlan.ifconfig())
    else:
        print("Failed to connect")
