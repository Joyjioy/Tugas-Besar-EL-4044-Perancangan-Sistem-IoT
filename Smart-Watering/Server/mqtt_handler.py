import json
import paho.mqtt.client as mqtt
from email_service import send_email
from config import (
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_USERNAME,
    MQTT_PASSWORD,
    TOPIC_SOIL,
    TOPIC_PUMP_CMD
)
# Import fungsi kendali feedback yang baru
from irrigation_logic import evaluate_feedback_control
from weather_service import weather_data
from database import save_history

latest_data = {
    "soil": 0,
    "pump": "OFF",
    "weather": {}
}

client = mqtt.Client()
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

def publish_pump_action(action):
    """Mengirim perintah kontrol ON/OFF ke ESP8266 via MQTT"""
    payload = {
        "action": action
    }
    
    # Kirim notifikasi email hanya saat pompa pertama kali menyala
    if action == "ON":
        send_email("Pompa Aktif", "Pompa menyala, mendeteksi tanah kering. Memulai kendali feedback.")

    client.publish(
        TOPIC_PUMP_CMD,
        json.dumps(payload)
    )
    
    latest_data["pump"] = action

def on_connect(client, userdata, flags, rc):
    print("MQTT Connected")
    client.subscribe(TOPIC_SOIL)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        soil = data["soil"]

        latest_data["soil"] = soil
        latest_data["weather"] = dict(weather_data)

        print(f"Soil Sensor Feedback: {soil}")

        # Proteksi Faktor Cuaca
        if weather_data["rain"]:
            print("Skip/Stop watering because rain")
            # Jika sedang menyiram lalu mendadak hujan, matikan pompa seketika
            if latest_data["pump"] == "ON":
                publish_pump_action("OFF")
        else:
            # Jalankan logika sistem kendali closed-loop
            action = evaluate_feedback_control(soil)
            
            if action in ["ON", "OFF"]:
                publish_pump_action(action)

        # Simpan log ke database SQLite
        save_history(
            soil=soil,
            pump=latest_data["pump"],
            humidity=weather_data["humidity"],
            temperature=weather_data["temperature"],
            rain=weather_data["rain"]
        )

    except Exception as e:
        print("MQTT Error:", e)

client.on_connect = on_connect
client.on_message = on_message

def start_mqtt():
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()