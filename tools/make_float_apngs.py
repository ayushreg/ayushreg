"""Build transparent animated PNGs (APNG) that autoplay on GitHub."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image

dst = Path(r"C:\Users\regmi\OneDrive\Desktop\About me\ayushreg-profile\assets")


def resize_max(im: Image.Image, max_w: int) -> Image.Image:
    w, h = im.size
    if w <= max_w:
        return im
    nh = max(1, int(h * (max_w / w)))
    return im.resize((max_w, nh), Image.Resampling.LANCZOS)


def make_bob_apng(
    sprite: Image.Image,
    out: Path,
    canvas: tuple[int, int],
    amplitude: float,
    drift: float,
    frames: int = 20,
    duration: int = 70,
    phase: float = 0.0,
) -> None:
    cw, ch = canvas
    sw, sh = sprite.size
    out_frames: list[Image.Image] = []
    for i in range(frames):
        t = i / frames * 2 * math.pi + phase
        dx = int(math.sin(t) * drift)
        dy = int(math.cos(t) * amplitude)
        frame = Image.new("RGBA", canvas, (0, 0, 0, 0))
        x = (cw - sw) // 2 + dx
        y = (ch - sh) // 2 + dy
        frame.alpha_composite(sprite, (max(0, x), max(0, y)))
        out_frames.append(frame)

    out_frames[0].save(
        out,
        save_all=True,
        append_images=out_frames[1:],
        duration=duration,
        loop=0,
        disposal=2,
        optimize=False,
        default_image=False,
    )
    print("wrote", out.name, out.stat().st_size)


def make_strip_apng(out: Path) -> None:
    cloud = resize_max(Image.open(dst / "cloud.png").convert("RGBA"), 110)
    cloud2 = resize_max(Image.open(dst / "cloud.png").convert("RGBA"), 90)
    island = resize_max(Image.open(dst / "island.png").convert("RGBA"), 120)
    island2 = resize_max(Image.open(dst / "island-small.png").convert("RGBA"), 90)

    W, H = 900, 160
    n = 24
    sprites = [
        (cloud, 40, 25, 8, 16, 0.0),
        (island, 220, 30, 11, 5, 1.1),
        (cloud2, 430, 18, 7, 14, 2.3),
        (island2, 620, 40, 10, 4, 3.5),
        (cloud, 760, 28, 9, 12, 4.7),
    ]
    frames: list[Image.Image] = []
    for i in range(n):
        base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for sprite, bx, by, amp, drift, phase in sprites:
            t = i / n * 2 * math.pi + phase
            x = int(bx + math.sin(t) * drift)
            y = int(by + math.cos(t) * amp)
            x = max(0, min(W - sprite.size[0], x))
            y = max(0, min(H - sprite.size[1], y))
            base.alpha_composite(sprite, (x, y))
        frames.append(base)

    frames[0].save(
        out,
        save_all=True,
        append_images=frames[1:],
        duration=70,
        loop=0,
        disposal=2,
        optimize=False,
        default_image=False,
    )
    print("wrote", out.name, out.stat().st_size)


def main() -> None:
    cloud = resize_max(Image.open(dst / "cloud.png").convert("RGBA"), 150)
    cloud_sm = resize_max(Image.open(dst / "cloud.png").convert("RGBA"), 100)
    island = resize_max(Image.open(dst / "island.png").convert("RGBA"), 140)
    island_sm = resize_max(Image.open(dst / "island-small.png").convert("RGBA"), 100)

    make_bob_apng(cloud, dst / "cloud-float.png", (190, 150), amplitude=9, drift=12, phase=0)
    make_bob_apng(cloud_sm, dst / "cloud-float-sm.png", (130, 110), amplitude=7, drift=9, phase=1.2)
    make_bob_apng(island, dst / "island-float.png", (190, 180), amplitude=12, drift=5, phase=0.5)
    make_bob_apng(island_sm, dst / "island-float-sm.png", (140, 130), amplitude=10, drift=4, phase=2.0)
    make_strip_apng(dst / "sky-float-strip.png")

    # Remove old opaque GIFs / unused svg attempts if present
    for name in [
        "cloud-float.gif",
        "cloud-float-sm.gif",
        "island-float.gif",
        "island-float-sm.gif",
        "sky-float-strip.gif",
        "cloud-float.svg",
        "cloud-float-sm.svg",
        "island-float.svg",
        "island-float-sm.svg",
        "sky-float-strip.svg",
    ]:
        p = dst / name
        if p.exists():
            p.unlink()
            print("removed", name)


if __name__ == "__main__":
    main()
