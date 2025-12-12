# MicroPython ESP32 Temperature and Humidity Sensor

## Features
Modular structure (`boot.py`, `main.py`, modules)

- **Sensor loop:** `src/main.py` reads a DHT22 sensor (default pin 14) at a configurable interval (default 300s / 5 minutes) and prints temperature and humidity.
- **Time & networking:** attempts to connect to Wi‑Fi using credentials from `secrets.py`, synchronizes time via NTP (stores sync time in RTC), and applies an optional timezone offset.
- **Uploads:** supports optional uploads configured in `secrets.py` via `UPLOAD_METHOD` — `http` (POST JSON), `mqtt` (publish JSON), or `prometheus`/`pushgateway` (Pushgateway text metrics). The script handles missing libraries gracefully and prints helpful messages on failure.
- **Power saving:** disables WLAN and uses `machine.deepsleep()` between measurements to conserve power.
- **Configurable:** behaviour and credentials are controlled via constants at the top of `src/main.py` (e.g. `PIN_DHT`, `MEASURE_INTERVAL`, `TZ_OFFSET_SECONDS`) and by values in `secrets.py` (`SSID`, `PASSWORD`, `UPLOAD_METHOD`, etc.).

- Works well with WSL + VS Code

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

## Scripts (Windows / PowerShell)

This repo now includes PowerShell helper scripts for Windows under `scripts/ps1/`.

- `scripts/ps1/repl.ps1` — open an `mpremote` REPL: `mpremote connect auto repl`
- `scripts/ps1/reset.ps1` — soft-reset the connected device: `mpremote connect auto reset`
- `scripts/ps1/list-files.ps1` — list files on the device: `mpremote connect auto fs ls -r`
-- `scripts/ps1/write-flash-esp.ps1` — download Micropython firmware and flash via `esptool` (default port `COM4`). You can override the port by passing `-Port COM5` to the script or setting the `ESP_PORT` environment variable. Use `-Yes` to skip the interactive confirmation (e.g. for automation).

Run these from PowerShell (may need to set execution policy or run with `-ExecutionPolicy Bypass`). Example:

```powershell
# Run the REPL script
pwsh -NoProfile -ExecutionPolicy Bypass -File ./scripts/ps1/repl.ps1
```

PowerShell write-flash usage examples (port and auto-confirm):

```powershell
# Flash using COM3 and prompt for confirmation
pwsh -NoProfile -ExecutionPolicy Bypass -File ./scripts/ps1/write-flash-esp.ps1 -Port COM3

# Flash using COM3 without prompting (automation)
pwsh -NoProfile -ExecutionPolicy Bypass -File ./scripts/ps1/write-flash-esp.ps1 -Port COM3 -Yes

# Or set the ESP_PORT env var for convenience (current session)
$env:ESP_PORT = 'COM3'
pwsh -NoProfile -ExecutionPolicy Bypass -File ./scripts/ps1/write-flash-esp.ps1 -Yes
```

## Scripts (POSIX / Bash)

POSIX-compatible shell scripts are available under `scripts/sh/` for Linux/macOS/WSL users.

- `scripts/sh/repl.sh` — open `mpremote` REPL
- `scripts/sh/reset.sh` — reset the device
- `scripts/sh/list_files.sh` — list files on the device (uses `mpremote` and `DEVICE` env var)
-- `scripts/sh/write-flash-esp.sh` — download and flash Micropython firmware via `esptool`. Accepts `-y`/`--yes` to skip the interactive confirmation. The serial port can be set with the `PORT` env var or passed as the first positional argument.

Example (bash):

```bash
# Run the list-files script (uses DEVICE env var if set, default: auto)
./scripts/sh/list_files.sh
```

Bash write-flash usage examples (port and auto-confirm):

```bash
# Flash using COM3 (or a tty path under Linux) and prompt for confirmation
./scripts/sh/write-flash-esp.sh COM3

# Flash using COM3 without prompting (automation)
./scripts/sh/write-flash-esp.sh -y COM3

# Or set the PORT env var
PORT=COM3 ./scripts/sh/write-flash-esp.sh -y
```

## CI / Automation

Use the non-interactive flags to run the write-flash helper in CI or automation. Examples below show a single CI step that invokes the appropriate script and skips the interactive confirmation.

PowerShell (Windows runner / GitHub Actions step):

```yaml
- name: Flash MicroPython (Windows)
	run: pwsh -NoProfile -ExecutionPolicy Bypass -File ./scripts/ps1/write-flash-esp.ps1 -Port COM3 -Yes
	env:
		ESP_PORT: COM3
```

Bash (Linux runner):

```yaml
- name: Flash MicroPython (Linux)
	run: PORT=/dev/ttyUSB0 ./scripts/sh/write-flash-esp.sh -y /dev/ttyUSB0
```

Notes:

- Use `-Yes` (PowerShell) or `-y`/`--yes` (shell) to skip confirmation in automated runs.
- Ensure the CI runner has permission to access the serial device (or use a dedicated flashing runner).


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

	**Safety — Backup & Confirm Before Flashing**

	- Always back up important files (for example, `src/boot.py` and `src/main.py`) before flashing firmware or overwriting the device filesystem.
	- The `write-flash` helpers prompt for confirmation by default; avoid using `-Yes`/`-y` in interactive sessions unless you intentionally want to skip the prompt.
	- For CI/automation, take extra care: run flashing steps on a dedicated runner, ensure artifacts are backed up, and only enable non-interactive flashing after validating the workflow.

### Steps I use locally to deploy reliably

1. (Optional) Back up `src/boot.py`: `cp src/boot.py src/boot.py.bak`
2. Edit `src/boot.py` and comment out the `import main` block so `main.py` won't auto-run.
3. Run a normal deploy: `./scripts/deploy.sh`
4. Restore `src/boot.py` from the backup and re-deploy or reboot the device so `main.py` runs with the updated code.

If you prefer to avoid editing files, a quick replug of the device and an immediate `./scripts/deploy.sh` usually succeeds.

If you run into persistent problems, open the serial console (`picocom -b 115200 /dev/ttyUSB0`) and press Ctrl-C at the REPL prompt to stop a running script, then re-run the deploy.
