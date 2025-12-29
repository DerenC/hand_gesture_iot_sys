import paho.mqtt.client as mqtt

class IOTConnection():

    def __init__(self, topic="home/central", broker="broker.hivemq.com"):
        self.topic = topic
        self.broker = broker
        self.client = mqtt.Client()

        self.client.connect(self.broker, 1883, 60)

    def _send_to_topic(self, message):
        self.client.publish(self.topic, message)
