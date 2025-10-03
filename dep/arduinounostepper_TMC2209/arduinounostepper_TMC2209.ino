#include <TMC2209.h>
#include <ArduinoJson.h>
#include "pinconfig.h"

TMC2209 stepper;
bool motorMoving = false;

#define INPUT_BUFFER_SIZE 56
#define OUTPUT_BUFFER_SIZE 192

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
  CMD_SET_REPLY_DELAY = 18,
  CMD_GET_STALL_GUARD_RESULT = 19,
  CMD_IS_STANDING_STILL = 20,
  CMD_SENSORLESS_HOMING = 21,
  CMD_RESET_TO_SAFE_CURRENT = 22
};

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    ;  // 等待串口連接
  }

  // 初始化TMC2209
  stepper.setup(driverSerial, UNO_BAUDRATE);
  stepper.setHardwareEnablePin(ENABLE_PIN);
  stepper.enableAutomaticCurrentScaling();
  stepper.enableAutomaticGradientAdaptation();
  stepper.setStandstillMode(TMC2209::NORMAL);
  
  // 設定安全的電流值，防止馬達過熱
  resetToSafeCurrentSettings();

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

  int32_t commandCode{ -1 };
  JsonVariant commandValue;
  if (!parseCommand(jsonInput, commandCode, commandValue))
    return;

  int32_t out_value = -1;
  char out_message[OUTPUT_BUFFER_SIZE] = { 0 };
  bool success = executeCommand(commandCode, commandValue, out_value, out_message);
  sendResponse(out_message, success, out_value);
}

