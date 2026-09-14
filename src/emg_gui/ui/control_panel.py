from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QComboBox, QGroupBox, QPushButton, QVBoxLayout

from emg_gui.acquisition.dataset_files import get_all_labels
from emg_gui.core.enums import DatasetSplit


class EMGControlPanel(QGroupBox):

    stream_request = pyqtSignal()
    record_request = pyqtSignal(str, str)
    marker_request = pyqtSignal()
    reset_request = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.control_layout = QVBoxLayout()

        self.folders = QComboBox()

        self.datasplit = QComboBox()

        self.add_widgets()

    def add_widgets(self):
        self.datasplit.addItems(data_split.value for data_split in DatasetSplit)
        self.datasplit.setCurrentIndex(-1)
        self.datasplit.currentTextChanged.connect(self.update_dir_list_dropdown)

        self.stream_button = QPushButton("Stream Data")
        self.stream_button.clicked.connect(lambda: self.stream_request.emit())

        self.record_button = QPushButton("Record")
        self.record_button.clicked.connect(lambda: self.record_request.emit(self.selected_datasplit, self.selected_folder))

        self.marker_button = QPushButton("Start Movement")
        self.marker_button.clicked.connect(lambda: self.marker_request.emit())

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(lambda: self.reset_request.emit())

        self.control_layout.addWidget(self.datasplit)
        self.control_layout.addWidget(self.folders)
        self.control_layout.addWidget(self.stream_button)
        self.control_layout.addWidget(self.record_button)
        self.control_layout.addWidget(self.marker_button)
        self.control_layout.addWidget(self.reset_button)

        self.setLayout(self.control_layout)

    @property
    def selected_datasplit(self) -> str:
        return self.datasplit.currentText()

    @property
    def selected_folder(self) -> str:
        return self.folders.currentText()

    @pyqtSlot(str)
    def set_stream_button_text(self, text: str) -> None:
        self.stream_button.setText(text)

    @pyqtSlot(str)
    def set_record_button_text(self, text: str) -> None:
        self.record_button.setText(text)

    @pyqtSlot(str)
    def set_marker_button_text(self, text: str) -> None:
        self.marker_button.setText(text)

    @pyqtSlot(str)
    def set_reset_button_text(self, text: str) -> None:
        self.reset_button.setText(text)

    def update_dir_list_dropdown(self, selected_datasplit) -> None:
        self.folders.blockSignals(True)
        self.folders.clear()
        self.folders.addItems(get_all_labels(selected_datasplit))
        self.folders.setCurrentIndex(-1)
        self.folders.blockSignals(False)
