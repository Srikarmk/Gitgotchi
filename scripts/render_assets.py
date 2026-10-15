"""Render the images used in the README.

    pip install -e ".[dev]"
    python scripts/render_assets.py
"""
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

from gitgotchi.pet import theme
from gitgotchi.pet.states import PetForm, PetStats
from gitgotchi.render import Pose, render_scene
from gitgotchi.render.card import hex_rgb, make_card
from gitgotchi.render.font import draw_text, text_width
from gitgotchi.render.forms import form_for
from gitgotchi.render.scene import encode_png, upscale

OUT = Path(__file__).resolve().parent.parent / "docs"
LINEUP = [PetForm.EGG, PetForm.GHOST, PetForm.ANGEL, PetForm.DEMON, PetForm.ZOMBIE, PetForm.WRAITH, PetForm.POLTERGEIST]


def forms_lineup() -> None:
    tiles = []
    for form in LINEUP:
        scene = render_scene(form_for(form.value), 0.15, 64, 48).astype(float)
        tile = np.zeros((60, 68, 4))
        tile[:, :, :3] = (18, 10, 32)
        tile[:, :, 3] = 255
        tile[2:50, 2:66] = scene
        info = theme.form_info(form)
        label = info.title.upper()
        draw_text(tile, label, (68 - text_width(label)) // 2, 52, hex_rgb(info.color))
        tiles.append(tile)
    sheet = np.concatenate(tiles, axis=1).astype(np.uint8)
    (OUT / "forms.png").write_bytes(encode_png(upscale(sheet, 4)))


def card() -> None:
    stats = PetStats()
    stats.pet_name = "Pumpkin"
    stats.current_form = PetForm.POLTERGEIST
    stats.total_commits, stats.ai_commits, stats.quality_score = 1284, 809, 74
    image = make_card(stats, "spooky-api", Counter({"Claude": 612, "Copilot": 197}))
    (OUT / "card.png").write_bytes(encode_png(upscale(image, 5)))


def haunt_gif() -> None:
    """Pumpkin hops, gets fed, evolves to Ghost, then gets possessed."""
    frames = []

    def add(form, t, **kw):
        image = render_scene(form_for(form.value), t, **kw)
        frames.append(Image.fromarray(upscale(image, 6)[:, :, :3]))

    for i in range(30):
        add(PetForm.EGG, i / 30, sparkles=12 if 14 <= i < 24 else 0, seed=i)
    for i in range(36):
        p = i / 35
        if p < 0.55:
            k = p / 0.55
            add(PetForm.EGG, p, pose=Pose(yaw=k * k * 14, bob=0.05 + 0.1 * k), flash=k * 0.9, sparkles=int(k * 18), seed=i)
        else:
            k = (p - 0.55) / 0.45
            add(PetForm.GHOST, p, flash=max(0.0, 1 - k * 1.6), sparkles=int((1 - k) * 22) + 4, seed=i)
    for i in range(30):
        add(PetForm.GHOST, i / 30, glitch=i in (8, 9, 10, 20, 21), sparkles=6 if i > 8 else 0, seed=i)
    for i in range(48):
        add(PetForm.POLTERGEIST, i / 48, sparkles=4, seed=i)

    frames[0].save(OUT / "haunt.gif", save_all=True, append_images=frames[1:], duration=80, loop=0, optimize=True)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    forms_lineup()
    card()
    haunt_gif()
    print(f"Wrote images to {OUT}")
