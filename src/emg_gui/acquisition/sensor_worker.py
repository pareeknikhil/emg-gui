import numpy as np
from dvg_ringbuffer import RingBuffer
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot

from emg_gui.acquisition.data_source import DataSource
from emg_gui.config.constants import (EDGE_ARTIFACT_BUFFER, GUI_WIDTH,
                                      SENSOR_POLL_INTERVAL_MS)
from emg_gui.core.logger import Logger
from emg_gui.core.types import EMGArray


class SensorWorker(QObject):

    stream_changed = pyqtSignal(str)
    record_changed = pyqtSignal(str)
    marker_changed = pyqtSignal(str)
    reset_changed = pyqtSignal(str)

    def __init__(self, logger: Logger, board: DataSource) -> None:
        super().__init__()
        self.logger = logger
        self.board = board

        _buffer_length = GUI_WIDTH+EDGE_ARTIFACT_BUFFER
        self._emg_channel_count = board.emg_channel_count

        self.zero_window = np.zeros((_buffer_length, self._emg_channel_count), dtype=np.float64)

        self.ring_buffer = RingBuffer(capacity=_buffer_length, dtype= (np.float64, self._emg_channel_count))  # pyright: ignore[reportArgumentType]
        self.ring_buffer.extend(self.zero_window)

        self.latest_snapshot = self.zero_window.T.copy(order="C")

        self.sensor_timer = QTimer(self)
        self.sensor_timer.timeout.connect(self.receive_sensor_data)
        self.sensor_timer.setInterval(SENSOR_POLL_INTERVAL_MS)

    @pyqtSlot()
    def receive_sensor_data(self) -> None:
        emg_with_marker_data = self.board.get_data()
        self.board.record(emg_with_marker_data)
        emg_data = self.board.extract_emg_data(emg_with_marker_data)
        self.ring_buffer.extend(emg_data.T)
        buffer_copy = self.ring_buffer[:].T.copy(order="C")
        self.latest_snapshot = buffer_copy # atomic assignment swaps without locks: thread safe

    @pyqtSlot()
    def publish_buffer_snapshot(self) -> tuple[EMGArray, bool]:
        """Called/Runs directly by the GUI thread without any locks."""
        return (self.latest_snapshot, self.board.is_streaming)

    @pyqtSlot()
    def stream(self) -> None:
        if self.board.is_streaming:
            self.sensor_timer.stop()
            self.ring_buffer.extend(self.zero_window)
            self.latest_snapshot = self.zero_window.T.copy(order="C")
            self.board.stop_stream()
            self.stream_changed.emit("Stream")
            return

        self.board.start_stream()
        self.sensor_timer.start()
        self.stream_changed.emit("Streaming")

    @pyqtSlot()
    def shutdown_timer(self) -> None:
        if self.sensor_timer.isActive():
            self.logger.info("SENSORWORKER: Killed QTimer in sensor thread")
            self.sensor_timer.stop()

    @pyqtSlot(str, str)
    def record(self, selected_datasplit: str, selected_folder: str) -> None:
        if self.board.is_recording:
            self.board.stop_recording()
            self.board.write_to_csv(selected_datasplit, selected_folder)
            self.record_changed.emit('Record')
            return

        self.board.start_recording()
        self.record_changed.emit('Recording')

    @pyqtSlot()
    def marker(self) -> None:
        if self.board.is_active:
            self.board.insert_stop_marker()
            self.marker_changed.emit('Start Movement')
            return

        self.board.insert_start_marker()
        self.marker_changed.emit('Stop Movement')

    @pyqtSlot()
    def reset(self) -> None:
        self.ring_buffer.extend(self.zero_window)
