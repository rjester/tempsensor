# main.py
import time
from blink import blink_led
import config
import os

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

            # compute Fahrenheit for convenience
            try:
                tf = round((float(t) * 9.0 / 5.0) + 32.0, 2)
            except Exception:
                tf = None

            line = f"{ts} T:{t}C/{tf}F H:{h}%"
            if tf is not None:
                print(f"Temperature: {t} °C ({tf} °F), Humidity: {h} %")
            else:
                print(f"Temperature: {t} °C, Humidity: {h} %")

            # Append to log file on device
            try:
                with open('sensor.log', 'a') as lf:
                    lf.write(line + "\n")

                # Rotate logs if enabled and file exceeds configured size
                max_bytes = getattr(config, 'LOG_MAX_BYTES', None)
                backups = getattr(config, 'LOG_BACKUPS', 3)
                if max_bytes is not None and max_bytes > 0:
                    try:
                        # obtain file size in a cross-platform way
                        st = os.stat('sensor.log')
                        # stat may return an object with st_size or a tuple (index 6)
                        size = getattr(st, 'st_size', None)
                        if size is None:
                            try:
                                size = st[6]
                            except Exception:
                                size = None

                        if size is not None and size > max_bytes:
                            # rotate: sensor.log.(N-1) -> sensor.log.N, then sensor.log -> sensor.log.1
                            try:
                                # remove oldest
                                oldest = f"sensor.log.{backups}"
                                try:
                                    os.remove(oldest)
                                except Exception:
                                    pass

                                # shift backups
                                for i in range(backups - 1, 0, -1):
                                    src = f"sensor.log.{i}"
                                    dst = f"sensor.log.{i+1}"
                                    try:
                                        os.rename(src, dst)
                                    except Exception:
                                        # missing file is fine
                                        pass

                                # finally rotate current log
                                try:
                                    os.rename('sensor.log', 'sensor.log.1')
                                except Exception as e:
                                    print('Failed to rotate sensor.log:', e)
                            except Exception as e:
                                print('Log rotation error:', e)
                    except Exception:
                        # if stat fails, skip rotation
                        pass
            except Exception as e:
                print("Failed to write sensor log:", e)
        else:
            # No sensor configured; just sleep
            pass

        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting main loop")
