#include <TMC2209.h>
#include <ArduinoJson.h>
#include "pinconfig.h"

TMC2209 stepper;

SoftwareSerial driverSerial(UNO_RX_PIN, UNO_TX_PIN);

// 定義命令代碼枚舉
enum CommandCode {
  CMD_ENABLE = 0,
  CMD_SET_HARDWARE_ENABLE_PIN = 1,
  CMD_HARDWARE_DISABLED = 2,
  CMD_ENABLE_ANALOG_CURRENT_SCALING = 3,
  CMD_DISABLE_AUTOMATIC_CURRENT_SCALING = 4,
  CMD_ENABLE_AUTOMATIC_CURRENT_SCALING = 5,
  CMD_ENABLE_AUTOMATIC_GRADIENT_ADAPTATION = 6,
  CMD_SET_PWM_OFFSET = 7,
  CMD_SET_PWM_GRADIENT = 8,
  CMD_SET_RUN_CURRENT = 9,
  CMD_SET_HOLD_CURRENT = 10,
  CMD_SET_STANDSTILL_MODE = 11,
  CMD_SET_STALL_GUARD_THRESHOLD = 12,
  CMD_SET_MICROSTEPS_PER_STEP = 13,
  CMD_SET_MICROSTEPS_PER_STEP_POWER_OF_TWO = 14,
  CMD_MOVE_AT_VELOCITY = 15,
  CMD_MOVE_USING_STEP_DIR_INTERFACE = 16,
  CMD_IS_SETUP_AND_COMMUNICATING = 17,
  CMD_SET_REPLY_DELAY = 18
};

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    ; // 等待串口連接
  }
  
  // initialize enable pin
  pinMode(ENABLE_PIN, OUTPUT);
  pinMode(DIAG_PIN, INPUT_PULLUP);
  
  // 初始化TMC2209
  stepper.setup(driverSerial, UNO_BAUDRATE);
  stepper.setHardwareEnablePin(ENABLE_PIN);
  stepper.enableAutomaticCurrentScaling();
  stepper.enableAutomaticGradientAdaptation();

  sendResponse("Ready.", true, 0);
}

void loop() {
  if (Serial.available()) {
    const String input = Serial.readStringUntil('\n');
    input.trim();
    
    if (input.length() > 0) {
      processCommand(input.c_str());
    }
  }
}

void processCommand(const char* jsonInput) {

  int32_t commandCode{-1};
  JsonVariant commandValue;
  if (!parseCommand(jsonInput, commandCode, commandValue))
    return; 

  int32_t out_value = -1;
  char out_message[56] = {0};
  executeCommand(commandCode, commandValue, out_value, out_message);
  sendResponse(out_message, true, out_value);
  memset(out_message, 0, sizeof(out_message));
}

bool parseCommand(const char* jsonInput, int32_t& out_commandCode, JsonVariant& out_value)
{
  StaticJsonDocument<56> doc;
  DeserializationError error = deserializeJson(doc, jsonInput);
  
  if (error) {
    sendErrorResponse("JSON error");
    return false;
  }
  
  if (!doc.containsKey("CommandCode")) {
    sendErrorResponse("Missing CommandCode");
    return false;
  }
  
  out_commandCode = doc["CommandCode"].as<int32_t>();
  out_value = doc["Value"];

  return true;
}

