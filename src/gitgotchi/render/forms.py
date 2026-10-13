"""3D models for every pet form."""
from dataclasses import dataclass, field

import numpy as np

from gitgotchi.render.raster import Form, Frame, Pose, ellipse, smin

TAU = 2 * np.pi


def capsule(p, a, b, r):
    pa = p - np.asarray(a, float)
    ba = np.asarray(b, float) - np.asarray(a, float)
    h = np.clip((pa @ ba) / (ba @ ba), 0, 1)
    return np.linalg.norm(pa - h[:, None] * ba, axis=1) - r


def rounded_box(p, center, half, r):
    q = np.abs(p - np.asarray(center, float)) - np.asarray(half, float)
    outside = np.linalg.norm(np.maximum(q, 0), axis=1)
    inside = np.minimum(q.max(axis=1), 0)
    return outside + inside - r


def sphere(p, center, r):
    return np.linalg.norm(p - np.asarray(center, float), axis=1) - r


def blinking(t: float, at: float = 0.62, length: float = 0.05) -> bool:
    return at <= t % 1 < at + length


def hop(t: float, hops: int = 2, height: float = 0.14) -> Pose:
    phase = (t * hops) % 1
    lift = 4 * phase * (1 - phase)
    return Pose(
        yaw=0.35 * np.sin(t * TAU),
        bob=height * lift - 0.02,
        squash=0.86 + 0.2 * lift if lift < 0.6 else 1.04,
    )


@dataclass
class Pumpkin(Form):
    """Starting form: a little jack-o'-lantern with a glowing face."""

    name: str = "pumpkin"
    outline: tuple = (58, 22, 18)
    rim: tuple = (140, 40, 90)
    colors: dict = field(
        default_factory=lambda: {
            0: (242, 134, 42),
            1: (206, 98, 30),
            2: (112, 146, 62),
            3: (255, 222, 112),
        }
    )
    emissive: set = field(default_factory=lambda: {3})

    def pose(self, t):
        return hop(t)

    def sdf(self, p, t):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        ribs = 0.042 * np.cos(8 * np.arctan2(z, x))
        flat = np.stack([x, (y + 0.3) * 1.25, z], axis=1)
        body = (np.linalg.norm(flat, axis=1) - (0.68 + ribs)) / 1.25
        stem = capsule(p, (0, 0.12, 0), (0.08, 0.42, 0.02), 0.075)
        return smin(body, stem, 0.04)

    def paint(self, p, n, t):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        out = np.zeros(len(p), dtype=int)
        out[np.cos(8 * np.arctan2(z, x)) < -0.75] = 1
        out[y > 0.17] = 2

        front = z < -0.2
        face = np.zeros(len(p), dtype=bool)
        if not blinking(t):
            for side in (-1, 1):
                cx, top, bottom = side * 0.26, 0.02, -0.2
                within = (y < top) & (y > bottom)
                face |= within & (np.abs(x - cx) < (y - bottom) / (top - bottom) * 0.13)
        upper = -0.37 + 0.55 * x**2
        lower = -0.55 + 1.05 * x**2
        mouth = (np.abs(x) < 0.42) & (y < upper) & (y > lower)
        tooth = (np.abs(np.abs(x) - 0.14) < 0.045) & (y > upper - 0.07)
        face |= mouth & ~tooth
        out[front & face] = 3
        return out


@dataclass
class Ghost(Form):
    """The default friendly spirit."""

    name: str = "ghost"
    colors: dict = field(
        default_factory=lambda: {
            0: (234, 230, 252),
            1: (30, 16, 46),
            2: (255, 255, 255),
            3: (255, 140, 175),
        }
    )

    def sdf(self, p, t):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        yc = np.clip(y, -0.75, 0.3)
        r = 0.62 + 0.18 * np.clip((0.3 - y) / 1.05, 0, 1)
        body = np.sqrt(x**2 + (y - yc) ** 2 + z**2) - r
        hem = -0.66 + 0.1 * np.sin(np.arctan2(z, x) * 5 + t * TAU)
        body = np.maximum(body, hem - y)
        for side in (-1, 1):
            wave = 0.04 * np.sin(t * TAU * 2 + side)
            arm = sphere(p * [1, 1.5, 1], (side * 0.76, -0.1 + wave, 0), 0.19)
            body = smin(body, arm, 0.12)
        return body

    def paint(self, p, n, t):
        return paint_cute_face(p, t, eye_y=0.32)


