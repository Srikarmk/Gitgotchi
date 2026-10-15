"""A tiny vectorized raymarcher that turns signed distance fields into pixel art.

Every form is a 3D shape described by a signed distance function. Rays are
cast orthographically from in front of the canvas, hit points are cel-shaded
into a few bands, and the silhouette gets a 1px outline so the result reads
as hand-made pixel art.
"""
from dataclasses import dataclass, field
from typing import Dict, Optional, Set, Tuple

import numpy as np

RGB = Tuple[int, int, int]

LIGHT = np.array([-0.55, 0.65, -0.55]) / np.linalg.norm([-0.55, 0.65, -0.55])

# Brightness of each cel-shading band, darkest to brightest
BANDS = np.array([0.56, 0.74, 0.9, 1.0, 1.1])


@dataclass
class Pose:
    yaw: float = 0.0
    bob: float = 0.0
    squash: float = 1.0
    tilt: float = 0.0


@dataclass
class Frame:
    """One rendered frame: RGBA pixels plus which pixels glow."""

    rgba: np.ndarray  # (h, w, 4) float, 0-255
    glow: np.ndarray  # (h, w, 3) float, emissive color per pixel (0 if none)


@dataclass
class Form:
    """Base class for a pet form. Subclasses provide sdf() and paint()."""

    name: str = "form"
    outline: RGB = (43, 20, 66)
    rim: RGB = (90, 40, 140)
    colors: Dict[int, RGB] = field(default_factory=lambda: {0: (232, 228, 250)})
    emissive: Set[int] = field(default_factory=set)
    opacity: float = 1.0
    eyes_closed: bool = False

    def shut(self, t: float, at: float = 0.62, length: float = 0.05) -> bool:
        """Whether the eyes are closed at time t (asleep, or mid-blink)."""
        return self.eyes_closed or at <= t % 1 < at + length

    def pose(self, t: float) -> Pose:
        wave = np.sin(t * 2 * np.pi)
        return Pose(yaw=0.55 * wave, bob=0.06 * np.sin(t * 4 * np.pi))

    def sdf(self, p: np.ndarray, t: float) -> np.ndarray:
        raise NotImplementedError

    def paint(self, p: np.ndarray, n: np.ndarray, t: float) -> np.ndarray:
        """Material id for each surface point (object space)."""
        return np.zeros(len(p), dtype=int)

    def post(self, frame: Frame, t: float) -> Frame:
        """Optional 2D effect applied after shading."""
        return frame


def rot_y(p: np.ndarray, angle: float) -> np.ndarray:
    c, s = np.cos(angle), np.sin(angle)
    out = p.copy()
    out[:, 0] = c * p[:, 0] + s * p[:, 2]
    out[:, 2] = -s * p[:, 0] + c * p[:, 2]
    return out


def rot_z(p: np.ndarray, angle: float) -> np.ndarray:
    c, s = np.cos(angle), np.sin(angle)
    out = p.copy()
    out[:, 0] = c * p[:, 0] - s * p[:, 1]
    out[:, 1] = s * p[:, 0] + c * p[:, 1]
    return out


def to_object(p: np.ndarray, pose: Pose) -> np.ndarray:
    """View space -> object space for a given pose."""
    q = p.copy()
    q[:, 1] -= pose.bob
    q = rot_z(q, -pose.tilt)
    q = rot_y(q, pose.yaw)
    q[:, 1] /= pose.squash
    q[:, 0] *= np.sqrt(pose.squash)
    q[:, 2] *= np.sqrt(pose.squash)
    return q


def smin(a: np.ndarray, b: np.ndarray, k: float) -> np.ndarray:
    """Smooth union of two distance fields."""
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def ellipse(x, y, cx, cy, rx, ry) -> np.ndarray:
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1


