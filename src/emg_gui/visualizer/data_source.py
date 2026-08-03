import sys
import time
from typing import Protocol

import numpy as np
from brainflow.board_shim import BoardIds, BoardShim, BrainFlowInputParams
from brainflow.data_filter import DataFilter
from typing_extensions import override

from emg_gui.configs.constants import IS_SYNTHETIC_BOARD, MARKER_END_ACTIVITY, MARKER_START_ACTIVITY, SERIAL_PORT_LINUX
from emg_gui.core.enums import ActivityState, RecordingState
from emg_gui.core.types import EMGArray
from emg_gui.utils.tfrecord_utils import get_all_files


class DataSource(Protocol):
    @classmethod
    def get_list_emg_channels(cls) -> list[int]: ...

    @classmethod
    def get_count_emg_channels(cls) -> int: ...

    def start_stream(self) -> None: ...

    def stop_stream(self) -> None: ...

    def start_recording(self) -> None: ...

    def stop_recording(self) -> None: ...

    def insert_start_marker(self) -> None: ...

    def insert_stop_marker(self) -> None: ...

    def get_data(self, num_of_samples_expctd: int) -> EMGArray: ...

    def write_to_disk(self, type: str, label: str) -> None: ...

    @property
    def recording_state(self) -> RecordingState: ...

    @property
    def activity_state(self) -> ActivityState: ...


class RealOpenBCI:
    BOARDID = BoardIds.SYNTHETIC_BOARD if IS_SYNTHETIC_BOARD else BoardIds.CYTON_BOARD

    __instance = None

    @classmethod
    def get_instance(cls, logger) -> DataSource:
        if cls.__instance is None:
            cls.__instance = cls(logger)
        return cls.__instance

    @classmethod
    def get_list_emg_channels(cls) -> list[int]:
        channels = BoardShim.get_emg_channels(board_id=BoardIds.CYTON_BOARD)  ## [TECH DEBT: hardcoded to cyton]
        marker_channel = BoardShim.get_marker_channel(board_id=BoardIds.CYTON_BOARD)  ## [TECH DEBT: hardcoded to cyton]
        return channels + [
            marker_channel
        ]  ## hard-coded: suppose to work for synthetic or cyton board (not any other config)

    @classmethod
    def get_count_emg_channels(cls) -> int:
        num_of_channels = len(BoardShim.get_emg_channels(board_id=BoardIds.CYTON_BOARD)) + len(
            [BoardShim.get_marker_channel(board_id=BoardIds.CYTON_BOARD)]
        )
        return num_of_channels

    def __init__(self, logger) -> None:
        BoardShim.enable_dev_board_logger()
        self.logger = logger

        _params = BrainFlowInputParams()
        _params.serial_port = SERIAL_PORT_LINUX

        self._emg_channels = RealOpenBCI.get_list_emg_channels()
        self._board = BoardShim(board_id=self.BOARDID, input_params=_params)
        self._board.prepare_session()
        if not self._board.is_prepared():
            sys.exit(1)

        self._turn_off_srb(self._board)
        self.logger.info("DATASOURCE: Board initialized and SRB channels turned-off")

        self._recording_state = RecordingState.IDLE
        self._activity_state = ActivityState.INACTIVE

        self._emg_recording: list[EMGArray] = []

    def start_stream(self) -> None:
        if self._board.is_prepared():
            self._board.start_stream()
            self.logger.info(f"DATASOURCE: Data Stream Started (synthetic data: {IS_SYNTHETIC_BOARD})")
        else:
            self.logger.error("DATASOURCE: Unable to connect with OpenBCI board")
            sys.exit(1)

    def stop_stream(self) -> None:
        self._board.stop_stream()
        self._board.release_session()
        self.logger.info("DATASOURCE: OpenBCI Stream closed successfully")

    def start_recording(self) -> None:
        if self._recording_state is RecordingState.RECORDING:
            raise RuntimeError("DATASOURCE: Recording has already started")

        self._recording_state = RecordingState.RECORDING

    def stop_recording(self) -> None:
        if self.recording_state is RecordingState.IDLE:
            raise RuntimeError("DATASOURCE: Recording has already stopped")

        self._recording_state = RecordingState.IDLE

    def insert_start_marker(self) -> None:
        if self.activity_state is ActivityState.ACTIVE:
            raise RuntimeError("DATASOURCE: Activity has already started")

        self._board.insert_marker(MARKER_START_ACTIVITY)
        self._activity_state = ActivityState.ACTIVE

    def insert_stop_marker(self) -> None:
        if self.activity_state is ActivityState.INACTIVE:
            raise RuntimeError("DATASOURCE: Activity has already stopped")

        self._board.insert_marker(MARKER_END_ACTIVITY)
        self._activity_state = ActivityState.INACTIVE

    def get_data(self, num_of_samples_expctd: int) -> EMGArray:
        board_data = self._board.get_board_data(num_samples=num_of_samples_expctd)
        emg_data = board_data[self._emg_channels, :]
        if self.recording_state is RecordingState.RECORDING:
            self._emg_recording.append(emg_data)
        num_of_sampl_recvd = board_data.shape[-1]
        self.logger.info(
            f"DATASOURCE: Received data per channel from board: {num_of_sampl_recvd}, requested: {num_of_samples_expctd}"
        )
        if num_of_sampl_recvd == num_of_samples_expctd:
            return emg_data

        padded_emg_data = np.zeros([len(self._emg_channels), num_of_samples_expctd])
        padded_emg_data[:, : emg_data.shape[1]] = emg_data
        self.logger.info(f"DATASOURCE: Padded data on per channel (new no. of samples {padded_emg_data.shape[1]})")
        return padded_emg_data

    def write_to_disk(self, type: str, label: str) -> None:
        emg_numpy = np.concatenate(self._emg_recording, axis=1)
        file_path = f"data/csv/{type}/{label}/{str(int(time.time()))}__{label}.csv"
        DataFilter.write_file(data=emg_numpy, file_name=file_path, file_mode="w")
        file_ds = get_all_files(
            pattern=f"data/csv/{type}/{label}/*.csv", shuffle_flag=False
        )  ## hard-coded: [TECH DEBT]
        print(f"DATASOURCE: File written in folder: {type}/{label} (Total files: {sum(1 for _ in file_ds)})")
        self._emg_recording.clear()
        print("DATASOURCE: Source data storage cleaned(Reset)")

    @property
    def recording_state(self) -> RecordingState:
        return self._recording_state

    @property
    def activity_state(self) -> ActivityState:
        return self._activity_state

    def _turn_off_srb(self, board):
        for channel in self._emg_channels:
            if channel != 23:  ##--------Temp fix(excluded marker channel)-------------##
                board_response = board.config_board(f"x{channel}060100X")[:1]
                if board_response not in {"S", "C"}:
                    sys.exit(1)