def paint_cute_face(p, t, eye_y=0.32, eye_x=0.25, cheeks=True):
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    out = np.zeros(len(p), dtype=int)
    front = z < 0
    closed = blinking(t)
    for side in (-1, 1):
        cx = side * eye_x
        if cheeks:
            out[front & ellipse(x, y, side * 0.42, eye_y - 0.2, 0.1, 0.05)] = 3
        if closed:
            out[front & ellipse(x, y, cx, eye_y - 0.03, 0.11, 0.025)] = 1
        else:
            out[front & ellipse(x, y, cx, eye_y, 0.11, 0.16)] = 1
            out[front & ellipse(x, y, cx - 0.04, eye_y + 0.05, 0.04, 0.05)] = 2
    mouth = ellipse(x, y, 0, eye_y - 0.19, 0.08, 0.06) & (y < eye_y - 0.19)
    out[front & mouth] = 1
    return out


@dataclass
class Poltergeist(Form):
    """Unlocked when AI agents write most of the commits: a glitchy spirit
    with keycaps orbiting it."""

    name: str = "poltergeist"
    outline: tuple = (14, 26, 54)
    rim: tuple = (60, 110, 220)
    colors: dict = field(
        default_factory=lambda: {
            0: (172, 206, 250),
            1: (110, 255, 230),
            2: (226, 230, 242),
            3: (250, 250, 255),
            4: (24, 18, 48),
        }
    )
    emissive: set = field(default_factory=lambda: {1})
    opacity: float = 0.86
    keys: int = 4
    glitchy: bool = True

    def pose(self, t):
        return Pose(
            yaw=0.4 * np.sin(t * TAU),
            bob=0.1 + 0.07 * np.sin(t * TAU * 2),
            tilt=0.06 * np.sin(t * TAU),
        )

    def _key_centers(self, t):
        for i in range(self.keys):
            a = -t * TAU + i * TAU / self.keys
            yield np.array([0.98 * np.cos(a), 0.02 + 0.16 * np.sin(a * 2), 0.6 * np.sin(a)])

    def _body(self, p, t):
        d = sphere(p, (0, 0.3, 0), 0.5)
        for k in range(1, 9):
            s = k / 8
            center = (0.3 * np.sin(s * 2.6 + t * TAU) * s, 0.3 - s * 1.12, 0)
            d = smin(d, sphere(p, center, 0.48 * (1 - s) ** 1.15 + 0.04), 0.16)
        for side in (-1, 1):
            wave = 0.05 * np.sin(t * TAU * 2 + side)
            d = smin(d, sphere(p, (side * 0.55, 0.0 + wave, 0), 0.13), 0.18)
        return d

    def _key(self, p, center):
        return rounded_box(p, center, (0.13, 0.08, 0.11), 0.035)

    def sdf(self, p, t):
        d = self._body(p, t)
        for c in self._key_centers(t):
            d = np.minimum(d, self._key(p, c))
        return d

    def paint(self, p, n, t):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        out = np.zeros(len(p), dtype=int)

        for c in self._key_centers(t):
            on_key = self._key(p, c) < 0.01
            out[on_key] = 2
            out[on_key & (n[:, 1] > 0.6)] = 3
            glyph = (np.abs(x - c[0]) < 0.06) & (np.abs(y - c[1] - 0.01) < 0.035)
            out[on_key & (n[:, 2] < -0.6) & glyph] = 1

        body = out == 0
        front = body & (z < -0.1)
        for side in (-1, 1):
            u = x - side * 0.2
            v = y - 0.29 + side * u * 0.5
            out[front & (u**2 / 0.14**2 + v**2 / 0.075**2 < 1)] = 1
        grin = ellipse(x, y, 0, 0.1, 0.13, 0.05) & (y < 0.1)
        out[front & grin] = 4
        return out

    def post(self, frame: Frame, t: float) -> Frame:
        step = int(t * 24)
        if not self.glitchy or step % 8 != 0:
            return frame
        rng = np.random.default_rng(step)
        rgba = frame.rgba
        for _ in range(3):
            row = rng.integers(0, rgba.shape[0] - 3)
            shift = int(rng.choice([-2, -1, 1, 2]))
            rgba[row : row + 2] = np.roll(rgba[row : row + 2], shift, axis=1)
        red = np.roll(rgba[:, :, [0, 3]], -1, axis=1)
        blue = np.roll(rgba[:, :, [2, 3]], 1, axis=1)
        rgba[:, :, 0] = np.maximum(rgba[:, :, 0], red[:, :, 0] * (red[:, :, 1] > 0))
        rgba[:, :, 2] = np.maximum(rgba[:, :, 2], blue[:, :, 0] * (blue[:, :, 1] > 0))
        rgba[:, :, 3] = np.maximum(rgba[:, :, 3], np.maximum(red[:, :, 1], blue[:, :, 1]))
        return frame


