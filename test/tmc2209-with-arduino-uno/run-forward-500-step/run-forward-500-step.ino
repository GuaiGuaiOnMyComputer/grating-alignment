#include <SoftwareSerial.h>
#include <TMC2209.h>

// Pin assignments
const int RX_PIN = 10;     // Arduino RX (to TMC2209 TX)
const int TX_PIN = 11;     // Arduino TX (to TMC2209 PDN_UART)
const int EN_PIN = 4;      // Enable pin (active LOW)

SoftwareSerial tmcSerial(RX_PIN, TX_PIN);
TMC2209 driver;

void setup() {
  Serial.begin(115200);
  while (!Serial);

  Serial.println("TMC2209 UART Init with Error Checking");

  pinMode(EN_PIN, OUTPUT);
  digitalWrite(EN_PIN, LOW); // Enable driver (active LOW)

  tmcSerial.begin(115200);

  Serial.println("Setting up driver...");
  driver.setup(tmcSerial, 115200);

  // === Check communication ===
  TMC2209::Status status = driver.getStatus();

  // === Set run and hold current ===
  uint8_t runCurrent = 71;   // ~1.5A RMS if R_sense = 0.11Ω
  driver.setRunCurrent(runCurrent);
  driver.setHoldCurrent(20);  // 20% hold current

  Serial.print("Run current set to: ");
  Serial.print(runCurrent);
  Serial.println("% (approx. 1.5A RMS)");

  // === Set standstill mode ===
  driver.setStandstillMode(2);  // 2 = HOLD

  // === Move motor ===
  const long speed = 5120;           // microsteps per second
  const long steps = 51200;          // move one full rev at 256 microsteps
  unsigned long moveTime = steps * 1000UL / speed;

  driver.enable();
  driver.moveAtVelocity(speed);
  Serial.println("Motor moving forward...");

  delay(moveTime);

  driver.moveAtVelocity(0);
  driver.disable();
  digitalWrite(EN_PIN, HIGH);  // disable driver via EN pin
  Serial.println("Motor stopped and driver disabled.");
}

void loop() {
  // nothing here
}
