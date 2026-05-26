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

from irrigation_logic import (
    should_water,
    watering_duration
)

from weather_service import weather_data

from database import save_history

latest_data = {
    "soil": 0,
    "pump": "OFF",
    "weather": {}
}


client = mqtt.Client()
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

def publish_pump(duration):

    send_email(
    "Pompa Aktif",
    f"Pompa menyala selama {duration} detik"
    )
    payload = {
        "action": "ON",
        "duration": duration
    }

    client.publish(
        TOPIC_PUMP_CMD,
        json.dumps(payload)
    )

    latest_data["pump"] = f"ON {duration}s"

    save_pump(duration)



def on_connect(client, userdata, flags, rc):
    print("MQTT Connected")
    client.subscribe(TOPIC_SOIL)



def on_message(client, userdata, msg):

    try:

        data = json.loads(msg.payload.decode())

        soil = data["soil"]

        latest_data["soil"] = soil
        latest_data["weather"] = dict(weather_data)

        print(f"Soil: {soil}")

        # default state
        latest_data["pump"] = "OFF"

        # skip jika hujan
        if weather_data["rain"]:

            print("Skip watering because rain")

        # watering
        elif should_water(soil):

            duration = watering_duration(soil)

            publish_pump(duration)

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