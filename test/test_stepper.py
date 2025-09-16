import os
import logging
import asyncio
from typing import Tuple, List
from logging import Handler, StreamHandler, FileHandler
from tmc_driver.tmc_2209 import MovementAbsRel
from grating_alignment.StepperMotorWrapper import Tmc2209StepperWrapperFactory, Tmc220xStepperWrapper
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

async def main():
    main_logger, _ = _initialize_logger(__name__)
    main_logger.info("Running stepper test...")

    stepper_logger, stepper_handlers = _initialize_logger("stepper", log_to_console = True)
    stepper_logger.info("Creating stepper...")
    stepper: Tmc220xStepperWrapper = Tmc2209StepperWrapperFactory.create(
        enable_pin = 10,
        step_signal_pin = 11,
        step_direction_pin = 12,
        log_prefix = "stepper",
        log_formatter = ColoredLoggingFormatter.instance(),
        log_handler = stepper_handlers
    )
    stepper.set_motor_enabled(True)

    await stepper.run_to_position_steps_async(1000, MovementAbsRel.RELATIVE)
    stepper.stop()
    stepper.emergency_stop()

    main_logger.info("Stepper move completed.")

if __name__ == "__main__":
    asyncio.run(main())