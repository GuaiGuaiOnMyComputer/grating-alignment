import sys
import logging
from typing import Dict
from ui.UserInterface import MainWindowUI
from shared.LoggingUtils import ColoredConsoleLoggerFactorySingleton
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCommandLineParser, QCommandLineOption

def _process_command_line_args(app:QApplication) -> Dict:
    """
    Summary:
      Parse command line arguments. Please call this function after creating QApplication(sys.argv).
    """

    parser: QCommandLineParser = QCommandLineParser()

    log_level_option: QCommandLineOption = QCommandLineOption(("v", "llevel"), "Console log level.", valueName = "log_level", defaultValue = str(logging.INFO))
    parser.addOption(log_level_option)
    parser.process(app)

    return {
        log_level_option.valueName(): int(parser.value(log_level_option))
    }

def main():
    main_application = QApplication(sys.argv)
    command_line_args:Dict = _process_command_line_args(main_application)

    logger_factory: ColoredConsoleLoggerFactorySingleton = ColoredConsoleLoggerFactorySingleton.instance()
    main_logger, _ = logger_factory.create_logger(__name__, default_level = command_line_args["log_level"])
    main_logger.debug("Received command line arguments: %s", command_line_args)

    main_logger.info("Starting application...")
    main_gui_window:MainWindowUI = MainWindowUI(main_logger)
    main_gui_window.show()

    sys.exit(main_application.exec())



if __name__ == "__main__":
    main()