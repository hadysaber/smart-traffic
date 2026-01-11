# ESP32 Traffic Lights Controller

This firmware polls the backend `/api/get_timings` endpoint and runs a 6-phase traffic
signal plan. It uses ArduinoJson to parse timing data and falls back to fixed timings
if the backend is unavailable.

## Pin Mapping
Define your pins at the top of `traffic_lights.ino` for each direction:
- **North**: red/yellow/green
- **East**: red/yellow/green
- **South**: red/yellow/green
- **West**: red/yellow/green

## Configuration
Update these constants in `traffic_lights.ino`:
- `WIFI_SSID` / `WIFI_PASSWORD`
- `SERVER_URL` (example: `http://192.168.1.50:5000/api/get_timings`)

## Usage
1. Install the ArduinoJson library in the Arduino IDE.
2. Flash the sketch to your ESP32.
3. Observe the serial output to confirm successful polling.

If the backend fails to respond, the controller uses a local fallback plan to keep
signals cycling safely.
