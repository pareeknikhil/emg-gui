import moderngl
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QSurfaceFormat
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QLabel,
    QMenu,
    QOpenGLWidget,
    QPushButton,
    QShortcut,
    QToolButton,
)
from typing_extensions import override

from emg_gui.configs.constants import (
    FRAME_RATE,
    GUI_HEIGHT,
    GUI_WIDTH,
    HOP_SIZE,
    SPECTROGRAM_WINDOW,
)
from emg_gui.core.enums import ActivityState, RecordingState
from emg_gui.utils.tfrecord_utils import get_all_labels
from emg_gui.visualizer.data_source import DataSource
from emg_gui.visualizer.spectrogram import Spectrogram
from emg_gui.visualizer.time_series import TimeSeries


class EMGSignalAnalyzer(QOpenGLWidget):
    def __init__(self, logger, data_source: DataSource) -> None:

        super().__init__()

        self.logger = logger
        self.data_source = data_source

        self.setWindowTitle("EMG Analyzer")
        self.setFixedSize(GUI_WIDTH, GUI_HEIGHT)

        _fmt = QSurfaceFormat()
        _fmt.setVersion(3, 3)
        _fmt.setProfile(QSurfaceFormat.CoreProfile)
        _fmt.setDefaultFormat(_fmt)
        _fmt.setSamples(4)
        self.setFormat(_fmt)

        QShortcut(Qt.Key_Escape, self, self.close)

        self.__timer = QTimer()
        self.__timer.timeout.connect(self.update)
        self.__timer.start(int(1000 / FRAME_RATE))

        self.add_buttons()

        self.logger.info("WINDOW: Initialized EMG Signal Analyzer...")

    def add_buttons(self) -> None:
        self.start_button = QPushButton("Start Recording", self)
        self.start_button.clicked.connect(self.on_click)
        self.start_button.setStyleSheet(self.get_stylesheet(color="green"))
        self.start_button.move(0, 30)

        self.activity_button = QPushButton("Start Activity", self)
        self.activity_button.clicked.connect(self.on_activity)
        self.activity_button.setStyleSheet(self.get_stylesheet(color="green"))
        self.activity_button.move(0, 60)

        self.label = QLabel("Ready", self)
        self.label.move(120, 30)
        self.label.setStyleSheet("font-size: 20px;")
        self.label.setStyleSheet("color: red;")

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_countdown)

        self.reset_button = QPushButton("Reset", self)
        self.reset_button.clicked.connect(self.on_reset)
        self.reset_button.move(0, 95)
        self.reset_button.setStyleSheet(self.get_stylesheet(color="purple"))

        self.type_dropdown = self.create_dropdown_button(
            label="Type",
            items=["train", "validate", "test"],
            color="blue",
            position=(0, 0),
            callback=self.on_type_selected,
        )

        self.dropdown = self.create_dropdown_button(
            label="Activity",
            items=get_all_labels(),
            color="brown",
            position=(80, 0),
            callback=self.on_activity_selected,
        )

    def create_dropdown_button(
        self, label, items, color, position, callback
    ) -> QToolButton:
        button = QToolButton(self)
        button.setText(label)
        button.setPopupMode(QToolButton.MenuButtonPopup)
        button.setStyleSheet(self.get_stylesheet(color=color))
        button.move(*position)

        menu = QMenu(self)
        for item in items:
            action = QAction(item, self)
            action.triggered.connect(lambda checked=False, i=item: callback(i))
            menu.addAction(action)

        button.setMenu(menu)
        return button

    def on_activity_selected(self, name) -> None:
        self.dropdown.setText(name)
        self.location = name  # or use self.sender().text()

    def on_type_selected(self, type_name) -> None:
        self.type_dropdown.setText(type_name)
        self.selected_type = type_name

    def on_click(self) -> None:
        self.remaining_time = 0

        if self.data_source.recording_state is RecordingState.IDLE:
            self.data_source.start_recording()
            self.timer.start()

            self.start_button.setText("Stop Recording")
            self.start_button.setStyleSheet(self.get_stylesheet(color="red"))
            return

        self.data_source.stop_recording()
        self.timer.stop()

        self.label.setText(f"{self.remaining_time}")
        self.start_button.setText("Start Recording")
        self.start_button.setStyleSheet(self.get_stylesheet(color="green"))
        self.data_source.write_to_disk(
            self.selected_type,
            self.location,
        )

    def on_activity(self) -> None:

        if self.data_source.activity_state is ActivityState.INACTIVE:
            self.data_source.insert_start_marker()
            self.activity_button.setText("Stop Activity")
            self.activity_button.setStyleSheet(self.get_stylesheet(color="red"))
            return

        self.data_source.insert_stop_marker()
        self.activity_button.setText("Start Activity")
        self.activity_button.setStyleSheet(self.get_stylesheet(color="green"))

    def update_countdown(self) -> None:
        self.remaining_time += 1
        self.label.setText(f"{self.remaining_time}")

    def on_reset(self) -> None:
        self.time_series.reset()
        self.spec_series.reset()
        self.logger.info("WINDOW: Analyzer reset completed")

    @override
    def closeEvent(self, event) -> None:
        self.close_gui()
        super().closeEvent(event)

    @override
    def initializeGL(self) -> None:
        self.ctx = moderngl.create_context(require=330)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.multisample = True

        emg_channel_count = self.data_source.get_count_emg_channels()

        self.time_series = TimeSeries(self.ctx, self.logger, emg_channel_count)

        self.spec_series = Spectrogram(self.ctx, 40, 80, self.logger, emg_channel_count)

        self.data_source.start_stream()

    @override
    def resizeGL(self, w, h) -> None:
        self.spec_series.size(w, h)
        self.logger.info(f"WINDOW: Size - {w} , {h}")

    @override
    def paintGL(self):

        emg_data = self.data_source.get_data(num_of_samples_expctd=HOP_SIZE)

        self.time_series.add(new_wave_data=emg_data)
        self.time_series.draw()

        filtrd_emg = self.time_series.get_filtrd_emg(
            n_latest_samples=SPECTROGRAM_WINDOW
        )

        self.spec_series.add(filtrd_emg)
        self.spec_series.draw()

    def close_gui(self) -> None:
        self.logger.info("WINDOW: Closing GUI resources...")
        self.data_source.stop_stream()
        self.time_series.release()
        self.spec_series.release()
        self.ctx.release()
        self.logger.info("WINDOW: Closed GUI successfully")
        self.logger.release()

    @staticmethod
    def get_stylesheet(color) -> str:
        return f"""
            QPushButton {{
                background-color: {color};
                font-size:15px;
                font-family: Arial;
            }}
        """

    @classmethod
    def run(cls, logger, cyton: DataSource) -> None:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        window = QApplication([])
        main = cls(logger, cyton)
        main.show()
        window.exit(window.exec())
