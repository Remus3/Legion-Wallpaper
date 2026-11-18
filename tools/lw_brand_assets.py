"""Generate LW's original brand assets: icon, README banner, social preview card.

# arch: one geometry -> docs/assets/lw-icon.svg, lw-banner.svg, lw-social-preview.png

THE MARK. An abstract 16:9 wallpaper frame holding a small landscape (sky
gradient, sun, two hills). The left part shows the scene as coarse pixel
blocks - the low-resolution source; the right part shows it smooth - the
restored output; a bright scan bar divides them; a green check badge on the
corner is the gate ladder passing. Every shape is drawn here from numbers: no
third-party artwork, logo or character (operator order 2026-11-17).

The pixel cells are the same scene function sampled at each cell centre, so
the two halves always agree. The SVGs are deterministic text and are pinned
byte-for-byte by tests/test_lw_brand_assets.py. The PNG is drawn with Pillow
from the same geometry (GitHub's social preview takes a raster image; it has
no API, the operator uploads it at Settings > General > Social preview).

    python tools/lw_brand_assets.py --write   # regenerate all three
    python tools/lw_brand_assets.py --check   # exit 1 when a committed SVG drifted
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "docs" / "assets"

# ---- palette --------------------------------------------------------------
BG_TOP, BG_BOTTOM = "#161b22", "#0d1117"
FRAME_STROKE = "#30363d"
SKY = ("#1e2a78", "#8957e5", "#f2a65a")      # top, middle, horizon
SUN_COLOR = "#ffe3b3"
BACK_HILL = "#4b3a8c"
FRONT_HILL = "#1a1f4a"
SCAN = "#58a6ff"
GATE = "#2ea44f"
TEXT, MUTED, ACCENT = "#f0f6fc", "#8b949e", "#58a6ff"

# ---- scene in frame-local unit coordinates (u right, v down) ---------------
SUN = (0.52, 0.42, 0.22)                     # centre u, centre v, radius (in v units)
ASPECT = 16 / 9
SPLIT = 0.52                                 # u of the scan bar
CELLS_V = 6                                  # pixel rows in the low-res part


def _back_hill(u: float) -> float:
    return 0.66 - 0.10 * math.sin(math.pi * (1.2 * u + 0.15))


def _front_hill(u: float) -> float:
    return 0.80 - 0.07 * math.cos(math.pi * (1.6 * u - 0.2))


def _hex(c: str) -> tuple[int, int, int]:
    return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)


def _mix(a: str, b: str, t: float) -> str:
    ra, rb = _hex(a), _hex(b)
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ra, rb, strict=True))


def sky_color(v: float) -> str:
    v = min(max(v, 0.0), 1.0)
    if v < 0.5:
        return _mix(SKY[0], SKY[1], v / 0.5)
    return _mix(SKY[1], SKY[2], (v - 0.5) / 0.5)


def scene_color(u: float, v: float) -> str:
    """Colour of the scene at (u, v); front shapes win."""
    if v >= _front_hill(u):
        return FRONT_HILL
    if v >= _back_hill(u):
        return BACK_HILL
    du = (u - SUN[0]) * ASPECT
    if du * du + (v - SUN[1]) ** 2 <= SUN[2] ** 2:
        return SUN_COLOR
    return sky_color(sky_t(u, v))


def sky_t(u: float, v: float) -> float:
    """Position along the diagonal sky gradient (0 top-left, 1 horizon)."""
    return SKY_DV * v + SKY_DU * (u - 0.5)


SKY_DV, SKY_DU = 0.80, 0.55


def _f(x: float) -> str:
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _hill_path(fn, x0: float, y0: float, w: float, h: float, steps: int = 32) -> str:
    pts = [(x0 + w * i / steps, y0 + h * fn(i / steps)) for i in range(steps + 1)]
    d = "M" + " L".join(f"{_f(x)} {_f(y)}" for x, y in pts)
    return d + f" L{_f(x0 + w)} {_f(y0 + h)} L{_f(x0)} {_f(y0 + h)} Z"


def _mark(x0: float, y0: float, size: float, uid: str) -> list[str]:
    """SVG elements of the mark in a size x size box at (x0, y0)."""
    s = size / 256.0
    fw, fh = 200 * s, 200 * s / ASPECT
    fx, fy = x0 + 28 * s, y0 + (256 * s - fh) / 2 - 6 * s
    split_x = fx + fw * SPLIT
    cell = fh / CELLS_V
    out = [
        f'<rect x="{_f(x0)}" y="{_f(y0)}" width="{_f(size)}" height="{_f(size)}" '
        f'rx="{_f(48 * s)}" fill="url(#{uid}bg)"/>',
        f'<clipPath id="{uid}clip"><rect x="{_f(fx)}" y="{_f(fy)}" width="{_f(fw)}" '
        f'height="{_f(fh)}" rx="{_f(10 * s)}"/></clipPath>',
        f'<g clip-path="url(#{uid}clip)">',
        f'<g id="{uid}restored">',
        f'<rect x="{_f(fx)}" y="{_f(fy)}" width="{_f(fw)}" height="{_f(fh)}" '
        f'fill="url(#{uid}sky)"/>',
        f'<circle cx="{_f(fx + fw * SUN[0])}" cy="{_f(fy + fh * SUN[1])}" '
        f'r="{_f(fh * SUN[2])}" fill="{SUN_COLOR}"/>',
        f'<path d="{_hill_path(_back_hill, fx, fy, fw, fh)}" fill="{BACK_HILL}"/>',
        f'<path d="{_hill_path(_front_hill, fx, fy, fw, fh)}" fill="{FRONT_HILL}"/>',
        "</g>",
        f'<g id="{uid}lowres">',
    ]
    cols = math.ceil((split_x - fx) / cell)
    for j in range(CELLS_V):
        for i in range(cols):
            cx0 = fx + i * cell
            cw = min(cell, split_x - cx0)
            u = (cx0 + cell / 2 - fx) / fw
            v = (j + 0.5) / CELLS_V
            out.append(f'<rect x="{_f(cx0)}" y="{_f(fy + j * cell)}" width="{_f(cw + 0.3 * s)}" '
                       f'height="{_f(cell + 0.3 * s)}" fill="{scene_color(u, v)}"/>')
    out += [
        "</g>",
        "</g>",
        f'<rect id="{uid}frame" x="{_f(fx)}" y="{_f(fy)}" width="{_f(fw)}" height="{_f(fh)}" '
        f'rx="{_f(10 * s)}" fill="none" stroke="{FRAME_STROKE}" stroke-width="{_f(4 * s)}"/>',
        f'<g id="{uid}scanbar">',
        f'<rect x="{_f(split_x - 7 * s)}" y="{_f(fy - 8 * s)}" width="{_f(14 * s)}" '
        f'height="{_f(fh + 16 * s)}" rx="{_f(7 * s)}" fill="{SCAN}" opacity="0.25"/>',
        f'<rect x="{_f(split_x - 2 * s)}" y="{_f(fy - 8 * s)}" width="{_f(4 * s)}" '
        f'height="{_f(fh + 16 * s)}" rx="{_f(2 * s)}" fill="{SCAN}"/>',
        "</g>",
    ]
    gx, gy, gr = fx + fw - 8 * s, fy + fh + 4 * s, 26 * s
    out += [
        f'<g id="{uid}gate">',
        f'<circle cx="{_f(gx)}" cy="{_f(gy)}" r="{_f(gr + 6 * s)}" fill="{BG_BOTTOM}"/>',
        f'<circle cx="{_f(gx)}" cy="{_f(gy)}" r="{_f(gr)}" fill="{GATE}"/>',
        f'<path d="M{_f(gx - 12 * s)} {_f(gy + 1 * s)} L{_f(gx - 3 * s)} {_f(gy + 10 * s)} '
        f'L{_f(gx + 13 * s)} {_f(gy - 9 * s)}" fill="none" stroke="#ffffff" '
        f'stroke-width="{_f(6 * s)}" stroke-linecap="round" stroke-linejoin="round"/>',
        "</g>",
    ]
    return out


def _defs(uid: str, size: float, y0: float, fy: float, fh: float) -> list[str]:
    s = size / 256.0
    fw = 200 * s
    fx = (BANNER_MARK_X if uid else 0) + 28 * s
    # t(x, y) = SKY_DV (y - fy) / fh + SKY_DU ((x - fx) / fw - 0.5); the gradient
    # runs along grad t from the point where t = 0 to the point where t = 1.
    gx, gy = SKY_DU / fw, SKY_DV / fh
    g2 = gx * gx + gy * gy
    t0 = -SKY_DU * 0.5
    p1 = (fx + gx * (0 - t0) / g2, fy + gy * (0 - t0) / g2)
    p2 = (fx + gx * (1 - t0) / g2, fy + gy * (1 - t0) / g2)
    return [
        "<defs>",
        f'<linearGradient id="{uid}bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG_BOTTOM}"/>'
        "</linearGradient>",
        f'<linearGradient id="{uid}sky" gradientUnits="userSpaceOnUse" '
        f'x1="{_f(p1[0])}" y1="{_f(p1[1])}" x2="{_f(p2[0])}" y2="{_f(p2[1])}">'
        f'<stop offset="0" stop-color="{SKY[0]}"/><stop offset="0.5" stop-color="{SKY[1]}"/>'
        f'<stop offset="1" stop-color="{SKY[2]}"/></linearGradient>',
        "</defs>",
    ]


def _frame_geom(y0: float, size: float) -> tuple[float, float]:
    s = size / 256.0
    fh = 200 * s / ASPECT
    return y0 + (256 * s - fh) / 2 - 6 * s, fh


def _svg(w: int, h: int, title: str, body: list[str]) -> str:
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-labelledby="t">')
    return "\n".join([head, f'<title id="t">{title}</title>', *body, "</svg>"]) + "\n"


def icon_svg() -> str:
    """256 x 256 icon. Element ids are bare (frame, lowres, ...)."""
    fy, fh = _frame_geom(0, 256)
    return _svg(256, 256, "Legion Wallpaper icon",
                _defs("", 256, 0, fy, fh) + _mark(0, 0, 256, ""))


BANNER_W, BANNER_H = 1280, 320
BANNER_MARK_X = 48.0
STAGES = ("intake", "first pass", "cleaning", "final", "last pass", "end review")
TAGLINE = "Staged, self-auditing restoration for wallpaper art"
SUBLINE = "one upscale - masked inpainting - face repair - gate ladder - 2560x1440"


def banner_svg() -> str:
    """1280 x 320 README banner: the mark, the name, the tagline, the stages."""
    size, x0, y0 = 240.0, BANNER_MARK_X, 40.0
    fy, fh = _frame_geom(y0, size)
    body = [f'<rect width="{BANNER_W}" height="{BANNER_H}" rx="24" fill="{BG_BOTTOM}"/>']
    body += _defs("b", size, y0, fy, fh) + _mark(x0, y0, size, "b")
    tx = 332
    sans = 'font-family="Segoe UI, Helvetica, Arial, sans-serif"'
    mono = 'font-family="Consolas, Menlo, monospace"'
    body += [
        f'<text x="{tx}" y="132" {sans} font-size="64" font-weight="700" '
        f'fill="{TEXT}">Legion Wallpaper</text>',
        f'<text x="{tx}" y="180" {sans} font-size="28" fill="{MUTED}">{TAGLINE}</text>',
        f'<text x="{tx}" y="222" {mono} font-size="19" fill="{ACCENT}">{SUBLINE}</text>',
    ]
    x = tx
    for i, name in enumerate(STAGES):
        w = 18 + 10.5 * len(name)
        body.append(f'<rect x="{_f(x)}" y="246" width="{_f(w)}" height="30" rx="8" '
                    f'fill="#161b22" stroke="{FRAME_STROKE}"/>')
        body.append(f'<text x="{_f(x + w / 2)}" y="266" {mono} font-size="16" '
                    f'text-anchor="middle" fill="{TEXT}">{name}</text>')
        x += w + (22 if i < len(STAGES) - 1 else 0)
        if i < len(STAGES) - 1:
            body.append(f'<text x="{_f(x - 11)}" y="266" {mono} font-size="16" '
                        f'text-anchor="middle" fill="#d29922">&gt;</text>')
    return _svg(BANNER_W, BANNER_H, "Legion Wallpaper banner", body)


# ---- raster card (Pillow) -------------------------------------------------

def _font(names: tuple[str, ...], px: int):
    from PIL import ImageFont
    for n in names:
        for base in (Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype/dejavu")):
            p = base / n
            if p.is_file():
                return ImageFont.truetype(str(p), px)
    return ImageFont.load_default(size=px)


def _draw_mark(img, x0: float, y0: float, size: float) -> None:
    from PIL import Image, ImageDraw
    s = size / 256.0
    d = ImageDraw.Draw(img)
    fw, fh = 200 * s, 200 * s / ASPECT
    fx, fy = x0 + 28 * s, y0 + (256 * s - fh) / 2 - 6 * s
    split_x = fx + fw * SPLIT
    # background tile: vertical gradient inside a rounded square
    tile = Image.new("RGB", (int(size), int(size)))
    td = ImageDraw.Draw(tile)
    for yy in range(int(size)):
        td.line([(0, yy), (int(size), yy)], fill=_hex(_mix(BG_TOP, BG_BOTTOM, yy / size)))
    m = Image.new("L", tile.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, int(size) - 1, int(size) - 1],
                                        radius=int(48 * s), fill=255)
    img.paste(tile, (int(x0), int(y0)), m)
    # scene: smooth on the right, cells on the left, all clipped to the frame
    scene = Image.new("RGB", (int(fw), int(fh)))
    sd = ImageDraw.Draw(scene)
    for yy in range(int(fh)):
        for xx in range(0, int(fw), 2):
            sd.line([(xx, yy), (xx + 1, yy)], fill=_hex(sky_color(sky_t(xx / fw, yy / fh))))
    r = fh * SUN[2]
    sd.ellipse([fw * SUN[0] - r, fh * SUN[1] - r, fw * SUN[0] + r, fh * SUN[1] + r],
               fill=_hex(SUN_COLOR))
    for fn, col in ((_back_hill, BACK_HILL), (_front_hill, FRONT_HILL)):
        pts = [(fw * i / 64, fh * fn(i / 64)) for i in range(65)] + [(fw, fh), (0, fh)]
        sd.polygon(pts, fill=_hex(col))
    cell = fh / CELLS_V
    cols = math.ceil((split_x - fx) / cell)
    for j in range(CELLS_V):
        for i in range(cols):
            cx0 = i * cell
            cw = min(cell, split_x - fx - cx0)
            u = (cx0 + cell / 2) / fw
            sd.rectangle([cx0, j * cell, cx0 + cw, (j + 1) * cell],
                         fill=_hex(scene_color(u, (j + 0.5) / CELLS_V)))
    sm = Image.new("L", scene.size, 0)
    ImageDraw.Draw(sm).rounded_rectangle([0, 0, scene.size[0] - 1, scene.size[1] - 1],
                                         radius=int(10 * s), fill=255)
    img.paste(scene, (int(fx), int(fy)), sm)
    d.rounded_rectangle([fx, fy, fx + fw, fy + fh], radius=int(10 * s),
                        outline=_hex(FRAME_STROKE), width=max(1, int(4 * s)))
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle(
        [split_x - 7 * s, fy - 8 * s, split_x + 7 * s, fy + fh + 8 * s],
        radius=int(7 * s), fill=(*_hex(SCAN), 64))
    img.paste(Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB"))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([split_x - 2 * s, fy - 8 * s, split_x + 2 * s, fy + fh + 8 * s],
                        radius=int(2 * s), fill=_hex(SCAN))
    gx, gy, gr = fx + fw - 8 * s, fy + fh + 4 * s, 26 * s
    d.ellipse([gx - gr - 6 * s, gy - gr - 6 * s, gx + gr + 6 * s, gy + gr + 6 * s],
              fill=_hex(BG_BOTTOM))
    d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill=_hex(GATE))
    d.line([(gx - 12 * s, gy + 1 * s), (gx - 3 * s, gy + 10 * s), (gx + 13 * s, gy - 9 * s)],
           fill=(255, 255, 255), width=int(6 * s), joint="curve")


def render_social_png(out: Path, scale: int = 2) -> None:
    """1280 x 640 social preview, drawn at `scale`x and downsampled."""
    from PIL import Image, ImageDraw
    W, H = 1280 * scale, 640 * scale
    img = Image.new("RGB", (W, H), _hex(BG_BOTTOM))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 6 * scale], fill=_hex(ACCENT))
    _draw_mark(img, 72 * scale, 168 * scale, 304 * scale)
    d = ImageDraw.Draw(img)
    sans_b = _font(("segoeuib.ttf", "DejaVuSans-Bold.ttf"), 76 * scale)
    sans = _font(("segoeui.ttf", "DejaVuSans.ttf"), 32 * scale)
    mono = _font(("consola.ttf", "DejaVuSansMono.ttf"), 22 * scale)
    tx = 432 * scale
    d.text((tx, 200 * scale), "Legion Wallpaper", font=sans_b, fill=_hex(TEXT))
    d.text((tx, 300 * scale), TAGLINE.replace("restoration ", "restoration\n"),
           font=sans, fill=_hex(MUTED), spacing=8 * scale)
    d.text((tx, 400 * scale), "one upscale - masked inpainting - face repair",
           font=mono, fill=_hex(ACCENT))
    d.text((tx, 432 * scale), "metric + vision gate ladder - 2560x1440 PNG",
           font=mono, fill=_hex(ACCENT))
    chip = _font(("consola.ttf", "DejaVuSansMono.ttf"), 18 * scale)
    x = tx
    for label in ("Apache-2.0", "Python 3.14", "TDD + CI"):
        w = d.textlength(label, font=chip) + 24 * scale
        d.rounded_rectangle([x, 492 * scale, x + w, 528 * scale], radius=6 * scale,
                            fill=_hex("#161b22"), outline=_hex(FRAME_STROKE), width=scale)
        d.text((x + 12 * scale, 499 * scale), label, font=chip, fill=_hex(MUTED))
        x += w + 12 * scale
    card = img.resize((1280, 640), Image.LANCZOS)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp.png")
    card.save(tmp, "PNG", optimize=True)
    tmp.replace(out)


def _targets() -> dict[str, str]:
    return {"lw-icon.svg": icon_svg(), "lw-banner.svg": banner_svg()}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="regenerate every asset")
    g.add_argument("--check", action="store_true", help="exit 1 on SVG drift or a missing PNG")
    a = ap.parse_args(argv)
    if a.write:
        ASSETS.mkdir(parents=True, exist_ok=True)
        for name, text in _targets().items():
            tmp = ASSETS / (name + ".tmp")
            tmp.write_bytes(text.encode("ascii"))
            tmp.replace(ASSETS / name)
        render_social_png(ASSETS / "lw-social-preview.png")
        print(f"wrote {len(_targets()) + 1} assets to {ASSETS}")
        return 0
    bad = [n for n, t in _targets().items()
           if not (ASSETS / n).is_file() or (ASSETS / n).read_bytes() != t.encode("ascii")]
    if not (ASSETS / "lw-social-preview.png").is_file():
        bad.append("lw-social-preview.png")
    for n in bad:
        print(f"DRIFT {n}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