def ellipsoid(p, center, radii):
    q = (p - np.asarray(center, float)) / np.asarray(radii, float)
    return (np.linalg.norm(q, axis=1) - 1) * min(radii)


def torus(p, center, major, minor, tilt=0.0):
    q = p - np.asarray(center, float)
    if tilt:
        c, s = np.cos(tilt), np.sin(tilt)
        y, z = q[:, 1].copy(), q[:, 2].copy()
        q[:, 1] = c * y - s * z
        q[:, 2] = s * y + c * z
    ring = np.sqrt(q[:, 0] ** 2 + q[:, 2] ** 2) - major
    return np.sqrt(ring**2 + q[:, 1] ** 2) - minor


def spin_z(p, pivot, angle):
    q = p - np.asarray(pivot, float)
    c, s = np.cos(angle), np.sin(angle)
    out = q.copy()
    out[:, 0] = c * q[:, 0] + s * q[:, 1]
    out[:, 1] = -s * q[:, 0] + c * q[:, 1]
    return out


@dataclass
class Angel(Ghost):
    """High quality path: a ghost with a golden halo and little wings."""

    name: str = "angel"
    rim: tuple = (160, 120, 60)
    colors: dict = field(
        default_factory=lambda: {
            0: (250, 246, 236),
            1: (36, 24, 40),
            2: (255, 255, 255),
            3: (255, 150, 170),
            4: (255, 214, 92),
            5: (226, 236, 255),
        }
    )
    emissive: set = field(default_factory=lambda: {4})

    def _halo(self, p, t):
        return torus(p, (0, 0.98 + 0.03 * np.sin(t * TAU * 2), 0.05), 0.3, 0.06, tilt=-0.55)

    def _wings(self, p, t):
        flap = 0.25 * np.sin(t * TAU * 3)
        d = np.full(len(p), 1e3)
        for side in (-1, 1):
            q = spin_z(p, (side * 0.6, 0.25, 0.3), side * (0.6 + flap))
            d = np.minimum(d, ellipsoid(q, (side * 0.18, 0, 0), (0.34, 0.2, 0.07)))
        return d

    def sdf(self, p, t):
        d = Ghost.sdf(self, p, t)
        return np.minimum(np.minimum(d, self._halo(p, t)), self._wings(p, t))

    def paint(self, p, n, t):
        out = Ghost.paint(self, p, n, t)
        out[self._wings(p, t) < 0.01] = 5
        out[self._halo(p, t) < 0.01] = 4
        return out


