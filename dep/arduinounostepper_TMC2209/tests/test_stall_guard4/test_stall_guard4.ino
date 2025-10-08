#include <TMC2209.h>
#include <SoftwareSerial.h>
#include <ArduinoJson.h>
#include "pinconfig.h"

constexpr uint8_t OUTPUT_BUFFER_SIZE = 192;
constexpr uint8_t INPUT_BUFFER_SIZE = 32;

// 定義命令代碼枚舉
enum CommandCode {
    CMD_ENABLE = 0,
    CMD_SET_VELOCITY = 1,
    CMD_MOVE = 2,
  };

TMC2209 stepper;
SoftwareSerial driverSerial(UNO_RX_PIN, UNO_TX_PIN);

bool motorMoving = false;
bool motorEnabled = false;
int32_t velocity = 600; // 設定預設速度
unsigned long latestLoopTime = 0;

// 用於儲存最後執行的命令訊息
char lastCommandMessage[OUTPUT_BUFFER_SIZE] = { 0 };
bool hasNewCommandMessage = false;

void setup() 
{

    Serial.begin(UNO_BAUDRATE);
    while (!Serial) {}

    pinMode(DIAG_PIN, INPUT);

    stepper.setup(driverSerial, UNO_BAUDRATE);
    stepper.enableStealthChop();
    stepper.setHardwareEnablePin(ENABLE_PIN);
    stepper.setMicrostepsPerStepPowerOfTwo(1);
    resetToSafeCurrentSettings();

    // according to the datasheet:
    // A higher value gives a higher sensitivity. A higher value makes StallGuard4 more sensitive and requires less torque to indicate a stall. 
    // when calling getStallGuardResult(), the returned value is the headroom before stall is declared.
    // if the returnd value of getStallGuardResult() is <= 240 * 2, then the motor is stalled.
    stepper.setStallGuardThreshold(252);
    stepper.enableAutomaticCurrentScaling();
    stepper.enableAutomaticGradientAdaptation();
}

void loop()
{
    if (Serial.available()) {
        const String input = Serial.readStringUntil('\n');
        input.trim();

        if (input.length() > 0) {
            processCommand(input.c_str());
        }
    }
    if (motorEnabled && motorMoving) {
        moveAtVelocity();
    }

    const bool uartStall = checkStallGuardUart();
    const bool diagStall = digitalRead(DIAG_PIN) == LOW;

    char out_message[OUTPUT_BUFFER_SIZE] = { 0 };
    
    // 如果有新的命令訊息，則包含在回應中
    if (hasNewCommandMessage) {
        snprintf(out_message, OUTPUT_BUFFER_SIZE, "%s | UART Stall: %d, DIAG Stall: %d", 
                lastCommandMessage, uartStall, diagStall);
        hasNewCommandMessage = false; // 重置標記
    } else {
        snprintf(out_message, OUTPUT_BUFFER_SIZE, "UART Stall: %d, DIAG Stall: %d", uartStall, diagStall);
    }
    
    sendResponse(out_message, true, 0);
}

void resetToSafeCurrentSettings() 
{
    // 將電流設定重置為安全值，防止馬達過熱
    // 抱歉我炸過一塊TMC2209
    stepper.setRunCurrent(50);    // 設定為 50% 運行電流
    stepper.setHoldCurrent(20);   // 設定為 20% 保持電流
    stepper.setPwmOffset(0);      // 重置 PWM 偏移。enableAutomaticCurrentScaling模式下，PwmOffset數值僅用於初始化，此參數會自動調整
    stepper.setPwmGradient(0);    // 重置 PWM 梯度。enableAutomaticGradientAdaptation模式下，PwmGradient數值僅用於初始化，此參數會自動調整
}

void processCommand(const char* jsonInput) 
{

    int32_t commandCode{ -1 };
    JsonVariant commandValue;
    if (!parseCommand(jsonInput, commandCode, commandValue))
        return;

    int32_t out_value = -1;
    char out_message[OUTPUT_BUFFER_SIZE] = { 0 };
    bool success = executeCommand(commandCode, commandValue, out_value, out_message);
    
    // 儲存命令訊息供 loop 函數使用
    strncpy(lastCommandMessage, out_message, OUTPUT_BUFFER_SIZE - 1);
    lastCommandMessage[OUTPUT_BUFFER_SIZE - 1] = '\0'; // 確保字串結尾
    hasNewCommandMessage = true;
}

bool executeCommand(int32_t commandCode, JsonVariant value, int32_t& out_value, char* out_message) {
    switch (commandCode) {
      case CMD_ENABLE: {
        if (value.is<int32_t>()) {
          int32_t enableValue = value.as<int32_t>();
          if (enableValue == 1) {
            stepper.enable();
            motorEnabled = true;
            out_value = 1;
            stepper.enable();
            strcpy(out_message, "ENB");
            return true;
          } else if (enableValue == 0) {
            stepper.disable();
            motorEnabled = false;
            motorMoving = false; // 停用時也停止移動
            out_value = 0;
            stepper.moveAtVelocity(0);
            stepper.disable();
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
      case CMD_SET_VELOCITY: {
        if (value.is<int32_t>()) {
          velocity = value.as<int32_t>();
          out_value = velocity;
          snprintf(out_message, OUTPUT_BUFFER_SIZE, "Velocity set to %d", velocity);
          return true;
        } else {
          strcpy(out_message, "Velocity must be int.");
          return false;
        }
      }
      case CMD_MOVE: {
        if (value.is<int32_t>()) {
          int32_t moveValue = value.as<int32_t>();
          if (moveValue == 1) {
            if (motorEnabled) {
              motorMoving = true;
              latestLoopTime = millis(); // 重置計時器
              out_value = 1;
              strcpy(out_message, "Move started");
              return true;
            } else {
              strcpy(out_message, "Motor not enabled");
              return false;
            }
          } else if (moveValue == 0) {
            motorMoving = false;
            stepper.moveAtVelocity(0); // 停止馬達
            out_value = 0;
            strcpy(out_message, "Move stopped");
            return true;
          } else {
            strcpy(out_message, "Move must = 0 or 1");
            return false;
          }
        } else {
          strcpy(out_message, "Move value must be int.");
          return false;
        }
      }
      default:
        out_value = commandCode;
        snprintf(out_message, OUTPUT_BUFFER_SIZE, "Unknown CommandCode %d", commandCode);
        return false;
      
    }
  }

void moveAtVelocity() 
{
    if (!motorMoving)
        return;

    const unsigned long currentTimeStamp = millis();
    const bool shouldReverse = ((currentTimeStamp - latestLoopTime) > 3000);
    
    if (shouldReverse) {
        Serial.println("Reversing motor");
        stepper.moveAtVelocity(0); // stop motor before reversing
        velocity *= -1;
        latestLoopTime = currentTimeStamp; // 更新時間戳記
    }
    
    stepper.moveAtVelocity(velocity);
}

bool checkStallGuardUart()
{
    uint16_t sgResult = stepper.getStallGuardResult();
    return sgResult <= 240 * 2; // according to the datasheet, stall is declared when sgResult <= 240 * 2
}

bool parseCommand(const char* jsonInput, int32_t& out_commandCode, JsonVariant& out_value) 
{
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
  

void sendResponse(const char* message, const bool& success, const int32_t& value) 
{
    StaticJsonDocument<OUTPUT_BUFFER_SIZE> response;
    // response["success"] = success;
    response["message"] = message;
    // response["value"] = value;
  
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