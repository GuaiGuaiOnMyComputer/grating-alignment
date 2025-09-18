from typing import NamedTuple
from enum import Enum
from typing import NamedTuple

class StepperDriverPins(NamedTuple):

    direction: int
    step: int
    ms1:int
    ms2:int
    ms3:int
    sleep:int
    reset:int
    enable:int

class DriverLineEnum(Enum):
    A4988 = 0
    DRV8825 = 1
    TMC2209 = 2
    Unknown = 999

class StepperMotorInitParams(NamedTuple):

    enable_pin:int
    ms1: int

class StepperMotor4Line:

    def __init__(self, init_params):
        pass