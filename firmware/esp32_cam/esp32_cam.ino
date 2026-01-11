#include "esp_camera.h"
#include <WiFi.h>

const char *WIFI_SSID = "YOUR_WIFI_SSID";
const char *WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char *SERVER_URL = "http://192.168.1.50:5000/api/process_image";

const unsigned long CAPTURE_INTERVAL_MS = 10000;

#define CAMERA_MODEL_AI_THINKER

#if defined(CAMERA_MODEL_AI_THINKER)
#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27
#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22
#endif

unsigned long lastCapture = 0;

struct UrlParts {
  String host;
  uint16_t port;
  String path;
};

UrlParts parseUrl(const char *url) {
  String working(url);
  UrlParts parts;
  parts.port = 80;

  if (working.startsWith("http://")) {
    working.remove(0, 7);
  }

  int slashIndex = working.indexOf('/');
  String hostPort = slashIndex >= 0 ? working.substring(0, slashIndex) : working;
  parts.path = slashIndex >= 0 ? working.substring(slashIndex) : "/";

  int colonIndex = hostPort.indexOf(':');
  if (colonIndex >= 0) {
    parts.host = hostPort.substring(0, colonIndex);
    parts.port = hostPort.substring(colonIndex + 1).toInt();
  } else {
    parts.host = hostPort;
  }

  return parts;
}

void setupCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
  }
}

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void sendImage() {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    return;
  }

  UrlParts parts = parseUrl(SERVER_URL);
  WiFiClient client;

  if (!client.connect(parts.host.c_str(), parts.port)) {
    Serial.println("Failed to connect to server");
    esp_camera_fb_return(fb);
    return;
  }

  const char *boundary = "----SmartTrafficBoundary";
  String startPart = "--" + String(boundary) + "\r\n";
  startPart += "Content-Disposition: form-data; name=\"imageFile\"; filename=\"capture.jpg\"\r\n";
  startPart += "Content-Type: image/jpeg\r\n\r\n";
  String endPart = "\r\n--" + String(boundary) + "--\r\n";

  uint32_t contentLength = startPart.length() + fb->len + endPart.length();

  client.printf("POST %s HTTP/1.1\r\n", parts.path.c_str());
  client.printf("Host: %s\r\n", parts.host.c_str());
  client.println("Connection: close");
  client.printf("Content-Type: multipart/form-data; boundary=%s\r\n", boundary);
  client.printf("Content-Length: %lu\r\n\r\n", static_cast<unsigned long>(contentLength));

  client.print(startPart);
  client.write(fb->buf, fb->len);
  client.print(endPart);

  Serial.println("Upload sent, waiting for response...");

  String statusLine = client.readStringUntil('\n');
  Serial.println(statusLine);

  while (client.connected() || client.available()) {
    if (client.available()) {
      String line = client.readStringUntil('\n');
      Serial.println(line);
    }
  }

  client.stop();
  esp_camera_fb_return(fb);
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  connectWiFi();
  setupCamera();
}

void loop() {
  unsigned long now = millis();
  if (now - lastCapture >= CAPTURE_INTERVAL_MS) {
    lastCapture = now;
    sendImage();
  }
  delay(100);
}
