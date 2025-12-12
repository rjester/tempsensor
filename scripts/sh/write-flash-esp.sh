#!/usr/bin/env bash
FIRMWARE_URL="https://micropython.org/resources/firmware/ESP32_GENERIC-20250911-v1.26.1.bin"
curl -L -o firmware.bin "$FIRMWARE_URL"
esptool --chip esp32 --port COM4 --baud 115200 write-flash -z 0x1000 firmware.bin
rm -f firmware.bin