void executeCommand(int commandCode, JsonVariant value, int32_t& out_value, char* out_message) {
  switch (commandCode) {
    case CMD_ENABLE:
      if (value.is<int32_t>()) {
        int32_t enableValue = value.as<int32_t>();
        if (enableValue == 1) {
          stepper.enable();
          out_value = 1;
          strcpy(out_message, "Enabled");
          return;
        } else if (enableValue == 0) {
          stepper.disable();
          out_value = 0;
          strcpy(out_message, "Disabled");
          return;
        } else {
          strcpy(out_message, "Enable must = 0 or 1");
          return;
        }
      } else {
        strcpy(out_message, "Enable be int.");
        return;
      }
      
    case CMD_SET_HARDWARE_ENABLE_PIN:
      if (value.is<int32_t>()) {
        int32_t pin = value.as<int32_t>();
        if (pin >= 0 && pin <= 255) {
          stepper.setHardwareEnablePin(pin);
          out_value = pin;
          strcpy(out_message, "Hardware enable pin set");
          return;
        } else {
          strcpy(out_message, "Pin must be 0-255");
          return;
        }
      } else {
        strcpy(out_message, "Pin must be int.");
        return;
      }
      
    case CMD_HARDWARE_DISABLED:
      out_value = stepper.hardwareDisabled() ? 0 : 1;
      strcpy(out_message, stepper.hardwareDisabled() ? "Disabled" : "Enabled");
      return;
      
    case CMD_ENABLE_ANALOG_CURRENT_SCALING:
      stepper.enableAnalogCurrentScaling();
      out_value = 1;
      strcpy(out_message, "Analog current scaling enb");
      return;
      
    case CMD_DISABLE_AUTOMATIC_CURRENT_SCALING:
      stepper.disableAutomaticCurrentScaling();
      out_value = 0;
      strcpy(out_message, "Auto current scaling dsb");
      return;
      
    case CMD_ENABLE_AUTOMATIC_CURRENT_SCALING:
      stepper.enableAutomaticCurrentScaling();
      out_value = 1;
      strcpy(out_message, "Auto current scaling enb");
      return;
      
    case CMD_ENABLE_AUTOMATIC_GRADIENT_ADAPTATION:
      stepper.enableAutomaticGradientAdaptation();
      out_value = 1;
      strcpy(out_message, "Auto gradient adaptation enb");
      return;
      
    case CMD_SET_PWM_OFFSET:
      if (value.is<int>()) {
        int pwmOffset = value.as<int>();
        if (pwmOffset >= 0 && pwmOffset <= 255) {
          stepper.setPwmOffset(pwmOffset);
          out_value = pwmOffset;
          strcpy(out_message, "PWM offset set");
          return;
        } else {
          strcpy(out_message, "PWM offset must be 0-255");
          return;
        }
      } else {
        strcpy(out_message, "PWM offset must be int");
        return;
      }
      
    case CMD_SET_PWM_GRADIENT:
      if (value.is<int>()) {
        int pwmGradient = value.as<int>();
        if (pwmGradient >= 0 && pwmGradient <= 255) {
          stepper.setPwmGradient(pwmGradient);
          out_value = pwmGradient;
          strcpy(out_message, "PWM gradient set");
          return;
        } else {
          strcpy(out_message, "PWM gradient must be 0-255");
          return;
        }
      } else {
        strcpy(out_message, "PWM gradient must be int.");
        return;
      }
      
    case CMD_SET_RUN_CURRENT:
      if (value.is<int>()) {
        int runCurrent = value.as<int>();
        if (runCurrent >= 0 && runCurrent <= 100) {
          stepper.setRunCurrent(runCurrent);
          out_value = runCurrent;
          strcpy(out_message, "Run current set");
          return;
        } else {
          strcpy(out_message, "Run current in [0, 100]");
          return;
        }
      } else {
        strcpy(out_message, "Run current must be int.");
        return;
      }
      
    case CMD_SET_HOLD_CURRENT:
      if (value.is<int>()) {
        int holdCurrent = value.as<int>();
        if (holdCurrent >= 0 && holdCurrent <= 100) {
          stepper.setHoldCurrent(holdCurrent);
          out_value = holdCurrent;
          strcpy(out_message, "Hold current set");
          return;
        } else {
          strcpy(out_message, "Hold current in [0, 100]");
          return;
        }
      } else {
        strcpy(out_message, "Hold current must be int");
        return;
      }
      
    case CMD_SET_STANDSTILL_MODE:
      if (value.is<int>()) {
        int mode = value.as<int>();
        switch (mode) {
          case 0:
            stepper.setStandstillMode(TMC2209::NORMAL);
            out_value = 0;
            strcpy(out_message, "Mode=NORMAL");
            return;
          case 1:
            stepper.setStandstillMode(TMC2209::FREEWHEELING);
            out_value = 1;
            strcpy(out_message, "Mode=FREEWHEELING");
            return;
          case 2:
            stepper.setStandstillMode(TMC2209::STRONG_BRAKING);
            out_value = 2;
            strcpy(out_message, "Mode=STRONG_BRAKING");
            return;
          case 3:
            stepper.setStandstillMode(TMC2209::BRAKING);
            out_value = 3;
            strcpy(out_message, "Mode=BRAKING");
            return;
          default:
            strcpy(out_message, "Invalid standstill mode, use 0-3");
            return;
        }
      } else {
        strcpy(out_message, "Standstill mode must be int.");
        return;
      }
      
    case CMD_SET_STALL_GUARD_THRESHOLD:
      if (value.is<int>()) {
        int threshold = value.as<int>();
        if (threshold >= 0 && threshold <= 255) {
          stepper.setStallGuardThreshold(threshold);
          out_value = threshold;
          strcpy(out_message, "StallGuard threshold set");
          return;
        } else {
          strcpy(out_message, "Threshold in [0-255]");
          return;
        }
      } else {
        strcpy(out_message, "Threshold must be int.");
        return;
      }
      
    case CMD_SET_MICROSTEPS_PER_STEP:
      if (value.is<int>()) {
        int microsteps = value.as<int>();
        if (isPowerOfTwo(microsteps)) {
          stepper.setMicrostepsPerStep(microsteps);
          out_value = microsteps;
          strcpy(out_message, "Microsteps per step set");
          return;
        } else {
          strcpy(out_message, "Microsteps must be power of 2");
          return;
        }
      } else {
        strcpy(out_message, "Microsteps must be int.");
        return;
      }
      
    case CMD_SET_MICROSTEPS_PER_STEP_POWER_OF_TWO:
      if (value.is<int>()) {
        int exponent = value.as<int>();
        if (exponent >= 0 && exponent <= 6) {
          stepper.setMicrostepsPerStepPowerOfTwo(exponent);
          out_value = exponent;
          strcpy(out_message, "Microstep exponent set");
          return;
        } else {
          strcpy(out_message, "Exponent must be 0-6");
          return;
        }
      } else {
        strcpy(out_message, "Exponent must be int");
        return;
      }
      
    case CMD_MOVE_AT_VELOCITY:
      if (value.is<int>()) {
        int velocity = value.as<int>();
        stepper.moveAtVelocity(velocity);
        out_value = velocity;
        strcpy(out_message, "Moving at velocity");
        return;
      } else {
        strcpy(out_message, "Velocity must be int");
        return;
      }
      
    case CMD_MOVE_USING_STEP_DIR_INTERFACE:
      stepper.moveUsingStepDirInterface();
      out_value = 1;
      strcpy(out_message, "Switched to step/dir mode");
      return;
      
    case CMD_IS_SETUP_AND_COMMUNICATING:
      out_value = stepper.isSetupAndCommunicating() ? 1 : 0;
      strcpy(out_message, stepper.isSetupAndCommunicating() ? "Setup OK" : "Setup failed");
      return;
      
    case CMD_SET_REPLY_DELAY:
      if (value.is<int>()) {
        int delay = value.as<int>();
        stepper.setReplyDelay(delay);
        out_value = delay;
        strcpy(out_message, "Reply delay set");
        return;
      } else {
        strcpy(out_message, "Delay must be int");
        return;
      }
      
    default:
      strcpy(out_message, "Unknown command code");
      return;
  }
}

bool isPowerOfTwo(int n) {
  return n > 0 && (n & (n - 1)) == 0;
}

void sendResponse(const char* message, const bool& success, const int32_t& value) {
  StaticJsonDocument<128> response;  // 減少到128字節以節省記憶體
  response["success"] = success;
  response["message"] = message;
  response["value"] = value;
  
  char jsonBuffer[128];  // 相應減少緩衝區大小
  size_t len = serializeJson(response, jsonBuffer, sizeof(jsonBuffer));
  
  if (len == 0) {
    Serial.println("{\"s\":false,\"m\":\"JSON err\",\"v\":0}");  // 縮短錯誤消息
    return;
  }

  Serial.println(jsonBuffer);
}

void sendErrorResponse(const char* errorMessage) {
  sendResponse(errorMessage, false, 0);
}