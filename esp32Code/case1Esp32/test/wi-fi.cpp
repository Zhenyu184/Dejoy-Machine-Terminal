#include <Arduino.h>
#include <WiFi.h>

void setup() {
  Serial.begin(9600);
  WiFi.begin("DJ-Guest", "0227731355");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
  Serial.print("\nIP位址：");
  Serial.println(WiFi.localIP());
  Serial.print("WiFi RSSI: ");
  Serial.println(WiFi.RSSI());
}

void loop() {
}











