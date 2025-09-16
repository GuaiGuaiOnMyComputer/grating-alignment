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

class A4988StepperMotorContorl:

    def __init__(self):
        pass