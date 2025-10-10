from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QEvent, QObject, pyqtSignal
from PyQt6.QtGui import QWheelEvent
from typing import Callable, List

class MouseEventFilter(QObject):
    """
    Summary:
        An event filter that is meant to be installed on a parent widget, monitoring certain events in the child widgets.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    @property
    def hover_entered(self) -> pyqtSignal:
        """An event triggered when mouse pointer enters a widget."""
        return self.__hover_entered
    
    @property
    def hover_left(self) -> pyqtSignal:
        """An event triggered when mouse pointer leaves a widget."""
        return self.__hover_left
    
    @property
    def wheel(self) -> pyqtSignal:
        """An event triggered when mouse wheel is scrolled in a widget."""
        return self.__wheel
    
    @property
    def wheel_event_handler(self) -> List[Callable[[QWidget, QWheelEvent], None]]:
        """
        Summary:
            A list of functions to call when a wheel event is triggered. These functions must have the following parameters in order:
                1. The widget on which the wheel is scrolled on.
                2. The wheel event object.
            Return value of the functions are ignored.
        """
        return self.__wheel_event_handler
    
    __hover_entered = pyqtSignal(QEvent)
    __hover_left = pyqtSignal(QEvent)
    __wheel = pyqtSignal(QEvent)

    __wheel_event_handler: List[Callable[[QWidget, QWheelEvent], None]] = []

    def eventFilter(self, watched_object: QWidget, event: QEvent):

        if event.type() == QEvent.Type.Enter:
            self.__hover_entered.emit(event)
            return True # Event handled

        if event.type() == QEvent.Type.Leave:
            self.__hover_left.emit(event)
            return True # Event handled
        
        if event.type() == QEvent.Type.Wheel:
            self.__wheel.emit(event)
            handler: Callable[[QWidget, QWheelEvent], None]
            for handler in self.__wheel_event_handler:
                handler(watched_object, event)

            return True

        return super().eventFilter(watched_object, event)