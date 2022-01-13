#include <Servo.h>

Servo s1;
Servo s2;
Servo s3;
Servo s4;

String serialData;

int parseData1(String data) {
  data.remove(data.indexOf("a"), 1);
  data.remove(data.indexOf("b"));
  return data.toInt();
}

int parseData2(String data) {
  data.remove(0, data.indexOf("b")+1);
  data.remove(data.indexOf("c"));
  return data.toInt();
}

int parseData3(String data) {
  data.remove(0, data.indexOf("c")+1);
  data.remove(data.indexOf("d"));
  return data.toInt();
}

int parseData4(String data) {
  data.remove(0, data.indexOf("d")+1);
  return data.toInt();
}

void setup() {

  s1.attach(3);
  s2.attach(5);
  s3.attach(6);
  s4.attach(9);

  Serial.begin(9600);
  Serial.setTimeout(10);

  s1.write(90);
  s2.write(45);
  s3.write(135);
  s4.write(0);

  delay(3000);

}

void loop() {
  
  //lol

}

void serialEvent() {

  serialData = Serial.readString();
  
  s1.write(parseData1(serialData));
  s2.write(parseData2(serialData));
  s3.write(parseData3(serialData));
  s4.write(parseData4(serialData));

}
