import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
TOPIC = "home/central"

def on_message(client, userdata, message):
    r = int(message.payload.decode())
    print(f"I receive: {r}")

client = mqtt.Client()
client.on_message = on_message
client.connect(BROKER, 1883, 60)
client.subscribe(TOPIC)

print("Listening to the messages...")

client.loop_forever()
