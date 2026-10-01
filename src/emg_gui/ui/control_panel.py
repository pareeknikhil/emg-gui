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
        self._control_layout = QVBoxLayout()

        self._folders = QComboBox()

        self._datasplit = QComboBox()

        self._add_widgets()

    def _add_widgets(self):
        self._datasplit.addItems(data_split.value for data_split in DatasetSplit)
        self._datasplit.setCurrentIndex(-1)
        self._datasplit.currentTextChanged.connect(self._update_dir_list_dropdown)

        self._stream_button = QPushButton("Stream Data")
        self._stream_button.clicked.connect(lambda: self.stream_request.emit())

        self._record_button = QPushButton("Record")
        self._record_button.clicked.connect(
            lambda: self.record_request.emit(
                self.selected_datasplit, self.selected_folder
            )
        )

        self._marker_button = QPushButton("Start Movement")
        self._marker_button.clicked.connect(lambda: self.marker_request.emit())

        self._reset_button = QPushButton("Reset")
        self._reset_button.clicked.connect(lambda: self.reset_request.emit())

        self._control_layout.addWidget(self._datasplit)
        self._control_layout.addWidget(self._folders)
        self._control_layout.addWidget(self._stream_button)
        self._control_layout.addWidget(self._record_button)
        self._control_layout.addWidget(self._marker_button)
        self._control_layout.addWidget(self._reset_button)

        self.setLayout(self._control_layout)

    @property
    def selected_datasplit(self) -> str:
        return self._datasplit.currentText()

    @property
    def selected_folder(self) -> str:
        return self._folders.currentText()

    @pyqtSlot(str)
    def set_stream_button_text(self, text: str) -> None:
        self._stream_button.setText(text)

    @pyqtSlot(str)
    def set_record_button_text(self, text: str) -> None:
        self._record_button.setText(text)

    @pyqtSlot(str)
    def set_marker_button_text(self, text: str) -> None:
        self._marker_button.setText(text)

    @pyqtSlot(str)
    def set_reset_button_text(self, text: str) -> None:
        self._reset_button.setText(text)

    def _update_dir_list_dropdown(self, selected_datasplit) -> None:
        self._folders.blockSignals(True)
        self._folders.clear()
        self._folders.addItems(get_all_labels(selected_datasplit))
        self._folders.setCurrentIndex(-1)
        self._folders.blockSignals(False)
