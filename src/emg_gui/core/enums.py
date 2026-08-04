from enum import Enum, auto


class RecordingState(Enum):
    IDLE = auto()
    RECORDING = auto()


class ActivityState(Enum):
    ACTIVE = auto()
    INACTIVE = auto()
