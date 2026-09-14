from curses import raw

import moderngl
import numpy as np

from emg_gui.config.constants import GUI_WIDTH
from emg_gui.core.logger import Logger
from emg_gui.core.types import EMGArray
from emg_gui.visualizer.shaders.shader_loader import (wave_fragment_shader,
                                                      wave_vertex_shader)


class TimeSeriesRenderer:
    def __init__(self, logger: Logger, number_of_emg_channels: int, moderngl_context: moderngl.Context) -> None:

        _buffer_size = number_of_emg_channels * GUI_WIDTH * 2 * np.dtype("f4").itemsize

        self.logger = logger

        self.x_points = np.linspace(start=-1, stop=1, num=GUI_WIDTH)

        self.prog = moderngl_context.program(
            vertex_shader=wave_vertex_shader, fragment_shader=wave_fragment_shader
        )
        self.buffer = moderngl_context.buffer(reserve=_buffer_size, dynamic=True)
        self.vao = moderngl_context.vertex_array(self.prog, self.buffer, "in_position")

        self.logger.info("TIMESERIES: ModernGL GPU resources created")

    def draw(self, raw_snapshot: EMGArray, filtered_snapshot: EMGArray) -> None:

        if raw_snapshot.shape != filtered_snapshot.shape:
            raise ValueError("Raw and filtered snapshots must have matching shapes")

        channels, _ = raw_snapshot.shape

        y_max = np.maximum(raw_snapshot.max(axis=1, keepdims=True),
                           filtered_snapshot.max(axis=1, keepdims=True)
        )

        y_min = np.minimum(raw_snapshot.min(axis=1, keepdims=True),
                           filtered_snapshot.min(axis=1, keepdims=True)
        )

        y_range = y_max - y_min
        flat_channels = y_range < 0.0000001
        safe_range = np.where(flat_channels, 1.0, y_range)

        x_vals = np.tile(A=self.x_points, reps=(channels, 1))

        self._render_snapshot(raw_snapshot, x_vals, y_max, safe_range, 
                              flat_channels, color=(0.55, 0.55, 0.55, 1.0))

        self._render_snapshot(filtered_snapshot, x_vals, y_max, safe_range, 
                              flat_channels, color=(0.1, 1.0, 0.6, 1.0))

    def _render_snapshot(self, snapshot: EMGArray, x_vals: np.ndarray, y_max: np.ndarray, 
                         safe_range: np.ndarray, flat_channels: np.ndarray, color: tuple[float, float, float, float]) -> None:

        channels, width = snapshot.shape

        y_norm = (snapshot - y_max) * 0.05 / safe_range + 1.0
        y_norm = np.where(flat_channels, 1.0, y_norm)
        positions = np.stack(arrays=[x_vals, y_norm], axis=-1).reshape(-1, 2)
        self.buffer.write(positions.astype("f4"))

        self.prog["u_color"] = color

        for channel_index in range(channels):
            self.prog["u_channel_index"] = float(channel_index)
            self.vao.render(moderngl.LINE_STRIP, vertices=width, first=channel_index * width)

    def release(self) -> None:
        self.prog.release()
        self.buffer.release()
        self.vao.release()
        self.logger.info("TIMESERIES: ModernGL GPU resources released")
