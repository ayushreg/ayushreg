from PIL import Image
from pathlib import Path
import math

src = Path(r"C:\Users\regmi\.cursor\projects\c-Users-regmi-OneDrive-Desktop-About-me\assets")
dst = Path(r"C:\Users\regmi\OneDrive\Desktop\About me\ayushreg-profile\assets")
dst.mkdir(parents=True, exist_ok=True)

cloud = Image.open(src / "cloud.png").convert("RGBA")
island = Image.open(src / "island.png").convert("RGBA")
island_small = Image.open(src / "island-small.png").convert("RGBA")


def resize_max(im, max_w=None, max_h=None):
    w, h = im.size
    scale = 1.0
    if max_w:
        scale = min(scale, max_w / w)
    if max_h:
        scale = min(scale, max_h / h)
    if scale != 1.0:
        im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
    return im


cloud_sm = resize_max(cloud, max_w=220)
cloud_md = resize_max(cloud, max_w=160)
cloud_tiny = resize_max(cloud, max_w=110)
island_md = resize_max(island, max_w=200)
island_sm = resize_max(island_small, max_w=140)
island_tiny = resize_max(island, max_w=120)

cloud_sm.save(dst / "cloud.png")
island_md.save(dst / "island.png")
island_sm.save(dst / "island-small.png")


def rgba_to_gif_frames(frames_rgba):
    """Convert RGBA frames to palette GIFs with transparency."""
    out = []
    for frame in frames_rgba:
        # Composite onto near-white then mark white-ish as transparent? Better: quantize with alpha
        alpha = frame.split()[-1]
        # Use a rare color as transparent key
        bg = Image.new("RGBA", frame.size, (1, 2, 3, 255))
        composed = Image.alpha_composite(bg, frame)
        pal = composed.convert("P", palette=Image.Palette.ADAPTIVE, colors=255)
        # find palette index closest to key color
        mask = alpha.point(lambda a: 255 if a < 20 else 0)
        pal.info["transparency"] = 255  # temporary
        # Put transparent pixels to index 0 after remapping
        datas = pal.getdata()
        # Simpler approach: paste with disposal using RGBA save via pillow gif
        out.append(composed.convert("P", palette=Image.Palette.ADAPTIVE, colors=255))
    return out


SKY = (214, 236, 250, 255)  # soft sky blue so GIF frames look clean on GitHub


def make_bob_gif(sprite, out_path, canvas=(260, 220), amplitude=12, frames=16, duration=90, drift=8):
    frames_out = []
    sw, sh = sprite.size
    cw, ch = canvas
    for i in range(frames):
        t = i / frames * 2 * math.pi
        dx = int(math.sin(t) * drift)
        dy = int(math.cos(t) * amplitude)
        frame = Image.new("RGBA", canvas, SKY)
        x = (cw - sw) // 2 + dx
        y = (ch - sh) // 2 + dy
        frame.paste(sprite, (x, y), sprite)
        frames_out.append(frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=256))

    frames_out[0].save(
        out_path,
        save_all=True,
        append_images=frames_out[1:],
        duration=duration,
        loop=0,
        disposal=2,
        optimize=False,
    )
    print("wrote", out_path.name, out_path.stat().st_size)


make_bob_gif(cloud_sm, dst / "cloud-float.gif", canvas=(280, 200), amplitude=10, drift=14, frames=18, duration=80)
make_bob_gif(cloud_tiny, dst / "cloud-float-sm.gif", canvas=(160, 120), amplitude=8, drift=10, frames=16, duration=90)
make_bob_gif(island_md, dst / "island-float.gif", canvas=(280, 260), amplitude=14, drift=6, frames=20, duration=85)
make_bob_gif(island_tiny, dst / "island-float-sm.gif", canvas=(180, 170), amplitude=11, drift=5, frames=18, duration=95)

# Wide sky strip
W, H = 900, 180
nframes = 24
sprites = [
    (cloud_tiny, 40, 30, 9, 16, 0.0),
    (cloud_md, 280, 20, 7, 18, 1.2),
    (island_tiny, 520, 35, 12, 5, 2.1),
    (cloud_tiny, 700, 55, 8, 12, 3.4),
    (island_sm, 160, 70, 10, 4, 4.0),
]
strip_frames = []
for i in range(nframes):
    base = Image.new("RGBA", (W, H), SKY)
    for sprite, bx, by, amp, drift, phase in sprites:
        t = i / nframes * 2 * math.pi + phase
        x = int(bx + math.sin(t) * drift)
        y = int(by + math.cos(t) * amp)
        x = max(0, min(W - sprite.size[0], x))
        y = max(0, min(H - sprite.size[1], y))
        base.alpha_composite(sprite, (x, y))
    strip_frames.append(base.convert("P", palette=Image.Palette.ADAPTIVE, colors=256))

out = dst / "sky-float-strip.gif"
strip_frames[0].save(
    out,
    save_all=True,
    append_images=strip_frames[1:],
    duration=80,
    loop=0,
    disposal=2,
    optimize=False,
)
print("wrote", out.name, out.stat().st_size)
print("done")
