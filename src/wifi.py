# wifi.py
import network
import time
import config

def connect(blocking=True):
    """Connect to WiFi.

    If `blocking` is False, initiate the connection and return immediately.
    When `blocking` is True (default), wait up to ~10s for the connection to succeed.
    """
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not config.WIFI_SSID:
        print("No WiFi config, skipping connect")
        return

    if not wlan.isconnected():
        # print("Connecting to WiFi...")
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

        if blocking:
            for _ in range(20):
                if wlan.isconnected():
                    break
                time.sleep(0.5)

    # if wlan.isconnected():
    #     try:
    #         print("Connected:", wlan.ifconfig())
    #     except Exception:
    #         # some ports may not support ifconfig in the same way
    #         print("Connected")
    # else:
    #     print("Failed to connect")
