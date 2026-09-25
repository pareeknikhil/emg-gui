from pathlib import Path
from typing import Any

import freetype
import moderngl
import numpy as np

from emg_gui.config.constants import TEXT_FONT_SIZE, TEXT_SCALE
from emg_gui.core.logger import Logger
from emg_gui.processing.window_functions import orthographic
from emg_gui.visualizer.shaders.shader_loader import (
    text_fragment_shader,
    text_vertex_shader,
)


class CharacterSlot:

    def __init__(self, ctx, glyph):
        if not isinstance(glyph, freetype.GlyphSlot):
            raise RuntimeError("TEXT: Unknown glyph type")

        self.width = glyph.bitmap.width
        self.height = glyph.bitmap.rows
        self.advance = glyph.advance.x

        size = (self.width, self.height)

        data = np.array(glyph.bitmap.buffer, dtype="u1")
        self.texture = ctx.texture(size, 1, data)
        self.texture.repeat_x = False
        self.texture.repeat_y = False


class TextRenderer:

    def __init__(
        self,
        logger: Logger,
        window_duration_sec: float,
        moderngl_context: moderngl.Context,
    ) -> None:
        self._logger = logger
        self._window_duration_sec = window_duration_sec

        self._prog = moderngl_context.program(
            vertex_shader=text_vertex_shader, fragment_shader=text_fragment_shader
        )

        self._buffer = moderngl_context.buffer(reserve=6 * 4 * 4, dynamic=True)

        self._vao = moderngl_context.vertex_array(
            self._prog, self._buffer, "vertex", "uv"
        )

        self._prog["color"] = (0.5, 0.5, 0.55, 1)

        _font_path = Path("src/emg_gui/config/Roboto-Black.ttf")
        self.init_font(_font_path.as_posix(), moderngl_context)

        self.texts: list[tuple[str, float, float, str]] = []

        self._logger.info("TEXT: ModernGL GPU resources created")

    def init_font(self, font: str, moderngl_context: moderngl.Context) -> None:
        self.characters = dict()
        size = int(TEXT_FONT_SIZE * TEXT_SCALE)
        face = freetype.Face(font)
        face.set_pixel_sizes(size, size)

        for char in "0123456789s":
            face.load_char(char)
            character = CharacterSlot(moderngl_context, face.glyph)
            self.characters[char] = character

    def set_geometry(self, x, y, w, h) -> None:
        vertices = np.array(
            [
                x,
                y,
                0,
                1,
                x + w,
                y,
                1,
                1,
                x + w,
                y - h,
                1,
                0,
                x,
                y,
                0,
                1,
                x + w,
                y - h,
                1,
                0,
                x,
                y - h,
                0,
                0,
            ]
        )
        vertices = vertices.astype("f4")
        self._buffer.write(vertices)

    def text_width(self, text) -> Any:
        w = 0
        for c in text:
            character = self.characters[c]
            w += (character.advance >> 6) / TEXT_SCALE
        return w

    def add(self, text, x, y, align="left") -> None:
        self.texts.append((text, x, y, align))

    def size(self, w, h, w_offset, h_offset) -> None:
        P = orthographic(w, h)
        self._prog["P"].write(P)  # pyright: ignore[reportAttributeAccessIssue]

        tick_gap = (w - w_offset) / self._window_duration_sec
        y = h - h_offset

        self.texts.clear()

        for i in range(1, int(self._window_duration_sec) + 1):
            label = f"{i}s"
            half_width = self.text_width(label) / 2
            x = w - i * tick_gap
            x = max(w_offset + half_width, min(x, w - half_width))
            self.add(label, x, y, align="center")

    def draw(self) -> None:
        for text, x, y, align in self.texts:
            if align == "center":
                w = self.text_width(text)
                x -= w / 2
            if align == "right":
                w = self.text_width(text)
                x -= w
            for i, c in enumerate(text):
                character = self.characters[c]
                character.texture.use(0)
                w = character.width
                h = character.height
                self.set_geometry(x, y, w / TEXT_SCALE, h / TEXT_SCALE)
                self._vao.render()
                x = x + (character.advance >> 6) / TEXT_SCALE

    def release(self) -> None:
        for character in self.characters.values():
            character.texture.release()
        self._prog.release()
        self._buffer.release()
        self._vao.release()
        self._logger.info("TEXT: ModernGL GPU resources released")
