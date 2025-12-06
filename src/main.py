# main.py
import time
from blink import blink_led
import config

print("ESP32 MicroPython project starting...")

# Blink the LED a few times on startup
for i in range(10):
    blink_led()
    time.sleep(0.2)

print("Done blinking. Starting sensor loop...")

sensor = None
if getattr(config, 'DHT_PIN', None) is not None:
    try:
        from drivers.dht22 import DHT22Sensor
        sensor = DHT22Sensor(config.DHT_PIN)
        print(f"DHT22 sensor initialized on pin {config.DHT_PIN}")
    except Exception as e:
        print("Failed to initialize DHT22 sensor:", e)

try:
    while True:
        if sensor is not None:
            t, h = sensor.read()
            print(f"Temperature: {t} °C, Humidity: {h} %")
        else:
            # No sensor configured; just sleep
            pass

        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting main loop")
