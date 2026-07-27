import sys
import time

import numpy as np
from brainflow.board_shim import BoardIds, BoardShim, BrainFlowInputParams
from brainflow.data_filter import DataFilter

from configs.constants import IS_SYNTHETIC_BOARD, SERIAL_PORT_LINUX, MARKER_START_ACTIVITY, MARKER_END_ACTIVITY

from ..utils.tfrecord_utils import get_all_files
from ..core.enums import RecordingState, ActivityState

class Source():
    BOARDID = BoardIds.SYNTHETIC_BOARD if IS_SYNTHETIC_BOARD else BoardIds.CYTON_BOARD

    __instance = None

    @classmethod
    def get_instance(cls, logger) -> "Source":
        if cls.__instance is None:
            cls.__instance = cls(logger)
        return cls.__instance

    def __init__(self, logger) -> None:
        BoardShim.enable_dev_board_logger()
        self.logger = logger

        _params = BrainFlowInputParams()
        _params.serial_port = SERIAL_PORT_LINUX

        self.emg_channels = Source.get_emg_channels()
        self.board = BoardShim(board_id=Source.BOARDID, input_params=_params)
        self.board.prepare_session()
        if not self.board.is_prepared():
            sys.exit(1)

        self.turn_off_srb(self.board)
        self.logger.info("SOURCE: Board initialized and SRB channels turned-off")

        self.recording_state = RecordingState.IDLE
        self.activity_state = ActivityState.INACTIVE

        self.emg_recording = []

    def start_recording(self) -> None:
        if self.recording_state is RecordingState.RECORDING:
            raise RuntimeError("Recording has already started")
        
        self.recording_state = RecordingState.RECORDING

    def stop_recording(self) -> None:
        if self.recording_state is RecordingState.IDLE:
            raise RuntimeError("Recording has already stopped")
        
        self.recording_state = RecordingState.IDLE

    def insert_start_marker(self) -> None:
        if self.activity_state is ActivityState.ACTIVE:
            raise RuntimeError("Activity has already started")

        self.board.insert_marker(MARKER_START_ACTIVITY)
        self.activity_state = ActivityState.ACTIVE

    def insert_stop_marker(self) -> None:
        if self.activity_state is ActivityState.INACTIVE:
            raise RuntimeError("Activity has already stopped")

        self.board.insert_marker(MARKER_END_ACTIVITY)
        self.activity_state = ActivityState.INACTIVE

    @staticmethod
    def get_emg_channels():
        channels = BoardShim.get_emg_channels(board_id=BoardIds.CYTON_BOARD)
        marker_channel = BoardShim.get_marker_channel(board_id=Source.BOARDID)
        return channels + [marker_channel] ## hard-coded: suppose to work for synthetic or cyton board (not any other config) 

    @staticmethod
    def get_num_emg_channels():
        num_of_channels = len(BoardShim.get_emg_channels(board_id=BoardIds.CYTON_BOARD)) + len([BoardShim.get_marker_channel(board_id=BoardIds.CYTON_BOARD)])
        return num_of_channels

    def turn_off_srb(self, board):
        for channel in self.emg_channels:
            if channel != 23: ##--------Temp fix(excluded marker channel)-------------##
                board_response = board.config_board(f'x{channel}060100X')[:1]
                if board_response not in {'S', 'C'}:
                    sys.exit(1)

    def start_stream(self) -> None:
        if self.board.is_prepared():
            self.board.start_stream()
            self.logger.info(f"SOURCE: Data Stream Started (synthetic data: {IS_SYNTHETIC_BOARD})")
        else:
            self.logger.error("SOURCE: Unable to connect with OpenBCI board")
            sys.exit(1)

    def get_data(self, num_of_samples_expctd) -> np.ndarray:
        board_data = self.board.get_board_data(num_samples=num_of_samples_expctd)
        emg_data = board_data[self.emg_channels, :]
        if self.recording_state is RecordingState.RECORDING:
            self.emg_recording.append(emg_data)
        num_of_sampl_recvd = board_data.shape[-1]
        self.logger.info(f"SOURCE: Received data per channel from board: {num_of_sampl_recvd}, requested: {num_of_samples_expctd}")
        if num_of_sampl_recvd == num_of_samples_expctd:
            return emg_data

        padded_emg_data = np.zeros([len(self.emg_channels), num_of_samples_expctd])
        padded_emg_data[:, :emg_data.shape[1]] = emg_data
        self.logger.info(f"SOURCE: Padded data on per channel (new no. of samples {padded_emg_data.shape[1]})")
        return padded_emg_data

    def release_board(self) -> None:
        self.board.stop_stream()
        self.board.release_session()
        self.logger.info("SOURCE: OpenBCI Stream closed successfully")

    def write_to_disk(self, type, label) -> None:
        emg_numpy = np.concatenate(self.emg_recording, axis=1)
        file_path = f'data/csv/{type}/{label}/{str(int(time.time()))}__{label}.csv'
        DataFilter.write_file(data=emg_numpy, file_name=file_path, file_mode='w')
        file_ds = get_all_files(pattern=f'data/csv/{type}/{label}/*.csv', shuffle_flag=False) ## hard-coded: [TECH DEBT]
        print(f"SOURCE: File written in folder: {type}/{label} (Total files: {sum(1 for _ in file_ds)})")
        self.emg_recording.clear()
        print("SOURCE: Source data storage cleaned(Reset)")