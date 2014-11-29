#define trigPinA 6
#define trigPinB 9

#define echoPinA 5
#define echoPinB 10

int distanceA;
int distanceB;

unsigned long sensorATime;
unsigned long sensorBTime;

void setup() {                
	Serial.begin(9600);
	pinMode(trigPinA, OUTPUT);
        pinMode(trigPinB, OUTPUT);
	pinMode(echoPin, INPUT);
  
	digitalWrite(trigPinA, LOW);
        digitalWrite(trigPinB, LOW);
	delayMicroseconds(2);
}

void loop() {
	distanceA = getDistance(trigPinA, echoPinA);
	distanceB = getDistance(trigPinB, echoPinB);

        Serial.print(distanceA);
        Serial.print(" ");
        Serial.println(distanceB);

	delay(100);
	//delay(10);
}

unsigned int getDistance(int trigPin, int echoPin) {
	long duration, distance;
	digitalWrite(trigPin, HIGH);
	delayMicroseconds(10); // Added this line
	digitalWrite(trigPin, LOW);
	duration = pulseIn(echoPin, HIGH);
	distance = (duration/2) / 29.1;

	if (distance < 200 && distance > 0) {
		return distance;
	} else {
		return -1;
	}
}
