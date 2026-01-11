# Smart Traffic Light System

A full-stack Smart Traffic Light System that uses camera uploads and heuristic ML
predictions to drive traffic signal timings.

```
+-------------------+        WiFi        +-----------------------+
|   ESP32-CAM       |  JPEG upload (POST)|  Flask Backend API     |
|  (captures image) +------------------->|  /api/process_image    |
+-------------------+                    |  /api/get_timings      |
                                         +-----------+-----------+
                                                     |
                                                     | JSON timings
                                                     v
                                         +-----------+-----------+
                                         |  ESP32 Traffic Lights |
                                         | (runs 6-phase cycle)  |
                                         +-----------------------+
```

## Repository Layout
```
smart-traffic/
  README.md
  backend/
    app.py
    ml_model.py
    cv_hook.py
    config.py
    requirements.txt
  firmware/
    esp32_cam/
      esp32_cam.ino
      README.md
    traffic_lights/
      traffic_lights.ino
      README.md
  tools/
    send_counts.py
    test_upload_image.py
```

## Backend Setup (Windows)
1. Open PowerShell in the repo root.
2. Create a virtual environment:
   ```
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```
   pip install -r backend\requirements.txt
   ```
4. Run the backend:
   ```
   python backend\app.py
   ```

The API listens on `http://0.0.0.0:5000`.

## Testing the Backend
### Health & status
```
curl http://localhost:5000/api/health
curl http://localhost:5000/api/status
```

### Send simulated counts
```
python tools/send_counts.py 8 2 9 3
```

### Upload a JPEG
```
python tools/test_upload_image.py path\to\image.jpg
```

### cURL upload example
```
curl -F "imageFile=@sample.jpg" http://localhost:5000/api/process_image
```

## Firmware Setup
### ESP32-CAM (Uploader)
1. Open `firmware/esp32_cam/esp32_cam.ino` in Arduino IDE.
2. Set `WIFI_SSID`, `WIFI_PASSWORD`, and `SERVER_URL`.
3. Select the **AI Thinker ESP32-CAM** board profile.
4. Connect GPIO0 to GND for flash mode, then upload.
5. Remove GPIO0 from GND and reset to run.

See `firmware/esp32_cam/README.md` for wiring details.

### ESP32 Traffic Lights (Controller)
1. Open `firmware/traffic_lights/traffic_lights.ino`.
2. Set WiFi credentials and `SERVER_URL` (point to `/api/get_timings`).
3. Install the ArduinoJson library.
4. Map the GPIO pins to your LEDs/relays.
5. Flash the sketch and monitor serial output.

See `firmware/traffic_lights/README.md` for pin mapping tips.

## Troubleshooting
- **CORS errors**: Ensure the backend is running with Flask-CORS (enabled by default).
- **WiFi fails**: Double-check SSID/password and use 2.4GHz WiFi for ESP32.
- **Wrong SERVER_URL**: Use LAN IP of your machine, not `localhost`.
- **Multipart field name**: Must be `imageFile` for `/api/process_image`.
- **No timings**: `/api/get_timings` falls back to default counts if none exist.
