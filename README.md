# MicroPython ESP32 Starter

## Features
 Modular structure (`boot.py`, `main.py`, modules)
 Wi-Fi support
 Onboard LED blink example
 mpremote deploy scripts
 Works well with WSL + VS Code

## Deploy
This project includes a small deploy helper script and VS Code tasks to copy files to an ESP32 running MicroPython.

Usage (from the workspace root):

```bash
# Run a real deployment (copies files and soft-resets the device)
./scripts/deploy.sh

# Preview what would be uploaded without touching the device
./scripts/deploy.sh --dry-run
```

VS Code Tasks:

- **Deploy to ESP32** — runs the deploy script and updates the device.
- **Deploy to ESP32 (dry-run)** — previews uploads (no device changes).

Notes on device paths and `mpremote`:

- The deploy script uses `mpremote` and prefixes remote paths with `:` (e.g. `:utils/logger.py`).
- If `mpremote` cannot connect, the script exits with an error; use `--dry-run` to debug commands without connecting.

Serial console (picocom)
------------------------

To open a serial REPL with `picocom`, use your ESP32 device node (common examples: `/dev/ttyUSB0`, `/dev/ttyACM0`, or a path under `/dev/serial/by-id/`). Example:

```bash
picocom -b 115200 /dev/ttyUSB0
```

Helpful `picocom` tips:

- Quit: Ctrl-A then Ctrl-X
- Show help while connected: Ctrl-A then Ctrl-H
- If you need CR/LF mapping (only if output looks joined), try:

```bash
picocom -b 115200 /dev/ttyUSB0 --omap crcrlf --imap lfcrlf
```

Permissions: if you see "permission denied" when opening the serial device, add your user to the `dialout` group:

```bash
sudo usermod -aG dialout $USER
# then log out and back in
```

If you'd like, I can add a small README snippet that includes the exact `/dev/serial/by-id/...` path from this machine.
