import os
import logging
import time
from typing import Tuple, List
from logging import Handler, StreamHandler, FileHandler
from dep.steppercontrol.StepperMotorWrapper import Tmc2209StepperWrapperFactory, Tmc220xStepperWrapper
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

def test_tmc2209_movement():
    """Test TMC2209 stepper movement with 500 steps"""
    main_logger, _ = _initialize_logger(__name__)
    main_logger.info("Running TMC2209 stepper test...")

    stepper_logger, _ = _initialize_logger("TMC2209", log_to_console=True)
    stepper_logger.info("Creating TMC2209 driver...")

    # Initialize TMC2209 stepper with GPIO settings
    # Enable pin 11, Step pin 15, Direction pin 13
    stepper = Tmc2209StepperWrapperFactory.create(
        enable_pin=11,
        step_signal_pin=15,
        step_direction_pin=13,
        com_uart=None,  # No UART communication
        log_prefix="TMC2209-Stepper",
        log_formatter=None,
        log_handler=None
    )

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

        # Set current (700mA run current, 50% hold current)
        MAX_CURRENT = 700  # in mA
        HOLD_MULTIPLIER = 0.5
        stepper.set_current(MAX_CURRENT, HOLD_MULTIPLIER)
        main_logger.info("Current set to %d mA with %.1f hold multiplier", MAX_CURRENT, HOLD_MULTIPLIER)
        
        # Set microstepping mode (1/2 microsteps)
        stepper.set_microstepping_resolution(2)
        main_logger.info("Microstepping set to 1/2")

        # Note: TMC2209 doesn't have built-in speed/acceleration control like TMC5160
        # Movement speed is controlled by the step frequency from the host
        main_logger.info("Movement parameters will be controlled by step frequency")

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
        main_logger.info(f"Final position: {final_pos}")

        # Verify movement
        expected_pos = initial_pos + target_steps
        if final_pos == expected_pos:
            main_logger.info("SUCCESS: Motor moved exactly %d steps!", target_steps)
        else:
            main_logger.warning(f"Movement error: Expected {expected_pos}, got {final_pos}")

        # Move back to original position
        main_logger.info("Moving back to original position...")
        return_steps = initial_pos - final_pos
        return_stop_mode = stepper.run_to_position_steps(return_steps, MovementAbsRel.RELATIVE)
        main_logger.info("Return movement completed with stop mode: %s", return_stop_mode)

        main_logger.info("Movement test completed successfully")

    except Exception as e:
        main_logger.error(f"Error during movement test: {e}")
        raise
    finally:
        # Clean up
        main_logger.info("Cleaning up...")
        try:
            # Disable motor
            stepper.set_motor_enabled(False)
            main_logger.info("Motor disabled")
        except Exception as e:
            main_logger.warning(f"Error during cleanup: {e}")
        
        main_logger.info("Test completed")

if __name__ == "__main__":
    test_tmc2209_movement()