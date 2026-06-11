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
    Menentukan kategori kondisi tanah.
    Nilai soil semakin besar = tanah semakin kering.
    """

    if soil > DRY_LIMIT:
        return "Kering"

    elif soil <= LIMIT_AKTIF:
        return "Basah"

    else:
        return "Normal"


def get_recommendation(soil, pump, rain):
    """
    Membuat rekomendasi/penjelasan keputusan sistem untuk dashboard.
    """

    soil_status = get_soil_status(soil)

    if rain:
        return "Penyiraman ditunda karena terdeteksi hujan."

    if soil_status == "Kering" and pump == "ON":
        return "Tanah kering, pompa dinyalakan."

    if soil_status == "Kering" and pump != "ON":
        return "Tanah kering, tetapi sistem menunggu cooldown atau keputusan kontrol."

    if soil_status == "Normal":
        return "Kelembapan tanah masih dalam batas aman."

    if soil_status == "Basah":
        return "Tanah sudah cukup basah, pompa dimatikan."

    return "Sistem sedang memantau kondisi tanah."


def publish_pump_action(action):
    """
    Mengirim perintah ON/OFF ke aktuator melalui MQTT.
    Payload yang dikirim:
    {"action": "ON"} atau {"action": "OFF"}
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

    if action == "ON":
        send_email(
            "Pompa Aktif",
            "Pompa menyala karena tanah terdeteksi kering. Sistem feedback control dimulai."
        )


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT Connected")
        client.subscribe(TOPIC_SOIL)
        print(f"Subscribed to: {TOPIC_SOIL}")
    else:
        print(f"MQTT connection failed with code: {rc}")


def on_message(client, userdata, msg):

    try:
        payload_text = msg.payload.decode()
        data = json.loads(payload_text)

        if "soil" not in data:
            print("MQTT Error: key 'soil' not found in payload")
            return

        soil = int(data["soil"])

        latest_data["soil"] = soil
        latest_data["soil_status"] = get_soil_status(soil)
        latest_data["weather"] = dict(weather_data)
        latest_data["last_update"] = time.time()

        print(f"Soil: {soil}")
        print(f"Soil status: {latest_data['soil_status']}")

        rain = bool(weather_data.get("rain", False))

        if rain:
            print("Skip watering because rain")

            if latest_data["pump"] != "OFF":
                publish_pump_action("OFF")
            else:
                latest_data["pump"] = "OFF"

        else:
            action = evaluate_feedback_control(soil)

            if action == "ON":
                print("Feedback control result: PUMP ON")
                publish_pump_action("ON")

            elif action == "OFF":
                print("Feedback control result: PUMP OFF")
                publish_pump_action("OFF")

            else:
                print("Feedback control result: no change")

        latest_data["recommendation"] = get_recommendation(
            soil=soil,
            pump=latest_data["pump"],
            rain=rain
        )

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
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
