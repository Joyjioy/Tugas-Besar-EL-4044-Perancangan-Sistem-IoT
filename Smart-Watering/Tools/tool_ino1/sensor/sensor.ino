#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ================= CONFIGURATION =================
// Kredensial jaringan lokal
const char* ssid         = "CISITU BARU 4G";
const char* password     = "cisitubaru72";

// Konfigurasi broker MQTT
const char* mqtt_server  = "iwkrmq.pptik.id";
const int mqtt_port      = 1883;
const char* mqtt_user    = "/trainerkit:trainerkit";
const char* mqtt_pass    = "12345678";

// Topik publikasi khusus untuk data sensor
const char* topic_publish = "smartwatering/soil/data";
// =================================================

// Pin analog A0 digunakan untuk membaca output sensor kelembapan tanah
const int SOIL_PIN = A0;

WiFiClient espClient;
PubSubClient client(espClient);

// Variabel untuk interval pengiriman data secara asinkron (tanpa fungsi delay)
unsigned long lastMsg = 0;
const unsigned long publishInterval = 3000; // Siklus pembacaan: 3 detik

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.println("Connecting to WiFi...");

  WiFi.mode(WIFI_STA); // Set mode sebagai Station (klien WiFi standar)
  WiFi.begin(ssid, password);

  // Menahan program hingga koneksi WiFi berhasil terbentuk
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
  // Looping perlindungan: terus mencoba selama koneksi ke broker terputus
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection (Sensor Node)...");

    // Membuat ID klien unik secara acak untuk menghindari bentrok koneksi di broker
    String clientId = "WemosSensor-";
    clientId += String(random(0xffff), HEX);

    if (client.connect(clientId.c_str(), mqtt_user, mqtt_pass)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000); // Jeda sebelum melakukan percobaan ulang
    }
  }
}

void setup() {
  Serial.begin(115200);
  setup_wifi();

  // Menetapkan alamat target server MQTT
  client.setServer(mqtt_server, mqtt_port);
  
  // Sinkronisasi waktu agar pembacaan pertama langsung dieksekusi di dalam loop()
  lastMsg = millis() - publishInterval;
}

void loop() {
  // Memastikan koneksi MQTT selalu hidup (keep-alive)
  if (!client.connected()) {
    reconnect();
  }

  // Menjaga proses background jaringan (seperti merespons ping dari broker)
  client.loop();

  unsigned long now = millis();

  // Mekanisme Non-Blocking: Blok ini hanya tereksekusi setiap 3 detik.
  if (now - lastMsg > publishInterval) {
    lastMsg = now;

    // Membaca nilai resistansi analog dari tanah (rentang nilai 0-1023)
    int soilValue = analogRead(SOIL_PIN);

    // Alokasi memori untuk struktur JSON (kapasitas 100 bytes sangat cukup)
    StaticJsonDocument<100> doc;
    doc["soil"] = soilValue;

    // Mengonversi objek JSON menjadi format string teks (serialisasi)
    char buffer[128];
    serializeJson(doc, buffer);

    Serial.print("Publishing soil data: ");
    Serial.println(buffer);

    // Mengirim payload JSON utuh ke broker untuk diolah oleh Server FastAPI
    client.publish(topic_publish, buffer);
  }
}
