from enum import Enum, auto


class StreamingState(Enum):
    IDLE = auto()
    STREAMING = auto()


class RecordingState(Enum):
    IDLE = auto()
    RECORDING = auto()


class ActivityState(Enum):
    ACTIVE = auto()
    INACTIVE = auto()


class DatasetSplit(str, Enum):
    TRAIN = "train"
    VALIDATE = "validate"
    TEST = "test"


class DataSourceType(str, Enum):
    REAL = "real"
    SYNTHETIC = "synthetic"
    PLAYBACK = "playback"
