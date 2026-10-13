"""3D pixel-art rendering for pet forms."""
import numpy as np

from gitgotchi.render.raster import Form, render
from gitgotchi.render.scene import backdrop, compose, ground_shadow

WIDTH = 64
HEIGHT = 48


def render_scene(
    form: Form,
    t: float,
    width: int = WIDTH,
    height: int = HEIGHT,
    stage: bool = True,
) -> np.ndarray:
    """Render a form on its night-sky stage. Returns uint8 RGBA (h, w, 4)."""
    frame = render(form, t, width, height, offset=(0.0, 0.12))
    if not stage:
        return compose(frame)
    lift = form.pose(t).bob / 0.15
    return compose(frame, backdrop(width, height, t), ground_shadow(width, height, lift))
