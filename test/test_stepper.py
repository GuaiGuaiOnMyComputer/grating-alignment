import os
import logging
import glob
import subprocess
import sys
from typing import Tuple, List, Optional
from logging import Handler, StreamHandler, FileHandler
from dep.steppercontrol.StepperMotorWrapper import Tmc2209StepperComUartWrapperFactory, Tmc220xStepperWrapper
from tmc_driver.tmc_220x import MovementAbsRel
from shared.LoggingFormatter import ColoredLoggingFormatter


def _initialize_logger(logger_name:str, log_to_console:bool = True, log_to_file:bool = False, log_level = logging.INFO) -> Tuple[logging.Logger, List[Handler]]:
    logger:logging.Logger = logging.getLogger(logger_name)
    logger.handlers.clear()
    
    console_handler: StreamHandler = StreamHandler()
    handlers: List[Handler] = []
    
    console_handler.setFormatter(ColoredLoggingFormatter.instance())
    console_handler.setLevel(log_level)
    if log_to_console:
        logger.addHandler(console_handler)
        handlers.append(console_handler)
    if log_to_file:
        os.makedirs("logs", exist_ok = True)
        file_handler: FileHandler = FileHandler(f"logs/{logger_name}.log")
        file_handler.setFormatter(ColoredLoggingFormatter.instance())
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)
        handlers.append(file_handler)
    
    logger.setLevel(log_level)
    logger.propagate = False
    return logger, handlers


def _detect_jetson_uart_ports() -> List[str]:
    """Detect available UART ports on Jetson Orin Nano
    
    Returns:
        List[str]: List of available UART device paths
    """
    uart_ports = []
    
    # Common UART device patterns on Jetson
    uart_patterns = [
        "/dev/ttyTHS*",  # Hardware UART (preferred)
        "/dev/ttyUSB*",  # USB-to-serial adapters
        "/dev/ttyACM*",  # USB CDC devices
    ]
    
    for pattern in uart_patterns:
        ports = glob.glob(pattern)
        uart_ports.extend(ports)
    
    # Sort ports for consistent ordering
    uart_ports.sort()
    return uart_ports


def _check_user_permissions() -> bool:
    """Check if user has proper permissions for UART access
    
    Returns:
        bool: True if user has proper permissions
    """
    try:
        # Check if user is in dialout group
        result = subprocess.run(["groups"], capture_output=True, text=True, check=True)
        groups = result.stdout.strip()
        return "dialout" in groups
    except:
        return False


def _try_fix_permissions(main_logger: logging.Logger) -> bool:
    """Try to fix UART permissions without interactive authentication
    
    Args:
        main_logger (logging.Logger): Logger instance for output
        
    Returns:
        bool: True if permissions were fixed or already correct
    """
    try:
        # Check if we can run sudo without password (passwordless sudo)
        result = subprocess.run(["sudo", "-n", "true"], capture_output=True, text=True)
        if result.returncode == 0:
            # We have passwordless sudo, try to fix permissions
            main_logger.info("Attempting to fix UART permissions...")
            
            # Add user to dialout group
            subprocess.run(["sudo", "usermod", "-a", "-G", "dialout", os.getenv("USER")], check=True)
            main_logger.info("Added user to dialout group")
            
            # Set permissions on common UART devices
            uart_ports = _detect_jetson_uart_ports()
            for port in uart_ports:
                if os.path.exists(port):
                    subprocess.run(["sudo", "chmod", "666", port], check=True)
                    main_logger.info(f"Set permissions for {port}")
            
            main_logger.info("Permissions fixed! Please log out and log back in for changes to take effect.")
            return True
        else:
            main_logger.warning("Passwordless sudo not available. Cannot fix permissions automatically.")
            return False
    except Exception as e:
        main_logger.warning(f"Could not fix permissions automatically: {e}")
        return False