class VisualizeFile(RealOpenBCI):
    @override
    def __init__(self, logger) -> None:
        super().__init__(logger)

        self.emg_channels = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        self.file = "data/csv/train/sample/1785181476__sample.csv"

        self.data = np.loadtxt(self.file, delimiter="\t").T
        self.current_idx = 0
        self.max_idx = self.data.shape[1]

    @override
    def get_data(self, num_of_samples_expctd: int) -> EMGArray:
        if (self.current_idx + 10) > self.max_idx:
            board_data = np.zeros([len(self.emg_channels), num_of_samples_expctd])
        else:
            board_data = self.data[:, self.current_idx : self.current_idx + 10]
            self.current_idx = self.current_idx + 10
        emg_data = board_data[self.emg_channels, :]
        if self.recording_state is RecordingState.RECORDING:
            self._emg_recording.append(emg_data)
        num_of_sampl_recvd = board_data.shape[-1]
        self.logger.info(
            f"DATASOURCE: Received data per channel from board: {num_of_sampl_recvd}, requested: {num_of_samples_expctd}"
        )
        if num_of_sampl_recvd == num_of_samples_expctd:
            return emg_data

        padded_emg_data = np.zeros([len(self.emg_channels), num_of_samples_expctd])
        padded_emg_data[:, : emg_data.shape[1]] = emg_data
        self.logger.info(f"DATASOURCE: Padded data on per channel (new no. of samples {padded_emg_data.shape[1]})")
        return padded_emg_data
