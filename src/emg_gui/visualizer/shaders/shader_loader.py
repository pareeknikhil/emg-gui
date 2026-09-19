from importlib import resources


def _load_shader_file(*paths: str) -> str:
    return (
        resources.files("emg_gui.visualizer.shaders")
        .joinpath(*paths)
        .read_text(encoding="utf-8")
    )


wave_vertex_shader = _load_shader_file("wave", "vertex.glsl")

wave_fragment_shader = _load_shader_file("wave", "fragment.glsl")

spec_vertex_shader = _load_shader_file("spec", "vertex.glsl")

spec_fragment_shader = _load_shader_file("spec", "fragment.glsl")
