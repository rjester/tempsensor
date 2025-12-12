import sys
import network
import ntptime
import machine
import utime as time
import dht
import ujson as json

# Configuration
PIN_DHT = 14
MEASURE_INTERVAL = 300  # seconds (5 minutes)
TZ_OFFSET_SECONDS = 0  # override here or in secrets.py (seconds east of UTC)


def safe_import_secrets():
    try:
        import secrets
        ssid = getattr(secrets, 'SSID', None)
        pwd = getattr(secrets, 'PASSWORD', None)
        tz = getattr(secrets, 'TZ_OFFSET_SECONDS', None)
        if tz is not None:
            global TZ_OFFSET_SECONDS
            TZ_OFFSET_SECONDS = int(tz)
        if not ssid or not pwd:
            raise ImportError('SSID or PASSWORD missing in secrets.py')
        return ssid, pwd
    except Exception as e:
        print('Error importing secrets.py:', e)
        print('Create `secrets.py` from `secrets.py.example`')
        raise


def connect_wifi(ssid, password, timeout=20):
    wlan = network.WLAN(network.STA_IF)
    if not wlan.active():
        wlan.active(True)
    if wlan.isconnected():
        # print('Already connected, network config:', wlan.ifconfig())
        return True

    # print('Connecting to Wi-Fi SSID:', ssid)
    wlan.connect(ssid, password)
    start = time.time()
    iter = 0
    # Reduce serial spam: only print a dot every 5 seconds
    while not wlan.isconnected() and time.time() - start < timeout:
        time.sleep(1)
        iter += 1
        if iter % 5 == 0:
            print('.', end='')
    print('')

    if wlan.isconnected():
        # ('Connected, network config:', wlan.ifconfig())
        return True
    else:
        print('Failed to connect to Wi-Fi within timeout')
        return False


def sync_time(retries=3):
    ntptime.host = 'pool.ntp.org'
    for attempt in range(1, retries + 1):
        try:
            # print('Syncing time with', ntptime.host, ' (attempt', attempt, ')')
            ntptime.settime()
            # print('Time synced (UTC):', time.localtime())
            return True
        except Exception as e:
            print('ntp sync failed:', e)
            time.sleep(2)
    return False


def timestamp(offset_seconds=0):
    # Get current UTC time from RTC, apply offset, and return ISO-like string
    t = time.localtime()
    if offset_seconds:
        try:
            secs = time.mktime((t[0], t[1], t[2], t[3], t[4], t[5], 0, 0)) + int(offset_seconds)
            t = time.localtime(secs)
        except Exception:
            pass
    return '{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}'.format(t[0], t[1], t[2], t[3], t[4], t[5])


def read_dht(sensor, retries=3):
    for i in range(retries):
        try:
            # temp = 1
            # hum = 1
            sensor.measure()
            temp = sensor.temperature()
            hum = sensor.humidity()
            return temp, hum
        except Exception as e:
            print('DHT read error (attempt', i+1, '):', e)
            time.sleep(2)
    return None, None


