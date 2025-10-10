import sys
import time
import importlib.resources
import serial.tools.list_ports
import logging
import functools
from typing import List
from logging import Logger
from pathlib import Path
from PyQt6.QtCore import QByteArray
from PyQt6.QtGui import QIcon, QWheelEvent
from PyQt6.QtWidgets import QMainWindow, QLabel
from dep.camerautils.Pylon import PylonCameraWrapper
from dep.arduinounostepper_TMC2209.ArduinoStepper_TMC2209 import ArduinoStepper_TMC2209
from shared.LoggingUtils import ColoredConsoleLoggerFactorySingleton
from .compiledui.CompiledUi import Ui_MainWindow
from .mouseeventfilters.MouseEventFilter import MouseEventFilter

class MainWindowUI(QMainWindow):
    """繼承自 QMainWindow 並使用編譯後的 UI"""
    
    def __init__(self, logger: Logger | None = None):
        super().__init__()

        self.__ui: Ui_MainWindow = Ui_MainWindow()
        self.__ui.setupUi(self)
        self.__logger: Logger = logger

        if self.__logger is None:
            self.__logger = Logger()
            self.__logger.addHandler(logging.NullHandler())

        self.__latest_motor_enable_toggle_time: float = 0.0

        self.__camera_wrapper: PylonCameraWrapper | None = None
        self.__stepper_motor_wrapper: ArduinoStepper_TMC2209 | None = None

        self.__connect_serial_port_icon:QIcon = self.__load_icon_resource(Path("connect.svg"))
        self.__disconnect_serial_port_icon:QIcon = self.__load_icon_resource(Path("disconnect.svg"))
        self.__motor_sprint_icon:QIcon = self.__load_icon_resource(Path("motor-sprint.svg"))
        self.__align_icon:QIcon = self.__load_icon_resource(Path("align.svg"))
        self.__arrow_forward_icon:QIcon = self.__load_icon_resource(Path("arrow-forward.svg"))
        self.__arrow_back_icon:QIcon = self.__load_icon_resource(Path("arrow-back.svg"))

        self.__initialize_icons()
        self.__setup_callback_functions()
        self.__load_serial_port_list()

    @property
    def ui(self) -> Ui_MainWindow:
        return self.__ui
    
    @property
    def stepper_speed() -> int:
        return 300
    
    def __on_mouse_wheel_in_motor_manual_label(self, _:QLabel, wheel_event:QWheelEvent):

        self.__logger.debug("Mouse wheel event triggered in motor manual label.")
        if self.__stepper_motor_wrapper is None:
            return

        scroll_direction:bool = wheel_event.angleDelta().y() > 0
        self.__logger.debug("Mouse wheel scrolled %s in manual label, moving motor %s", "forward" if scroll_direction else "backward", "forward" if scroll_direction else "backwards")


    def __on_motor_serial_connect_btn_pressed(self):
        """串列連接回調函數"""

        self.__logger.debug("Motor serial connect button pressed. Serial connection stete before press = %s", self.__stepper_motor_wrapper.is_serial_connected)
        assert self.__stepper_motor_wrapper is not None, "Stepper motor wrapper is not initialized."

        if self.__stepper_motor_wrapper.is_serial_connected:
            self.__disconnect_serial_port()
        else:
            self.__connect_serial_port()

    def __on_motor_enable_toggle(self, checked: bool):

        self.__logger.debug("Toggled motor enable checkbox %s.", checked)
        assert self.__stepper_motor_wrapper is not None, "Stepper motor wrapper is not initialized."

        if time.time() - self.__latest_motor_enable_toggle_time < 3:
            self.__logger.warning("Motor enable toggle is too frequent. Please wait 3 seconds before toggling again.")
            self.__ui.motorEnable_chkbx.setChecked(not checked)
            time.sleep(1)
            self.__ui.motorEnable_chkbx.setChecked(checked)

        self.__logger.info("Motor enable toggled to %s", checked)
        self.__stepper_motor_wrapper.enable(checked)

        if checked:
            self.__ui.motorSerialConnect_btn.isEnabled(False)
            self.__ui.motorSerialPort_cmbbox.isEnabled(False)

    def __on_motor_manual_move_toggle(self, checked: bool):

        self.__logger.debug("Motor manual mode %s", "enabled" if checked else "disabled")
        assert self.__stepper_motor_wrapper is not None, "Stepper motor wrapper not initialized."

        self.__ui.motorAlign_btn.setEnabled(not checked)
        self.__ui.motorSprint_btn.setEnabled(checked)
        self.__ui.motorManualLeft_btn.setEnabled(checked)
        self.__ui.motorManualRight_btn.setEnabled(checked)

    def __on_motor_serial_port_change(self, index: int):
        """串列埠選擇回調函數"""
        self.__logger.debug("Motor serial port changed to %s", self.__ui.motorSerialPort_cmbbox.currentText())

        if not self.__ui.motorSerialPort_cmbbox.currentText():
            self.__stepper_motor_wrapper = None
            self.__ui.motorSerialConnect_btn.setEnabled(False)
            return

        self.__logger.debug("Instantiating stepper motor wrapper on port %s", self.__ui.motorSerialPort_cmbbox.currentText())
        self.__stepper_motor_wrapper = ArduinoStepper_TMC2209(
            port = self.__ui.motorSerialPort_cmbbox.currentText(), 
            logger = ColoredConsoleLoggerFactorySingleton.instance().create_logger("TMC2209", default_level = logging.INFO)[0]
        )
        self.__ui.motorSerialConnect_btn.setEnabled(True)

    def __setup_callback_functions(self):
        """設定按鈕和控件的連接事件"""
        self.__ui.motorSerialConnect_btn.clicked.connect(self.__on_motor_serial_connect_btn_pressed)
        self.__ui.motorEnable_chkbx.toggled.connect(self.__on_motor_enable_toggle)
        self.__ui.motorSerialPort_cmbbox.currentIndexChanged.connect(self.__on_motor_serial_port_change)

        self.__ui.motorManualLeft_btn.pressed.connect(functools.partial(self.__command_motor_manual_move, 0))
        self.__ui.motorManualLeft_btn.released.connect(self.__command_motor_stop)
        self.__ui.motorManualRight_btn.pressed.connect(functools.partial(self.__command_motor_manual_move, 1))
        self.__ui.motorManualRight_btn.released.connect(self.__command_motor_stop)

        self.__ui.motorManual_chkbx.toggled.connect(self.__on_motor_manual_move_toggle)

        motor_manual_label_hover_event_filter: MouseEventFilter = MouseEventFilter(self.__ui.motorPanel_grdlyt)
        motor_manual_label_hover_event_filter.wheel_event_handler.append(self.__on_mouse_wheel_in_motor_manual_label)
        self.__ui.motorManual_lbl.installEventFilter(motor_manual_label_hover_event_filter)



    def __command_motor_manual_move(self, direction: int) -> None:

        assert direction == 0 or direction == 1, "Direction must be an interger, 0 for move left and 1 for mover right."

        self.__logger.debug("Motor manual move button pressed. Dir = %s", "left" if direction == 0 else "right")
        assert self.__stepper_motor_wrapper is not None, "Stepper motor wrapper not initialized."
        
        if not self.__stepper_motor_wrapper.is_serial_connected:
            self.__logger.error("Lost serial connection to stepper motor controller.")
            return
        
        self.__stepper_motor_wrapper.move_at_velocity(self.stepper_speed * (-1 ** direction))

    def __command_motor_stop(self):

        self.__logger.debug("Motor stop command issued.")
        assert self.__stepper_motor_wrapper is not None, "Stepper motor wrapper not initialized."

        self.__stepper_motor_wrapper.move_at_velocity(0)

    def __load_serial_port_list(self) -> None:

        self.__logger.debug("Loading serial port list.")

        available_ports: List = serial.tools.list_ports.comports()
        self.__ui.motorSerialPort_cmbbox.clear()
        self.__ui.motorSerialPort_cmbbox.addItems([port.device for port in available_ports])

        self.__logger.debug("Available serial ports: %s", [port.device for port in available_ports])
        if len(available_ports) == 0:
            self.__logger.warning("No serial ports found.")

    def __load_icon_resource(self, icon_name: str) -> QIcon:
        """載入圖標資源，支援開發和打包環境"""
        
        # 檢查是否在打包環境中運行
        if getattr(sys, 'frozen', False):
            # 打包環境：使用 importlib.resources
            try:
                resource_data = importlib.resources.read_binary("ui.resource", icon_name)
                icon = QIcon()
                icon.addData(QByteArray(resource_data))
                return icon
            except Exception as e:
                self.__logger.warning("Failed to load icon from resources: %s, error: %s", icon_name, e)
                return QIcon()
        else:
            # 開發環境：使用檔案系統路徑
            current_file_dir = Path(__file__).parent
            icon_path = current_file_dir / "resource" / icon_name
            
            if not icon_path.exists():
                self.__logger.warning("Icon resource not found: %s", icon_path)
                return QIcon()
            
            return QIcon(str(icon_path))
        
    def __initialize_icons(self):
        self.__ui.motorSprint_btn.setIcon(self.__motor_sprint_icon)
        self.__ui.motorManualLeft_btn.setIcon(self.__arrow_back_icon)
        self.__ui.motorManualRight_btn.setIcon(self.__arrow_forward_icon)
        self.__ui.motorSerialConnect_btn.setIcon(self.__connect_serial_port_icon)
        self.__ui.motorAlign_btn.setIcon(self.__align_icon)

    def __connect_serial_port(self) -> None:

        self.__logger.info("Connecting to arduino stepper motor controller on port %s", self.__ui.motorSerialPort_cmbbox.currentText())

        connected: bool = self.__stepper_motor_wrapper.connect()
        if connected:
            self.__ui.motorSerialConnect_btn.icon = self.__disconnect_serial_port_icon
            self.__ui.motorEnable_chkbx.setEnabled(True)
            self.__ui.motorManual_chkbx.setEnabled(True)
            self.__logger.info("Connected to arduino stepper motor controller on port %s", self.__ui.motorSerialPort_cmbbox.currentText())
            return connected
        
    
        self.__ui.motorSerialConnect_btn.icon = self.__connect_serial_port_icon
        self.__ui.motorEnable_chkbx.setEnabled(False)
        self.__ui.motorEnable_chkbx.setEnabled(False)
        self.__logger.warning("Failed to connected to arduino stepper motor controller on port %s", self.__ui.motorSerialPort_cmbbox.currentText())
        

    def __disconnect_serial_port(self):

        self.__logger.info("Disconnecting from arduino stepper motor controller on port %s", self.__ui.motorSerialPort_cmbbox.currentText())

        self.__stepper_motor_wrapper.disconnect()

        self.__ui.motorSerialConnect_btn.icon = self.__connect_serial_port_icon
        self.__ui.motorEnable_chkbx.setEnabled(False)
        self.__logger.info("Disconnected from arduino stepper motor controller on port %s", self.__ui.motorSerialPort_cmbbox.currentText())
        return True