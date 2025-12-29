import paho.mqtt.client as mqtt
import time
import random

BROKER = "broker.hivemq.com"
TOPIC = "iot/example"

client = mqtt.Client()
client.connect(BROKER, 1883, 60)

while True:
    r = random.randint(10, 100)
    client.publish(TOPIC, r)
    print(f"We published {r}")
    time.sleep(2)
