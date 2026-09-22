from typing import Optional

import moderngl
import numpy as np

from emg_gui.core.logger import Logger
from emg_gui.processing.window_functions import orthographic
from emg_gui.visualizer.shaders.shader_loader import (ticks_fragment_shader,
                                                      ticks_vertex_shader)


class TicksRenderer:
    def __init__(self, logger: Logger, tick_height: int, tick_gap: int, moderngl_context: moderngl.Context) -> None:
        self._logger = logger
        self._tick_height = tick_height
        self._tick_gap = tick_gap
        self._moderngl_context  = moderngl_context

        self._prog = moderngl_context.program(
        vertex_shader = ticks_vertex_shader, fragment_shader=ticks_fragment_shader
        )
        self._buffer: Optional[moderngl.Buffer] = None
        self._vao: Optional[moderngl.VertexArray] = None

        self._prog['color'] = (0.4,0.4,0.5,1)

    def size(self, w: int, h: int) -> None:
        P = orthographic(w, h)
        self._prog["P"].write(P)  # pyright: ignore[reportAttributeAccessIssue]

        vertices = self._build_vertices(w, h)

        self._buffer = self._moderngl_context.buffer(vertices)
        self._vao = self._moderngl_context.vertex_array(self._prog, self._buffer, "vertex")

    def _build_vertices(self, widget_width: int, widget_height: int) -> np.ndarray:
        n = int(widget_width) // int(self._tick_gap) + 1
        vertices = np.zeros(n * 4, dtype="f4")

        for i in range(0, n):
            vertices[i*4:(i+1)*4] = [
					i * self._tick_gap, widget_height - self._tick_height,
					i * self._tick_gap, widget_height
				]

        return vertices

    def draw(self) -> None:
        if self._vao is None:
            return
        self._vao.render(moderngl.LINES)