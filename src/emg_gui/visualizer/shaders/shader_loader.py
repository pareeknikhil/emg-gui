from importlib import resources


def _load_shader_file(*paths: str) -> str:
    return (
        resources.files("emg_gui.visualizer.shaders")
        .joinpath(*paths)
        .read_text(encoding="utf-8")
    )


time_series_vertex_shader = _load_shader_file("time_series", "vertex.glsl")

time_series_fragment_shader = _load_shader_file("time_series", "fragment.glsl")

spec_vertex_shader = _load_shader_file("spec", "vertex.glsl")

spec_fragment_shader = _load_shader_file("spec", "fragment.glsl")

ticks_vertex_shader = _load_shader_file("ticks", "vertex.glsl")

ticks_fragment_shader = _load_shader_file("ticks", "fragment.glsl")

text_vertex_shader = _load_shader_file("text", "vertex.glsl")

text_fragment_shader = _load_shader_file("text", "fragment.glsl")
