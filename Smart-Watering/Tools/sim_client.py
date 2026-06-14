import time
import random
import json

import paho.mqtt.client as mqtt

# Konfigurasi koneksi jaringan ke broker MQTT
BROKER = "iwkrmq.pptik.id"
PORT = 1883

# Autentikasi perangkat
USERNAME = "/trainerkit:trainerkit"
PASSWORD = "12345678"

# Topik spesifik untuk mengirimkan data tiruan sensor tanah
TOPIC_SOIL = "smartwatering/soil/data"

# Inisialisasi klien MQTT dan pengaturan autentikasi
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)

# Membuka koneksi ke broker dengan batas waktu keep-alive 60 detik
client.connect(BROKER, PORT, 60)

print("Simulator Started")

# Infinite loop, merepresentasikan siklus baca-kirim pada mikrokontroler
while True:
    
    # Menghasilkan nilai resistansi tanah acak antara 300 hingga 850 untuk keperluan pengujian
    soil_value = random.randint(300, 850)

    # Membungkus nilai mentah ke dalam format JSON agar sesuai dengan standar protokol server
    payload = {
        "soil": soil_value
    }

    # Memublikasikan payload ke jaringan MQTT agar bisa ditangkap oleh sistem FastAPI Anda
    client.publish(
        TOPIC_SOIL,
        json.dumps(payload)
    )

    print(payload)

    # Memberikan jeda 5 detik antar pengiriman agar server tidak kelebihan beban (flooding)
    time.sleep(5)
