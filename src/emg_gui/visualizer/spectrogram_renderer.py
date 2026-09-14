import librosa
import matplotlib.cm as cm
import moderngl
import numpy as np
from pyrr import Matrix44

from emg_gui.config.constants import GUI_WIDTH, SPECTROGRAM_WINDOW
from emg_gui.core.logger import Logger
from emg_gui.processing.window_functions import get_hann_window
from emg_gui.visualizer.shaders.shader_loader import (
    spec_fragment_shader,
    spec_vertex_shader,
)


class SpectrogramRenderer:

    COLOR_MAP = cm.get_cmap(name="inferno")
    HANN_WINDOW = get_hann_window(window_size=SPECTROGRAM_WINDOW, skew=True)
    HANN_WINDOW.setflags(write=False)

    def __init__(
        self,
        logger: Logger,
        y: int,
        h: int,
        number_of_emg_channels: int,
        moderngl_context: moderngl.Context,
    ) -> None:
        self.logger = logger

        self._number_of_emg_channels = number_of_emg_channels

        self.frames = np.zeros(
            (self._number_of_emg_channels, SPECTROGRAM_WINDOW // 2 + 1, GUI_WIDTH, 3),
            dtype="u1",
        )

        self.prog = moderngl_context.program(
            vertex_shader=spec_vertex_shader, fragment_shader=spec_fragment_shader
        )

        vertices = []
        for i in range(self._number_of_emg_channels):
            y_offset = y + i * 125
            layer = float(i)
            vertices.extend(
                [
                    0,
                    y_offset,
                    0,
                    1,
                    layer,  # A
                    0,
                    y_offset + h,
                    0,
                    0,
                    layer,  # B
                    GUI_WIDTH,
                    y_offset + h,
                    1,
                    0,
                    layer,  # C
                    0,
                    y_offset,
                    0,
                    1,
                    layer,  # A
                    GUI_WIDTH,
                    y_offset + h,
                    1,
                    0,
                    layer,  # C
                    GUI_WIDTH,
                    y_offset,
                    1,
                    1,
                    layer,  # D,
                ]
            )

        vertices = np.array(vertices, dtype="f4")
        self.buffer = moderngl_context.buffer(vertices)
        self.vao = moderngl_context.vertex_array(
            self.prog, [(self.buffer, "2f 2f 1f", "in_position", "in_uv", "in_layer")]
        )

        self.textures = moderngl_context.texture_array(
            size=(GUI_WIDTH, SPECTROGRAM_WINDOW // 2 + 1, self._number_of_emg_channels),
            components=3,
            data=self.frames,
        )
        self.textures.repeat_x = False
        self.textures.repeat_y = True

        self.logger.info("SPEC: ModernGL GPU resources created")

    def reset(self) -> None:
        self.frames = np.zeros(
            (self._number_of_emg_channels, SPECTROGRAM_WINDOW // 2 + 1, GUI_WIDTH, 3),
            dtype="u1",
        )

    def add(self, window) -> None:
        slices = SpectrogramRenderer.stft_slice(window)
        new_slice = SpectrogramRenderer.stft_color(slices)
        self.frames[:, :, :-1, :] = self.frames[:, :, 1:, :]
        self.frames[:, :, -1, :] = new_slice

    def size(self, w, h) -> None:
        w = GUI_WIDTH
        P = SpectrogramRenderer.orthographic(w, h)
        self.prog["P"].write(P)  # pyright: ignore[reportAttributeAccessIssue]

    def draw(self) -> None:
        self.textures.write(self.frames)
        self.textures.use(0)
        for i in range(self._number_of_emg_channels):
            self.vao.render(mode=moderngl.TRIANGLES, vertices=6, first=i * 6)

    def release(self) -> None:
        self.prog.release()
        self.buffer.release()
        self.textures.release()
        self.vao.release()
        self.logger.info("SPEC: ModernGL GPU resources released")

    @staticmethod
    def stft_slice(window) -> np.ndarray:
        return np.fft.rfft(window * SpectrogramRenderer.HANN_WINDOW, axis=1)

    @staticmethod
    def stft_color(slices, min_db=-5, max_db=10):
        slices = librosa.amplitude_to_db(np.abs(slices))
        slices = slices.clip(min_db, max_db)
        slices = (slices - min_db) / (max_db - min_db)
        slices = SpectrogramRenderer.COLOR_MAP(slices)
        slices = (slices * 255).astype("u1")
        return slices[:, :, :3]

    @staticmethod
    def orthographic(w, h) -> Matrix44:
        P = Matrix44.orthogonal_projection(0, w, h, 0, -1, 1, dtype="f4")
        return P
