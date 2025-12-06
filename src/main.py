# main.py
import time
from blink import blink_led

print("ESP32 MicroPython project starting...")

for i in range(10):
    blink_led()
    time.sleep(0.2)

print("Done blinking. Looping...")

while True:
    time.sleep(1)
