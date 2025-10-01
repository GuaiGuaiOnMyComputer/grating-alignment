import logging
import os
import sys
import pypylon.pylon
import json
from typing import Tuple, List
from logging import Handler, StreamHandler, FileHandler
from dep.camerautils.Pylon.PylonCameraWrapper import PylonCameraWrapper
from dep.camerautils.PixelFormatEnum import PixelFormatEnum
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


def _acquire_pylon_camera_wrapper(logger:logging.Logger) -> PylonCameraWrapper | None:

    camera: PylonCameraWrapper | None = None
    try:
        pylon_camera = pypylon.pylon.TlFactory.GetInstance().CreateFirstDevice()
        camera = PylonCameraWrapper(pylon_camera, PixelFormatEnum.BGR8, logger)
    except pypylon.pylon.RuntimeException as e:
        logger.error(f"Error initializing pylon camera: {e}")

    return camera

def main():
    main_logger, _ = _initialize_logger(__name__, log_to_console = True)
    pylon_logger, _ = _initialize_logger("pylon", log_to_console = True)

    main_logger.info("Starting application...")
    camera: PylonCameraWrapper | None = _acquire_pylon_camera_wrapper(pylon_logger)
    if camera is None:
        sys.exit(1)

    camera.initialize_camera()
    main_logger.info(json.dumps(camera.get_camera_info(), indent = 4))
    camera.start_camera_streaming()

if __name__ == "__main__":
    main()