@dataclass
class Demon(Form):
    """Chaotic path: horns, a forked tail and burning eyes."""

    name: str = "demon"
    outline: tuple = (20, 6, 14)
    rim: tuple = (220, 60, 40)
    colors: dict = field(
        default_factory=lambda: {
            0: (118, 34, 74),
            1: (255, 120, 48),
            2: (232, 210, 186),
            3: (24, 8, 18),
        }
    )
    emissive: set = field(default_factory=lambda: {1})

    def pose(self, t):
        return Pose(
            yaw=0.5 * np.sin(t * TAU),
            bob=0.05 * np.sin(t * TAU * 2),
            tilt=0.05 * np.sin(t * TAU * 2),
        )

    def _horns(self, p):
        d = np.full(len(p), 1e3)
        for side in (-1, 1):
            for k in range(5):
                s = k / 4
                center = (side * (0.32 + 0.22 * s), 0.62 + 0.42 * s - 0.12 * s * s, -0.02)
                d = smin(d, sphere(p, center, 0.12 * (1 - s) + 0.025), 0.06)
        return d

    def _tail(self, p, t):
        d = np.full(len(p), 1e3)
        for k in range(7):
            s = k / 6
            wag = 0.25 * np.sin(t * TAU * 2 + s * 2) * s
            center = (0.55 * s + wag, -0.55 + 0.35 * s * s, 0.45 + 0.1 * s)
            d = smin(d, sphere(p, center, 0.07), 0.05)
        tip = (0.55 + 0.25 * np.sin(t * TAU * 2 + 2), -0.2, 0.55)
        q = spin_z(p, tip, np.pi / 4)
        return np.minimum(d, rounded_box(q, (0, 0, 0), (0.08, 0.08, 0.02), 0.02))

    def _body(self, p, t):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        yc = np.clip(y, -0.7, 0.28)
        r = 0.6 + 0.12 * np.clip((0.28 - y) / 1.0, 0, 1)
        d = np.sqrt(x**2 + (y - yc) ** 2 + z**2) - r
        hem = -0.62 + 0.16 * np.abs(np.sin(np.arctan2(z, x) * 2.5 + t * TAU))
        return np.maximum(d, hem - y)

    def sdf(self, p, t):
        d = smin(self._body(p, t), self._horns(p), 0.05)
        return np.minimum(d, self._tail(p, t))

    def paint(self, p, n, t):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        out = np.zeros(len(p), dtype=int)
        out[self._horns(p) < 0.012] = 2
        front = (z < 0) & (out == 0)
        for side in (-1, 1):
            u = x - side * 0.24
            v = y - 0.3 - side * u * 0.7
            out[front & (u**2 / 0.13**2 + v**2 / 0.05**2 < 1)] = 1
        grin_top = 0.1 + 0.35 * x**2
        grin = (np.abs(x) < 0.3) & (y < grin_top) & (y > grin_top - 0.09)
        teeth = (np.abs(np.abs(x) - 0.12) < 0.035) & (y > grin_top - 0.06)
        out[front & grin] = 3
        out[front & grin & teeth] = 1
        return out


