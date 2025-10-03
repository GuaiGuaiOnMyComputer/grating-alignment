#!/usr/bin/env python3
"""
Arduino TMC2209 Test Script
Tests TMC2209 stepper motor driver functionality through serial communication
"""

import serial
import json
import time
import logging
import sys
import argparse
from pathlib import Path
from shared.LoggingFormatter import ColoredLoggingFormatter

class ArduinoTMC2209Tester:
    """Test class for Arduino TMC2209 functionality"""
    
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200, timeout=2):
        """
        Initialize the tester
        
        Args:
            port (str): Serial port (e.g., '/dev/ttyUSB0', 'COM3')
            baudrate (int): Baud rate for serial communication
            timeout (float): Serial timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """Setup logger with colored formatter"""
        logger = logging.getLogger('ArduinoTMC2209Tester')
        logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        
        # Use the colored formatter
        formatter = ColoredLoggingFormatter.instance()
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        return logger
    
    def connect(self):
        """Connect to Arduino via serial port"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            time.sleep(2)  # Wait for Arduino to initialize
            self.logger.info("Connected to Arduino on %s at %d baud", self.port, self.baudrate)
            self.logger.info("Arduino response: %s", self.serial_conn.readline().decode('utf-8').strip())
            return True
        except serial.SerialException as e:
            self.logger.error("Failed to connect to Arduino: %s", e)
            return False
    
    def disconnect(self):
        """Disconnect from Arduino"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.logger.info("Disconnected from Arduino")
    
    def send_command(self, command_code, value=None):
        """
        Send a command to Arduino and receive response
        
        Args:
            command_code (int): Command code (0-18)
            value: Command value (int, str, or None)
            
        Returns:
            dict: Response from Arduino or None if failed
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            self.logger.error("Not connected to Arduino")
            return None
        
        # Prepare command
        command = {"CommandCode": command_code}
        if value is not None:
            command["Value"] = value
        
        # Send command
        command_json = json.dumps(command)
        self.logger.debug("Sending command: %s", command_json)
        
        try:
            self.serial_conn.write((command_json + '\n').encode('utf-8'))
            self.serial_conn.flush()
            
            # Read response
            response_line = self.serial_conn.readline().decode('utf-8').strip()
            
            if response_line:
                try:
                    response = json.loads(response_line)
                    self.logger.info("Response: %s", response)
                    
                    # Log the message from response
                    message = response.get('message')
                    if message:
                        self.logger.info("Response message: %s", message)
                    
                    return response
                except json.JSONDecodeError as e:
                    self.logger.error("Failed to parse response: %s", response_line)
                    return None
            else:
                self.logger.warning("No response received from Arduino")
                return None
                
        except Exception as e:
            self.logger.error("Error sending command: %s", e)
            return None
    
    def test_basic_commands(self):
        """Test basic TMC2209 commands"""
        self.logger.info("=== Testing Basic Commands ===")
        
        # Test 1: Enable driver
        self.logger.info("Test 1: Enable driver")
        response = self.send_command(0, 1)  # Enable
        if response and response.get('success'):
            self.logger.info("✓ Driver enabled successfully")
        else:
            self.logger.error("✗ Failed to enable driver")
        
        time.sleep(0.5)
        
        # Test 2: Disable driver
        self.logger.info("Test 2: Disable driver")
        response = self.send_command(0, 0)  # Disable
        if response and response.get('success'):
            self.logger.info("✓ Driver disabled successfully")
        else:
            self.logger.error("✗ Failed to disable driver")
        
        time.sleep(0.5)
        
        # Test 3: Check hardware disabled status
        self.logger.info("Test 3: Check hardware disabled status")
        response = self.send_command(2)  # Hardware disabled check
        if response and response.get('success'):
            self.logger.info("✓ Hardware status: %s", response.get('message'))
        else:
            self.logger.error("✗ Failed to check hardware status")
    
    def test_current_settings(self):
        """Test current setting commands"""
        self.logger.info("=== Testing Current Settings ===")
        
        # Test run current
        self.logger.info("Test 4: Set run current to 50%")
        response = self.send_command(9, 50)  # Set run current
        if response and response.get('success'):
            self.logger.info("✓ Run current set successfully")
        else:
            self.logger.error("✗ Failed to set run current")
        
        time.sleep(0.5)
        
        # Test hold current
        self.logger.info("Test 5: Set hold current to 25%")
        response = self.send_command(10, 25)  # Set hold current
        if response and response.get('success'):
            self.logger.info("✓ Hold current set successfully")
        else:
            self.logger.error("✗ Failed to set hold current")
    
    def test_standstill_modes(self):
        """Test standstill mode commands"""
        self.logger.info("=== Testing Standstill Modes ===")
        
        modes = [
            (0, "NORMAL"),
            (1, "FREEWHEELING"),
            (2, "STRONG_BRAKING"),
            (3, "BRAKING")
        ]
        
        for mode_value, mode_name in modes:
            self.logger.info("Test 6.%d: Set standstill mode to %s", mode_value + 1, mode_name)
            response = self.send_command(11, mode_value)
            if response and response.get('success'):
                self.logger.info("✓ Standstill mode set to %s", mode_name)
            else:
                self.logger.error("✗ Failed to set standstill mode to %s", mode_name)
            time.sleep(0.5)
    
    def test_microstepping(self):
        """Test microstepping commands"""
        self.logger.info("=== Testing Microstepping ===")
        
        # Test microsteps per step (powers of 2)
        microstep_values = [1, 2, 4, 8, 16, 32, 64]
        
        for i, microsteps in enumerate(microstep_values):
            self.logger.info("Test 7.%d: Set microsteps per step to %d", i + 1, microsteps)
            response = self.send_command(13, microsteps)
            if response and response.get('success'):
                self.logger.info("✓ Microsteps per step set to %d", microsteps)
            else:
                self.logger.error("✗ Failed to set microsteps to %d", microsteps)
            time.sleep(0.5)
        
        # Test microstep exponent
        self.logger.info("Test 8: Set microstep exponent to 3 (2^3 = 8)")
        response = self.send_command(14, 3)
        if response and response.get('success'):
            self.logger.info("✓ Microstep exponent set successfully")
        else:
            self.logger.error("✗ Failed to set microstep exponent")
    
    def test_pwm_settings(self):
        """Test PWM settings"""
        self.logger.info("=== Testing PWM Settings ===")
        
        # Test PWM offset
        self.logger.info("Test 9: Set PWM offset to 128")
        response = self.send_command(7, 128)
        if response and response.get('success'):
            self.logger.info("✓ PWM offset set successfully")
        else:
            self.logger.error("✗ Failed to set PWM offset")
        
        time.sleep(0.5)
        
        # Test PWM gradient
        self.logger.info("Test 10: Set PWM gradient to 64")
        response = self.send_command(8, 64)
        if response and response.get('success'):
            self.logger.info("✓ PWM gradient set successfully")
        else:
            self.logger.error("✗ Failed to set PWM gradient")
    
    def test_communication(self):
        """Test communication status"""
        self.logger.info("=== Testing Communication ===")
        
        # Test communication status
        self.logger.info("Test 11: Check communication status")
        response = self.send_command(17)  # Is setup and communicating
        if response and response.get('success'):
            self.logger.info("✓ Communication status: %s", response.get('message'))
        else:
            self.logger.error("✗ Failed to check communication status")
    
    def test_error_handling(self):
        """Test error handling with invalid commands"""
        self.logger.info("=== Testing Error Handling ===")
        
        # Test invalid enable value
        self.logger.info("Test 12: Test invalid enable value (should fail)")
        response = self.send_command(0, 5)  # Invalid enable value
        if response and not response.get('success'):
            self.logger.info("✓ Error handling works correctly")
        else:
            self.logger.warning("✗ Error handling may not be working")
        
        time.sleep(0.5)
        
        # Test invalid command code
        self.logger.info("Test 13: Test invalid command code (should fail)")
        response = self.send_command(99)  # Invalid command code
        if response and not response.get('success'):
            self.logger.info("✓ Invalid command handling works correctly")
        else:
            self.logger.warning("✗ Invalid command handling may not be working")
    
    def run_all_tests(self):
        """Run all test suites"""
        self.logger.info("Starting Arduino TMC2209 Test Suite")
        self.logger.info("=" * 50)
        
        if not self.connect():
            return False
        
        try:
            self.test_basic_commands()
            self.test_current_settings()
            self.test_standstill_modes()
            self.test_microstepping()
            self.test_pwm_settings()
            self.test_communication()
            self.test_error_handling()
            
            self.logger.info("=" * 50)
            self.logger.info("All tests completed!")
            
        except KeyboardInterrupt:
            self.logger.warning("Test interrupted by user")
        except Exception as e:
            self.logger.error("Unexpected error during testing: %s", e)
        finally:
            self.disconnect()
        
        return True

def main():
    """Main function"""
    
    parser = argparse.ArgumentParser(description='Test Arduino TMC2209 functionality')
    parser.add_argument('--port', '-p', default='/dev/ttyUSB0',
                       help='Serial port (default: /dev/ttyUSB0)')
    parser.add_argument('--baudrate', '-b', type=int, default=115200,
                       help='Baud rate (default: 115200)')
    parser.add_argument('--timeout', '-t', type=float, default=2.0,
                       help='Serial timeout in seconds (default: 2.0)')
    
    args = parser.parse_args()
    
    # Create and run tester
    tester = ArduinoTMC2209Tester(
        port=args.port,
        baudrate=args.baudrate,
        timeout=args.timeout
    )
    
    tester.run_all_tests()

if __name__ == "__main__":
    main()