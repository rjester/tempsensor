#!/usr/bin/env pwsh
# list usb devices
usbipd list

# prompt to enter a bus-id after dispalying out put from usbipd list
$BUSID = Read-Host "Enter the Bus ID of the USB device to attach (e.g., 1-1)"

usbipd attach --busid $BUSID


# mpremote connect auto
# mpremote disconnect
# mpremote repl

