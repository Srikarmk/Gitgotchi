import numpy as np
import pytest
from rich.console import Console

from gitgotchi.render import render_scene
from gitgotchi.render.forms import FORMS, form_for
from gitgotchi.render.scene import encode_png
from gitgotchi.render.terminal import PixelArt


@pytest.mark.parametrize("name", sorted(FORMS))
def test_every_form_renders(name):
    image = render_scene(form_for(name), 0.3)
    assert image.shape == (48, 64, 4)
    assert image.dtype == np.uint8
    # the pet should cover a decent part of the canvas
    plain = render_scene(form_for(name), 0.3, stage=False)
    assert (plain[:, :, 3] > 0).mean() > 0.08


def test_effects_do_not_crash():
    form = form_for("demon")
    render_scene(form, 0.5, sparkles=20, glitch=True, flash=0.5, seed=3)
    render_scene(form_for("egg"), 0.5, sleeping=True)


def test_png_encoding():
    png = encode_png(render_scene(form_for("ghost"), 0.0))
    assert png.startswith(b"\x89PNG\r\n\x1a\n")


def test_pixel_art_width():
    console = Console(width=100, color_system="truecolor", record=True, file=open("/dev/null", "w"))
    console.print(PixelArt(render_scene(form_for("ghost"), 0.0)))
    lines = console.export_text().splitlines()
    assert len(lines) == 24
    assert max(len(line) for line in lines) == 64
