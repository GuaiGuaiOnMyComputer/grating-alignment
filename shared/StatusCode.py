from enum import IntEnum

class StatusCode(IntEnum):

    EmergencyStop = 0
    StandBy = 1
    TaskRunning = 2
    TaskCancelled = 3
    TaskComplete = 4
    