def main():
    # Small startup delay to allow user to interrupt (Ctrl-C) after reset
    # This provides a brief window to stop a noisy auto-running script.
    time.sleep(2)
    # print('Starting main()')
    rtc = machine.RTC()

    # Wake reason
    # if machine.reset_cause() == machine.DEEPSLEEP_RESET:
        #print('Woke from deep sleep')
    # else:
        # print('Normal boot')

    try:
        ssid, password = safe_import_secrets()
    except Exception:
        sys.exit(1)

    # Attempt to connect to Wi-Fi and sync time
    if connect_wifi(ssid, password, timeout=20):
        if sync_time():
            # store last sync time in RTC memory for potential future use
            try:
                now = int(time.time())
                rtc.memory(str(now))
            except Exception:
                pass
        else:
            print('Could not sync time')
    else:
        print('Continuing without network — will measure with current RTC')

    sensor = dht.DHT22(machine.Pin(PIN_DHT))

    ts = timestamp(TZ_OFFSET_SECONDS)
    
    temp, hum = read_dht(sensor)
    
    if temp is None:
        print(ts, 'DHT read failed after retries')
    else:
        f = temp * 9 / 5 + 32
        print('{}  Temp: {:.1f} C / {:.1f} F  Humidity: {:.1f} %'.format(ts, temp, f, hum))

        # Prepare payload
        payload = {
            'timestamp': ts,
            'temp_c': round(temp, 2),
            'temp_f': round(f, 2),
            'humidity': round(hum, 2)
        }

        # Try upload if configured in secrets.py
        try:
            import secrets as _secrets
            upload_method = getattr(_secrets, 'UPLOAD_METHOD', None)
        except Exception:
            upload_method = None

        if upload_method:
            um = str(upload_method).lower()
            if um == 'http':
                url = getattr(_secrets, 'HTTP_URL', None)
                if url:
                    try:
                        try:
                            import urequests as requests
                        except Exception:
                            requests = None
                        if requests:
                            resp = requests.post(url, data=json.dumps(payload), headers={'Content-Type':'application/json'})
                            print('HTTP upload status:', getattr(resp, 'status_code', None))
                            try:
                                resp.close()
                            except Exception:
                                pass
                        else:
                            print('urequests unavailable; skipping HTTP upload')
                    except Exception as e:
                        print('HTTP upload failed:', e)
                else:
                    print('HTTP_URL not set in secrets.py; skipping HTTP upload')

            elif um == 'mqtt':
                broker = getattr(_secrets, 'MQTT_BROKER', None)
                if broker:
                    port = getattr(_secrets, 'MQTT_PORT', 1883)
                    topic = getattr(_secrets, 'MQTT_TOPIC', 'esp32/dht')
                    user = getattr(_secrets, 'MQTT_USER', None)
                    pwd = getattr(_secrets, 'MQTT_PASS', None)
                    try:
                        from umqtt.simple import MQTTClient
                        client_id = getattr(_secrets, 'MQTT_CLIENT_ID', 'esp32')
                        client = MQTTClient(client_id, broker, port, user, pwd)
                        client.connect()
                        client.publish(topic, json.dumps(payload))
                        client.disconnect()
                        print('MQTT publish succeeded to', topic)
                    except Exception as e:
                        print('MQTT upload failed:', e)
                else:
                    print('MQTT_BROKER not set in secrets.py; skipping MQTT upload')
            elif um in ('prometheus', 'pushgateway'):
                # Prometheus Pushgateway support
                pg = getattr(_secrets, 'PROMETHEUS_PUSHGATEWAY', None) or getattr(_secrets, 'PUSHGATEWAY_URL', None)
                job = getattr(_secrets, 'PROMETHEUS_JOB', 'esp32')
                # Allow per-device instance: use PROMETHEUS_INSTANCE if set,
                # otherwise derive from device unique id or WLAN MAC so each
                # device reports a distinct instance label.
                instance = getattr(_secrets, 'PROMETHEUS_INSTANCE', None)
                if not instance:
                    try:
                        import ubinascii
                        uid = machine.unique_id()
                        instance = ubinascii.hexlify(uid).decode()
                    except Exception:
                        try:
                            wlan = network.WLAN(network.STA_IF)
                            mac = wlan.config('mac')
                            # mac may be bytes; convert to hex string
                            instance = ''.join('{:02x}'.format(b) for b in mac)
                        except Exception:
                            instance = None
                if pg:
                    try:
                        # Build simple text-format metrics with timestamp
                        # Pushgateway prefers metrics without explicit timestamps — omit them
                        body = ''
                        body += 'esp32_temp_c {}\n'.format(payload['temp_c'])
                        body += 'esp32_temp_f {}\n'.format(payload['temp_f'])
                        body += 'esp32_humidity {}\n'.format(payload['humidity'])

                        url = pg.rstrip('/')
                        url += '/metrics/job/{}'.format(job)
                        if instance:
                            url += '/instance/{}'.format(instance)

                        try:
                            try:
                                import urequests as requests
                            except Exception:
                                requests = None
                            if requests:
                                resp = requests.put(url, data=body, headers={'Content-Type': 'text/plain; version=0.0.4'})
                                status = getattr(resp, 'status_code', None)
                                print('Prometheus pushgateway upload status:', status)
                                # Print response body on failure to aid debugging
                                try:
                                    if status is None or status >= 400:
                                        print('Response body:', getattr(resp, 'text', None) or getattr(resp, 'content', None))
                                except Exception:
                                    pass
                                try:
                                    resp.close()
                                except Exception:
                                    pass
                            else:
                                print('urequests unavailable; skipping Prometheus upload')
                        except Exception as e:
                            print('Prometheus upload failed:', e)
                    except Exception as e:
                        print('Prometheus upload preparation failed:', e)
                else:
                    print('PROMETHEUS_PUSHGATEWAY not set in secrets.py; skipping Prometheus upload')
            else:
                print('Unknown UPLOAD_METHOD in secrets.py:', upload_method)

    # Prepare to deep sleep (disconnect wlan first)
    try:
        wlan = network.WLAN(network.STA_IF)
        if wlan.active():
            wlan.active(False)
    except Exception:
        pass

    sleep_ms = int(MEASURE_INTERVAL * 1000)
    # print('Entering deep sleep for {} seconds'.format(MEASURE_INTERVAL))
    # Small delay to ensure prints flush
    time.sleep(0.1)
    machine.deepsleep(sleep_ms)


main()
# while True:
#     sleep(0.5)  # Add delay between iterations
#     print("Doing something...")
