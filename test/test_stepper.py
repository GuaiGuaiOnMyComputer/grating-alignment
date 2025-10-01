import os
import logging
import time
from typing import Tuple, List
from logging import Handler, StreamHandler, FileHandler
from dep.microPython_TMC5160.TMC5160_jetson import TMC5160TPro
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

def test_tmc5160_movement():
    """Test TMC5160T Pro movement with 500 steps"""
    main_logger, _ = _initialize_logger(__name__)
    main_logger.info("Running TMC5160T stepper test...")

    stepper_logger, _ = _initialize_logger("TMC5160", log_to_console=True)
    stepper_logger.info("Creating TMC5160T driver...")

    # Initialize TMC5160T Pro with SPI settings according to README.md
    # SPI bus 0, device 0, CS pin 15, ENN pin 11, DIAG pins 13, 16
    stepper = TMC5160TPro(
        spi_bus=0,
        spi_device=0,
        cs_pin=15,
        enn_pin=None,     # Hardware enable pin (active low)
        diag0_pin=None,   # Diagnostic pin 0
        diag1_pin=None,   # Diagnostic pin 1
        logger=stepper_logger
    )

    try:
        # Test SPI communication first
        main_logger.info("Testing SPI communication...")
        if not stepper.test_spi_communication():
            main_logger.error("SPI communication test failed - aborting test")
            return
            
        # Configure SPI mode (disable STEP/DIR interface)
        main_logger.info("Configuring SPI mode...")
        if not stepper.configure_spi_mode():
            main_logger.error("SPI mode configuration failed - aborting test")
            return
            
        # Test basic register access
        main_logger.info("Testing basic register access...")

        # Try to read GSTAT register
        gstat_value, gstat_status = stepper.readReg(stepper.GSTAT)
        main_logger.info("GSTAT read: value=0x%08X, status=%d", gstat_value, gstat_status)
        
        # Try to read GCONF register
        gconf_value, gconf_status = stepper.readReg(stepper.GCONF)
        main_logger.info("GCONF read: value=0x%08X, status=%d", gconf_value, gconf_status)
        
        if gstat_status == 2 or gconf_status == 2:
            main_logger.error("Basic register read failed - SPI communication problem")
            return

        # Enable the motor
        stepper.enable()
        main_logger.info("Motor enabled")

        # Set current (1.5A run current, 15% idle current)
        MAX_CURRENT = 0.7
        IDLE_PERCENT = 15
        current_status = stepper.setCurrent(MAX_CURRENT, IDLE_PERCENT)
        if current_status != 0:
            main_logger.error("Failed to set current: status=%d", current_status)
            return
        main_logger.info("Current set to %.2f A with %d percent idle", MAX_CURRENT, IDLE_PERCENT)
        
        # Set microstepping mode (1/2 microsteps)
        stepper.setStepMode(stepper.MicroStep2)
        main_logger.info("Microstepping set to 1/2")

        # Set movement parameters (speed and acceleration)
        SPEED = 10000
        ACCEL = 5000
        stepper.setAutoRamp(speed=SPEED, accel=ACCEL)
        main_logger.info("Ramp parameters set (speed=%d, accel=%d)", SPEED, ACCEL)

        # Check driver status
        status = stepper.getStatus()
        main_logger.info("Driver status: %s", status)
        if status.driver_error:
            main_logger.warning("Driver error detected!")
        if status.reset_flag:
            main_logger.warning("Reset flag detected!")

        # Get initial position
        initial_pos = stepper.getPos()
        main_logger.info("Initial position: %d", initial_pos)

        # Move 500 steps (relative movement)
        target_pos = initial_pos + 500
        main_logger.info("Moving from %d to %d", initial_pos, target_pos)

        # Execute movement command
        move_status = stepper.moveToPos(target_pos)
        if move_status == 2:
            main_logger.error("Move command failed - status error")
            return

        # Wait for movement to complete with timeout and status monitoring
        timeout_counter = 0
        max_timeout = 10000  # 10 seconds timeout
        
        while not stepper.getStatus().position_reached and timeout_counter < max_timeout:
            current_status = stepper.getStatus()
            
            # Check for driver errors during movement
            if current_status.driver_error:
                main_logger.error("Driver error during movement!")
                break
                
            # Log progress every 1000 iterations
            if timeout_counter % 1000 == 0:
                current_pos = stepper.getPos()
                main_logger.info(f"Moving... Current position: {current_pos}, Target: {target_pos}")
            
            time.sleep(0.001)
            timeout_counter += 1

        if timeout_counter >= max_timeout:
            main_logger.warning("Movement timeout - motor may be stuck")

        # Check final position
        final_pos = stepper.getPos()
        main_logger.info(f"Final position: {final_pos}")

        # Verify movement
        if final_pos == target_pos:
            main_logger.info("SUCCESS: Motor moved exactly 500 steps!")
        else:
            main_logger.warning(f"Movement error: Expected {target_pos}, got {final_pos}")

        # Move back to original position
        main_logger.info("Moving back to original position...")
        move_status = stepper.moveToPos(initial_pos)
        if move_status == 2:
            main_logger.error("Return move command failed - status error")
            return
            
        timeout_counter = 0
        while not stepper.getStatus().position_reached and timeout_counter < max_timeout:
            time.sleep(0.001)
            timeout_counter += 1
            
        if timeout_counter >= max_timeout:
            main_logger.warning("Return movement timeout")

        main_logger.info("Movement test completed successfully")

    except Exception as e:
        main_logger.error(f"Error during movement test: {e}")
        raise
    finally:
        # Clean up
        main_logger.info("Cleaning up...")
        try:
            # Hardware disable first (if available)
            stepper.hardware_disable()
            main_logger.info("Hardware disabled")
        except:
            pass
            
        # Software disable
        stepper.disable()
        main_logger.info("Software disabled")
        
        # Clean up resources
        stepper.cleanup()
        main_logger.info("Test completed")

if __name__ == "__main__":
    test_tmc5160_movement()