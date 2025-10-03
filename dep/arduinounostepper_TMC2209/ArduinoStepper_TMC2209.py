import logging
import serial
import json
import sys
import time
from enum import IntEnum
from typing import Optional
from dataclasses import dataclass


class TMC2209Command(IntEnum):
    """TMC2209 command codes corresponding to commandcode.csv"""
    ENABLE = 0
    SET_HARDWARE_ENABLE_PIN = 1
    HARDWARE_DISABLED = 2
    ENABLE_ANALOG_CURRENT_SCALING = 3
    DISABLE_AUTOMATIC_CURRENT_SCALING = 4
    ENABLE_AUTOMATIC_CURRENT_SCALING = 5
    ENABLE_AUTOMATIC_GRADIENT_ADAPTATION = 6
    SET_PWM_OFFSET = 7
    SET_PWM_GRADIENT = 8
    SET_RUN_CURRENT = 9
    SET_HOLD_CURRENT = 10
    SET_STANDSTILL_MODE = 11
    SET_STALL_GUARD_THRESHOLD = 12
    SET_MICROSTEPS_PER_STEP = 13
    SET_MICROSTEPS_PER_STEP_POWER_OF_TWO = 14
    MOVE_AT_VELOCITY = 15
    MOVE_USING_STEP_DIR_INTERFACE = 16
    IS_SETUP_AND_COMMUNICATING = 17
    SET_REPLY_DELAY = 18
    GET_STALL_GUARD_RESULT = 19
    IS_STANDING_STILL = 20
    SENSORLESS_HOMING = 21
    RESET_TO_SAFE_CURRENT = 22

class StandstillMode(IntEnum):
    """Standstill mode values for command 11"""
    NORMAL = 0
    FREEWHEELING = 1
    STRONG_BRAKING = 2
    BRAKING = 3


@dataclass(slots = True)
class _DriverBoardCommand:
    """Structured command for driver board communication"""
    command_code: TMC2209Command
    value: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        cmd_dict = {"CommandCode": int(self.command_code)}
        if self.value is not None:
            cmd_dict["Value"] = self.value
        return cmd_dict
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


