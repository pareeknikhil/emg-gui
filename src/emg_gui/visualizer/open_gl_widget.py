import moderngl
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QSurfaceFormat
from PyQt5.QtWidgets import QOpenGLWidget
from typing_extensions import override

from emg_gui.config.constants import EDGE_ARTIFACT_BUFFER, SPECTROGRAM_WINDOW
from emg_gui.core.logger import Logger
from emg_gui.core.types import EMGArray
from emg_gui.processing.filter import filter_data
from emg_gui.visualizer.spectrogram_renderer import SpectrogramRenderer
from emg_gui.visualizer.time_series_renderer import TimeSeriesRenderer


class EMGOpenGLWidget(QOpenGLWidget):

    frame_rendered = pyqtSignal()

    def __init__(self, logger: Logger, number_of_emg_channels: int) -> None:
        super().__init__()

        surface_format = QSurfaceFormat()
        surface_format.setVersion(3, 3)
        surface_format.setProfile(QSurfaceFormat.CoreProfile)
        surface_format.setSamples(4)
        self.setFormat(surface_format)

        self.logger = logger
        self._number_of_emg_channels = number_of_emg_channels

        self._reference_to_raw_snapshot = None
        self._reference_to_filtered_snapshot = None

        self._last_snapshot_received = None

    @override
    def initializeGL(self) -> None:
        self.modern_gl_context = moderngl.create_context(require=330)
        self.modern_gl_context.enable(moderngl.BLEND)
        self.time_series = TimeSeriesRenderer(self.logger, self._number_of_emg_channels, self.modern_gl_context)
        self.spectrogram = SpectrogramRenderer(self.logger, 40, 80, self._number_of_emg_channels, self.modern_gl_context)#create spectrogram instance
        self.logger.info("OpenGL: Created opengl resources")

    @override
    def paintGL(self) -> None:
        if self._reference_to_raw_snapshot is None or self._reference_to_filtered_snapshot is None:
            return

        self.time_series.draw(self._reference_to_raw_snapshot, self._reference_to_filtered_snapshot)
        self.spectrogram.add(self._reference_to_filtered_snapshot[:, -SPECTROGRAM_WINDOW:])
        self.spectrogram.draw()
        self._reference_to_raw_snapshot, self._reference_to_filtered_snapshot = None, None 
        self.frame_rendered.emit()

    @override
    def resizeGL(self, w, h) -> None:
        self.spectrogram.size(w, h)
        self.logger.info(f"WINDOW: Size - {w} , {h}")

    def submit_snapshot(self, raw_snapshot: EMGArray, freeze_duplicate_snapshots: bool) -> None:
        if self._last_snapshot_received is raw_snapshot and freeze_duplicate_snapshots:
            self.frame_rendered.emit()
            return
        filter_snapshot = raw_snapshot.copy()
        for count in range(self._number_of_emg_channels):
            filter_data(time_series=filter_snapshot[count, :])
        self._reference_to_raw_snapshot = raw_snapshot[:, EDGE_ARTIFACT_BUFFER:]
        self._reference_to_filtered_snapshot = filter_snapshot[:, EDGE_ARTIFACT_BUFFER:]
        self._last_snapshot_received = raw_snapshot
        self.update()

    def release(self) -> None:
        self.makeCurrent()
        self.time_series.release()
        self.spectrogram.release()
        self.modern_gl_context.release()
        self.logger.info("OpenGL: Released openGL context")
        self.doneCurrent()
