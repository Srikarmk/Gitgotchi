"""README badge: a tiny pixel portrait of the pet plus its form, as SVG."""
import hashlib
from html import escape

import numpy as np

from gitgotchi.pet import theme
from gitgotchi.pet.states import PetStats
from gitgotchi.render import render_scene
from gitgotchi.render.card import hex_rgb
from gitgotchi.render.forms import form_for

HEIGHT = 28
PORTRAIT_MAX_H = 24
FONT = "Verdana,Geneva,DejaVu Sans,sans-serif"
# Rough Verdana advances at 11px (regular and bold)
CHAR_WIDTH = 6.9
BOLD_CHAR_WIDTH = 7.7
PAD = 9

LABEL_BG = "#2a1c42"
LABEL_FG = "#f2e8cf"


def _text_width(text: str, bold: bool = False) -> int:
    return int(round(len(text) * (BOLD_CHAR_WIDTH if bold else CHAR_WIDTH)))


def _readable_on(hex_color: str) -> str:
    r, g, b = hex_rgb(hex_color)
    return "#1a0f2d" if 0.299 * r + 0.587 * g + 0.114 * b > 150 else "#ffffff"


def portrait(stats: PetStats) -> np.ndarray:
    """The pet cropped to itself, at the largest size that fits the badge."""
    form = form_for(stats.current_form.value)
    for height in range(48, 15, -2):
        image = render_scene(form, 0.15, height * 4 // 3, height, stage=False)
        rows = np.nonzero(image[:, :, 3].any(axis=1))[0]
        cols = np.nonzero(image[:, :, 3].any(axis=0))[0]
        if rows.size and rows[-1] - rows[0] + 1 <= PORTRAIT_MAX_H:
            return image[rows[0] : rows[-1] + 1, cols[0] : cols[-1] + 1]
    return image


def _portrait_rects(image: np.ndarray, x0: int, y0: int) -> str:
    """The pet as one <rect> per horizontal run of same-colored pixels."""
    rects = []
    for y in range(image.shape[0]):
        x = 0
        while x < image.shape[1]:
            px = image[y, x]
            if px[3] == 0:
                x += 1
                continue
            run = 1
            while x + run < image.shape[1] and np.array_equal(image[y, x + run], px):
                run += 1
            color = "#%02x%02x%02x" % tuple(int(c) for c in px[:3])
            opacity = "" if px[3] == 255 else f' fill-opacity="{px[3] / 255:.2f}"'
            rects.append(f'<rect x="{x0 + x}" y="{y0 + y}" width="{run}" height="1" fill="{color}"{opacity}/>')
            x += run
    return "".join(rects)


def make_badge(stats: PetStats) -> str:
    info = theme.form_info(stats.current_form)
    label = "gitgotchi"
    value = info.title
    if stats.ai_commits:
        value += f" · {stats.possession:.0%} possessed"

    pet = portrait(stats)
    portrait_w = pet.shape[1] + 8
    label_w = _text_width(label) + 2 * PAD
    value_w = _text_width(value, bold=True) + 2 * PAD
    width = portrait_w + label_w + value_w
    value_bg = info.color
    value_fg = _readable_on(value_bg)
    text_y = HEIGHT / 2 + 4
    title = escape(f"{stats.pet_name} the {info.title}: {value}")
    # Unique per badge, so several badges inlined in one page don't share a clip
    clip = "gg" + hashlib.sha1(f"{value}{width}".encode()).hexdigest()[:8]

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{HEIGHT}" '
        f'viewBox="0 0 {width} {HEIGHT}" role="img" aria-label="{title}">'
        f"<title>{title}</title>"
        f'<clipPath id="{clip}"><rect width="{width}" height="{HEIGHT}" rx="4"/></clipPath>'
        f'<g clip-path="url(#{clip})">'
        f'<rect width="{portrait_w + label_w}" height="{HEIGHT}" fill="{LABEL_BG}"/>'
        f'<rect x="{portrait_w + label_w}" width="{value_w}" height="{HEIGHT}" fill="{value_bg}"/>'
        f'<g shape-rendering="crispEdges">{_portrait_rects(pet, 6, (HEIGHT - pet.shape[0]) // 2)}</g>'
        f"</g>"
        f'<g font-family="{FONT}" font-size="11" text-anchor="middle">'
        f'<text x="{portrait_w + label_w / 2}" y="{text_y}" fill="{LABEL_FG}">{escape(label)}</text>'
        f'<text x="{portrait_w + label_w + value_w / 2}" y="{text_y}" fill="{value_fg}" font-weight="bold">{escape(value)}</text>'
        f"</g></svg>"
    )