@dataclass(slots = True)
class _DriverBoardResponse:
    """Structured response from driver board"""
    success: bool
    message: str
    value: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> '_DriverBoardResponse':
        """Create response from dictionary"""
        return cls(
            success=data.get('success', False),
            message=data.get('message', ''),
            value=data.get('value')
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> '_DriverBoardResponse':
        """Create response from JSON string"""
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError:
            return cls(success=False, message="JSON parse error", value=None)
    
class ArduinoStepper_TMC2209:
    """Arduino TMC2209 Stepper Motor Driver Controller"""

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 2, logger: Optional[logging.Logger] = None):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        self.__logger = self._setup_logger() if logger is None else logger

    def _setup_logger(self) -> logging.Logger:
        """Setup default logger"""
        logger = logging.getLogger('ArduinoStepper_TMC2209')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def connect(self) -> bool:
        """Connect to Arduino via serial port"""
        try:
            # Windows 特定處理：確保端口格式正確
            if sys.platform.startswith('win'):
                if not self.port.startswith('COM'):
                    self.__logger.warning("Windows detected but port doesn't start with COM: %s", self.port)
            
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            
            # 等待 Arduino 初始化
            time.sleep(2)
            
            self.__logger.info("Connected to Arduino on %s at %d baud", self.port, self.baudrate)
            
            # 讀取 Arduino 的歡迎訊息
            try:
                response = self.serial_conn.readline().decode('utf-8').strip()
                if response:
                    self.__logger.info("Arduino response: %s", response)
            except Exception as e:
                self.__logger.warning("Could not read Arduino response: %s", e)
            
            return True
        except serial.SerialException as e:
            self.__logger.error("Failed to connect to Arduino: %s", e)
            return False

    def disconnect(self) -> bool:
        """Disconnect from Arduino"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.__logger.info("Disconnected from Arduino")
        return True

    def disable(self) -> _DriverBoardResponse:
        """Disable the stepper driver"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.ENABLE, 0))

    def enable(self, enable: bool | int) -> _DriverBoardResponse:
        """Enable or disable the stepper driver"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.ENABLE, int(enable)))

    def set_hardware_enable_pin(self, pin: int) -> _DriverBoardResponse:
        """Set hardware enable pin"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.SET_HARDWARE_ENABLE_PIN, pin))

    def is_hardware_disabled(self) -> _DriverBoardResponse:
        """Check if hardware is disabled"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.HARDWARE_DISABLED))

    def enable_analog_current_scaling(self) -> _DriverBoardResponse:
        """Enable analog current scaling"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.ENABLE_ANALOG_CURRENT_SCALING))

    def disable_automatic_current_scaling(self) -> _DriverBoardResponse:
        """Disable automatic current scaling"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.DISABLE_AUTOMATIC_CURRENT_SCALING))

    def enable_automatic_current_scaling(self) -> _DriverBoardResponse:
        """Enable automatic current scaling"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.ENABLE_AUTOMATIC_CURRENT_SCALING))

    def enable_automatic_gradient_adaptation(self) -> _DriverBoardResponse:
        """Enable automatic gradient adaptation"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.ENABLE_AUTOMATIC_GRADIENT_ADAPTATION))

    def set_pwm_offset(self, offset: int) -> _DriverBoardResponse:
        """Set PWM offset (0-255)"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.SET_PWM_OFFSET, offset))

    def set_pwm_gradient(self, gradient: int) -> _DriverBoardResponse:
        """Set PWM gradient (0-255)"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.SET_PWM_GRADIENT, gradient))

    def set_run_current(self, current_percent: int) -> _DriverBoardResponse:
        """Set run current percentage (0-100)"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.SET_RUN_CURRENT, current_percent))

    def set_hold_current(self, current_percent: int) -> _DriverBoardResponse:
        """Set hold current percentage (0-100)"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.SET_HOLD_CURRENT, current_percent))

    def set_standstill_mode(self, mode: StandstillMode) -> _DriverBoardResponse:
        """Set standstill mode"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.SET_STANDSTILL_MODE, int(mode)))

    def set_stall_guard_threshold(self, threshold: int) -> _DriverBoardResponse:
        """Set StallGuard threshold (0-255)"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.SET_STALL_GUARD_THRESHOLD, threshold))

    def set_microsteps_per_step(self, microsteps: int) -> _DriverBoardResponse:
        """Set microsteps per step (must be power of 2)"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.SET_MICROSTEPS_PER_STEP, microsteps))

    def set_microsteps_per_step_power_of_two(self, exponent: int) -> _DriverBoardResponse:
        """Set microsteps per step using power of two exponent (0-6)"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.SET_MICROSTEPS_PER_STEP_POWER_OF_TWO, exponent))

    def move_at_velocity(self, velocity: int) -> _DriverBoardResponse:
        """Move at specified velocity"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.MOVE_AT_VELOCITY, velocity))

    def stop_moving(self) -> _DriverBoardResponse:
        """Stop moving"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.MOVE_AT_VELOCITY, 0))

    def move_using_step_dir_interface(self) -> _DriverBoardResponse:
        """Switch to step/dir interface mode"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.MOVE_USING_STEP_DIR_INTERFACE))

    def is_setup_and_communicating(self) -> _DriverBoardResponse:
        """Check if setup and communication is OK"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.IS_SETUP_AND_COMMUNICATING))

    def set_reply_delay(self, delay: int) -> _DriverBoardResponse:
        """Set reply delay"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.SET_REPLY_DELAY, delay))

    def get_stall_guard_result(self) -> _DriverBoardResponse:
        """Get StallGuard result"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.GET_STALL_GUARD_RESULT))

    def is_standing_still(self) -> _DriverBoardResponse:
        """Check if motor is standing still"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.IS_STANDING_STILL))

    def reset_to_safe_current(self) -> _DriverBoardResponse:
        """Reset to safe current"""
        return self._send_command_and_receive_response(_DriverBoardCommand(TMC2209Command.RESET_TO_SAFE_CURRENT))

    def _send_command(self, command: _DriverBoardCommand) -> bool:
        """Send command to Arduino and receive response"""
        if not self.serial_conn or not self.serial_conn.is_open:
            self.__logger.error("Not connected to Arduino")
            return False

        # Send command
        command_json = command.to_json()
        self.__logger.debug("Sending command: %s", command_json)

        try:
            self.serial_conn.write((command_json + '\n').encode('utf-8'))
            self.serial_conn.flush()
            return True

        except serial.SerialException as e:
            self.__logger.error("Error sending command: %s", e)
            return False

    def _receive_response(self) -> _DriverBoardResponse:
        """Receive response from Arduino"""

        response_line: str | None = None
        try:
            # Read response
            response_line = self.serial_conn.readline().decode('utf-8').strip()

            if response_line:
                self.__logger.debug("Received response: %s", response_line)
                return _DriverBoardResponse.from_json(response_line)

            return _DriverBoardResponse(success=False, message="No response", value=None)

        except serial.SerialTimeoutException as e:
            self.__logger.error("Timeout receiving response: %s", e)
            return _DriverBoardResponse(success=False, message="Timeout", value=None)

        except json.JSONDecodeError as e:
            self.__logger.error("Error decoding response: %s", e)
            return _DriverBoardResponse(success = False, message = f"Cannot decode response: {response_line}", value = None)

    def _send_command_and_receive_response(self, command: _DriverBoardCommand) -> _DriverBoardResponse:
        """Send command and receive response"""
        if not self._send_command(command):
            self.__logger.error("Command failed when sending command %s", command.command_code)
            return _DriverBoardResponse(success=False, message="Communication error", value=None)

        response: _DriverBoardResponse = self._receive_response()
        if not response.success:
            self.__logger.error("Receive response error after sending command %s: %s", command.command_code, response.message)
            return response

        self.__logger.debug("Received response after sending command %s: %s", command.command_code, response.message)
        return response