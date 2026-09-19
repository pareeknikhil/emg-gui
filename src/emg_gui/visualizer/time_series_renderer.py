import moderngl
import numpy as np

from emg_gui.config.constants import TIME_WINDOW_SAMPLES
from emg_gui.core.logger import Logger
from emg_gui.core.types import EMGArray
from emg_gui.visualizer.shaders.shader_loader import (wave_fragment_shader,
                                                      wave_vertex_shader)


class TimeSeriesRenderer:
    def __init__(
        self,
        logger: Logger,
        number_of_emg_channels: int,
        moderngl_context: moderngl.Context,
    ) -> None:

        _components_per_vertex = 2
        _bytes_per_float = np.dtype("f4").itemsize
        _buffer_size = (
            number_of_emg_channels
            * TIME_WINDOW_SAMPLES
            * _components_per_vertex
            * _bytes_per_float
        )

        self._logger = logger

        self._x_points = np.linspace(start=-1, stop=1, num=TIME_WINDOW_SAMPLES, dtype="f4")

        self._prog = moderngl_context.program(
            vertex_shader=wave_vertex_shader, fragment_shader=wave_fragment_shader
        )
        self._buffer = moderngl_context.buffer(reserve=_buffer_size, dynamic=True)
        self._vao = moderngl_context.vertex_array(self._prog, self._buffer, "in_position")

        self._logger.info("TIMESERIES: ModernGL GPU resources created")

    def draw(self, raw_snapshot: EMGArray, filtered_snapshot: EMGArray) -> None:

        if raw_snapshot.shape != filtered_snapshot.shape:
            raise ValueError("Raw and filtered snapshots must have matching shapes")

        channels, _ = raw_snapshot.shape

        y_max = np.maximum(
            raw_snapshot.max(axis=1, keepdims=True),
            filtered_snapshot.max(axis=1, keepdims=True),
        )

        y_min = np.minimum(
            raw_snapshot.min(axis=1, keepdims=True),
            filtered_snapshot.min(axis=1, keepdims=True),
        )

        y_range = y_max - y_min
        flat_channel_mask = y_range < 0.0000001
        safe_range = np.where(flat_channel_mask, 1.0, y_range)

        x_vals = np.tile(A=self._x_points, reps=(channels, 1))

        self._render_snapshot(
            raw_snapshot,
            x_vals,
            y_min,
            safe_range,
            flat_channel_mask,
            color=(0.55, 0.55, 0.55, 1.0),
        )

        self._render_snapshot(
            filtered_snapshot,
            x_vals,
            y_min,
            safe_range,
            flat_channel_mask,
            color=(0.1, 1.0, 0.6, 1.0),
        )

    def _render_snapshot(
        self,
        snapshot: EMGArray,
        x_vals: np.ndarray,
        y_min: np.ndarray,
        safe_range: np.ndarray,
        flat_channel_mask: np.ndarray,
        color: tuple[float, float, float, float],
    ) -> None:

        channels, width = snapshot.shape

        y_norm = (snapshot - y_min) / safe_range
        y_norm = np.where(flat_channel_mask, 0.5, y_norm)
        positions = np.stack(arrays=[x_vals, y_norm], axis=-1).reshape(-1, 2)
        self._buffer.write(positions.astype("f4"))

        self._prog["u_color"] = color
        self._prog["u_channel_count"] = float(channels)

        for channel_index in range(channels):
            self._prog["u_channel_index"] = float(channel_index)
            self._vao.render(
                moderngl.LINE_STRIP, vertices=width, first=channel_index * width
            )

    def release(self) -> None:
        self._prog.release()
        self._buffer.release()
        self._vao.release()
        self._logger.info("TIMESERIES: ModernGL GPU resources released")
