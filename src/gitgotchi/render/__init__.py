"""3D pixel-art rendering for pet forms."""
from typing import Optional

import numpy as np

from gitgotchi.render import effects
from gitgotchi.render.raster import Form, Pose, render
from gitgotchi.render.scene import backdrop, compose, ground_shadow

WIDTH = 64
HEIGHT = 48


def render_scene(
    form: Form,
    t: float,
    width: int = WIDTH,
    height: int = HEIGHT,
    stage: bool = True,
    pose: Optional[Pose] = None,
    flash: float = 0.0,
    sparkles: int = 0,
    seed: int = 0,
    sleeping: bool = False,
    glitch: bool = False,
) -> np.ndarray:
    """Render a form on its night-sky stage. Returns uint8 RGBA (h, w, 4)."""
    pose = pose or form.pose(t)
    if sleeping:
        pose = Pose(yaw=0.0, bob=0.015 * np.sin(t * 2 * np.pi), squash=0.97, tilt=0.0)
        form.eyes_closed = True

    # Framed tight so the pet gets as many pixels as the canvas allows
    frame = render(form, t, width, height, span=1.2, offset=(0.0, 0.07), pose=pose)
    frame.rgba = effects.flash(frame.rgba, flash)
    if not stage:
        return compose(frame)

    lift = pose.bob / 0.15
    image = compose(frame, backdrop(width, height, t), ground_shadow(width, height, lift))
    image = image.astype(float)
    if form.name == "demon":
        image = effects.embers(image, t)
    if sleeping:
        image = effects.dim(image, 0.25)
        image = effects.snores(image, t)
    image = effects.sparkles(image, t, sparkles, seed)
    if glitch:
        image = effects.glitch(image, seed)
    return np.clip(image, 0, 255).astype(np.uint8)
