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
            line = None
            try:
                # Try to get a friendly timestamp
                tm = time.localtime()
                ts = f"{tm[0]:04d}-{tm[1]:02d}-{tm[2]:02d}T{tm[3]:02d}:{tm[4]:02d}:{tm[5]:02d}"
            except Exception:
                ts = str(time.time())

            line = f"{ts} T:{t}C H:{h}%"
            print(f"Temperature: {t} °C, Humidity: {h} %")

            # Append to log file on device
            try:
                with open('sensor.log', 'a') as lf:
                    lf.write(line + "\n")
            except Exception as e:
                print("Failed to write sensor log:", e)
        else:
            # No sensor configured; just sleep
            pass

        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting main loop")
