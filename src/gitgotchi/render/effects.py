"""2D effects drawn on top of a composed scene."""
import numpy as np

SPARKLE_COLORS = np.array([[255, 236, 160], [255, 255, 255], [255, 170, 80], [200, 160, 255]], float)
EMBER_COLORS = np.array([[255, 120, 40], [255, 190, 80], [220, 60, 40]], float)

Z_GLYPH = np.array([[1, 1, 1], [0, 0, 1], [0, 1, 0], [1, 0, 0], [1, 1, 1]], bool)


def flash(rgba: np.ndarray, amount: float) -> np.ndarray:
    """Blend visible pixels toward white (used by the evolution animation)."""
    if amount <= 0:
        return rgba
    out = rgba.astype(float)
    on = out[:, :, 3] > 0
    out[on, :3] = out[on, :3] * (1 - amount) + 255 * amount
    return out


def sparkles(image: np.ndarray, t: float, count: int, seed: int = 0, spread: float = 0.42) -> np.ndarray:
    """Twinkling plus-shaped sparkles scattered around the middle of the canvas."""
    if count <= 0:
        return image
    out = image.astype(float)
    h, w = out.shape[:2]
    rng = np.random.default_rng(seed)
    for _ in range(count):
        cx = int(w / 2 + (rng.random() - 0.5) * 2 * spread * w)
        cy = int(h * 0.45 + (rng.random() - 0.5) * 2 * spread * h)
        phase = rng.random()
        life = np.sin(((t + phase) % 1) * np.pi)
        if life < 0.25:
            continue
        color = SPARKLE_COLORS[rng.integers(len(SPARKLE_COLORS))]
        arm = 1 if life < 0.7 else 2
        for dx, dy in [(0, 0)] + [(d, 0) for d in range(-arm, arm + 1)] + [(0, d) for d in range(-arm, arm + 1)]:
            x, y = cx + dx, cy + dy
            if 0 <= x < w and 0 <= y < h:
                strength = life if (dx, dy) == (0, 0) else life * 0.75
                out[y, x, :3] = out[y, x, :3] * (1 - strength) + color * strength
    return out


def embers(image: np.ndarray, t: float, count: int = 10, seed: int = 3) -> np.ndarray:
    """Glowing embers drifting upward (Demon)."""
    out = image.astype(float)
    h, w = out.shape[:2]
    rng = np.random.default_rng(seed)
    for _ in range(count):
        x0, speed, phase = rng.random(), 0.5 + rng.random(), rng.random()
        progress = (t * speed + phase) % 1
        x = int(w * (0.3 + 0.4 * x0) + np.sin(progress * 6 + x0 * 9) * 2)
        y = int(h * (0.85 - 0.75 * progress))
        if 0 <= x < w and 0 <= y < h:
            fade = 1 - progress
            color = EMBER_COLORS[rng.integers(len(EMBER_COLORS))]
            out[y, x, :3] = out[y, x, :3] * (1 - fade) + color * fade
    return out


def snores(image: np.ndarray, t: float) -> np.ndarray:
    """Little Z's floating up (dormant pets)."""
    out = image.astype(float)
    h, w = out.shape[:2]
    for i in range(3):
        progress = (t + i / 3) % 1
        x = int(w * 0.62 + progress * w * 0.12)
        y = int(h * 0.35 - progress * h * 0.25)
        fade = np.sin(progress * np.pi)
        gh, gw = Z_GLYPH.shape
        for gy in range(gh):
            for gx in range(gw):
                if Z_GLYPH[gy, gx] and 0 <= y + gy < h and 0 <= x + gx < w:
                    px = out[y + gy, x + gx, :3]
                    out[y + gy, x + gx, :3] = px * (1 - fade) + np.array([200, 190, 255]) * fade
    return out


def glitch(image: np.ndarray, seed: int, strength: int = 3) -> np.ndarray:
    """Shifted rows and an RGB split, like the screen got possessed."""
    out = image.copy()
    rng = np.random.default_rng(seed)
    h = out.shape[0]
    for _ in range(strength):
        row = int(rng.integers(0, h - 3))
        rows = int(rng.integers(1, 4))
        out[row : row + rows] = np.roll(out[row : row + rows], int(rng.integers(-4, 5)), axis=1)
    out[:, :, 0] = np.roll(out[:, :, 0], -1, axis=1)
    out[:, :, 2] = np.roll(out[:, :, 2], 1, axis=1)
    return out


def dim(image: np.ndarray, amount: float) -> np.ndarray:
    out = image.astype(float)
    out[:, :, :3] *= 1 - amount
    return out
