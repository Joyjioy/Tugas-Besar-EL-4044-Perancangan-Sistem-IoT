import time
import random
import json

import paho.mqtt.client as mqtt

BROKER = "iwkrmq.pptik.id"
PORT = 1883

USERNAME = "/trainerkit:trainerkit"
PASSWORD = "12345678"

TOPIC_SOIL = "smartwatering/soil/data"

client = mqtt.Client()

client.username_pw_set(USERNAME, PASSWORD)

client.connect(BROKER, PORT, 60)

print("Simulator Started")

while True:

    soil_value = random.randint(300, 850)

    payload = {
        "soil": soil_value
    }

    client.publish(
        TOPIC_SOIL,
        json.dumps(payload)
    )

    print(payload)

    time.sleep(5)