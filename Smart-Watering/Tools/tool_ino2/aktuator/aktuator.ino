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

const char* topic_subscribe = "smartwatering/pump/cmd";
const char* topic_status    = "smartwatering/pump/status";
// =================================================

// Kalau pakai Generic ESP8266, jangan pakai D1.
// D1 pada Wemos D1 Mini = GPIO5
const int PUMP_PIN = 5;

// Sesuaikan dengan relay
// Jika relay active HIGH:
const int PUMP_ON  = HIGH;
const int PUMP_OFF = LOW;

// Jika relay active LOW, pakai ini:
// const int PUMP_ON  = LOW;
// const int PUMP_OFF = HIGH;

WiFiClient espClient;
PubSubClient client(espClient);

// Status pompa
bool pumpRunning = false;

// Safety timeout, agar pompa tidak menyala selamanya jika server gagal kirim OFF
unsigned long pumpStartTime = 0;
const unsigned long SAFETY_TIMEOUT_MS = 30000; // 30 detik


void publishStatus(const char* status) {
  StaticJsonDocument<100> doc;
  doc["pump"] = status;

  char buffer[100];
  serializeJson(doc, buffer);

  client.publish(topic_status, buffer);
}


void pumpOn() {
  if (!pumpRunning) {
    digitalWrite(PUMP_PIN, PUMP_ON);
    pumpRunning = true;
    pumpStartTime = millis();

    Serial.println("ACTUATOR: Pump ON");
    publishStatus("ON");
  } else {
    Serial.println("ACTUATOR: Pump already ON");
  }
}


void pumpOff() {
  if (pumpRunning) {
    digitalWrite(PUMP_PIN, PUMP_OFF);
    pumpRunning = false;

    Serial.println("ACTUATOR: Pump OFF");
    publishStatus("OFF");
  } else {
    Serial.println("ACTUATOR: Pump already OFF");
  }
}


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


void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Command arrived [");
  Serial.print(topic);
  Serial.print("] ");

  String message = "";

  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.println(message);

  if (String(topic) != topic_subscribe) {
    return;
  }

  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, message);

  if (error) {
    Serial.print("JSON parse failed: ");
    Serial.println(error.c_str());
    return;
  }

  const char* action = doc["action"];

  if (action == NULL) {
    Serial.println("Invalid command: action not found");
    return;
  }

  String actionString = String(action);

  if (actionString == "ON") {
    pumpOn();
  }
  else if (actionString == "OFF") {
    pumpOff();
  }
  else {
    Serial.print("Unknown action: ");
    Serial.println(actionString);
  }
}


void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection (Actuator Node)...");

    String clientId = "ESP8266Actuator-";
    clientId += String(random(0xffff), HEX);

    if (client.connect(clientId.c_str(), mqtt_user, mqtt_pass)) {
      Serial.println("connected");

      client.subscribe(topic_subscribe);

      Serial.print("Subscribed to: ");
      Serial.println(topic_subscribe);

      publishStatus("READY");
    } 
    else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");

      delay(5000);
    }
  }
}


void setup() {
  Serial.begin(115200);

  pinMode(PUMP_PIN, OUTPUT);

  // Kondisi awal wajib OFF
  digitalWrite(PUMP_PIN, PUMP_OFF);
  pumpRunning = false;

  setup_wifi();

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}


void loop() {
  if (!client.connected()) {
    reconnect();
  }

  client.loop();

  // Safety timeout: jika pompa ON terlalu lama dan tidak ada OFF dari server,
  // aktuator akan mematikan pompa sendiri.
  if (pumpRunning && millis() - pumpStartTime >= SAFETY_TIMEOUT_MS) {
    Serial.println("SAFETY TIMEOUT: Pump forced OFF");
    pumpOff();
  }
}