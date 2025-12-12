#!/usr/bin/env pwsh
$FIRMWARE_URL = "https://micropython.org/resources/firmware/ESP32_GENERIC-20250911-v1.26.1.bin"
Invoke-WebRequest -Uri $FIRMWARE_URL -OutFile firmware.bin
# Call esptool (external program). Use the call operator `&` to run the executable.
& esptool --chip esp32 --port COM4 --baud 115200 write-flash -z 0x1000 firmware.bin
Remove-Item firmware.bin -Force