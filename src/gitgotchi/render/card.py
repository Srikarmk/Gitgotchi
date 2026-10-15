"""Shareable pet card: the 3D scene plus stats, as a PNG."""
from typing import Dict, Tuple

import numpy as np

from gitgotchi.pet import theme
from gitgotchi.pet.states import PetStats
from gitgotchi.render import render_scene
from gitgotchi.render.font import draw_text, text_width
from gitgotchi.render.scene import upscale
from gitgotchi.render.forms import form_for

CARD_W, CARD_H = 240, 126
SCENE_W, SCENE_H = 112, 84
SCALE = 5

BG_TOP = np.array([18, 10, 32], float)
BG_BOTTOM = np.array([40, 20, 60], float)
SHADOW = (8, 4, 14)


def hex_rgb(color: str) -> Tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def _bar(image, x, y, width, fraction, color):
    image[y : y + 4, x : x + width, :3] = (60, 42, 82)
    filled = int(round(max(0.0, min(1.0, fraction)) * width))
    image[y : y + 4, x : x + filled, :3] = color
    image[y, x : x + filled, :3] = np.minimum(255, np.array(color) + 50)


def agent_line(agents: Dict[str, int], width: int) -> str:
    """As many "NAME COUNT" pairs as fit, then "+N" for the rest."""
    ranked = sorted(agents.items(), key=lambda kv: -kv[1])
    for shown in range(len(ranked), 0, -1):
        line = " ".join(f"{n} {c:,}" for n, c in ranked[:shown])
        if shown < len(ranked):
            line += f" +{len(ranked) - shown}"
        if text_width(line) <= width:
            return line
    return ranked[0][0][: width // 6]


def make_card_gif(stats: PetStats, repo_name: str, agents: Dict[str, int], scale: int = SCALE, frames: int = 24) -> bytes:
    """The card with the pet moving, as an animated GIF (needs Pillow)."""
    from io import BytesIO

    from PIL import Image

    images = [
        Image.fromarray(upscale(make_card(stats, repo_name, agents, t=i / frames), scale)[:, :, :3])
        for i in range(frames)
    ]
    # One shared palette keeps colors from flickering between frames
    palette = images[0].quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    paletted = [image.quantize(palette=palette, dither=Image.Dither.NONE) for image in images]
    out = BytesIO()
    paletted[0].save(out, format="GIF", save_all=True, append_images=paletted[1:], duration=1000 // 12, loop=0, optimize=True)
    return out.getvalue()


def make_card(stats: PetStats, repo_name: str, agents: Dict[str, int], t: float = 0.15) -> np.ndarray:
    """Render the card at 1x pixel scale. Returns uint8 RGBA (126, 240, 4)."""
    rows = np.linspace(0, 1, CARD_H)[:, None, None]
    card = np.broadcast_to(BG_TOP * (1 - rows) + BG_BOTTOM * rows, (CARD_H, CARD_W, 3)).copy()
    card = np.dstack([card, np.full((CARD_H, CARD_W), 255.0)])

    rng = np.random.default_rng(len(repo_name))
    for _ in range(40):
        x, y = rng.integers(SCENE_W + 14, CARD_W), rng.integers(0, CARD_H)
        card[y, x, :3] = card[y, x, :3] * 0.5 + np.array([220, 200, 255]) * 0.5 * rng.random()

    purple, orange = hex_rgb(theme.PURPLE), hex_rgb(theme.ORANGE)
    card[0, :, :3] = card[-1, :, :3] = purple
    card[:, 0, :3] = card[:, -1, :3] = purple

    form = form_for(stats.current_form.value)
    scene = render_scene(form, t, SCENE_W, SCENE_H, sparkles=10, seed=7)
    sx, sy = 9, (CARD_H - SCENE_H) // 2
    card[sy - 1 : sy + SCENE_H + 1, sx - 1 : sx + SCENE_W + 1, :3] = orange
    card[sy : sy + SCENE_H, sx : sx + SCENE_W] = scene

    info = theme.form_info(stats.current_form)
    form_color = hex_rgb(info.color)
    dim, bone = hex_rgb(theme.DIM), hex_rgb(theme.BONE)

    x = sx + SCENE_W + 12
    right = CARD_W - 9
    draw_text(card, "GITGOTCHI", x, 10, orange)

    name = stats.pet_name.upper()
    while name and text_width(name, 2) > right - x:
        name = name[:-1]
    draw_text(card, name, x, 22, bone, scale=2, shadow=SHADOW)
    draw_text(card, f"THE {info.title}", x, 40, form_color, shadow=SHADOW)

    y = 54
    draw_text(card, "COMMITS", x, y, dim)
    value = f"{stats.total_commits:,}"
    draw_text(card, value, right - text_width(value), y, bone)

    for label, fraction, shown, color in [
        ("QUALITY", stats.quality_score / 100, f"{stats.quality_score:.0f}", theme.GREEN),
        ("POSSESSED", stats.possession, f"{stats.possession:.0%}", theme.CYAN),
    ]:
        y += 12
        draw_text(card, label, x, y, dim)
        draw_text(card, shown, right - text_width(shown), y, bone)
        _bar(card, x, y + 9, right - x, fraction, hex_rgb(color))
        y += 6

    y += 13
    if agents:
        draw_text(card, agent_line(agents, right - x), x, y, hex_rgb(theme.CYAN))
    else:
        draw_text(card, "NO AGENTS YET", x, y, dim)

    footer_y = CARD_H - 13
    repo = repo_name.upper()
    while repo and text_width(repo) > right - x:
        repo = repo[:-1]
    draw_text(card, repo, x, footer_y, dim)

    return np.clip(card, 0, 255).astype(np.uint8)
