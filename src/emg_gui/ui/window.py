from PyQt5.QtCore import QMetaObject, Qt, QThread, QTimer
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QWidget

from emg_gui.acquisition.data_source import DataSource
from emg_gui.acquisition.sensor_worker import SensorWorker
from emg_gui.core.logger import Logger
from emg_gui.ui.control_panel import EMGControlPanel
from emg_gui.visualizer.open_gl_widget import EMGOpenGLWidget


class EMGVisualizerWindow(QMainWindow):

    def __init__(self, logger: Logger, board: DataSource) -> None:
        super().__init__()

        self._logger = logger

        self.setWindowTitle("emg-gui")
        self.showMaximized()

        self._control_section = EMGControlPanel()

        self._open_gl_widget = EMGOpenGLWidget(
            self._logger, board.emg_channel_count, board.sampling_rate
        )

        main_layout = QHBoxLayout()
        main_layout.addWidget(self._control_section, stretch=1)
        main_layout.addWidget(self._open_gl_widget, stretch=12)

        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

        self._sensor_thread = QThread()
        self._sensor_worker = SensorWorker(self._logger, board)
        self._sensor_worker.moveToThread(self._sensor_thread)

        self._control_section.stream_request.connect(self._sensor_worker.stream)
        self._sensor_worker.stream_changed.connect(
            self._control_section.set_stream_button_text
        )

        self._control_section.record_request.connect(self._sensor_worker.record)
        self._sensor_worker.record_changed.connect(
            self._control_section.set_record_button_text
        )

        self._control_section.marker_request.connect(self._sensor_worker.marker)
        self._sensor_worker.marker_changed.connect(
            self._control_section.set_marker_button_text
        )

        self._control_section.reset_request.connect(self._sensor_worker.reset)
        self._sensor_worker.reset_changed.connect(
            self._control_section.set_reset_button_text
        )

        self._open_gl_widget.frame_rendered.connect(self._schedule_next_render)

        self._sensor_thread.start()

        QTimer.singleShot(0, self._render_loop)

    def _render_loop(self) -> None:
        buffer_snapshot, is_streaming = (
            self._sensor_worker.publish_buffer_snapshot()
        )  # buffer snapshot is read-only for GUI/Main thread
        self._open_gl_widget.submit_snapshot(
            raw_snapshot=buffer_snapshot, freeze_duplicate_snapshots=is_streaming
        )

    def _schedule_next_render(self) -> None:
        QTimer.singleShot(0, self._render_loop)

    def closeEvent(self, a0) -> None:
        QMetaObject.invokeMethod(
            self._sensor_worker,
            "shutdown_timer",
            Qt.ConnectionType.BlockingQueuedConnection,
        )
        self._sensor_thread.quit()
        self._sensor_thread.wait()
        self._logger.info("WINDOW: SensorWorker closed successfully")
        self._open_gl_widget.release()
        self._logger.info("WINDOW: ModernGL GPU resources released")
        super().closeEvent(a0)

    @classmethod
    def run(cls, logger: Logger, board: DataSource) -> None:
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        qt_app = QApplication([])
        window = cls(logger, board)
        window.show()
        qt_app.exit(qt_app.exec())