def _check_access_to_port(port: str, main_logger: logging.Logger) -> bool:
    """Configure UART port for Jetson Orin Nano
    
    Args:
        port (str): UART device path
        main_logger (logging.Logger): Logger instance for output
        baudrate (int): Baud rate (default 115200)
        
    Returns:
        bool: True if configuration successful
    """
    try:
        # Check if port exists and is accessible
        if not os.path.exists(port):
            main_logger.warning("UART port %s does not exist", port)
            return False
        
        # Check if we can read the port (without changing permissions)
        try:
            with open(port, 'rb') as f:
                pass  # Just test if we can open it
            main_logger.info("UART port %s is accessible", port)
        except PermissionError:
            main_logger.warning("UART port %s exists but requires permission changes", port)
            main_logger.info("To fix this, run: sudo chmod 666 " + port)
            main_logger.info("Or add your user to the dialout group: sudo usermod -a -G dialout $USER")
            return False
        except Exception as e:
            main_logger.warning("Cannot access UART port %s: %s", port, e)
            return False
        
        # Configure UART settings if it's a hardware UART
        if "ttyTHS" in port:
            # For hardware UART, we might need to configure via device tree
            # This is typically done at boot time, but we can check if it's available
            main_logger.info("Hardware UART %s detected", port)
        
        return True
    except Exception as e:
        main_logger.error("Error checking UART %s: %s", port, e)
        return False


def _find_available_uart_port(main_logger: logging.Logger) -> List[str]:
    """Find an available UART port for TMC2209 communication
    
    Args:
        main_logger (logging.Logger): Logger instance for output
        
    Returns:
        Optional[str]: Available UART port path or None
    """
    # Check user permissions first
    if not _check_user_permissions():
        main_logger.error("User is not in dialout group. UART access may be limited.")
        main_logger.info("To fix this manually, run:")
        main_logger.info("  sudo usermod -a -G dialout $USER")
        main_logger.info("  sudo chmod 666 /dev/ttyTHS*")
        main_logger.info("Then log out and log back in, or run: newgrp dialout")
        return []
    
    uart_ports = _detect_jetson_uart_ports()
    
    if not uart_ports:
        main_logger.error("No UART ports found!")
        main_logger.info("Please check:")
        main_logger.info("- UART is enabled in device tree")
        main_logger.info("- TMC2209 is connected")
        main_logger.info("- USB-to-serial adapter is connected (if using USB UART)")
        return []
    
    main_logger.info("Found UART ports: %s", uart_ports)
    
    # Try each port to find one that works
    for port in uart_ports:
        main_logger.info("Testing UART port: %s", port)
        if not _check_access_to_port(port, main_logger):
            main_logger.info("Cannot access UART port: %s", port)
            uart_ports.remove(port)
            continue

    if not uart_ports:
        main_logger.error("No accessible UART ports found!")
        main_logger.info("Please check permissions and connections.")
        return None
    
    main_logger.info("Found accessible UART ports: %s", uart_ports)
    return uart_ports

