// float in = 0.00;
// float cm = 0.00;
// int SonarPin = A0;
// int sensorValue;

// void setup() {
// 	pinMode(SonarPin, INPUT);
// 	Serial.begin(9600);
// }

// void loop() {
// 	  sensorValue = analogRead(SonarPin);
// 	  delay(50);
// 	  //in = (sensorValue * 0.497);
// 	  cm = (sensorValue * 1.26238);
// 	//  Serial.println(sensorValue);
// 	//  Serial.print(in);
// 	//  Serial.println("inch");
// 	  Serial.println(cm);
// 	 //Serial.println(" cm");
// 	  delay(500);
// }



#define trigPin 6
#define echoPin 5

void setup() {
  Serial.begin (9600);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
}

void loop() {
  long duration, distance;
  digitalWrite(trigPin, LOW);  // Added this line
  delayMicroseconds(2); // Added this line
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10); // Added this line
  digitalWrite(trigPin, LOW);
  duration = pulseIn(echoPin, HIGH);
  distance = (duration/2) / 29.1;

  if (distance < 200 || distance > 0) {
    Serial.println(distance);
    //Serial.println(" cm");
  }
  delay(200);
}