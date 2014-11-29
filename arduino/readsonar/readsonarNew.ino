#define trigPin 6
#define echoPin 5

void setup() {
    Serial.begin (9600);
    pinMode(trigPin, OUTPUT);
    digitalWrite(trigPin, LOW);
    pinMode(echoPin, INPUT);
}

void loop() {
    unsigned long duration;
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);
    duration = pulseIn(echoPin, HIGH);

    Serial.println(duration);
    delay(500);
}
