#define trigPinA 6
#define trigPinB 9

#define echoPin 5

int distanceA;
int distanceB;

unsigned long sensorATime;
unsigned long sensorBTime;

void setup() {                
	Serial.begin(9600);
	pinMode(trigPinA, OUTPUT);
        pinMode(trigPinB, OUTPUT);
	pinMode(echoPin, INPUT);
  
	digitalWrite(trigPinA, LOW);  // Added this line  
        digitalWrite(trigPinB, LOW);
	delayMicroseconds(2); // Added this line
}

void loop() {
	distanceA = getDistance(trigPinA);
	distanceB = getDistance(trigPinB);

	Serial.print("{\"A\": ");
        Serial.print(distanceA);
        Serial.print(", \"B\": ");
        Serial.print(distanceB);
        Serial.println("}; ");

	delay(100);
	//delay(10);
}

unsigned int getDistance(int trigPin) {
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
