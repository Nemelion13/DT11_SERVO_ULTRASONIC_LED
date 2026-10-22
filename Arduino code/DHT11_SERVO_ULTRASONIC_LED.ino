#include "DHT.h"
#include <Servo.h>
#include <Wire.h>


#define TRIG_PIN 6
#define ECHO_PIN 7
#define LEDPin 8      // LED contrôlée par Python
#define BuzzerPin 2
#define ledAlert 4    // LED d'alerte distance
#define servoPIN 9
#define DHTPIN 11
#define DHTTYPE DHT11



DHT dht(DHTPIN, DHTTYPE);
Servo myservo;

// Variables de contrôle
bool autoMode = false;
int servoAngle = 90;
int servoDirection = 1;
unsigned long prevMillisDHT = 0;
unsigned long prevMillisServo = 0;
unsigned long prevMillisAlert = 0;
bool alertBlink = false;

const int DISTANCE_THRESHOLD = 15;

void setup() {
  Serial.begin(9600);
  dht.begin();
  
  myservo.attach(servoPIN);
  pinMode(LEDPin, OUTPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(ledAlert, OUTPUT);
  pinMode(BuzzerPin, OUTPUT);
}

void loop() {
  unsigned long currentMillis = millis();

  // 1. RÉCEPTION DES COMMANDES PYTHON
  if (Serial.available() > 0) {
    char type = Serial.read();
    if (type == 'L') {
      digitalWrite(LEDPin, Serial.parseInt());
    } 
    else if (type == 'M') {
      autoMode = Serial.parseInt();
    }
    else if (type == 'S') {
      servoAngle = Serial.parseInt();
      if (!autoMode) myservo.write(servoAngle);
    }
  }

  // 2. MODE AUTOMATIQUE SERVO
  if (autoMode) {
    if (currentMillis - prevMillisServo >= 20) {
      prevMillisServo = currentMillis;
      servoAngle += servoDirection;
      if (servoAngle >= 180 || servoAngle <= 0) servoDirection *= -1;
      myservo.write(servoAngle);
    }
  }

  // 3. LECTURE CAPTEURS ET ALERTE
  if (currentMillis - prevMillisDHT >= 500) { // On vérifie la distance plus souvent (0.5s)
    prevMillisDHT = currentMillis;
    
    // Mesure distance ultrason
    digitalWrite(TRIG_PIN, LOW); delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH); delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);
    long duration = pulseIn(ECHO_PIN, HIGH, 30000); // Timeout pour éviter de bloquer
    float distance_cm = (duration * 0.0343) / 2;
    

    // --- LOGIQUE D'ALERTE ---
    if (distance_cm > 0 && distance_cm < DISTANCE_THRESHOLD) {
      // Clignotement et bip (non-bloquant via l'état alertBlink)
      alertBlink = !alertBlink;
      digitalWrite(ledAlert, alertBlink);
      if (alertBlink) tone(BuzzerPin, 400, 200); 
    } else {
      digitalWrite(ledAlert, LOW);
      noTone(BuzzerPin);
    }

    // Envoi JSON vers Python toutes les 2 secondes (via un compteur)
    static int jsonCounter = 0;
    jsonCounter++;
    if (jsonCounter >= 4) { // 4 * 500ms = 2s
      jsonCounter = 0;
      float h = dht.readHumidity();
      float t = dht.readTemperature();
      if (!isnan(h) && !isnan(t)) {
        float hic = dht.computeHeatIndex(t, h, false);
        Serial.print(F("{\"Humidity\":")); Serial.print(h);
        Serial.print(F(",\"Temperature\":")); Serial.print(t);
        Serial.print(F(",\"Heat_index\":")); Serial.print(hic);
        Serial.print(F(",\"Distance\":")); Serial.print(distance_cm);
        Serial.println(F("}"));
      }
    }

  }
}