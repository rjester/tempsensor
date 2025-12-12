#!/usr/bin/env pwsh
param(
	[string]$Port = $(if ($env:ESP_PORT) { $env:ESP_PORT } else { 'COM4' }),
	[switch]$Yes
)

$FIRMWARE_URL = "https://micropython.org/resources/firmware/ESP32_GENERIC-20250911-v1.26.1.bin"
$FIRMWARE_URL = "https://micropython.org/resources/firmware/ESP32_GENERIC-20250911-v1.26.1.bin"

if (-not $Yes) {
	# Confirm before downloading and flashing
	$confirm = Read-Host "Proceed to flash MicroPython to $Port? Type 'yes' to continue"
	if ($confirm -ne 'yes') {
		Write-Host "Aborted by user."
		exit 0
	}
} else {
	Write-Host "Auto-confirm enabled; proceeding to flash on $Port"
}

Invoke-WebRequest -Uri $FIRMWARE_URL -OutFile firmware.bin
# Call esptool (external program). Use the call operator `&` to run the executable.
& esptool --chip esp32 --port $Port --baud 115200 write-flash -z 0x1000 firmware.bin
Remove-Item firmware.bin -Force