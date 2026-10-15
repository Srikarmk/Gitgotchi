import io

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
    console = Console(width=100, color_system="truecolor", record=True, file=io.StringIO())
    console.print(PixelArt(render_scene(form_for("ghost"), 0.0)))
    lines = console.export_text().splitlines()
    assert len(lines) == 24
    assert max(len(line) for line in lines) == 64


def test_card_renders_and_fits_agents():
    from collections import Counter

    from gitgotchi.pet.states import PetForm, PetStats
    from gitgotchi.render.card import CARD_H, CARD_W, agent_line, make_card

    stats = PetStats()
    stats.pet_name = "AVeryLongCompanionName"
    stats.current_form = PetForm.POLTERGEIST
    card = make_card(stats, "my-repo", Counter({"Claude": 900, "Copilot": 300}))
    assert card.shape == (CARD_H, CARD_W, 4)

    assert agent_line({"Claude": 9}, 98) == "Claude 9"
    assert agent_line({"Claude": 927, "Copilot": 305}, 98) == "Claude 927 +1"


def test_filled_notch_is_not_inked_as_a_far_part():
    from gitgotchi.render.raster import Frame, borrow_depth, clean_pixels, draw_inner_lines

    # A 5x5 block with a one-pixel notch in its top edge; the notch's ray missed (depth 6)
    on = np.ones((5, 5), bool)
    on[0, 2] = False
    material = np.where(on, 0, -1)
    band = np.zeros((5, 5), int)
    depth = np.where(on, 2.0, 6.0)

    hit = on.copy()
    on, material, band = clean_pixels(on, material, band)
    assert on[0, 2], "clean_pixels should fill the notch"

    depth_map = borrow_depth(np.where(on, depth, 0.0), on & ~hit, hit & on)
    frame = Frame(np.full((5, 5, 4), 200.0), np.zeros((5, 5, 3)))
    draw_inner_lines(frame, on, depth_map, (0, 0, 0))
    assert (frame.rgba[0, 2, :3] == 200).all(), "the filled notch should not get an inner line"
