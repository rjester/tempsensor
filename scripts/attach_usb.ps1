# list usb devices
usbipd list

# prompt to enter a bus-id after dispalying out put from usbipd list
$BUSID = Read-Host "Enter the Bus ID of the USB device to attach (e.g., 1-1)"

usbipd attach --busid $BUSID


# mpremote connect auto
# mpremote disconnect
# mpremote repl
# Optional: helper to download and flash firmware using a configurable port.
param(
	[string]$Port = $(if ($env:ESP_PORT) { $env:ESP_PORT } else { 'COM4' })
)

# To use this helper, uncomment the lines below and run this script with `-Port COM5` or set `ESP_PORT` env var.
# $FIRMWARE_URL = "https://micropython.org/resources/firmware/ESP32_GENERIC-20250911-v1.26.1.bin"
# Invoke-WebRequest -Uri $FIRMWARE_URL -OutFile firmware.bin
# & esptool --chip esp32 --port $Port --baud 115200 write-flash -z 0x1000 firmware.bin
# Remove-Item firmware.bin -Force

