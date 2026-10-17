"""Side-by-side presentation of two original decorative concepts."""
from cadgen import build123d as bd
from cadgen import glb, step

from dart_display import dart_display
from delta_display import delta_display


@step(out="../STEP/display_pair.step")
@glb(out="../GLB/display_pair.glb")
def display_pair():
    delta = delta_display().moved(bd.Location((0.0, 48.0, 0.0)))
    dart = dart_display().moved(bd.Location((0.0, -48.0, 0.0)))
    delta.label = "delta_display"
    dart.label = "dart_display"
    return bd.Compound(children=[delta, dart], label="invented_display_concepts")


if __name__ == "__main__":
    # The existing Windows cadgen 0.7.19 installation timed out starting
    # concurrent child workers. Populate the child cache sequentially first.
    delta_display()
    dart_display()
    display_pair()
    from pathlib import Path
    from lib.mesh_finish import finish_print_meshes

    finish_print_meshes(Path(__file__).resolve().parents[1])
