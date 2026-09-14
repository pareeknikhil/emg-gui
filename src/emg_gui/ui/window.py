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

        self.logger = logger

        self.setWindowTitle("emg-gui")
        self.showMaximized()

        self.control_section = EMGControlPanel() 

        self.open_gl_widget = EMGOpenGLWidget(self.logger, board.emg_channel_count)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.control_section, stretch=1)
        main_layout.addWidget(self.open_gl_widget, stretch=12)

        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

        self.sensor_thread = QThread()
        self.sensor_worker = SensorWorker(self.logger, board)
        self.sensor_worker.moveToThread(self.sensor_thread)

        self.control_section.stream_request.connect(self.sensor_worker.stream)
        self.sensor_worker.stream_changed.connect(self.control_section.set_stream_button_text)

        self.control_section.record_request.connect(self.sensor_worker.record)
        self.sensor_worker.record_changed.connect(self.control_section.set_record_button_text)

        self.control_section.marker_request.connect(self.sensor_worker.marker)
        self.sensor_worker.marker_changed.connect(self.control_section.set_marker_button_text)

        self.control_section.reset_request.connect(self.sensor_worker.reset)
        self.sensor_worker.reset_changed.connect(self.control_section.set_reset_button_text)

        self.open_gl_widget.frame_rendered.connect(self.schedule_next_render)

        self.sensor_thread.start()

        QTimer.singleShot(0, self.render_loop)

    def render_loop(self) -> None:
        buffer_snapshot, is_streaming = self.sensor_worker.publish_buffer_snapshot() # buffer snapshot is read-only for GUI/Main thread
        self.open_gl_widget.submit_snapshot(raw_snapshot=buffer_snapshot, freeze_duplicate_snapshots=is_streaming)

    def schedule_next_render(self) -> None:
        QTimer.singleShot(0, self.render_loop)

    def closeEvent(self, a0) -> None:
        QMetaObject.invokeMethod(
            self.sensor_worker,
            "shutdown_timer",
            Qt.ConnectionType.BlockingQueuedConnection,
        )
        self.sensor_thread.quit()
        self.sensor_thread.wait()
        self.logger.info("WINDOW: SensorWorker closed successfully")
        self.open_gl_widget.release()
        self.logger.info("WINDOW: ModernGL GPU resources released")
        super().closeEvent(a0)

    @classmethod
    def run(cls, logger: Logger, board: DataSource) -> None:
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        qt_app = QApplication([])
        window = cls(logger, board)
        window.show()
        qt_app.exit(qt_app.exec())
