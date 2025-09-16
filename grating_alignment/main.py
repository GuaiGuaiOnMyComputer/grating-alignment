import logging
import os
import sys
import pypylon.pylon
from typing import Tuple, List
from logging import Handler, StreamHandler, FileHandler
from dep.camerautils.Pylon import PylonCameraWrapper
from shared.LoggingFormatter import ColoredLoggingFormatter

def _initialize_logger(logger_name:str, log_to_console:bool = True, log_to_file:bool = False) -> Tuple[logging.Logger, List[Handler]]:
    logger:logging.Logger = logging.getLogger(logger_name)
    console_handler: StreamHandler = StreamHandler()

    handlers: List[Handler] = []
    console_handler.setFormatter(ColoredLoggingFormatter.instance())
    if log_to_console:
        logger.addHandler(console_handler)
        handlers.append(console_handler)
    if log_to_file:
        os.makedirs("logs", exist_ok = True)
        file_handler: FileHandler = FileHandler(f"logs/{logger_name}.log")
        file_handler.setFormatter(ColoredLoggingFormatter.instance())
        logger.addHandler(file_handler)
        handlers.append(file_handler)

    return logger, handlers


def _acquire_pylon_camera(logger:logging.Logger) -> PylonCameraWrapper | None:

    camera: PylonCameraWrapper | None = None
    try:
        pylon_camera = pypylon.pylon.TlFactory.GetInstance().CreateFirstDevice()
        camera = PylonCameraWrapper(pylon_camera, logger)
    except pypylon.pylon.RuntimeException as e:
        logger.error(f"Error initializing pylon camera: {e}")

    return camera

def main():
    main_logger, _ = _initialize_logger(__name__, log_to_console = True)
    pylon_logger, _ = _initialize_logger("pylon", log_to_console = True)

    camera: PylonCameraWrapper | None = _acquire_pylon_camera(pylon_logger)
    if camera is None:
        sys.exit(1)
    
    camera.start_camera_streaming()

if __name__ == "__main__":
    main()