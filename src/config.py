# config.py

WIFI_SSID = "enzo"
WIFI_PASSWORD = "bc42cd67"

LED_PIN = 2   # Most ESP32 boards use GPIO2 for onboard LED

# DHT22 data pin (set to a GPIO number, or None to disable)
# Example: DHT_PIN = 4
DHT_PIN = 14

# Logging rotation settings (bytes and number of backups)
# Logging rotation settings were removed — file logging is disabled.
# (Previously: LOG_MAX_BYTES, LOG_BACKUPS)
