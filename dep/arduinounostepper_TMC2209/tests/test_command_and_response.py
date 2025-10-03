#!/usr/bin/env python3
"""
Arduino TMC2209 Test Script
Tests TMC2209 stepper motor driver functionality through serial communication
"""

import time
import logging
import argparse
import serial.tools.list_ports
from typing import Literal
from shared.LoggingFormatter import ColoredLoggingFormatter
from dep.arduinounostepper_TMC2209.ArduinoStepper_TMC2209 import ArduinoStepper_TMC2209, StandstillMode

class ArduinoTMC2209Tester:
    """Test class for Arduino TMC2209 functionality"""
    
    def __init__(self, port, skip_movement_tests: bool = True, baudrate = 115200, timeout = 2, logger: logging.Logger | None = None):
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
        self.logger = self._setup_logger() if logger is None else logger
        self.skip_movement_tests = skip_movement_tests
        self.stepper = ArduinoStepper_TMC2209(self.port, baudrate, timeout, self._setup_logger("ArduinoTMC2209", is_disabled = False, default_level = logging.DEBUG))
        
    def _setup_logger(self, logger_name: str = 'ArduinoTMC2209Tester', default_level: Literal = logging.DEBUG, is_disabled: bool = False) -> logging.Logger:
        """Setup logger with colored formatter"""
        logger = logging.getLogger(logger_name)
        logger.setLevel(default_level)
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create console handler
        console_handler = logging.StreamHandler() if not is_disabled else logging.NullHandler()
        console_handler.setLevel(default_level)
        
        # Use the colored formatter
        formatter = ColoredLoggingFormatter.instance()
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        return logger
    
    def connect(self):
        """Connect to Arduino via serial port"""
        return self.stepper.connect()
    
    def disconnect(self):
        """Disconnect from Arduino"""
        return self.stepper.disconnect()
    
    def test_basic_commands(self) -> bool:
        """Test basic TMC2209 commands"""
        self.logger.info("=== Testing Basic Commands ===")
        
        all_passed = True
        
        # Test 1: Enable driver
        self.logger.info("Test 1: Enable driver")
        response = self.stepper.enable(1)
        if response.success:
            self.logger.info("✓ Driver enabled successfully")
        else:
            self.logger.error("✗ Failed to enable driver: %s", response.message)
            all_passed = False
        
        time.sleep(0.5)
        
        # Test 2: Disable driver
        self.logger.info("Test 2: Disable driver")
        response = self.stepper.enable(0)
        if response.success:
            self.logger.info("✓ Driver disabled successfully")
        else:
            self.logger.error("✗ Failed to disable driver: %s", response.message)
            all_passed = False
        
        time.sleep(0.5)
        
        # Test 3: Check hardware disabled status
        self.logger.info("Test 3: Check hardware disabled status")
        response = self.stepper.is_hardware_disabled()
        if response.success:
            self.logger.info("✓ Hardware status: %s", response.message)
        else:
            self.logger.error("✗ Failed to check hardware status: %s", response.message)
            all_passed = False
        
        return all_passed
    
    def test_current_settings(self) -> bool:
        """Test current setting commands"""
        self.logger.info("=== Testing Current Settings ===")
        
        all_passed = True
        
        # Test run current
        self.logger.info("Test 4: Set run current to 50%")
        response = self.stepper.set_run_current(50)
        if response.success:
            self.logger.info("✓ Run current set successfully")
        else:
            self.logger.error("✗ Failed to set run current: %s", response.message)
            all_passed = False
        
        time.sleep(0.5)
        
        # Test hold current
        self.logger.info("Test 5: Set hold current to 25%")
        response = self.stepper.set_hold_current(25)
        if response.success:
            self.logger.info("✓ Hold current set successfully")
        else:
            self.logger.error("✗ Failed to set hold current: %s", response.message)
            all_passed = False

        
        return all_passed
    
    def test_standstill_modes(self) -> bool:
        """Test standstill mode commands"""
        self.logger.info("=== Testing Standstill Modes ===")
        
        all_passed = True
        modes = [
            (StandstillMode.NORMAL, "NORMAL"),
            (StandstillMode.FREEWHEELING, "FREEWHEELING"),
            (StandstillMode.STRONG_BRAKING, "STRONG_BRAKING"),
            (StandstillMode.BRAKING, "BRAKING")
        ]
        
        for i, (mode, mode_name) in enumerate(modes):
            self.logger.info("Test 6.%d: Set standstill mode to %s", i + 1, mode_name)
            response = self.stepper.set_standstill_mode(mode)
            if response.success:
                self.logger.info("✓ Standstill mode set to %s", mode_name)
            else:
                self.logger.error("✗ Failed to set standstill mode to %s: %s", mode_name, response.message)
                all_passed = False
            time.sleep(0.5)
        
        return all_passed
    
    def test_microstepping(self) -> bool:
        """Test microstepping commands"""
        self.logger.info("=== Testing Microstepping ===")
        
        all_passed = True
        
        # Test microsteps per step (powers of 2)
        microstep_values = [2, 4, 8]
        
        for i, microsteps in enumerate(microstep_values):
            self.logger.info("Test 7.%d: Set microsteps per step to %d", i + 1, microsteps)
            response = self.stepper.set_microsteps_per_step(microsteps)
            if response.success:
                self.logger.info("✓ Microsteps per step set to %d", microsteps)
            else:
                self.logger.error("✗ Failed to set microsteps to %d: %s", microsteps, response.message)
                all_passed = False
            time.sleep(0.5)
        
        # Test microstep exponent
        self.logger.info("Test 8: Set microstep exponent to 3 (2^3 = 8)")
        response = self.stepper.set_microsteps_per_step_power_of_two(3)
        if response.success:
            self.logger.info("✓ Microstep exponent set successfully")
        else:
            self.logger.error("✗ Failed to set microstep exponent: %s", response.message)
            all_passed = False
        
        return all_passed
    
    def test_pwm_settings(self) -> bool:
        """Test PWM settings"""
        self.logger.info("=== Testing PWM Settings ===")
        
        all_passed = True
        
        # Test PWM offset
        self.logger.info("Test 9: Set PWM offset to 128")
        response = self.stepper.set_pwm_offset(128)
        if response.success:
            self.logger.info("✓ PWM offset set successfully")
        else:
            self.logger.error("✗ Failed to set PWM offset: %s", response.message)
            all_passed = False

        self.logger.info("Test 10: Reset PWM offset to 0")
        response = self.stepper.set_pwm_offset(0)
        if response.success:
            self.logger.info("✓ PWM offset reset successfully")
        else:
            self.logger.error("✗ Failed to reset PWM offset: %s", response.message)
            all_passed = False
        
        time.sleep(0.5)
        
        # Test PWM gradient
        self.logger.info("Test 10: Set PWM gradient to 64")
        response = self.stepper.set_pwm_gradient(64)
        if response.success:
            self.logger.info("✓ PWM gradient set successfully")
        else:
            self.logger.error("✗ Failed to set PWM gradient: %s", response.message)
            all_passed = False
        
        # reset PWM gradient to 0
        self.logger.info("Test 11: Reset PWM gradient to 0")
        response = self.stepper.set_pwm_gradient(0)
        if response.success:
            self.logger.info("✓ PWM gradient reset successfully")
        else:
            self.logger.error("✗ Failed to reset PWM gradient: %s", response.message)
            all_passed = False
        
        return all_passed

    def test_stall_guard_and_standing_still(self) -> bool:
        """Test StallGuard and standing still status commands"""
        self.logger.info("=== Testing StallGuard and Standing Still Status ===")
        
        all_passed = True
        
        # Test 14: Get StallGuard result
        self.logger.info("Test 14: Get StallGuard result")
        response = self.stepper.get_stall_guard_result()
        if response.success:
            stall_value = response.value if response.value is not None else 0
            self.logger.info("✓ StallGuard result: %s (value: %d)", response.message, stall_value)
        else:
            self.logger.error("✗ Failed to get StallGuard result: %s", response.message)
            all_passed = False
        
        time.sleep(0.5)
        
        # Test 15: Check if motor is standing still
        self.logger.info("Test 15: Check if motor is standing still")
        response = self.stepper.is_standing_still()
        if response.success:
            standing_still = response.value if response.value is not None else 0
            self.logger.info("✓ Standing still status: %s (value: %d)", response.message, standing_still)
        else:
            self.logger.error("✗ Failed to check standing still status: %s", response.message)
            all_passed = False
        
        return all_passed
    
    def test_communication(self) -> bool:
        """Test communication status"""
        self.logger.info("=== Testing Communication ===")
        
        all_passed = True
        
        # Test communication status
        self.logger.info("Test 11: Check communication status")
        response = self.stepper.is_setup_and_communicating()
        if response.success:
            self.logger.info("✓ Communication status: %s", response.message)
        else:
            self.logger.error("✗ Failed to check communication status: %s", response.message)
            all_passed = False
        
        return all_passed

    def test_reset_to_safe_current(self) -> bool:
        """Test reset to safe current"""
        self.logger.info("=== Testing Reset to Safe Current ===")
        
        all_passed = True
        
        # Test reset to safe current
        self.logger.info("Test 12: Reset to safe current")
        response = self.stepper.reset_to_safe_current()
        if response.success:
            self.logger.info("✓ Reset to safe current successfully")
        else:
            self.logger.error("✗ Failed to reset to safe current: %s", response.message)
            all_passed = False
        
        return all_passed
    
    def test_error_handling(self) -> bool:
        """Test error handling with invalid commands"""
        self.logger.info("=== Testing Error Handling ===")
        
        all_passed = True
        
        # Test invalid current percentage (should be handled by Arduino)
        self.logger.info("Test 12: Test invalid current percentage (should fail)")
        response = self.stepper.set_run_current(150)  # Invalid current percentage > 100
        if not response.success:
            self.logger.info("✓ Error handling works correctly: %s", response.message)
        else:
            self.logger.warning("✗ Error handling may not be working")
            all_passed = False
        
        time.sleep(0.5)
        
        # Test invalid microstep value (should be handled by Arduino)
        self.logger.info("Test 13: Test invalid microstep value (should fail)")
        response = self.stepper.set_microsteps_per_step(3)  # Invalid microstep (not power of 2)
        if not response.success:
            self.logger.info("✓ Invalid microstep handling works correctly: %s", response.message)
        else:
            self.logger.warning("✗ Invalid microstep handling may not be working")
            all_passed = False
        
        return all_passed
    
    def test_movement_commands(self) -> bool:
        """Test movement commands with user confirmation"""

        if self.skip_movement_tests:
            self.logger.info("Skipping movement tests as requested by user")
            return True  # Return True since user chose to skip (not a failure)
        
        self.logger.info("=== Testing Movement Commands ===")
        
        # Warning and user confirmation
        self.logger.info("Resetting to safe current")
        response = self.stepper.reset_to_safe_current()
        if response.success:
            self.logger.info("✓ Reset to safe current successfully")
        else:
            self.logger.error("✗ Failed to reset to safe current: %s", response.message)
            all_passed = False
        
        self.stepper.enable(True)
        self.logger.warning("Motor is enabled and about to start moving. Keep clear or press any key to skip this test")
        user_input = input("Enter 'Y' to continue with movement tests, or any other key to skip: ").strip().upper()
        
        if user_input != 'Y':
            self.stepper.disable()
            self.logger.info("Skipping movement tests as requested by user")
            return True  # Return True since user chose to skip (not a failure)
        
        all_passed = True
        TEST_SPEED = 50
        
        # Test 16: Move at positive velocity
        self.logger.info("Test 16: Move at positive velocity (%d)", TEST_SPEED)
        response = self.stepper.move_at_velocity(TEST_SPEED)
        if response.success:
            self.logger.info("✓ Motor started moving at velocity %d", TEST_SPEED)
        else:
            self.logger.error("✗ Failed to start movement: %s", response.message)
            all_passed = False
        
        time.sleep(5)  # Let motor run for 5 seconds
        
        # Test 17: Stop moving
        self.logger.info("Test 17: Stop moving")
        response = self.stepper.stop_moving()
        if response.success:
            self.logger.info("✓ Motor stopped successfully")
        else:
            self.logger.error("✗ Failed to stop motor: %s", response.message)
            all_passed = False
            # Disable motor if stop_moving fails
            self.logger.error("Disabling motor due to stop failure")
            disable_response = self.stepper.enable(False)
            if disable_response.success:
                self.logger.info("✓ Motor disabled successfully")
            else:
                self.logger.error("✗ Failed to disable motor: %s", disable_response.message)
        
        time.sleep(1)
        
        # Test 18: Move at negative velocity (reverse direction)
        self.logger.info("Test 18: Move at negative velocity (-%d)", TEST_SPEED)
        response = self.stepper.move_at_velocity(-TEST_SPEED)
        if response.success:
            self.logger.info("✓ Motor started moving at velocity -%d", TEST_SPEED)
        else:
            self.logger.error("✗ Failed to start reverse movement: %s", response.message)
            all_passed = False
        
        time.sleep(2)  # Let motor run for 2 seconds
        
        # Test 19: Stop moving again
        self.logger.info("Test 19: Stop moving again")
        response = self.stepper.stop_moving()
        if response.success:
            self.logger.info("✓ Motor stopped successfully")
        else:
            self.logger.error("✗ Failed to stop motor: %s", response.message)
            all_passed = False
            # Disable motor if stop_moving fails
            self.logger.error("Disabling motor due to stop failure")
            disable_response = self.stepper.enable(False)
            if disable_response.success:
                self.logger.info("✓ Motor disabled successfully")
            else:
                self.logger.error("✗ Failed to disable motor: %s", disable_response.message)
        
        time.sleep(1)
        
        # Test 20: Move at zero velocity (should stop)
        self.logger.info("Test 20: Move at zero velocity (should stop)")
        response = self.stepper.move_at_velocity(0)
        if response.success:
            self.logger.info("✓ Motor set to zero velocity")
        else:
            self.logger.error("✗ Failed to set zero velocity: %s", response.message)
            all_passed = False
        
        return all_passed
    
    def run_all_tests(self) -> bool:
        """Run all test suites"""
        self.logger.info("Starting Arduino TMC2209 Test Suite")
        self.logger.info("=" * 50)
        
        if not self.connect():
            return False
        
        all_tests_passed = True
        
        try:
            # Run basic tests first
            if not self.test_basic_commands():
                all_tests_passed = False
                self.logger.error("Basic commands test failed")
            
            if not self.test_current_settings():
                all_tests_passed = False
                self.logger.error("Current settings test failed")
            
            if not self.test_standstill_modes():
                all_tests_passed = False
                self.logger.error("Standstill modes test failed")
            
            if not self.test_microstepping():
                all_tests_passed = False
                self.logger.error("Microstepping test failed")
            
            if not self.test_pwm_settings():
                all_tests_passed = False
                self.logger.error("PWM settings test failed")
            
            if not self.test_stall_guard_and_standing_still():
                all_tests_passed = False
                self.logger.error("StallGuard and standing still test failed")
            
            if not self.test_communication():
                all_tests_passed = False
                self.logger.error("Communication test failed")
            
            if not self.test_error_handling():
                all_tests_passed = False
                self.logger.error("Error handling test failed")

            if not self.test_reset_to_safe_current():
                all_tests_passed = False
                self.logger.error("Reset to safe current test failed")
            
            # Only run movement tests if all other tests passed
            if all_tests_passed:
                self.logger.info("All basic tests passed. Proceeding with movement tests...")
                if not self.test_movement_commands():
                    all_tests_passed = False
                    self.logger.error("Movement commands test failed")
            else:
                self.logger.warning("Some basic tests failed. Skipping movement tests for safety.")
            
            self.logger.info("=" * 50)
            if all_tests_passed:
                self.logger.info("All tests completed successfully!")
            else:
                self.logger.error("Some tests failed!")
            
        except KeyboardInterrupt:
            self.logger.warning("Test interrupted by user")
            all_tests_passed = False
        except Exception as e:
            self.logger.error("Unexpected error during testing: %s", e)
            all_tests_passed = False
        finally:
            self.stepper.disable()
            self.disconnect()
        
        return all_tests_passed


