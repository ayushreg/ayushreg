"""Build transparent animated SVG floaters (autoplay, no solid backgrounds)."""
from __future__ import annotations

import base64
import math
from pathlib import Path

from PIL import Image

dst = Path(r"C:\Users\regmi\OneDrive\Desktop\About me\ayushreg-profile\assets")


def b64_png(path: Path, max_w: int) -> tuple[str, int, int]:
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    if w > max_w:
        nh = max(1, int(h * (max_w / w)))
        im = im.resize((max_w, nh), Image.Resampling.LANCZOS)
        w, h = im.size
    from io import BytesIO

    buf = BytesIO()
    im.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii"), w, h


def float_svg(
    out: Path,
    img_b64: str,
    w: int,
    h: int,
    canvas_w: int,
    canvas_h: int,
    amp: float,
    drift: float,
    dur: float,
    phase_deg: float = 0,
) -> None:
    # Keep padding so motion stays inside viewBox
    cx = (canvas_w - w) / 2
    cy = (canvas_h - h) / 2
    # SMIL path for gentle float
    values = []
    for i in range(9):
        t = i / 8 * 2 * math.pi + math.radians(phase_deg)
        x = cx + math.sin(t) * drift
        y = cy + math.cos(t) * amp
        values.append(f"{x:.1f},{y:.1f}")
    values_str = ";".join(values)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" viewBox="0 0 {canvas_w} {canvas_h}">
  <image href="data:image/png;base64,{img_b64}" width="{w}" height="{h}" x="0" y="0">
    <animateTransform attributeName="transform" type="translate"
      values="{values_str}"
      keyTimes="0;0.125;0.25;0.375;0.5;0.625;0.75;0.875;1"
      dur="{dur}s" repeatCount="indefinite" calcMode="spline"
      keySplines="0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1"/>
  </image>
</svg>
'''
    out.write_text(svg, encoding="utf-8")
    print("wrote", out.name, out.stat().st_size)


def strip_svg(out: Path) -> None:
    cloud_b64, cw, ch = b64_png(dst / "cloud.png", 110)
    island_b64, iw, ih = b64_png(dst / "island.png", 120)
    island2_b64, i2w, i2h = b64_png(dst / "island-small.png", 90)
    cloud2_b64, c2w, c2h = b64_png(dst / "cloud.png", 90)

    items = [
        (cloud_b64, cw, ch, 30, 25, 8, 18, 7.0, 0),
        (island_b64, iw, ih, 200, 40, 12, 6, 8.5, 40),
        (cloud2_b64, c2w, c2h, 420, 20, 7, 14, 6.5, 120),
        (island2_b64, i2w, i2h, 620, 45, 10, 5, 9.0, 200),
        (cloud_b64, cw, ch, 780, 30, 9, 16, 7.5, 280),
    ]

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="160" viewBox="0 0 900 160">',
        "  <!-- transparent sky decorations -->",
    ]
    for b64, w, h, bx, by, amp, drift, dur, phase in items:
        values = []
        for i in range(9):
            t = i / 8 * 2 * math.pi + math.radians(phase)
            x = bx + math.sin(t) * drift
            y = by + math.cos(t) * amp
            values.append(f"{x:.1f},{y:.1f}")
        values_str = ";".join(values)
        parts.append(
            f'''  <image href="data:image/png;base64,{b64}" width="{w}" height="{h}" x="0" y="0">
    <animateTransform attributeName="transform" type="translate"
      values="{values_str}"
      keyTimes="0;0.125;0.25;0.375;0.5;0.625;0.75;0.875;1"
      dur="{dur}s" repeatCount="indefinite" calcMode="spline"
      keySplines="0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1"/>
  </image>'''
        )
    parts.append("</svg>\n")
    out.write_text("\n".join(parts), encoding="utf-8")
    print("wrote", out.name, out.stat().st_size)


def main() -> None:
    cloud_b64, cw, ch = b64_png(dst / "cloud.png", 160)
    island_b64, iw, ih = b64_png(dst / "island.png", 150)
    island_sm_b64, isw, ish = b64_png(dst / "island-small.png", 110)
    cloud_sm_b64, csw, csh = b64_png(dst / "cloud.png", 110)

    float_svg(dst / "cloud-float.svg", cloud_b64, cw, ch, 200, 160, amp=9, drift=12, dur=6.5)
    float_svg(dst / "cloud-float-sm.svg", cloud_sm_b64, csw, csh, 140, 110, amp=7, drift=9, dur=5.8, phase_deg=90)
    float_svg(dst / "island-float.svg", island_b64, iw, ih, 200, 190, amp=12, drift=5, dur=7.5)
    float_svg(dst / "island-float-sm.svg", island_sm_b64, isw, ish, 150, 140, amp=10, drift=4, dur=8.0, phase_deg=180)
    strip_svg(dst / "sky-float-strip.svg")

    # Remove opaque GIFs so they aren't used by accident
    for name in [
        "cloud-float.gif",
        "cloud-float-sm.gif",
        "island-float.gif",
        "island-float-sm.gif",
        "sky-float-strip.gif",
    ]:
        p = dst / name
        if p.exists():
            p.unlink()
            print("removed", name)


if __name__ == "__main__":
    main()
