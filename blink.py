# blink.py
import machine
import time
import config

led = machine.Pin(config.LED_PIN, machine.Pin.OUT)

def blink_led():
    led.on()
    time.sleep(0.1)
    led.off()
    time.sleep(0.1)