def list_available_ports():
    """List all available serial ports"""
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("No serial ports found")
        return []
    
    print("Available serial ports:")
    for i, port in enumerate(ports):
        print("  %d: %s - %s", i, port.device, port.description)
    
    return [port.device for port in ports]

def main():
    """Main function"""
    def str2bool(s: str) -> bool:
        if s.lower() in ['y', 'yes', '1']:
            return True
        elif s.lower() in ['n', 'no', '0']:
            return False
        else:
            raise ValueError(f"Invalid boolean value: {s}")
    
    parser = argparse.ArgumentParser(description='Test Arduino TMC2209 functionality')
    parser.add_argument('--port', '-p', default=None,
                       help='Serial port (default: auto-detect)')
    parser.add_argument('--baudrate', '-b', type=int, default=115200,
                       help='Baud rate (default: 115200)')
    parser.add_argument('--timeout', '-t', type=float, default=2.0,
                       help='Serial timeout in seconds (default: 2.0)')
    parser.add_argument('--skip_movement_tests', type = str2bool, default = True,
                       help='Skip movement tests (default: True)')
    parser.add_argument('--list-ports', '-l', action='store_true',
                       help='List available serial ports and exit')
    
    args = parser.parse_args()
    
    # 如果要求列出端口，則列出並退出
    if args.list_ports:
        list_available_ports()
        return
    
    # Create and run tester
    tester = ArduinoTMC2209Tester(
        port=args.port,
        baudrate=args.baudrate,
        timeout=args.timeout,
        skip_movement_tests=args.skip_movement_tests
    )
    
    tester.run_all_tests()

if __name__ == "__main__":
    main()