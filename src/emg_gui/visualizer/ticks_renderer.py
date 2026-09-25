from typing import Optional

import moderngl
import numpy as np

from emg_gui.core.logger import Logger
from emg_gui.processing.window_functions import orthographic
from emg_gui.visualizer.shaders.shader_loader import (ticks_fragment_shader,
                                                      ticks_vertex_shader)


class TicksRenderer:
    def __init__(
        self,
        logger: Logger,
        tick_intervals_per_window: float,
        tick_height: int,
        moderngl_context: moderngl.Context,
    ) -> None:
        self._logger = logger
        self._tick_intervals_per_window = tick_intervals_per_window
        self._tick_height = tick_height
        self._moderngl_context = moderngl_context

        self._prog = moderngl_context.program(
            vertex_shader=ticks_vertex_shader, fragment_shader=ticks_fragment_shader
        )
        self._buffer: Optional[moderngl.Buffer] = None
        self._vao: Optional[moderngl.VertexArray] = None

        self._prog["color"] = (0.4, 0.4, 0.5, 1)

        self._logger.info("TICKS: ModernGL GPU resources created")


    def size(self, w: int, h: int, w_offset: int, h_offset:int) -> None:
        P = orthographic(w, h)
        self._prog["P"].write(P)  # pyright: ignore[reportAttributeAccessIssue]

        vertices = self._build_vertices(w, h, w_offset, h_offset)

        self._buffer = self._moderngl_context.buffer(vertices)
        self._vao = self._moderngl_context.vertex_array(
            self._prog, self._buffer, "vertex"
        )

    def _build_vertices(self, widget_width: int, widget_height: int, w_offset: int, h_offset:int) -> np.ndarray:
        plot_width = widget_width - w_offset
        tick_gap = plot_width / self._tick_intervals_per_window
        n = int(plot_width // tick_gap) + 1

        vertices = np.zeros(n * 4, dtype="f4")

        for i in range(n):
            vertices[i * 4 : (i + 1) * 4] = [
                widget_width - i * tick_gap,
                widget_height - h_offset,
                widget_width - i * tick_gap,
                widget_height - h_offset + self._tick_height,
            ]

        return vertices

    def draw(self) -> None:
        if self._vao is None:
            return
        self._vao.render(moderngl.LINES)

    def release(self) -> None:
        assert self._buffer and self._vao
        self._prog.release()
        self._buffer.release()
        self._vao.release()
        self._logger.info("TICKS: ModernGL GPU resources released")

