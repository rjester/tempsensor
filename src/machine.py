"""Host stub for MicroPython's `machine` module.

This allows running the MicroPython-targeted code on desktop Python for
local testing. It implements a minimal `Pin` class with `on`, `off`, and
`value` methods and common constants.
"""
class Pin:
    OUT = 0
    IN = 1

    def __init__(self, pin, mode=OUT):
        self.pin = pin
        self.mode = mode
        self._state = 0

    def on(self):
        self._state = 1
        print(f"[machine.stub] Pin {self.pin} -> ON")

    def off(self):
        self._state = 0
        print(f"[machine.stub] Pin {self.pin} -> OFF")

    def value(self, v=None):
        if v is None:
            return self._state
        self._state = 1 if v else 0
