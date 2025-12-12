
#!/usr/bin/env bash
FIRMWARE_URL="https://micropython.org/resources/firmware/ESP32_GENERIC-20250911-v1.26.1.bin"
# Support optional -y/--yes flag to skip confirmation. PORT can be env var or positional arg.
SKIP_CONFIRM=0
if [ "$1" = "-y" ] || [ "$1" = "--yes" ]; then
	SKIP_CONFIRM=1
	shift
fi
PORT="${PORT:-${1:-COM4}}"
if [ "$SKIP_CONFIRM" -ne 1 ]; then
	read -p "Proceed to flash MicroPython to $PORT? Type 'yes' to continue: " CONFIRM
	if [ "$CONFIRM" != "yes" ]; then
		echo "Aborted by user."
		exit 0
	fi
else
	echo "Auto-confirm enabled; proceeding to flash on $PORT"
fi

curl -L -o firmware.bin "$FIRMWARE_URL"
esptool --chip esp32 --port "$PORT" --baud 115200 write-flash -z 0x1000 firmware.bin
rm -f firmware.bin