def render(
    form: Form,
    t: float,
    width: int = 64,
    height: int = 48,
    span: float = 1.35,
    offset: Tuple[float, float] = (0.0, 0.0),
    pose: Optional[Pose] = None,
) -> Frame:
    """Render one frame of a form.

    Args:
        form: Form to draw
        t: Animation time in [0, 1); forms loop over this interval
        width, height: Canvas size in pixels
        span: Half of the visible world height
        offset: Shift of the camera in world units (x, y)
        pose: Override the form's own animation pose
    """
    pose = pose or form.pose(t)
    aspect = width / height
    xs = np.linspace(-span * aspect, span * aspect, width) + offset[0]
    ys = np.linspace(span, -span, height) + offset[1]
    gx, gy = np.meshgrid(xs, ys)
    count = width * height
    origin = np.stack([gx.ravel(), gy.ravel(), np.full(count, -3.0)], axis=1)

    def field_at(points: np.ndarray) -> np.ndarray:
        # Squash/stretch distorts distances; scale down to stay conservative
        return form.sdf(to_object(points, pose), t) * min(1.0, pose.squash) * 0.85

    depth = np.zeros(count)
    active = np.arange(count)
    hit = np.zeros(count, dtype=bool)
    for _ in range(90):
        if active.size == 0:
            break
        points = origin[active].copy()
        points[:, 2] += depth[active]
        d = field_at(points)
        done = d < 1e-3
        hit[active[done]] = True
        depth[active] += np.where(done, 0, d)
        active = active[~done & (depth[active] < 6)]

    rgba = np.zeros((count, 4))
    glow = np.zeros((count, 3))
    idx = np.nonzero(hit)[0]
    if idx.size:
        view_points = origin[idx].copy()
        view_points[:, 2] += depth[idx]
        obj = to_object(view_points, pose)

        e = 2e-3
        normal = np.empty_like(obj)
        for axis in range(3):
            step = np.zeros(3)
            step[axis] = e
            normal[:, axis] = form.sdf(obj + step, t) - form.sdf(obj - step, t)
        normal /= np.linalg.norm(normal, axis=1, keepdims=True) + 1e-9

        view_normal = rot_y(normal, -pose.yaw)
        view_normal = rot_z(view_normal, pose.tilt)
        diffuse = np.clip(view_normal @ LIGHT, 0, 1)
        band = np.digitize(diffuse, [0.08, 0.38, 0.72, 0.94])
        rim = np.clip(1 + view_normal[:, 2], 0, 1) ** 3

        material = form.paint(obj, normal, t)
        base = np.array([form.colors[m] for m in range(max(form.colors) + 1)], float)
        color = base[material] * BANDS[band][:, None]
        color += rim[:, None] * np.array(form.rim, float) * 0.55

        lit = np.isin(material, list(form.emissive))
        color[lit] = base[material[lit]]
        glow[idx[lit]] = base[material[lit]]

        rgba[idx, :3] = np.clip(color, 0, 255)
        rgba[idx, 3] = 255 * form.opacity

    frame = Frame(rgba.reshape(height, width, 4), glow.reshape(height, width, 3))
    frame = add_outline(frame, form.outline)
    return form.post(frame, t)


def add_outline(frame: Frame, color: RGB) -> Frame:
    mask = frame.rgba[:, :, 3] > 0
    grown = mask.copy()
    grown[1:] |= mask[:-1]
    grown[:-1] |= mask[1:]
    grown[:, 1:] |= mask[:, :-1]
    grown[:, :-1] |= mask[:, 1:]
    edge = grown & ~mask
    frame.rgba[edge] = [*color, 255]
    return frame


def blur(image: np.ndarray, radius: int) -> np.ndarray:
    """Cheap separable box blur, applied twice for a softer falloff."""
    out = image.astype(float)
    for _ in range(2):
        for axis in (0, 1):
            pad = [(0, 0)] * out.ndim
            pad[axis] = (radius, radius)
            padded = np.pad(out, pad, mode="edge")
            csum = np.cumsum(padded, axis=axis)
            csum = np.insert(csum, 0, 0, axis=axis)
            size = out.shape[axis]
            hi = np.take(csum, np.arange(2 * radius + 1, 2 * radius + 1 + size), axis=axis)
            lo = np.take(csum, np.arange(0, size), axis=axis)
            out = (hi - lo) / (2 * radius + 1)
    return out
