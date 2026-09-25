import librosa
import matplotlib.cm as cm
import moderngl
import numpy as np

from emg_gui.config.constants import SPECTROGRAM_WINDOW, TIME_WINDOW_SAMPLES
from emg_gui.core.logger import Logger
from emg_gui.processing.window_functions import get_hann_window, orthographic
from emg_gui.visualizer.shaders.shader_loader import (spec_fragment_shader,
                                                      spec_vertex_shader)


class SpectrogramRenderer:

    _COLOR_MAP = cm.get_cmap(name="inferno")
    _HANN_WINDOW = get_hann_window(window_size=SPECTROGRAM_WINDOW, skew=True)
    _HANN_WINDOW.setflags(write=False)

    def __init__(
        self,
        logger: Logger,
        number_of_emg_channels: int,
        moderngl_context: moderngl.Context,
    ) -> None:
        self._logger = logger

        self._number_of_emg_channels = number_of_emg_channels

        self._frames = np.zeros(
            (
                self._number_of_emg_channels,
                SPECTROGRAM_WINDOW // 2 + 1,
                TIME_WINDOW_SAMPLES,
                3,
            ),
            dtype="u1",
        )

        self._prog = moderngl_context.program(
            vertex_shader=spec_vertex_shader, fragment_shader=spec_fragment_shader
        )

        values_per_vertex = 5
        vertices_per_channel = 6
        bytes_per_float = np.dtype("f4").itemsize

        self._buffer = moderngl_context.buffer(
            reserve=(
                self._number_of_emg_channels
                * vertices_per_channel
                * values_per_vertex
                * bytes_per_float
            ),
            dynamic=True,
        )

        self._vao = moderngl_context.vertex_array(
            self._prog, [(self._buffer, "2f 2f 1f", "in_position", "in_uv", "in_layer")]
        )

        self._textures = moderngl_context.texture_array(
            size=(
                TIME_WINDOW_SAMPLES,
                SPECTROGRAM_WINDOW // 2 + 1,
                self._number_of_emg_channels,
            ),
            components=3,
            data=self._frames,
        )
        self._textures.repeat_x = False
        self._textures.repeat_y = True

        self._logger.info("SPEC: ModernGL GPU resources created")

    def reset(self) -> None:
        self._frames = np.zeros(
            (
                self._number_of_emg_channels,
                SPECTROGRAM_WINDOW // 2 + 1,
                TIME_WINDOW_SAMPLES,
                3,
            ),
            dtype="u1",
        )

    def add(self, window: np.ndarray) -> None:
        slices = SpectrogramRenderer._stft_slice(window)
        new_slice = SpectrogramRenderer._stft_color(slices)
        self._frames[:, :, :-1, :] = self._frames[:, :, 1:, :]
        self._frames[:, :, -1, :] = new_slice

    def size(self, w: int, h: int, w_offset: int, h_offset: int) -> None:
        P = orthographic(w, h)
        self._prog["P"].write(P)  # pyright: ignore[reportAttributeAccessIssue]
        vertices = self._build_vertices(w - w_offset, h - h_offset)
        self._buffer.write(vertices)

    def _build_vertices(self, widget_width: int, widget_height: int) -> np.ndarray:
        channel_height = widget_height / self._number_of_emg_channels

        spectrogram_top_offset = channel_height * 0.5
        spectrogram_height = channel_height * 0.5

        vertices = []

        for channel_index in range(self._number_of_emg_channels):
            y_top = channel_index * channel_height + spectrogram_top_offset
            y_bottom = y_top + spectrogram_height
            layer = float(channel_index)

            vertices.extend(
                [
                    0,
                    y_top,
                    0,
                    1,
                    layer,
                    0,
                    y_bottom,
                    0,
                    0,
                    layer,
                    widget_width,
                    y_bottom,
                    1,
                    0,
                    layer,
                    0,
                    y_top,
                    0,
                    1,
                    layer,
                    widget_width,
                    y_bottom,
                    1,
                    0,
                    layer,
                    widget_width,
                    y_top,
                    1,
                    1,
                    layer,
                ]
            )

        return np.array(vertices, dtype="f4")

    def draw(self) -> None:
        self._textures.write(self._frames)
        self._textures.use(0)
        for i in range(self._number_of_emg_channels):
            self._vao.render(mode=moderngl.TRIANGLES, vertices=6, first=i * 6)

    def release(self) -> None:
        self._prog.release()
        self._buffer.release()
        self._textures.release()
        self._vao.release()
        self._logger.info("SPEC: ModernGL GPU resources released")

    @staticmethod
    def _stft_slice(window) -> np.ndarray:
        return np.fft.rfft(window * SpectrogramRenderer._HANN_WINDOW, axis=1)

    @staticmethod
    def _stft_color(slices, min_db=-5, max_db=10):
        slices = librosa.amplitude_to_db(np.abs(slices))
        slices = slices.clip(min_db, max_db)
        slices = (slices - min_db) / (max_db - min_db)
        slices = SpectrogramRenderer._COLOR_MAP(slices)
        slices = (slices * 255).astype("u1")
        return slices[:, :, :3]
