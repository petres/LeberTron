#define trigPinA 6
#define echoPinA 5

#define trigPinB 9
#define echoPinB 10

int distanceA;
int distanceB;

void setup() {
	Serial.begin(9600);
	pinMode(trigPinA, OUTPUT);
	pinMode(trigPinB, OUTPUT);
	pinMode(echoPinA, INPUT);
	pinMode(echoPinB, INPUT);

	digitalWrite(trigPinA, LOW);
	digitalWrite(trigPinB, LOW);
}

void loop() {
	distanceA = getDistance(trigPinA, echoPinA);
	distanceB = getDistance(trigPinB, echoPinB);

	Serial.print(distanceA);
	Serial.print(" ");
	Serial.println(distanceB);
	Serial.flush();

	delay(40);
}

unsigned int getDistance(int trigPin, int echoPin) {
	digitalWrite(trigPin, HIGH);
	delayMicroseconds(10);
	digitalWrite(trigPin, LOW);
	return pulseIn(echoPin, HIGH, 10000);
}
