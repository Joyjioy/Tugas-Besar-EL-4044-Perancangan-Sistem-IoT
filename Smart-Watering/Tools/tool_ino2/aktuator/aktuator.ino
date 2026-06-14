#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ================= CONFIGURATION =================
// Kredensial WiFi lokal
const char* ssid         = "CISITU BARU 4G";
const char* password     = "cisitubaru72";

// Konfigurasi broker MQTT
const char* mqtt_server  = "iwkrmq.pptik.id";
const int mqtt_port      = 1883;
const char* mqtt_user    = "/trainerkit:trainerkit";
const char* mqtt_pass    = "12345678";

// Topik MQTT untuk mendengarkan perintah dan melaporkan status
const char* topic_subscribe = "smartwatering/pump/cmd";
const char* topic_status    = "smartwatering/pump/status";
// =================================================

// Pemetaan pin aktuator (Wemos D1 Mini: D1 = GPIO5)
const int PUMP_PIN = 5;

// Logika relay
const int PUMP_ON  = HIGH;
const int PUMP_OFF = LOW;

WiFiClient espClient;
PubSubClient client(espClient);

// State management pompa untuk melacak kondisi terkini
bool pumpRunning = false;

// Proteksi Fail-Safe: Batas maksimal pompa boleh menyala terus-menerus
unsigned long pumpStartTime = 0;
const unsigned long SAFETY_TIMEOUT_MS = 30000; // 30 detik


void publishStatus(const char* status) {
  // Mengirim feedback status ke server agar sinkron
  StaticJsonDocument<100> doc;
  doc["pump"] = status;

  char buffer[100];
  serializeJson(doc, buffer);

  client.publish(topic_status, buffer);
}


void pumpOn() {
  // Mencegah pengiriman sinyal HIGH berulang jika pompa sudah menyala
  if (!pumpRunning) {
    digitalWrite(PUMP_PIN, PUMP_ON);
    pumpRunning = true;
    pumpStartTime = millis(); // Mulai timer proteksi timeout

    Serial.println("ACTUATOR: Pump ON");
    publishStatus("ON");
  } else {
    Serial.println("ACTUATOR: Pump already ON");
  }
}


void pumpOff() {
  // Mencegah pengiriman sinyal LOW berulang jika pompa sudah mati
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
  Serial.println("\nConnecting to WiFi...");

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  // Menahan eksekusi program hingga koneksi WiFi stabil
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}


void callback(char* topic, byte* payload, unsigned int length) {
  // Handler yang dieksekusi otomatis saat menerima pesan dari MQTT Broker
  Serial.print("Command arrived [");
  Serial.print(topic);
  Serial.print("] ");

  String message = "";
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);

  // Abaikan pesan jika berasal dari topik yang tidak relevan
  if (String(topic) != topic_subscribe) {
    return;
  }

  // Melakukan parsing pada format JSON
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

  // Eksekusi fungsi aktuator berdasarkan instruksi dari server
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
  // Menjaga agar perangkat aktuator selalu terhubung ulang jika koneksi putus
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection (Actuator Node)...");

    String clientId = "ESP8266Actuator-";
    clientId += String(random(0xffff), HEX);

    if (client.connect(clientId.c_str(), mqtt_user, mqtt_pass)) {
      Serial.println("connected");

      // Subscribe
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

  // Deklarasi pin dan inisialisasi safe state (wajib mati saat pertama menyala)
  pinMode(PUMP_PIN, OUTPUT);
  digitalWrite(PUMP_PIN, PUMP_OFF);
  pumpRunning = false;

  setup_wifi();

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback); // Mendaftarkan fungsi penerima pesan
}


void loop() {
  if (!client.connected()) {
    reconnect();
  }

  // Mempertahankan proses lalu lintas data MQTT di latar belakang
  client.loop();

  // Proteksi Fail-Safe:
  // Mematikan pompa secara paksa jika menyala melampaui batas waktu aman (30 detik).
  if (pumpRunning && millis() - pumpStartTime >= SAFETY_TIMEOUT_MS) {
    Serial.println("SAFETY TIMEOUT: Pump forced OFF");
    pumpOff();
  }
}
