# boot.py
import wifi

# Start WiFi connection but avoid blocking boot. Prefer a non-blocking connect
# if supported; otherwise try to spawn a background thread, and finally fall
# back to a blocking call.
try:
    try:
        # prefer non-blocking call if available
        wifi.connect(blocking=False)
    except TypeError:
        # older wifi.connect signature -- try to start in background
        try:
            import _thread
            _thread.start_new_thread(wifi.connect, ())
        except Exception:
            # last resort: call blocking but catch exceptions
            try:
                wifi.connect()
            except Exception as e:
                print("WiFi error:", e)
except Exception as e:
    print("WiFi error:", e)

# Ensure main.py starts after boot; wrap in try/except so boot errors don't stop device
try:
    import main
except Exception as e:
    try:
        print("Failed to start main:", e)
    except Exception:
        # printing may fail in some early boot states
        pass
