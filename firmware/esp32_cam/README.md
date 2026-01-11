# ESP32-CAM Uploader Firmware

This firmware targets the **AI Thinker ESP32-CAM** module. It captures a JPEG frame and
uploads it to the backend `/api/process_image` endpoint as multipart/form-data.

## Wiring & Flashing
- Module: AI Thinker ESP32-CAM
- Connect **GPIO0** to **GND** to enter flashing mode.
- Connect **5V** and **GND** to a stable power supply (USB-UART adapter recommended).
- Use an FTDI/CP2102 adapter (3.3V logic) to flash the sketch.

## Configuration
Open `esp32_cam.ino` and set:
- `WIFI_SSID` / `WIFI_PASSWORD`
- `SERVER_URL` (example: `http://192.168.1.50:5000/api/process_image`)
- `CAPTURE_INTERVAL_MS`

## Notes
- The JPEG is sent as `imageFile` field name and raw bytes.
- Serial output prints HTTP status and response payload.