bool parseCommand(const char* jsonInput, int32_t& out_commandCode, JsonVariant& out_value) {
  StaticJsonDocument<INPUT_BUFFER_SIZE> doc;
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

bool executeCommand(int32_t commandCode, JsonVariant value, int32_t& out_value, char* out_message) {
  switch (commandCode) {
    case CMD_ENABLE: {
      if (value.is<int32_t>()) {
        int32_t enableValue = value.as<int32_t>();
        if (enableValue == 1) {
          stepper.enable();
          out_value = 1;
          strcpy(out_message, "ENB");
          return true;
        } else if (enableValue == 0) {
          stepper.disable();
          out_value = 0;
          strcpy(out_message, "DSB");
          return true;
        } else {
          strcpy(out_message, "Enable must = 0 or 1");
          return false;
        }
      } else {
        strcpy(out_message, "Enable is int.");
        return false;
      }
    }

    case CMD_SET_HARDWARE_ENABLE_PIN: {
      if (value.is<int32_t>()) {
        int32_t pin = value.as<int32_t>();
        if (pin >= 0 && pin <= 255) {
          stepper.setHardwareEnablePin(pin);
          out_value = pin;
          strcpy(out_message, "OK");
          return true;
        } else {
          strcpy(out_message, "Pin must be 0-255");
          return false;
        }
      } else {
        strcpy(out_message, "Pin is int.");
        return false;
      }
    }

    case CMD_HARDWARE_DISABLED:
      out_value = stepper.hardwareDisabled() ? 0 : 1;
      strcpy(out_message, stepper.hardwareDisabled() ? "ENB" : "DSB");
      return true;

    case CMD_ENABLE_ANALOG_CURRENT_SCALING:
      stepper.enableAnalogCurrentScaling();
      out_value = 1;
      strcpy(out_message, "Analog CRT SCL ENB");
      return true;

    case CMD_DISABLE_AUTOMATIC_CURRENT_SCALING:
      stepper.disableAutomaticCurrentScaling();
      out_value = 0;
      strcpy(out_message, "Auto CRT SCL DSB");
      return true;

    case CMD_ENABLE_AUTOMATIC_CURRENT_SCALING:
      stepper.enableAutomaticCurrentScaling();
      out_value = 1;
      strcpy(out_message, "Auto CRT SCL ENB");
      return true;

    case CMD_ENABLE_AUTOMATIC_GRADIENT_ADAPTATION:
      stepper.enableAutomaticGradientAdaptation();
      out_value = 1;
      strcpy(out_message, "Auto GRAD ADA ENB");
      return true;

    case CMD_SET_PWM_OFFSET: {
      if (value.is<int>()) {
        int pwmOffset = value.as<int>();
        if (pwmOffset >= 0 && pwmOffset <= 255) {
          stepper.setPwmOffset(pwmOffset);
          out_value = pwmOffset;
          strcpy(out_message, "OK");
          return true;
        } else {
          strcpy(out_message, "PWM offset in [0-255]");
          return false;
        }
      } else {
        strcpy(out_message, "PWM offset is int");
        return false;
      }
    }

    case CMD_SET_PWM_GRADIENT: {
      if (value.is<int>()) {
        int pwmGradient = value.as<int>();
        if (pwmGradient >= 0 && pwmGradient <= 255) {
          stepper.setPwmGradient(pwmGradient);
          out_value = pwmGradient;
          strcpy(out_message, "OK");
          return true;
        } else {
          strcpy(out_message, "PWM gradient is int in [0-255]");
          return false;
        }
      } else {
        strcpy(out_message, "PWM gradient is int in [0-255]");
        return false;
      }
    }

    case CMD_SET_RUN_CURRENT: {
      if (value.is<int>()) {
        int runCurrent = value.as<int>();
        if (runCurrent >= 0 && runCurrent <= 100) {
          stepper.setRunCurrent(runCurrent);
          out_value = runCurrent;
          strcpy(out_message, "OK");
          return true;
        } else {
          strcpy(out_message, "Run CRT is int in [0, 100]");
          return false;
        }
      } else {
        strcpy(out_message, "Run CRT is int in [0, 100]");
        return false;
      }
    }

    case CMD_SET_HOLD_CURRENT: {
      if (value.is<int>()) {
        int holdCurrent = value.as<int>();
        if (holdCurrent >= 0 && holdCurrent <= 100) {
          stepper.setHoldCurrent(holdCurrent);
          out_value = holdCurrent;
          strcpy(out_message, "OK");
          return true;
        } else {
          strcpy(out_message, "Hold CRT is int in [0, 100]");
          return false;
        }
      } else {
        strcpy(out_message, "Hold CRT is int in [0, 100]");
        return false;
      }
    }

    case CMD_SET_STANDSTILL_MODE: {
      if (value.is<int>()) {
        int mode = value.as<int>();
        switch (mode) {
          case 0:
            stepper.setStandstillMode(TMC2209::NORMAL);
            out_value = 0;
            snprintf(out_message, OUTPUT_BUFFER_SIZE, "Standstill mode=%d", mode);
            return true;
          case 1:
            stepper.setStandstillMode(TMC2209::FREEWHEELING);
            out_value = 1;
            snprintf(out_message, OUTPUT_BUFFER_SIZE, "Standstill mode=%d", mode);
            return true;
          case 2:
            stepper.setStandstillMode(TMC2209::STRONG_BRAKING);
            out_value = 2;
            snprintf(out_message, OUTPUT_BUFFER_SIZE, "Standstill mode=%d", mode);
            return true;
          case 3:
            stepper.setStandstillMode(TMC2209::BRAKING);
            out_value = 3;
            snprintf(out_message, OUTPUT_BUFFER_SIZE, "Standstill mode=%d", mode);
            return true;
          default:
            strcpy(out_message, "Standstill mode is int in [0-3]");
            return false;
        }
      } else {
        strcpy(out_message, "Standstill mode is int in [0-3]");
        return false;
      }
    }

    case CMD_SET_STALL_GUARD_THRESHOLD: {
      if (value.is<int>()) {
        int threshold = value.as<int>();
        if (threshold >= 0 && threshold <= 255) {
          stepper.setStallGuardThreshold(threshold);
          out_value = threshold;
          snprintf(out_message, OUTPUT_BUFFER_SIZE, "StallGuard thesh=%d", threshold);
          return true;
        } else {
          strcpy(out_message, "Threshold is int in [0-255]");
          return false;
        }
      } else {
        strcpy(out_message, "Threshold is int in [0-255]");
        return false;
      }
    }

    case CMD_SET_MICROSTEPS_PER_STEP: {
      if (value.is<int>()) {
        int microsteps = value.as<int>();
        if (isPowerOfTwo(microsteps)) {
          stepper.setMicrostepsPerStep(microsteps);
          out_value = microsteps;
          snprintf(out_message, OUTPUT_BUFFER_SIZE, "Microstep=1/%d", microsteps);
          return true;
        } else {
          strcpy(out_message, "Microsteps is int and must be power of 2");
          return false;
        }
      } else {
        strcpy(out_message, "Microsteps is int and must be power of 2");
        return false;
      }
    }

    case CMD_SET_MICROSTEPS_PER_STEP_POWER_OF_TWO: {
      if (value.is<int>()) {
        int exponent = value.as<int>();
        if (exponent >= 0 && exponent <= 6) {
          stepper.setMicrostepsPerStepPowerOfTwo(exponent);
          out_value = exponent;
          strcpy(out_message, "Ok");
          return true;
        } else {
          strcpy(out_message, "Exponent is int in [0-6]");
          return false;
        }
      } else {
        strcpy(out_message, "Exponent is int in [0-6]");
        return false;
      }
    }

    case CMD_MOVE_AT_VELOCITY: {
      if (!value.is<int>()) {
        strcpy(out_message, "Velocity is int");
        return false;
      }
      const int velocity = value.as<int>();

      if (velocity == 0) {
        motorMoving = false;
        // 停止時重置為安全電流設定
        resetToSafeCurrentSettings();
        strcpy(out_message, "Motor stop.");
        return true;
      }
      
      motorMoving = true;
      stepper.moveAtVelocity(velocity);
      out_value = velocity;
      snprintf(out_message, OUTPUT_BUFFER_SIZE, "Move at v=%d", velocity);
      return true;
    }

    case CMD_GET_STALL_GUARD_RESULT:
      out_value = stepper.getStallGuardResult();
      snprintf(out_message, OUTPUT_BUFFER_SIZE, "SG = %d", out_value);
      return true;

    case CMD_MOVE_USING_STEP_DIR_INTERFACE:
      stepper.moveUsingStepDirInterface();
      out_value = 1;
      strcpy(out_message, "OK");
      return true;

    case CMD_IS_SETUP_AND_COMMUNICATING:
      out_value = stepper.isSetupAndCommunicating() ? 1 : 0;
      strcpy(out_message, stepper.isSetupAndCommunicating() ? "Setup OK" : "Setup failed");
      return true;

    case CMD_SET_REPLY_DELAY: {
      if (value.is<int>()) {
        int delay = value.as<int>();
        stepper.setReplyDelay(delay);
        out_value = delay;
        strcpy(out_message, "OK");
        return true;
      } else {
        strcpy(out_message, "Delay is int");
        return false;
      }
    }

    case CMD_IS_STANDING_STILL: {
      TMC2209::Status status = stepper.getStatus();
      out_value = status.standstill ? 1 : 0;
      strcpy(out_message, status.standstill ? "Standing still" : "Moving");
      return true;
    }
      
    case CMD_SENSORLESS_HOMING: {
      if (!value.is<uint8_t>()) {
        strcpy(out_message, "Direction is uint8_t 0 or 1");
        return false;
      }

      const uint8_t direction = value.as<uint8_t>();
      if (!(direction == 0 || direction == 1)) {
        strcpy(out_message, "Direction is uint8_t 0 or 1");
        return false;
      }

      return sensorlessHoming(direction, out_message, out_value);
    }

    case CMD_RESET_TO_SAFE_CURRENT: {
      resetToSafeCurrentSettings();
      out_value = 1;
      strcpy(out_message, "Reset to safe current settings");
      return true;
    }

    default:
      out_value = commandCode;
      snprintf(out_message, OUTPUT_BUFFER_SIZE, "Unknown CommandCode %d", commandCode);
      return false;
    
  }
}

bool isPowerOfTwo(int n) {
  return n > 0 && (n & (n - 1)) == 0;
}

void sendResponse(const char* message, const bool& success, const int32_t& value) {
  StaticJsonDocument<OUTPUT_BUFFER_SIZE> response;
  response["success"] = success;
  response["message"] = message;
  response["value"] = value;

  char jsonBuffer[OUTPUT_BUFFER_SIZE];  // 相應減少緩衝區大小
  size_t len = serializeJson(response, jsonBuffer, sizeof(jsonBuffer));

  if (response.overflowed()) {
    while (true)
      Serial.println("Overflowed.");
  }

  Serial.println(jsonBuffer);
}

void sendErrorResponse(const char* errorMessage) {
  sendResponse(errorMessage, false, 0);
}

void resetToSafeCurrentSettings() {
  // 將電流設定重置為安全值，防止馬達過熱
  stepper.setRunCurrent(10);    // 設定為 10% 運行電流
  stepper.setHoldCurrent(5);    // 設定為 5% 保持電流
  stepper.setPwmOffset(0);      // 重置 PWM 偏移
  stepper.setPwmGradient(0);    // 重置 PWM 梯度
}

bool sensorlessHoming(uint8_t direction, char* out_message, int32_t& out_value) {
  // 檢查馬達是否正在移動
  if (motorMoving) {
    strcpy(out_message, "Motor is busy");
    return false;
  }
  
  // 設定無感歸零參數
  const uint8_t HOMING_SPEED = 100;           // 歸零速度
  const uint8_t STALL_THRESHOLD = 10;         // StallGuard 門檻
  const uint16_t TIMEOUT_MS = 5000;           // 超時時間 (5秒)
  const uint8_t BACKOFF_SPEED = 50;           // 回退速度
  const uint16_t BACKOFF_DURATION_MS = 200;   // 回退時間
  
  // 設定 StallGuard 參數
  stepper.setStallGuardThreshold(STALL_THRESHOLD);
  
  // 確保馬達啟用
  stepper.enable();
  
  // 開始向指定方向移動
  int32_t velocity = direction * HOMING_SPEED;
  stepper.moveAtVelocity(velocity);
  motorMoving = true;
  
  unsigned long startTime = millis();
  bool homingSuccess = false;
  
  // 輪詢 StallGuard 結果
  while (millis() - startTime < TIMEOUT_MS) {
    uint16_t stallValue = stepper.getStallGuardResult();
    
    // 檢查是否觸發 StallGuard (值小於等於門檻)
    if (stallValue <= STALL_THRESHOLD) {
      homingSuccess = true;
      break;
    }
    
    // 短暫延遲避免過度輪詢
    delay(10);
  }
  
  // 停止馬達
  stepper.moveAtVelocity(0);
  motorMoving = false;
  
  if (homingSuccess) {
    // 回退一小段距離
    stepper.moveAtVelocity(-direction * BACKOFF_SPEED);
    motorMoving = true;
    delay(BACKOFF_DURATION_MS);
    stepper.moveAtVelocity(0);
    motorMoving = false;
    
    out_value = 1;
    strcpy(out_message, "Homing successful");
    return true;
  } else {
    out_value = 0;
    strcpy(out_message, "Homing timeout");
    return false;
  }
}