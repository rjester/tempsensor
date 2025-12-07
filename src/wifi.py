# wifi.py
import network
import time
import config
import machine

try:
    import ntptime
except Exception:
    ntptime = None

import socket
import struct

def connect(blocking=True):
    """Connect to WiFi.

    If `blocking` is False, initiate the connection and return immediately.
    When `blocking` is True (default), wait up to ~10s for the connection to succeed.
    """
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not config.WIFI_SSID:
        print("No WiFi config, skipping connect")
        return

    if not wlan.isconnected():
        # print("Connecting to WiFi...")
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

        if blocking:
            for _ in range(20):
                if wlan.isconnected():
                    break
                time.sleep(0.5)

    # If connected, attempt to sync RTC from NTP
    if wlan.isconnected():
        try:
            sync_time()
        except Exception as e:
            try:
                print("Time sync failed:", e)
            except Exception:
                pass

    # if wlan.isconnected():
    #     try:
    #         print("Connected:", wlan.ifconfig())
    #     except Exception:
    #         # some ports may not support ifconfig in the same way
    #         print("Connected")
    # else:
    #     print("Failed to connect")


def _set_rtc_from_epoch(epoch_seconds):
    # epoch_seconds is seconds since Unix epoch (UTC)
    t = time.gmtime(epoch_seconds)
    # time.gmtime returns (year, month, mday, hour, min, sec, weekday, yearday)
    year, month, mday, hour, minute, second, weekday, yearday = t
    # machine.RTC().datetime expects (year, month, day, weekday, hours, minutes, seconds, subseconds)
    try:
        rtc = machine.RTC()
        rtc.datetime((year, month, mday, weekday + 1, hour, minute, second, 0))
    except Exception:
        # Some ports use rtc.init or accept slightly different tuples; try a fallback
        try:
            rtc = machine.RTC()
            rtc.init((year, month, mday, weekday + 1, hour, minute, second, 0))
        except Exception:
            raise


def _ntp_via_socket(server, timeout=5):
    # Minimal NTP client to fetch transmit timestamp (seconds since 1900)
    addr = socket.getaddrinfo(server, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    try:
        # NTP packet: li=0, vn=3, mode=3
        msg = b'\x1b' + 47 * b'\0'
        s.sendto(msg, addr)
        msg, _ = s.recvfrom(48)
    finally:
        s.close()

    if len(msg) < 48:
        raise OSError("Short NTP response")

    # unpack transmit timestamp (offset 40, 64-bit) -> seconds part
    t = struct.unpack('!I', msg[40:44])[0]
    # NTP epoch is 1900, Unix epoch is 1970 -> subtract 70 years in seconds
    return t - 2208988800


def sync_time(server=None, tz_offset=None):
    """Synchronize the RTC from NTP server.

    - `server`: optional NTP server hostname (defaults to `config.NTP_SERVER`).
    - `tz_offset`: optional timezone offset in seconds (defaults to `config.TZ_OFFSET`).
    """
    server = server or getattr(config, 'NTP_SERVER', 'pool.ntp.org')
    tz_offset = tz_offset if tz_offset is not None else getattr(config, 'TZ_OFFSET', 0)

    # Try ntptime if available
    if ntptime is not None:
        try:
            ntptime.host = server
            ntptime.settime()
            # ntptime.settime() sets RTC to UTC; apply tz_offset if non-zero
            if tz_offset:
                epoch = time.time() + tz_offset
                _set_rtc_from_epoch(int(epoch))
            return
        except Exception:
            # fall through to socket method
            pass

    # Fallback to socket-based NTP
    epoch = _ntp_via_socket(server)
    epoch += tz_offset
    _set_rtc_from_epoch(int(epoch))
    return
