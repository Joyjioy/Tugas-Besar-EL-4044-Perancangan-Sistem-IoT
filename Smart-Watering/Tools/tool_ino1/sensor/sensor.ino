#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ================= CONFIGURATION =================
const char* ssid         = "CISITU BARU 4G";
const char* password     = "cisitubaru72";

const char* mqtt_server  = "iwkrmq.pptik.id";
const int mqtt_port      = 1883;
const char* mqtt_user    = "/trainerkit:trainerkit";
const char* mqtt_pass    = "12345678";

const char* topic_publish = "smartwatering/soil/data";
// =================================================

const int SOIL_PIN = A0;

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastMsg = 0;
const unsigned long publishInterval = 3000; // 3 detik

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.println("Connecting to WiFi...");

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi connected");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection (Sensor Node)...");

    String clientId = "WemosSensor-";
    clientId += String(random(0xffff), HEX);

    if (client.connect(clientId.c_str(), mqtt_user, mqtt_pass)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  setup_wifi();

  client.setServer(mqtt_server, mqtt_port);
  lastMsg = millis() - publishInterval;
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }

  client.loop();

  unsigned long now = millis();

  if (now - lastMsg > publishInterval) {
    lastMsg = now;

    int soilValue = analogRead(SOIL_PIN);

    StaticJsonDocument<100> doc;
    doc["soil"] = soilValue;

    char buffer[128];
    serializeJson(doc, buffer);

    Serial.print("Publishing soil data: ");
    Serial.println(buffer);

    client.publish(topic_publish, buffer);
  }
}