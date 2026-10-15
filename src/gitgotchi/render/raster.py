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
    # 0 for matte; higher values give a bigger specular highlight
    gloss: float = 0.0
    # Color the shadows lean toward; None uses the default cool purple
    shadow: Optional[RGB] = None
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

    shape = (height, width)
    on = hit.reshape(shape)
    material = np.full(count, -1)
    band = np.zeros(count, dtype=int)
    shine = np.zeros(count, dtype=bool)
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
        view_normal = rot_z(rot_y(normal, -pose.yaw), pose.tilt)

        # Half-Lambert keeps the dark side readable; occlusion darkens the
        # creases where arms, horns and hems meet the body
        light = np.clip(view_normal @ LIGHT * 0.5 + 0.5, 0, 1)
        light *= 0.6 + 0.4 * occlusion(form, obj, normal, t)
        band[idx] = np.digitize(light, BAND_EDGES)
        if form.gloss:
            shine[idx] = (np.clip(view_normal @ HALFWAY, 0, 1) ** 40) > 1 - form.gloss
        material[idx] = form.paint(obj, normal, t)

    material = material.reshape(shape)
    band = band.reshape(shape)
    shine = shine.reshape(shape) & on
    on, material, band = clean_pixels(on, material, band)

    depth_map = np.where(on, depth.reshape(shape), 0.0)
    rgba = np.zeros((height, width, 4))
    glow = np.zeros((height, width, 3))
    for m in np.unique(material[on]):
        base = np.array(form.colors[m], float)
        where = on & (material == m)
        if m in form.emissive:
            rgba[where, :3] = base
            glow[where] = base
            continue
        tones = ramp(base, form.shadow)
        rgba[where, :3] = tones[np.minimum(band[where], len(tones) - 2)]
        lit = where & shine
        rgba[lit, :3] = tones[-1]
    rgba[on, 3] = 255 * form.opacity

    frame = Frame(rgba, glow)
    draw_inner_lines(frame, on, depth_map, form.outline)
    add_outline(frame, form.outline)
    return form.post(frame, t)


# Light from the upper left, slightly in front, so bands curve around the
# form instead of running down it in vertical stripes
LIGHT = np.array([-0.45, 0.72, -0.53]) / np.linalg.norm([-0.45, 0.72, -0.53])
HALFWAY = (LIGHT + np.array([0, 0, -1.0])) / np.linalg.norm(LIGHT + np.array([0, 0, -1.0]))
BAND_EDGES = [0.5, 0.67, 0.86]
# Depth jump (world units) between neighbouring pixels that counts as one part
# in front of another
INNER_LINE_GAP = 0.4
SHADOW_TINT = np.array([52, 28, 96], float)
LIGHT_TINT = np.array([255, 238, 196], float)


def shifted(a: np.ndarray, shift: int, axis: int, fill=0) -> np.ndarray:
    """Like np.roll, but without wrapping: cells shifted in from the edge get `fill`."""
    out = np.full_like(a, fill)
    src = [slice(None)] * a.ndim
    dst = [slice(None)] * a.ndim
    if shift > 0:
        src[axis], dst[axis] = slice(None, -shift), slice(shift, None)
    else:
        src[axis], dst[axis] = slice(-shift, None), slice(None, shift)
    out[tuple(dst)] = a[tuple(src)]
    return out


def ramp(base: np.ndarray, shadow: Optional[RGB] = None) -> np.ndarray:
    """Hue-shifted shades of one color: shadows lean cool, highlights warm.

    Very dark and near-white colors (eyes, shines) stay flat so faces stay
    crisp. The last entry is the specular highlight.
    """
    luma = base @ [0.299, 0.587, 0.114]
    if luma < 55 or luma > 245:
        return np.array([base] * 5)
    tint = SHADOW_TINT if shadow is None else np.array(shadow, float)
    return np.clip(
        np.array(
            [
                base * 0.46 * 0.68 + tint * 0.32,
                base * 0.7 * 0.84 + tint * 0.16,
                base,
                (base * 1.06) * 0.75 + LIGHT_TINT * 0.25,
                base * 0.35 + 255 * 0.65,
            ]
        ),
        0,
        255,
    )


def occlusion(form: "Form", p: np.ndarray, n: np.ndarray, t: float) -> np.ndarray:
    """Cheap ambient occlusion: how much nearby geometry crowds each point."""
    total = np.zeros(len(p))
    for distance, weight in ((0.06, 0.6), (0.16, 0.4)):
        free = form.sdf(p + n * distance, t)
        total += weight * np.clip(free / distance, 0, 1)
    return total


def clean_pixels(on: np.ndarray, material: np.ndarray, band: np.ndarray):
    """Pixel-art cleanup: shave one-pixel spurs, fill one-pixel notches, and
    merge isolated shading pixels into their surroundings."""
    def neighbours(mask):
        padded = np.pad(mask, 1).astype(int)
        return padded[:-2, 1:-1] + padded[2:, 1:-1] + padded[1:-1, :-2] + padded[1:-1, 2:]

    count = neighbours(on)
    spurs = on & (count <= 1)
    notches = ~on & (count >= 3)
    on = (on & ~spurs) | notches

    if notches.any():
        # A filled notch takes the material and shade of a neighbour
        for shift, axis in ((1, 0), (-1, 0), (1, 1), (-1, 1)):
            src_m = shifted(material, shift, axis, -1)
            src_b = shifted(band, shift, axis)
            take = notches & (material < 0) & (src_m >= 0)
            material[take] = src_m[take]
            band[take] = src_b[take]
        on &= material >= 0

    # A shading pixel unlike all four neighbours of the same material is noise
    stack_b = [shifted(band, s, a) for s, a in ((1, 0), (-1, 0), (1, 1), (-1, 1))]
    stack_m = [shifted(material, s, a, -1) for s, a in ((1, 0), (-1, 0), (1, 1), (-1, 1))]
    same = [(m == material) for m in stack_m]
    lonely = on & np.all([~s | (b != band) for s, b in zip(same, stack_b)], axis=0) & np.all(same, axis=0)
    if lonely.any():
        votes = np.stack(stack_b)
        tallies = np.stack([(votes == k).sum(axis=0) for k in range(len(BAND_EDGES) + 1)])
        band[lonely] = tallies.argmax(axis=0)[lonely]
    return on, material, band


def draw_inner_lines(frame: Frame, on: np.ndarray, depth: np.ndarray, color: RGB) -> None:
    """Dark lines where one part sits in front of another (arms, horns, keys)."""
    ink = np.array(color, float)
    for axis in (0, 1):
        for shift in (1, -1):
            nearer = shifted(depth, shift, axis)
            behind = on & shifted(on, shift, axis, False) & (depth - nearer > INNER_LINE_GAP)
            frame.rgba[behind, :3] = frame.rgba[behind, :3] * 0.35 + ink * 0.65


def add_outline(frame: Frame, color: RGB) -> Frame:
    """1px outline that picks up a little of the color it borders."""
    mask = frame.rgba[:, :, 3] > 0
    total = np.zeros(mask.shape + (3,))
    count = np.zeros(mask.shape)
    for axis in (0, 1):
        for shift in (1, -1):
            neighbour = shifted(mask, shift, axis, False)
            total += shifted(frame.rgba[:, :, :3], shift, axis) * neighbour[..., None]
            count += neighbour
    edge = ~mask & (count > 0)
    inside = total[edge] / count[edge][:, None]
    frame.rgba[edge, :3] = np.array(color, float) * 0.86 + inside * 0.14
    frame.rgba[edge, 3] = 255
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
