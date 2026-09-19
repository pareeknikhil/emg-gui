import numpy as np
from dvg_ringbuffer import RingBuffer
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot

from emg_gui.acquisition.data_source import DataSource
from emg_gui.config.constants import (
    EDGE_ARTIFACT_BUFFER,
    SENSOR_POLL_INTERVAL_MS,
    TIME_WINDOW_SAMPLES,
)
from emg_gui.core.logger import Logger
from emg_gui.core.types import EMGArray


class SensorWorker(QObject):

    stream_changed = pyqtSignal(str)
    record_changed = pyqtSignal(str)
    marker_changed = pyqtSignal(str)
    reset_changed = pyqtSignal(str)

    def __init__(self, logger: Logger, board: DataSource) -> None:
        super().__init__()
        self._logger = logger
        self._board = board

        _buffer_length = TIME_WINDOW_SAMPLES + EDGE_ARTIFACT_BUFFER
        self._emg_channel_count = board.emg_channel_count

        self._zero_window = np.zeros(
            (_buffer_length, self._emg_channel_count), dtype=np.float64
        )

        self._ring_buffer = RingBuffer(
            capacity=_buffer_length,
            dtype=(
                np.float64,
                self._emg_channel_count,
            ),  # pyright: ignore[reportArgumentType]
        )
        self._ring_buffer.extend(self._zero_window)

        self._latest_snapshot = self._zero_window.T.copy(order="C")

        self._sensor_timer = QTimer(self)
        self._sensor_timer.timeout.connect(self._receive_sensor_data)
        self._sensor_timer.setInterval(SENSOR_POLL_INTERVAL_MS)

    @pyqtSlot()
    def _receive_sensor_data(self) -> None:
        emg_with_marker_data = self._board.get_data()
        self._board.record(emg_with_marker_data)
        emg_data = self._board.extract_emg_data(emg_with_marker_data)
        self._ring_buffer.extend(emg_data.T)
        buffer_copy = self._ring_buffer[:].T.copy(order="C")
        self._latest_snapshot = (
            buffer_copy  # atomic assignment swaps without locks: thread safe
        )

    @pyqtSlot()
    def publish_buffer_snapshot(self) -> tuple[EMGArray, bool]:
        """Called/Runs directly by the GUI thread without any locks."""
        return (self._latest_snapshot, self._board.is_streaming)

    @pyqtSlot()
    def stream(self) -> None:
        if self._board.is_streaming:
            self._sensor_timer.stop()
            self._ring_buffer.extend(self._zero_window)
            self._latest_snapshot = self._zero_window.T.copy(order="C")
            self._board.stop_stream()
            self.stream_changed.emit("Stream")
            return

        self._board.start_stream()
        self._sensor_timer.start()
        self.stream_changed.emit("Streaming")

    @pyqtSlot()
    def shutdown_timer(self) -> None:
        if self._sensor_timer.isActive():
            self._logger.info("SENSORWORKER: Killed QTimer in sensor thread")
            self._sensor_timer.stop()

    @pyqtSlot(str, str)
    def record(self, selected_datasplit: str, selected_folder: str) -> None:
        if self._board.is_recording:
            self._board.stop_recording()
            self._board.write_to_csv(selected_datasplit, selected_folder)
            self.record_changed.emit("Record")
            return

        self._board.start_recording()
        self.record_changed.emit("Recording")

    @pyqtSlot()
    def marker(self) -> None:
        if self._board.is_active:
            self._board.insert_stop_marker()
            self.marker_changed.emit("Start Movement")
            return

        self._board.insert_start_marker()
        self.marker_changed.emit("Stop Movement")

    @pyqtSlot()
    def reset(self) -> None:
        self._ring_buffer.extend(self._zero_window)
