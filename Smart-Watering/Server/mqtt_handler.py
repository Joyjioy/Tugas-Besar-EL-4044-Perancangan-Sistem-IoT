import json
import time

import paho.mqtt.client as mqtt

from email_service import send_email

from config import (
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_USERNAME,
    MQTT_PASSWORD,
    TOPIC_SOIL,
    TOPIC_PUMP_CMD,
    DRY_LIMIT,
    LIMIT_AKTIF
)

from irrigation_logic import evaluate_feedback_control
from weather_service import weather_data
from database import save_history

# Dictionary 
latest_data = {
    "soil": 0,
    "soil_status": "Unknown",
    "pump": "OFF",
    "weather": {},
    "recommendation": "Menunggu data sensor.",
    "last_update": None
}


client = mqtt.Client()
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)


def get_soil_status(soil):
    """
    Mengonversi nilai numerik sensor kelembapan menjadi kategori tekstual.
    Nilai yang lebih tinggi menunjukkan resistansi tanah yang lebih besar, 
    yang berarti tanah semakin kering.
    """
    if soil > DRY_LIMIT:
        return "Kering"
    elif soil <= LIMIT_AKTIF:
        return "Basah"
    else:
        return "Normal"


def get_recommendation(soil, pump, rain):
    """
    Menghasilkan pesan status dinamis berdasarkan kombinasi tiga variabel:
    kondisi tanah, status pompa, dan cuaca, Untuk memberikan feedback
    real-time kepada pengguna di dashboard mengenai apa yang sedang dilakukan sistem.
    """
    soil_status = get_soil_status(soil)

    # Prioritas tertinggi: Evaluasi cuaca
    if rain:
        return "Penyiraman ditunda karena terdeteksi hujan."

    # Evaluasi saat sistem sedang aktif menyiram
    if soil_status == "Kering" and pump == "ON":
        return "Tanah kering, pompa dinyalakan."

    # Evaluasi proteksi cooldown atau delay kontrol
    if soil_status == "Kering" and pump != "ON":
        return "Tanah kering, tetapi sistem menunggu cooldown atau keputusan kontrol."

    # Kondisi ideal / idle
    if soil_status == "Normal":
        return "Kelembapan tanah masih dalam batas aman."

    # Kondisi pemutusan sistem
    if soil_status == "Basah":
        return "Tanah sudah cukup basah, pompa dimatikan."

    return "Sistem sedang memantau kondisi tanah."


def publish_pump_action(action):
    """
    Membungkus perintah string menjadi payload JSON yang valid sebelum dikirim via MQTT.
    """
    payload = {
        "action": action
    }

    client.publish(
        TOPIC_PUMP_CMD,
        json.dumps(payload)
    )

    latest_data["pump"] = action
    print(f"Publish pump command: {payload}")

    # Notifikasi hanya dipicu saat terjadi transisi state ke "ON"
    if action == "ON":
        send_email(
            "Pompa Aktif",
            "Pompa menyala karena tanah terdeteksi kering. Sistem feedback control dimulai."
        )


def on_connect(client, userdata, flags, rc):
    # rc (Return Code) bernilai 0 jika koneksi ke broker MQTT berhasil.
    if rc == 0:
        print("MQTT Connected")
        # Subskripsi ke topik sensor segera setelah koneksi terbentuk
        client.subscribe(TOPIC_SOIL)
        print(f"Subscribed to: {TOPIC_SOIL}")
    else:
        print(f"MQTT connection failed with code: {rc}")


def on_message(client, userdata, msg):
    """
    Fungsi callback (handler) utama yang tereksekusi setiap kali ada pesan 
    masuk dari topik TOPIC_SOIL.
    """
    try:
        # Decode data biner (byte) menjadi string, lalu parse ke dictionary
        payload_text = msg.payload.decode()
        data = json.loads(payload_text)

        # Error handling
        if "soil" not in data:
            print("MQTT Error: key 'soil' not found in payload")
            return

        soil = int(data["soil"])

        # Memperbarui state global dengan data terbaru untuk disajikan ke API
        latest_data["soil"] = soil
        latest_data["soil_status"] = get_soil_status(soil)
        latest_data["weather"] = dict(weather_data)
        latest_data["last_update"] = time.time()

        print(f"Soil: {soil}")
        print(f"Soil status: {latest_data['soil_status']}")

        # Pengambilan keputusan berlapis (Prioritas Cuaca vs Logika Tanah)
        rain = bool(weather_data.get("rain", False))

        if rain:
            print("Skip watering because rain")
            # Jika hujan turun saat pompa sedang menyala, lakukan interupsi paksa
            if latest_data["pump"] != "OFF":
                publish_pump_action("OFF")
            else:
                latest_data["pump"] = "OFF"

        else:
            # Jika cuaca cerah, serahkan keputusan ke modul logika umpan balik
            action = evaluate_feedback_control(soil)

            if action == "ON":
                print("Feedback control result: PUMP ON")
                publish_pump_action("ON")

            elif action == "OFF":
                print("Feedback control result: PUMP OFF")
                publish_pump_action("OFF")

            else:
                print("Feedback control result: no change")

        # Perbarui pesan rekomendasi setelah semua status terbaru terkalkulasi
        latest_data["recommendation"] = get_recommendation(
            soil=soil,
            pump=latest_data["pump"],
            rain=rain
        )

        # Catat jejak data sensor dan tindakan aktuator ke database
        save_history(
            soil=soil,
            pump=latest_data["pump"],
            humidity=weather_data.get("humidity", 0),
            temperature=weather_data.get("temperature", 0),
            rain=rain
        )

    except Exception as e:
        print("MQTT Error:", e)


client.on_connect = on_connect
client.on_message = on_message


def start_mqtt():
    # Menghubungkan client ke broker dengan batas waktu keep-alive 60 detik
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    # Memulai loop jaringan di thread terpisah agar tidak memblokir server utama
    client.loop_start()
