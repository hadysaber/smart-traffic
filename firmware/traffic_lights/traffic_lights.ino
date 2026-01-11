#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char *WIFI_SSID = "YOUR_WIFI_SSID";
const char *WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char *SERVER_URL = "http://192.168.1.50:5000/api/get_timings";

// Pin mapping (update for your wiring)
const int NORTH_RED = 2;
const int NORTH_YELLOW = 4;
const int NORTH_GREEN = 5;

const int EAST_RED = 12;
const int EAST_YELLOW = 13;
const int EAST_GREEN = 14;

const int SOUTH_RED = 15;
const int SOUTH_YELLOW = 16;
const int SOUTH_GREEN = 17;

const int WEST_RED = 18;
const int WEST_YELLOW = 19;
const int WEST_GREEN = 21;

const int POLL_INTERVAL_MS = 5000;

enum LightColor
{
    OFF,
    RED,
    YELLOW,
    GREEN
};

unsigned long lastPoll = 0;

void setupPins()
{
    int pins[] = {
        NORTH_RED, NORTH_YELLOW, NORTH_GREEN,
        EAST_RED, EAST_YELLOW, EAST_GREEN,
        SOUTH_RED, SOUTH_YELLOW, SOUTH_GREEN,
        WEST_RED, WEST_YELLOW, WEST_GREEN};
    for (int pin : pins)
    {
        pinMode(pin, OUTPUT);
        digitalWrite(pin, LOW);
    }
}

void setColor(int redPin, int yellowPin, int greenPin, LightColor color)
{
    digitalWrite(redPin, color == RED ? HIGH : LOW);
    digitalWrite(yellowPin, color == YELLOW ? HIGH : LOW);
    digitalWrite(greenPin, color == GREEN ? HIGH : LOW);
}

void setLightsNS_EW(LightColor nsColor, LightColor ewColor)
{
    setColor(NORTH_RED, NORTH_YELLOW, NORTH_GREEN, nsColor);
    setColor(SOUTH_RED, SOUTH_YELLOW, SOUTH_GREEN, nsColor);
    setColor(EAST_RED, EAST_YELLOW, EAST_GREEN, ewColor);
    setColor(WEST_RED, WEST_YELLOW, WEST_GREEN, ewColor);
}

void setAllRed()
{
    setLightsNS_EW(RED, RED);
}

void connectWiFi()
{
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    Serial.print("Connecting to WiFi");
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi connected");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
}

LightColor parseColor(const char *color)
{
    if (!color)
    {
        return RED;
    }
    if (strcmp(color, "GREEN") == 0)
    {
        return GREEN;
    }
    if (strcmp(color, "YELLOW") == 0)
    {
        return YELLOW;
    }
    return RED;
}

bool fetchTimings(JsonDocument &doc)
{
    if (WiFi.status() != WL_CONNECTED)
    {
        return false;
    }

    HTTPClient http;
    http.begin(SERVER_URL);
    int httpCode = http.GET();
    if (httpCode <= 0)
    {
        http.end();
        return false;
    }

    String payload = http.getString();
    http.end();

    DeserializationError error = deserializeJson(doc, payload);
    if (error)
    {
        Serial.print("JSON parse error: ");
        Serial.println(error.c_str());
        return false;
    }
    return true;
}

void runPhase(LightColor nsColor, LightColor ewColor, int durationSeconds, const char *label)
{
    Serial.print("Phase: ");
    Serial.print(label);
    Serial.print(" (");
    Serial.print(durationSeconds);
    Serial.println("s)");
    setLightsNS_EW(nsColor, ewColor);
    delay(durationSeconds * 1000);
}

void runAllRed(int durationSeconds, const char *label)
{
    Serial.print("Phase: ");
    Serial.print(label);
    Serial.print(" (");
    Serial.print(durationSeconds);
    Serial.println("s)");
    setAllRed();
    delay(durationSeconds * 1000);
}

void runFallbackPlan()
{
    runPhase(GREEN, RED, 30, "Fallback NS green");
    runPhase(YELLOW, RED, 3, "Fallback NS yellow");
    runAllRed(2, "Fallback all red");
    runPhase(RED, GREEN, 30, "Fallback EW green");
    runPhase(RED, YELLOW, 3, "Fallback EW yellow");
    runAllRed(2, "Fallback all red");
}

void executePlan(JsonDocument &doc)
{
    JsonObject commands = doc["commands"];
    if (commands.isNull())
    {
        Serial.println("Missing commands, using fallback");
        runFallbackPlan();
        return;
    }

    for (int phase = 1; phase <= 6; ++phase)
    {
        String key = "phase" + String(phase);
        JsonObject phaseObj = commands[key];
        if (phaseObj.isNull())
        {
            Serial.println("Missing phase data, using fallback");
            runFallbackPlan();
            return;
        }

        int duration = phaseObj["duration"] | 0;
        const char *ns = phaseObj["ns"] | nullptr;
        const char *ew = phaseObj["ew"] | nullptr;
        const char *all = phaseObj["all"] | nullptr;

        if (all && strcmp(all, "RED") == 0)
        {
            runAllRed(duration, key.c_str());
        }
        else
        {
            runPhase(parseColor(ns), parseColor(ew), duration, key.c_str());
        }
    }
}

void setup()
{
    Serial.begin(115200);
    delay(500);
    setupPins();
    connectWiFi();
    setAllRed();
}

void loop()
{
    unsigned long now = millis();
    if (now - lastPoll >= POLL_INTERVAL_MS)
    {
        lastPoll = now;
        StaticJsonDocument<2048> doc;
        if (fetchTimings(doc))
        {
            executePlan(doc);
        }
        else
        {
            Serial.println("Failed to fetch timings, using fallback");
            runFallbackPlan();
        }
    }
    delay(100);
}
