# boot.py
import wifi

try:
    wifi.connect()
except Exception as e:
    print("WiFi error:", e)
