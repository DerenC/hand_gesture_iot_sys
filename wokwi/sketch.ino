#include <WiFi.h>
#include <PubSubClient.h>
#include <ESP32Servo.h>

// connect to wifi
const char* ssid = "Wokwi-GUEST"; // Wifi name
const char* password = "";  // Wifi password
const char* mqtt_server = "broker.hivemq.com";

WiFiClient espClient;
PubSubClient client(espClient);

// init the pins
const int BL = 5;
const int GL = 12;
const int GD = 26;

// create servo object
Servo garage_door;
int opened = 180;
int closed = 0;

void callback(char* topic, byte* payload, unsigned int length) {
  String message;

  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  if (message == "BL_ON") {
    digitalWrite(BL, HIGH); // 5V
    Serial.println("--- BEDROOM LIGHT ON ---");
  } else if (message == "BL_OFF") {
    digitalWrite(BL, LOW);  // 0V
    Serial.println("--- BEDROOM LIGHT OFF ---");
  } else if (message == "GL_ON") {
    digitalWrite(GL, HIGH);
    Serial.println("--- GARAGE LIGHT ON ---");
  } else if (message == "GL_OFF") {
    digitalWrite(GL, LOW);
    Serial.println("--- GARAGE LIGHT OFF ---");
  } else if (message == "GD_ON") {
    garage_door.write(opened);
    Serial.println("--- GARAGE DOOR OPENED ---");
  } else if (message == "GD_OFF") {
    garage_door.write(closed);
    Serial.println("--- GARAGE DOOR CLOSED ---");
  } else {
    Serial.println("--- COMMAND NOR RECOGNISED ---");
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.println("Connecting to MQTT ...");
    if (client.connect("WokwiClient")) {
      Serial.println("--- SUCCESSFULLY CONNECTED!! ---");
      client.subscribe("home/central");
    } else {
      Serial.println("--- FAILED TO CONNECT. RC:");
      Serial.print(client.state());
      Serial.print(" ---");
      delay(1000);
      // delay() makes everything asleep and goes into dormant.
      // Be careful when using it. Using here is fine because it is not connected.
    }
  }
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200); // 115200 is the speed at which ESP read the Serial, make sure it matches your model

  // Init pins using vars
  pinMode(GL, OUTPUT);
  pinMode(BL, OUTPUT);

// Init the servo. Connect garage_door Servo object to GD
  garage_door.attach(GD);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
    Serial.print(".");
  }
  Serial.println("--- WIFI CONNECTED ---");

  // Connect to the MQTT server broker
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {
  // put your main code here, to run repeatedly:
  // All the codes here will run infinitely
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  delay(15);
}
