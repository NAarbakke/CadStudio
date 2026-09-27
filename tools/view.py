"""Interactive PyVista viewer for STEP, GLB and STL files.

    .venv\\Scripts\\python tools\\view.py models\\STEP\\tsirkon.step
    .venv\\Scripts\\python tools\\view.py models\\GLB\\tsirkon.glb shot.png   # render to a file instead

STEP is read through build123d (OCP) and tessellated finely, keeping part colours, so it looks
best; GLB/STL are drawn from their exported triangles.
"""
import pathlib
import sys

import pyvista as pv


def step_parts(path):
    import build123d as bd
    shape = bd.import_step(str(path))
    parts = [c for c in shape.children if isinstance(c, bd.Solid)] or [shape]
    bb = shape.bounding_box()
    tol = bb.diagonal * 2e-4  # ponytail: fixed relative chord tolerance, expose a flag if big models get slow
    for p in parts:
        verts, tris = p.tessellate(tol, angular_tolerance=0.1)
        faces = [v for t in tris for v in (3, *t)]
        mesh = pv.PolyData([tuple(v) for v in verts], faces)
        color = tuple(p.color)[:3] if p.color else (0.75, 0.75, 0.78)
        yield mesh, color


def main():
    path = pathlib.Path(sys.argv[1])
    out = sys.argv[2] if len(sys.argv) > 2 else None
    p = pv.Plotter(off_screen=bool(out), window_size=(1600, 1000))
    look = dict(smooth_shading=True, split_sharp_edges=True, specular=0.4, specular_power=20, diffuse=0.85, ambient=0.15)

    if path.suffix.lower() in (".step", ".stp"):
        for mesh, color in step_parts(path):
            p.add_mesh(mesh, color=color, **look)
            edges = mesh.extract_feature_edges(35, boundary_edges=False, manifold_edges=False)
            if edges.n_points:
                p.add_mesh(edges, color="black", opacity=0.35, line_width=1)
    elif path.suffix.lower() in (".glb", ".gltf"):
        p.import_gltf(str(path))
        for actor in p.renderer.actors.values():
            if hasattr(actor, "prop"):
                actor.prop.interpolation = "phong"
                actor.prop.specular, actor.prop.specular_power = 0.4, 20
    else:
        p.add_mesh(pv.read(path), color=(0.75, 0.75, 0.78), **look)

    p.set_background("#f4f5f7", top="#c9d0da")
    p.enable_anti_aliasing("ssaa")
    p.enable_ssao(radius=0.02 * p.length, kernel_size=128)
    p.add_axes()
    p.view_isometric()
    p.camera.zoom(1.5)
    if out:
        p.screenshot(out)
    else:
        p.show(title=path.name)


if __name__ == "__main__":
    main()