def _test_tmc2209_movement():
    """Test TMC2209 stepper movement with 500 steps on Jetson Orin Nano"""
    main_logger, _ = _initialize_logger(__name__)
    main_logger.info("Running TMC2209 stepper test on Jetson Orin Nano...")

    # Since Jetpack6, the UART port mapping to 8 and 10 pins is /dev/ttyTHS1
    PORT = "/dev/ttyTHS1"
    main_logger.info("Using UART port: %s", PORT)

    # Jetson Orin Nano GPIO pin configuration
    # Pin 11 is commonly used for enable on Jetson 40-pin header
    ENABLE_PIN = 11
    
    # Initialize TMC2209 stepper with UART communication
    stepper_logger_handler: StreamHandler = StreamHandler()
    stepper_logger_handler.setFormatter(ColoredLoggingFormatter.instance())
    stepper_logger_handler.setLevel(logging.INFO)
    _find_available_uart_port(main_logger)
    
    try:
        stepper: Tmc220xStepperWrapper = Tmc2209StepperComUartWrapperFactory.create(
            enable_pin = ENABLE_PIN,
            com_uart = PORT,
            log_prefix="TMC2209",
            log_formatter=ColoredLoggingFormatter.instance(),
            log_handler=[stepper_logger_handler],
            step_resolution=16,  # 1/16 microstepping for smooth operation
            max_step_per_second=2000,  # Higher speed for Jetson
            full_step_per_rev=200  # Standard stepper motor
        )
        main_logger.info("TMC2209 stepper initialized successfully")
    except Exception as e:
        main_logger.error(f"Failed to initialize TMC2209 stepper: {e}")
        return False

    try:
        # Test basic register access
        main_logger.info("Testing basic register access...")

        # Try to read GSTAT register
        gstat = stepper.read_gstat()
        main_logger.info("GSTAT read: %s", gstat)
        
        # Try to read GCONF register
        gconf = stepper.read_gconf()
        main_logger.info("GCONF read: %s", gconf)

        # Enable the motor
        stepper.set_motor_enabled(True)
        main_logger.info("Motor enabled")

        # Set current for Jetson Orin Nano (higher current capability)
        MAX_CURRENT = 1000  # in mA - Jetson can handle more current
        HOLD_MULTIPLIER = 0.3  # Lower hold current for efficiency
        stepper.set_current(MAX_CURRENT, HOLD_MULTIPLIER)
        main_logger.info("Current set to %d mA with %.1f hold multiplier", MAX_CURRENT, HOLD_MULTIPLIER)
        
        # Set microstepping mode (1/16 microsteps for smooth operation)
        stepper.set_microstepping_resolution(16)
        main_logger.info("Microstepping set to 1/16")

        # Jetson-specific configuration
        main_logger.info("Jetson Orin Nano configuration:")
        main_logger.info("- UART port: %s", PORT)
        main_logger.info("- Enable pin: %d", ENABLE_PIN)
        main_logger.info("- Step resolution: 1/16")
        main_logger.info("- Max speed: 2000 steps/second")

        # Check driver status
        drv_status = stepper.read_drv_status()
        main_logger.info("Driver status: %s", drv_status)
        if hasattr(drv_status, 'driver_error') and drv_status.driver_error:
            main_logger.warning("Driver error detected!")
        if hasattr(drv_status, 'reset_flag') and drv_status.reset_flag:
            main_logger.warning("Reset flag detected!")

        # Get initial position
        initial_pos = stepper.get_microstep_counter_in_steps()
        main_logger.info("Initial position: %d", initial_pos)

        # Move 500 steps (relative movement)
        target_steps = 500
        main_logger.info("Moving %d steps from position %d", target_steps, initial_pos)

        # Execute movement command (relative movement)
        stop_mode = stepper.run_to_position_steps(target_steps, MovementAbsRel.RELATIVE)
        main_logger.info("Movement completed with stop mode: %s", stop_mode)

        # Get final position
        final_pos = stepper.get_microstep_counter_in_steps()
        main_logger.info("Final position: %d", final_pos)

        # Verify movement
        expected_pos = initial_pos + target_steps
        if final_pos == expected_pos:
            main_logger.info("SUCCESS: Motor moved exactly %d steps!", target_steps)
        else:
            main_logger.warning("Movement error: Expected %d, got %d", expected_pos, final_pos)

        # Move back to original position
        main_logger.info("Moving back to original position...")
        return_steps = initial_pos - final_pos
        return_stop_mode = stepper.run_to_position_steps(return_steps, MovementAbsRel.RELATIVE)
        main_logger.info("Return movement completed with stop mode: %s", return_stop_mode)

        main_logger.info("Movement test completed successfully")
        return True

    except Exception as e:
        main_logger.error("Error during movement test: %s", e)
        main_logger.error("Please check:")
        main_logger.error("- TMC2209 is properly connected")
        main_logger.error("- UART communication is working")
        main_logger.error("- Enable pin is connected to GPIO %d", ENABLE_PIN)
        main_logger.error("- Power supply is adequate")
        return False
    finally:
        # Clean up
        main_logger.info("Cleaning up...")
        try:
            # Disable motor
            stepper.set_motor_enabled(False)
            main_logger.info("Motor disabled")
        except Exception as e:
            main_logger.warning(f"Error during cleanup: {e}")
        
        main_logger.info("Jetson Orin Nano test completed")

if __name__ == "__main__":
    _test_tmc2209_movement()