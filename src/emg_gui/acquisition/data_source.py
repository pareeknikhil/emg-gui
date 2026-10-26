import sys
import time
from dataclasses import dataclass
from typing import Protocol

import numpy as np
from brainflow.board_shim import BoardShim  # type: ignore[import-untyped]
from brainflow.board_shim import BrainFlowInputParams
from brainflow.data_filter import DataFilter  # type: ignore[import-untyped]

from emg_gui.acquisition.dataset_files import get_all_files
from emg_gui.config.constants import MARKER_END_ACTIVITY, MARKER_START_ACTIVITY
from emg_gui.core.enums import (ActivityState, OpenBCIBoardType,
                                RecordingState, StreamingState)
from emg_gui.core.logger import Logger
from emg_gui.core.types import EMGArray


@dataclass(frozen=True)
class OpenBCIConfig():
    board_type: OpenBCIBoardType
    polling_interval_ms: int = 40
    turn_off_srb: bool = False
    ip_port: int = 0
    serial_port: str = ""
    mac_address: str = ""
    other_info: str = ""
    serial_number: str = ""
    ip_address: str = ""
    ip_protocol: int = 0
    timeout: int = 0


@dataclass(frozen=True)
class PlayBackConfig():
    board_type: OpenBCIBoardType
    file_path: str = ""
    polling_interval_ms: int = 40


class DataSource(Protocol):

    def start_stream(self) -> None: ...

    def stop_stream(self) -> None: ...

    def start_recording(self) -> None: ...

    def stop_recording(self) -> None: ...

    def record(self, data) -> None: ...

    def insert_start_marker(self) -> None: ...

    def insert_stop_marker(self) -> None: ...

    def get_data(self) -> EMGArray: ...

    def extract_emg_data(self, emg_with_marker_data: EMGArray) -> EMGArray: ...

    def write_to_csv(self, datasplit: str, folder: str) -> None: ...

    def release(self) -> None: ...

    @property
    def emg_channel_count(self) -> int: ...

    @property
    def is_streaming(self) -> bool: ...

    @property
    def is_recording(self) -> bool: ...

    @property
    def is_active(self) -> bool: ...

    @property
    def sampling_rate(self) -> int: ...

    @property
    def polling_interval_ms(self) -> int: ...

