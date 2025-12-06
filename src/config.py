# config.py

WIFI_SSID = "enzo"
WIFI_PASSWORD = "bc42cd67"

LED_PIN = 2   # Most ESP32 boards use GPIO2 for onboard LED

# DHT22 data pin (set to a GPIO number, or None to disable)
# Example: DHT_PIN = 4
DHT_PIN = 14

# Logging rotation settings (bytes and number of backups)
# `LOG_MAX_BYTES` controls when rotation occurs; set to None to disable rotation.
LOG_MAX_BYTES = 16 * 1024
LOG_BACKUPS = 3
