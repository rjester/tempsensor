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

## Current Deployment Notes (important)

- The project uses `mpremote` via `./scripts/deploy.sh` to copy files into the device `:/` filesystem.
- If the device program (`main.py`) prints immediately on boot it can prevent `mpremote` from entering raw-REPL and performing filesystem operations (errors like "could not enter raw repl").
- Workarounds:
	- Temporary local change: `src/boot.py` can be backed up and its `import main` temporarily commented out so the device stays quiet during uploads. After uploading, restore the backup and reboot the device.
	- Physical replug: unplug the board and plug it back in, then run `./scripts/deploy.sh` immediately — this creates a short quiet window before `main.py` starts printing.
	- Soft-reset via DTR/RTS: toggling DTR with `pyserial` may sometimes create a quiet window, but results are less reliable than a replug.

### Steps I use locally to deploy reliably

1. (Optional) Back up `src/boot.py`: `cp src/boot.py src/boot.py.bak`
2. Edit `src/boot.py` and comment out the `import main` block so `main.py` won't auto-run.
3. Run a normal deploy: `./scripts/deploy.sh`
4. Restore `src/boot.py` from the backup and re-deploy or reboot the device so `main.py` runs with the updated code.

If you prefer to avoid editing files, a quick replug of the device and an immediate `./scripts/deploy.sh` usually succeeds.

If you run into persistent problems, open the serial console (`picocom -b 115200 /dev/ttyUSB0`) and press Ctrl-C at the REPL prompt to stop a running script, then re-run the deploy.
