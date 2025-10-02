#include <SoftwareSerial.h>

// RX = 10, TX = 11 (change these if you wired differently)
SoftwareSerial mySerial(10, 11);

void setup() {
  // USB Serial Monitor
  Serial.begin(115200);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB
  }

  // Serial from Jetson (via /dev/ttyTHS1)
  mySerial.begin(115200);
  Serial.println("Ready to receive ASCII messages from Jetson...");
}

void loop() {
  // Check if data is available on software serial
  while (mySerial.available() > 0) {
    // Read a byte
    byte incomingByte = mySerial.read();

    // Decode it to ASCII
    char asciiChar = (char)incomingByte;

    // Print ASCII character to Serial Monitor
    Serial.print(asciiChar);
  }
}
