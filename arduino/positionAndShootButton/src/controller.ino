#define trigPinDistance 6
#define echoPinDistance 5

#define shootButtonPin 13

int distance;
int shootButtonState;

void setup() {
	Serial.begin(9600);

	pinMode(trigPinDistance, OUTPUT);
	pinMode(echoPinDistance, INPUT);

	pinMode(shootButtonPin, INPUT_PULLUP);

	digitalWrite(trigPinDistance, LOW);
}

void loop() {
	distance = getDistance(trigPinDistance, echoPinDistance);
	//shootButtonState = (digitalRead(shootButtonPin) == HIGH);
	shootButtonState = digitalRead(shootButtonPin);

	Serial.print(distance);
	Serial.print(" ");
	Serial.println(shootButtonState);
	Serial.flush();

	delay(40);
}

unsigned int getDistance(int trigPin, int echoPin) {
	delay(40);
	digitalWrite(trigPin, HIGH);
	delayMicroseconds(10);
	digitalWrite(trigPin, LOW);
	return pulseIn(echoPin, HIGH, 10000);
}