class OpenBCIBoard:

    @staticmethod
    def _create_input_params(config: OpenBCIConfig) -> BrainFlowInputParams:
        _params = BrainFlowInputParams()

        for openbci_field in (
            "ip_port",
            "serial_port",
            "mac_address",
            "other_info",
            "serial_number",
            "ip_address",
            "ip_protocol",
            "timeout",
        ):
            user_passed_params = getattr(config, openbci_field)
            setattr(_params, openbci_field, user_passed_params)

        return _params

    def __init__(self, logger: Logger, config: OpenBCIConfig) -> None:
        BoardShim.enable_board_logger()
        self._logger = logger
        self._board_id = config.board_type
        self._polling_interval_ms = config.polling_interval_ms

        self._brainflow_emg_channels = BoardShim.get_emg_channels(
            board_id=config.board_type
        )
        brainflow_marker_channel = BoardShim.get_marker_channel(board_id=self._board_id)

        self._data_channels = self._brainflow_emg_channels + [brainflow_marker_channel]
        self._emg_channel_count = len(self._brainflow_emg_channels)

        _params = self._create_input_params(config)

        self._board = BoardShim(board_id=self._board_id, input_params=_params)
        self._board.prepare_session()
        if not self._board.is_prepared():
            self._logger.error("DATASOURCE: Board cannot be initialized")
            sys.exit(1)

        if config.turn_off_srb:
            self._turn_off_srb(self._board)
            self._logger.info("DATASOURCE: SRB channels turned-off")

        self._logger.info("DATASOURCE: Board initialized...")

        self._streaming_state = StreamingState.IDLE
        self._recording_state = RecordingState.IDLE
        self._activity_state = ActivityState.INACTIVE

        self._emg_recording: list[EMGArray] = []

    @property
    def emg_channel_count(self) -> int:
        return self._emg_channel_count

    def start_stream(self) -> None:
        if self.is_streaming:
            raise RuntimeError("DATASOURCE: Streaming has already started")

        if self._board.is_prepared():
            self._board.start_stream()
            self._logger.info(
                f"DATASOURCE: Streaming Data...)"
            )
        else:
            self._logger.error("DATASOURCE: Unable to connect with OpenBCI board")
            raise RuntimeError("DATASOURCE: Unable to connect with OpenBCI board")

        self._streaming_state = StreamingState.STREAMING

    def stop_stream(self) -> None:
        if not self.is_streaming:
            raise RuntimeError("DATASOURCE: Streaming has already stopped")

        self._board.stop_stream()
        self._logger.info("DATASOURCE: Data Stream closed successfully")

        flush_data = self._board.get_board_data()
        self._logger.info(
            f"DATASOURCE: Brainflow ring buffer cleaned: {flush_data.shape[1]}"
        )

        self._logger.info(
            f"DATASOURCE: Brainflow ring buffer after cleaning: {self._board.get_board_data_count()}"
        )

        self._streaming_state = StreamingState.IDLE

    def start_recording(self) -> None:
        if self.is_recording:
            raise RuntimeError("DATASOURCE: Recording has already started")

        self._recording_state = RecordingState.RECORDING

    def stop_recording(self) -> None:
        if not self.is_recording:
            raise RuntimeError("DATASOURCE: Recording has already stopped")

        self._recording_state = RecordingState.IDLE

    def record(self, data) -> None:
        if self.is_recording:
            self._emg_recording.append(data)

    def insert_start_marker(self) -> None:
        if self.is_active:
            raise RuntimeError("DATASOURCE: Activity has already started")

        self._board.insert_marker(MARKER_START_ACTIVITY)
        self._activity_state = ActivityState.ACTIVE

    def insert_stop_marker(self) -> None:
        if not self.is_active:
            raise RuntimeError("DATASOURCE: Activity has already stopped")

        self._board.insert_marker(MARKER_END_ACTIVITY)
        self._activity_state = ActivityState.INACTIVE

    def get_data(self) -> EMGArray:
        all_board_data = self._board.get_board_data()
        active_channel_data = all_board_data[self._data_channels, :]
        return active_channel_data

    def extract_emg_data(self, emg_with_marker_data: EMGArray) -> EMGArray:
        emg_data = emg_with_marker_data[
            : self.emg_channel_count, :
        ]  # assumes marker is last
        return emg_data

    def write_to_csv(self, datasplit: str, folder: str) -> None:
        emg_numpy = np.concatenate(self._emg_recording, axis=1)
        file_path = (
            f"data/csv/{datasplit}/{folder}/{str(int(time.time()))}__{folder}.csv"
        )
        DataFilter.write_file(data=emg_numpy, file_name=file_path, file_mode="w")
        file_ds = get_all_files(
            pattern=f"data/csv/{datasplit}/{folder}/*.csv", shuffle_flag=False
        )  # hard-coded: [TECH DEBT]
        self._logger.info(
            f"DATASOURCE: File written @ {file_path} (Total files: {sum(1 for _ in file_ds)})"
        )
        self._emg_recording.clear()
        self._logger.info("DATASOURCE: Source data storage cleaned(Reset)")

    def release(self) -> None:
        if self.is_streaming:
            self.stop_stream()
        if self._board.is_prepared():
            self._board.release_session()
        BoardShim.disable_board_logger()

    @property
    def sampling_rate(self) -> int:
        return self._board.get_sampling_rate(self._board_id)

    @property
    def polling_interval_ms(self) -> int:
        return self._polling_interval_ms

    @property
    def is_streaming(self) -> bool:
        return self._streaming_state is StreamingState.STREAMING

    @property
    def is_recording(self) -> bool:
        return self._recording_state is RecordingState.RECORDING

    @property
    def is_active(self) -> bool:
        return self._activity_state is ActivityState.ACTIVE

    def _turn_off_srb(self, board):
        for channel in self._brainflow_emg_channels:
            board_response = board.config_board(f"x{channel}060100X")[:1]
            if board_response not in {"S", "C"}:
                sys.exit(1)

