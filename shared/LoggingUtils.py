import logging
from typing import Tuple

class ColoredConsoleLoggerFactorySingleton:
    """Factory for ColoredLoggingFormatter with console handler"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ColoredConsoleLoggerFactorySingleton, cls).__new__(cls)
            
        return cls._instance
    
    def __init__(self, *args, **kwargs):
        if not self._initialized:
            super().__init__(*args, **kwargs)
            self._initialized = True
    
    def instance(self):
        if not ColoredConsoleLoggerFactorySingleton._instance:
            ColoredConsoleLoggerFactorySingleton._instance = ColoredConsoleLoggerFactorySingleton()
        return ColoredConsoleLoggerFactorySingleton._instance
    
    def create_logger(self, logger_name: str, format_string: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s', default_level: int = logging.INFO) -> Tuple[logging.Logger,logging.StreamHandler] :
        logger = logging.getLogger(logger_name)
        logger.setLevel(default_level)
        logger.handlers.clear()
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ColoredLoggingFormatter(format_string))
        console_handler.setLevel(default_level)
        logger.addHandler(console_handler)
        return logger, console_handler

    @staticmethod
    def instance():
        return ColoredConsoleLoggerFactorySingleton()

class ColoredLoggingFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def __init__(self, format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s', *args, **kwargs):
        super().__init__(format, *args, **kwargs)
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)