import logging

class ColoredLoggingFormatter(logging.Formatter):
    """Colored formatter for console output - Singleton implementation"""
    
    _instance = None
    _initialized = False
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ColoredLoggingFormatter, cls).__new__(cls)
        else:
            print("ColoredLoggingFormatter already initialized. Further initializations will be ignored.")
            
        return cls._instance
    
    def __init__(self, *args, **kwargs):
        if not self._initialized:
            super().__init__(*args, **kwargs)
            self._initialized = True
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)

    @staticmethod
    def instance():
        if not ColoredLoggingFormatter._instance:
            ColoredLoggingFormatter._instance = ColoredLoggingFormatter()
        return ColoredLoggingFormatter._instance