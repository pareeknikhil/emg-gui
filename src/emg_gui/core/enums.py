from enum import Enum, IntEnum, auto

from brainflow.board_shim import BoardIds  # type: ignore[import-untyped]
from brainflow.data_filter import NoiseTypes  # type: ignore[import-untyped]


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


class OpenBCIBoardType(IntEnum):
    CYTON_SERIAL = BoardIds.CYTON_BOARD
    CYTON_DAISY_SERIAL = BoardIds.CYTON_DAISY_BOARD
    GANGLION_DONGLE = BoardIds.GANGLION_BOARD
    GANGLION_NATIVE = BoardIds.GANGLION_NATIVE_BOARD
    CYTON_WIFI = BoardIds.CYTON_WIFI_BOARD
    CYTON_DAISY_WIFI = BoardIds.CYTON_DAISY_WIFI_BOARD
    GANGLION_WIFI = BoardIds.GANGLION_WIFI_BOARD
    SYNTHETIC = BoardIds.SYNTHETIC_BOARD


class MainsFrequency(IntEnum):
    FIFTY_HZ = NoiseTypes.FIFTY
    SIXTY_HZ = NoiseTypes.SIXTY