class PlaybackRecording:

    def __init__(self, logger: Logger, config: PlayBackConfig) -> None:
        self._logger = logger
        self._board_id = config.board_type
        self._file_path = config.file_path
        self._polling_interval_ms = config.polling_interval_ms

        self._data = np.loadtxt(self._file_path, delimiter="\t").T
        self._current_idx = 0
        self._max_idx = self._data.shape[1]

        self._data_channels = list(range(self._data.shape[0]))
        self._emg_channel_count = len(self._data_channels) - 1  # assumes marker is last

        self._logger.info(
            f"DATASOURCE: PlaybackRecording - file: {self._file_path}"
            f"- Channels: {self._data_channels}"
            f"- EMG Channels Count: {self._emg_channel_count}"
        )

        self._streaming_state = StreamingState.IDLE
        self._recording_state = RecordingState.IDLE
        self._activity_state = ActivityState.INACTIVE

    def start_stream(self) -> None:
        if self.is_streaming:
            raise RuntimeError("DATASOURCE: Playback has already started")

        self._logger.info("DATASOURCE: Playback Started (playing-recording)")
        self._current_idx = 0
        self._streaming_state = StreamingState.STREAMING

    def stop_stream(self) -> None:
        if not self.is_streaming:
            raise RuntimeError("DATASOURCE: Playback has already stopped")

        self._logger.info("DATASOURCE: Playback closed successfully")

        self._streaming_state = StreamingState.IDLE

    def start_recording(self) -> None:
        if self.is_recording:
            raise RuntimeError("DATASOURCE: Recording has already started")

        self._recording_state = RecordingState.RECORDING

    def stop_recording(self) -> None:
        if not self.is_recording:
            raise RuntimeError("DATASOURCE: Recording has already stopped")

        self._recording_state = RecordingState.IDLE

    def record(self, data) -> None:
        pass

    def insert_start_marker(self) -> None:
        if self.is_active:
            raise RuntimeError("DATASOURCE: Activity has already started")

        self._activity_state = ActivityState.ACTIVE

    def insert_stop_marker(self) -> None:
        if not self.is_active:
            raise RuntimeError("DATASOURCE: Activity has already stopped")

        self._activity_state = ActivityState.INACTIVE

    def get_data(self) -> EMGArray:
        expected_sample_count = round(
            self.sampling_rate * self._polling_interval_ms / 1000
        )  # playback speed

        end_idx = min(self._current_idx + expected_sample_count, self._max_idx)
        board_data = self._data[:, self._current_idx : end_idx]
        self._current_idx = end_idx

        return self._add_padding(
            board_data, len(self._data_channels), expected_sample_count
        )

    def extract_emg_data(self, emg_with_marker_data: EMGArray) -> EMGArray:
        emg_data = emg_with_marker_data[
            : self.emg_channel_count, :
        ]  # assumes marker is last
        return emg_data

    @staticmethod
    def _add_padding(
        board_data: EMGArray,
        channel_count: int,
        expected_samples: int,
    ) -> EMGArray:
        received_samples = board_data.shape[-1]

        if received_samples == expected_samples:
            return board_data

        padded_data = np.zeros(
            (channel_count, expected_samples),
            dtype=board_data.dtype,
        )
        padded_data[:, :received_samples] = board_data

        return padded_data

    def write_to_csv(self, datasplit: str, folder: str) -> None:
        return None

    def release(self) -> None:
        return None

    @property
    def sampling_rate(self) -> int:
        return BoardShim.get_sampling_rate(self._board_id)

    @property
    def polling_interval_ms(self) -> int:
        return self._polling_interval_ms

    @property
    def emg_channel_count(self) -> int:
        return self._emg_channel_count

    @property
    def is_streaming(self) -> bool:
        return self._streaming_state is StreamingState.STREAMING

    @property
    def is_recording(self) -> bool:
        return self._recording_state is RecordingState.RECORDING

    @property
    def is_active(self) -> bool:
        return self._activity_state is ActivityState.ACTIVE
        return self._activity_state is ActivityState.ACTIVE
