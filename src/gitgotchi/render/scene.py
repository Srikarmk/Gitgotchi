"""Night-sky backdrop and final compositing."""
import struct
import zlib
from typing import Optional

import numpy as np

from gitgotchi.render.raster import Frame, blur

SKY_TOP = np.array([22, 12, 38], float)
SKY_BOTTOM = np.array([52, 26, 72], float)
GROUND = np.array([28, 16, 34], float)
GROUND_EDGE = np.array([58, 34, 66], float)
MOON = np.array([255, 236, 190], float)


def backdrop(width: int, height: int, t: float = 0.0, seed: int = 7) -> np.ndarray:
    """A small Halloween night: gradient sky, twinkling stars, moon, hills."""
    rows = np.linspace(0, 1, height)[:, None, None]
    sky = SKY_TOP * (1 - rows) + SKY_BOTTOM * rows
    image = np.broadcast_to(sky, (height, width, 3)).copy()

    rng = np.random.default_rng(seed)
    for _ in range(max(6, width * height // 140)):
        x, y = rng.integers(0, width), rng.integers(0, int(height * 0.6))
        phase = rng.random()
        twinkle = 0.45 + 0.55 * max(0.0, np.sin((t + phase) * 2 * np.pi))
        image[y, x] = image[y, x] * (1 - twinkle) + np.array([255, 240, 220]) * twinkle

    yy, xx = np.mgrid[0:height, 0:width]
    mx, my, mr = width * 0.82, height * 0.18, max(2.5, height * 0.08)
    dist = np.sqrt((xx - mx) ** 2 + (yy - my) ** 2)
    halo = np.clip(1 - (dist - mr) / (mr * 2.2), 0, 1) ** 2 * 0.28
    image += halo[:, :, None] * (MOON - image)
    moon = dist < mr
    crater = np.sqrt((xx - mx - mr * 0.3) ** 2 + (yy - my + mr * 0.2) ** 2) < mr * 0.3
    image[moon] = MOON
    image[moon & crater] = MOON * 0.88

    hill = height * 0.86 + np.sin(xx[0] / width * 5.0 + 1.3) * height * 0.035
    ground = yy >= hill[None, :]
    image[ground] = GROUND
    image[ground & (yy < hill[None, :] + 1)] = GROUND_EDGE
    return image


def ground_shadow(width: int, height: int, lift: float) -> np.ndarray:
    """Soft dark ellipse under the pet; shrinks as the pet rises."""
    yy, xx = np.mgrid[0:height, 0:width]
    cx, cy = width / 2, height * 0.88
    lift = float(np.clip(lift, 0.0, 1.0))
    rx = width * (0.2 - 0.1 * lift)
    ry = max(1.2, height * 0.035)
    inside = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
    return np.clip(1 - inside, 0, 1) * (0.55 - 0.25 * lift)


def compose(
    frame: Frame,
    background: Optional[np.ndarray] = None,
    shadow: Optional[np.ndarray] = None,
    glow_strength: float = 0.9,
) -> np.ndarray:
    """Flatten a frame onto a background. Returns uint8 RGBA."""
    h, w = frame.rgba.shape[:2]
    if background is None:
        out = frame.rgba.copy()
        return np.clip(out, 0, 255).astype(np.uint8)

    image = background.astype(float).copy()
    if shadow is not None:
        image *= 1 - shadow[:, :, None]

    halo = blur(frame.glow, 2) * glow_strength
    image += halo * 0.6

    alpha = frame.rgba[:, :, 3:4] / 255
    image = frame.rgba[:, :, :3] * alpha + image * (1 - alpha)
    image += halo * 0.25
    rgba = np.dstack([np.clip(image, 0, 255), np.full((h, w), 255.0)])
    return rgba.astype(np.uint8)


def encode_png(rgba: np.ndarray) -> bytes:
    """Minimal PNG encoder so we don't need Pillow."""
    rgba = np.ascontiguousarray(rgba, dtype=np.uint8)
    h, w = rgba.shape[:2]
    rows = np.zeros((h, w * 4 + 1), dtype=np.uint8)
    rows[:, 1:] = rgba.reshape(h, w * 4)

    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(rows.tobytes(), 9))
        + chunk(b"IEND", b"")
    )


def upscale(rgba: np.ndarray, factor: int) -> np.ndarray:
    return rgba.repeat(factor, axis=0).repeat(factor, axis=1)