@dataclass
class Zombie(Form):
    """Too many reverts: a sleepy, stitched-up blob that needs coffee."""

    name: str = "zombie"
    outline: tuple = (22, 34, 24)
    rim: tuple = (120, 60, 140)
    colors: dict = field(
        default_factory=lambda: {
            0: (140, 190, 112),
            1: (26, 30, 24),
            2: (255, 255, 240),
            3: (120, 92, 160),
            4: (60, 74, 54),
        }
    )

    def pose(self, t):
        return Pose(
            yaw=0.3 * np.sin(t * TAU),
            bob=0.03 * np.abs(np.sin(t * TAU * 2)),
            tilt=0.12 * np.sin(t * TAU),
        )

    def sdf(self, p, t):
        body = ellipsoid(p, (0, -0.05, 0), (0.7, 0.78, 0.62))
        for side in (-1, 1):
            reach = 0.04 * np.sin(t * TAU * 2 + side)
            arm = capsule(p, (side * 0.55, -0.12, -0.1), (side * 0.86, 0.02 + reach, -0.62), 0.12)
            body = smin(body, arm, 0.12)
        return body

    def paint(self, p, n, t):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        out = np.zeros(len(p), dtype=int)
        front = z < -0.15
        patch = ellipse(x, y, 0.3, -0.35, 0.16, 0.13) & front
        out[patch] = 3
        stitch_line = (np.abs(y - 0.5 + 0.15 * x) < 0.02) & (np.abs(x + 0.15) < 0.25)
        stitches = (np.abs(((x + 0.15) % 0.1) - 0.05) < 0.015) & (np.abs(y - 0.5 + 0.15 * x) < 0.06) & (np.abs(x + 0.15) < 0.25)
        out[front & (stitch_line | stitches)] = 4
        out[front & ellipse(x, y, -0.24, 0.22, 0.13, 0.15)] = 1
        out[front & ellipse(x, y, -0.27, 0.26, 0.04, 0.05)] = 2
        droop = 0.03 if blinking(t, 0.3, 0.15) else 0.07
        out[front & ellipse(x, y, 0.24, 0.17, 0.11, droop)] = 1
        mouth = (np.abs(x) < 0.16) & (np.abs(y + 0.08 - 0.08 * x) < 0.025)
        out[front & mouth] = 1
        return out


@dataclass
class Wraith(Form):
    """Ultimate form: a hooded cloak with nothing inside but two eyes."""

    name: str = "wraith"
    outline: tuple = (6, 6, 18)
    rim: tuple = (60, 180, 170)
    colors: dict = field(
        default_factory=lambda: {
            0: (58, 52, 104),
            1: (150, 255, 220),
            2: (8, 6, 16),
            3: (40, 36, 78),
        }
    )
    emissive: set = field(default_factory=lambda: {1})

    def pose(self, t):
        return Pose(yaw=0.25 * np.sin(t * TAU), bob=0.12 + 0.06 * np.sin(t * TAU), tilt=0.04 * np.sin(t * TAU * 2))

    def sdf(self, p, t):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        hood = ellipsoid(p, (0, 0.42, 0.02), (0.46, 0.5, 0.46))
        peak = sphere(p, (0, 0.88 + 0.03 * np.sin(t * TAU), 0.18), 0.08)
        hood = smin(hood, peak, 0.25)
        spread = np.clip((0.4 - y) / 1.3, 0, 1)
        cloak = np.sqrt(x**2 + (z - 0.05) ** 2) - (0.4 + 0.42 * spread)
        ang = np.arctan2(z, x)
        tatter = -0.85 + 0.2 * np.abs(np.sin(ang * 4 + t * TAU)) + 0.08 * np.sin(ang * 11 - t * TAU * 2)
        cloak = np.maximum(cloak * 0.8, np.maximum(tatter - y, y - 0.45))
        d = smin(hood, cloak, 0.15)
        opening = ellipsoid(p, (0, 0.36, -0.42), (0.27, 0.3, 0.2))
        return np.maximum(d, -opening)

    def paint(self, p, n, t):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        out = np.zeros(len(p), dtype=int)
        out[y < -0.3] = 3
        inside = ellipsoid(p, (0, 0.36, -0.42), (0.29, 0.32, 0.22)) < 0.02
        out[inside] = 2
        if not blinking(t, 0.4, 0.04):
            for side in (-1, 1):
                out[inside & ellipse(x, y, side * 0.1, 0.36, 0.055, 0.035)] = 1
        return out


FORMS = {
    "egg": Pumpkin,
    "ghost": Ghost,
    "angel": Angel,
    "demon": Demon,
    "zombie": Zombie,
    "wraith": Wraith,
    "poltergeist": Poltergeist,
}


def form_for(name: str) -> Form:
    return FORMS.get(name, Ghost)()
