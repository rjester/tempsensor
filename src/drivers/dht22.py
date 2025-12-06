"""DHT22 sensor driver wrapper.

Uses the MicroPython `dht` module on device; falls back to a host simulator
when running on desktop Python for local testing.
"""
import time
import random

try:
    import dht
    ON_DEVICE = True
except Exception:
    dht = None
    ON_DEVICE = False

try:
    from machine import Pin
except Exception:
    # Host stub will provide machine.Pin
    from machine import Pin  # type: ignore


class DHT22Sensor:
    def __init__(self, pin_no):
        self.pin_no = pin_no
        if ON_DEVICE and dht is not None:
            self._device = dht.DHT22(Pin(pin_no))
        else:
            self._device = None

    def read(self):
        """Read the sensor and return (temperature_c, humidity).

        On device this queries the DHT22. On host this returns simulated
        values (useful for local testing).
        """
        if self._device is not None:
            # MicroPython DHT22: call measure() then temperature(), humidity()
            self._device.measure()
            t = self._device.temperature()
            h = self._device.humidity()
            return float(t), float(h)

        # Host simulation: generate plausible readings
        t = 20.0 + random.uniform(-5.0, 5.0)
        h = 40.0 + random.uniform(-20.0, 20.0)
        # Simulate sensor read delay
        time.sleep(0.05)
        return round(t, 2), round(h, 1)
