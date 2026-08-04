from importlib import resources


def load_shadr_file(*paths: str) -> str:
    return (
        resources.files("emg_gui.shaders").joinpath(*paths).read_text(encoding="utf-8")
    )


wave_vertex_shader = load_shadr_file("wave", "vertex.glsl")

wave_fragment_shader = load_shadr_file("wave", "fragment.glsl")

spec_vertex_shader = load_shadr_file("spec", "vertex.glsl")

spec_fragment_shader = load_shadr_file("spec", "fragment.glsl")
