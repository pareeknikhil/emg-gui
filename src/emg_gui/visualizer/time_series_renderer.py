import moderngl
import numpy as np

from emg_gui.config.constants import TIME_WINDOW_SAMPLES
from emg_gui.core.logger import Logger
from emg_gui.core.types import EMGArray
from emg_gui.processing.window_functions import orthographic
from emg_gui.visualizer.shaders.shader_loader import (
    time_series_fragment_shader,
    time_series_vertex_shader,
)


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

        self._prog = moderngl_context.program(
            vertex_shader=time_series_vertex_shader,
            fragment_shader=time_series_fragment_shader,
        )
        self._buffer = moderngl_context.buffer(reserve=_buffer_size, dynamic=True)
        self._vao = moderngl_context.vertex_array(
            self._prog, self._buffer, "in_position"
        )

        self._logger.info("TIMESERIES: ModernGL GPU resources created")

    def size(self, w: int, h: int, w_offset: int, h_offset: int) -> None:
        self._plot_width = w - w_offset
        self._plot_height = h - h_offset
        self._x_points = np.linspace(
            start=w_offset, stop=w, num=TIME_WINDOW_SAMPLES, dtype="f4"
        )
        P = orthographic(w, h)
        self._prog["P"].write(P)  # pyright: ignore[reportAttributeAccessIssue]

    def draw(self, raw_snapshot: EMGArray, filtered_snapshot: EMGArray) -> None:

        if raw_snapshot.shape != filtered_snapshot.shape:
            raise ValueError("Raw and filtered snapshots must have matching shapes")

        channels, _ = raw_snapshot.shape

        valid_raw_samples = np.any(raw_snapshot != 0.0, axis=0)

        if np.any(valid_raw_samples):
            raw_mean = raw_snapshot[:, valid_raw_samples].mean(axis=1, keepdims=True)
            raw_snapshot = raw_snapshot - raw_mean
            raw_snapshot[:, ~valid_raw_samples] = 0.0

        filtered_snapshot = filtered_snapshot - filtered_snapshot.mean(
            axis=1, keepdims=True
        )

        upper_bound = np.maximum(
            raw_snapshot.max(axis=1, keepdims=True),
            filtered_snapshot.max(axis=1, keepdims=True),
        )

        lower_bound = np.minimum(
            raw_snapshot.min(axis=1, keepdims=True),
            filtered_snapshot.min(axis=1, keepdims=True),
        )

        half_range = np.maximum(np.abs(upper_bound), np.abs(lower_bound))
        flat_channel_mask = half_range < 0.0000001
        y_min = -half_range
        safe_range = np.where(flat_channel_mask, 1.0, 2.0 * half_range)

        self._render_snapshot(
            raw_snapshot,
            y_min,
            safe_range,
            flat_channel_mask,
            color=(0.55, 0.55, 0.55, 1.0),
        )

        self._render_snapshot(
            filtered_snapshot,
            y_min,
            safe_range,
            flat_channel_mask,
            color=(0.1, 1.0, 0.6, 1.0),
        )

    def _render_snapshot(
        self,
        snapshot: EMGArray,
        y_min: np.ndarray,
        safe_range: np.ndarray,
        flat_channel_mask: np.ndarray,
        color: tuple[float, float, float, float],
    ) -> None:

        channels, width = snapshot.shape

        y_norm = (snapshot - y_min) / safe_range
        y_norm = np.where(flat_channel_mask, 0.5, y_norm)

        channel_height = self._plot_height / channels
        time_series_height = channel_height * 0.5

        x_vals = np.tile(self._x_points, reps=(channels, 1))
        y_vals = np.empty_like(y_norm, dtype="f4")

        for channel_index in range(channels):
            channel_top = channel_index * channel_height
            time_series_bottom = channel_top + time_series_height
            y_vals[channel_index] = (
                time_series_bottom - y_norm[channel_index] * time_series_height
            )

        positions = np.stack(arrays=[x_vals, y_vals], axis=-1).reshape(-1, 2)

        self._buffer.write(positions.astype("f4"))

        self._prog["u_color"] = color

        for channel_index in range(channels):
            self._vao.render(
                moderngl.LINE_STRIP, vertices=width, first=channel_index * width
            )

    def release(self) -> None:
        self._prog.release()
        self._buffer.release()
        self._vao.release()
        self._logger.info("TIMESERIES: ModernGL GPU resources released")
