"""Draw rendered pixels in a terminal."""
import base64
import os
from typing import Iterable, Optional

import numpy as np
from rich.color import Color
from rich.console import Console, ConsoleOptions, RenderResult
from rich.measure import Measurement
from rich.segment import Segment
from rich.style import Style

from gitgotchi.render.scene import encode_png, upscale

UPPER = "▀"
LOWER = "▄"


class PixelArt:
    """Rich renderable that draws RGBA pixels with half-block characters.

    Each character cell holds two vertically stacked pixels, so a 64x48 image
    takes 64 columns and 24 rows.
    """

    def __init__(self, rgba: np.ndarray) -> None:
        if rgba.shape[0] % 2:
            rgba = np.concatenate([rgba, np.zeros_like(rgba[:1])], axis=0)
        self.rgba = rgba
        self.width = rgba.shape[1]

    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement:
        return Measurement(self.width, self.width)

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        for row in range(0, self.rgba.shape[0], 2):
            yield from _merge(self._cells(self.rgba[row], self.rgba[row + 1]))
            yield Segment.line()

    @staticmethod
    def _cells(top: np.ndarray, bottom: np.ndarray) -> Iterable[Segment]:
        for t, b in zip(top, bottom):
            top_on, bottom_on = t[3] > 0, b[3] > 0
            if top_on and bottom_on:
                if tuple(t[:3]) == tuple(b[:3]):
                    yield Segment(" ", _style(bg=t))
                else:
                    yield Segment(UPPER, _style(fg=t, bg=b))
            elif top_on:
                yield Segment(UPPER, _style(fg=t))
            elif bottom_on:
                yield Segment(LOWER, _style(fg=b))
            else:
                yield Segment(" ")


_STYLE_CACHE: dict = {}


def _style(fg: Optional[np.ndarray] = None, bg: Optional[np.ndarray] = None) -> Style:
    key = (None if fg is None else tuple(fg[:3]), None if bg is None else tuple(bg[:3]))
    style = _STYLE_CACHE.get(key)
    if style is None:
        style = Style(
            color=None if fg is None else Color.from_rgb(*map(int, fg[:3])),
            bgcolor=None if bg is None else Color.from_rgb(*map(int, bg[:3])),
        )
        if len(_STYLE_CACHE) > 20000:
            _STYLE_CACHE.clear()
        _STYLE_CACHE[key] = style
    return style


def _merge(segments: Iterable[Segment]) -> Iterable[Segment]:
    """Join neighbouring cells that share a style to keep output small."""
    text, style = "", None
    for seg in segments:
        if seg.style == style:
            text += seg.text
            continue
        if text:
            yield Segment(text, style)
        text, style = seg.text, seg.style
    if text:
        yield Segment(text, style)


def graphics_protocol() -> Optional[str]:
    """Which inline-image protocol the terminal speaks, if any.

    Override with GITGOTCHI_GRAPHICS=blocks|kitty|iterm.
    """
    forced = os.environ.get("GITGOTCHI_GRAPHICS", "").lower()
    if forced in ("kitty", "iterm"):
        return forced
    if forced == "blocks":
        return None
    if os.environ.get("TMUX") or os.environ.get("STY"):
        return None

    term = os.environ.get("TERM", "")
    program = os.environ.get("TERM_PROGRAM", "")
    if os.environ.get("KITTY_WINDOW_ID") or term == "xterm-kitty" or program == "ghostty":
        return "kitty"
    if program in ("iTerm.app", "WezTerm") or os.environ.get("LC_TERMINAL") == "iTerm2":
        return "iterm"
    return None


def inline_image(rgba: np.ndarray, columns: int, protocol: str) -> str:
    """Escape sequence that draws an image `columns` cells wide."""
    png = encode_png(upscale(rgba, 6))
    data = base64.b64encode(png).decode()
    rows = max(1, round(columns * rgba.shape[0] / rgba.shape[1] / 2))

    if protocol == "iterm":
        return (
            f"\x1b]1337;File=inline=1;width={columns};height={rows};"
            f"preserveAspectRatio=1;size={len(png)}:{data}\a\n"
        )

    chunks = [data[i : i + 4096] for i in range(0, len(data), 4096)]
    out = []
    for i, chunk in enumerate(chunks):
        more = 1 if i < len(chunks) - 1 else 0
        if i == 0:
            out.append(f"\x1b_Ga=T,f=100,c={columns},r={rows},m={more};{chunk}\x1b\\")
        else:
            out.append(f"\x1b_Gm={more};{chunk}\x1b\\")
    return "".join(out) + "\n"
