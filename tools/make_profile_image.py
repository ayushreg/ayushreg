"""
Build one tall sky-themed profile image from content/profile.yaml.

Usage:
  python tools/make_profile_image.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import yaml

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
CONTENT = ROOT / "content" / "profile.yaml"
OUT = ASSETS / "profile.png"

W = 1200
MARGIN = 72
MAX_TEXT = W - MARGIN * 2


def load_font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    mapping = {
        "bold": ASSETS / "Poppins-Bold.ttf",
        "semibold": ASSETS / "Poppins-SemiBold.ttf",
        "regular": ASSETS / "Poppins-Regular.ttf",
    }
    path = mapping.get(weight, mapping["regular"])
    if path.exists():
        return ImageFont.truetype(str(path), size)
    fallbacks = [
        r"C:\Windows\Fonts\segoeuib.ttf" if weight != "regular" else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if weight != "regular" else r"C:\Windows\Fonts\arial.ttf",
    ]
    for fb in fallbacks:
        try:
            return ImageFont.truetype(fb, size)
        except OSError:
            continue
    return ImageFont.load_default()


def load_sky(h: int) -> Image.Image:
    candidates = [
        ASSETS / "sky-dense-clouds.png",
        Path(r"C:\Users\regmi\.cursor\projects\c-Users-regmi-OneDrive-Desktop-About-me\assets\sky-dense-clouds.png"),
        ASSETS / "sky-panel-bg.png",
    ]
    src = next((p for p in candidates if p.exists()), None)
    if src is None:
        raise SystemExit("Missing sky background image")
    img = Image.open(src).convert("RGBA")
    # Brighten slightly so white text panels contrast cleanly
    img = ImageEnhance.Brightness(img).enhance(1.05)
    img = ImageEnhance.Color(img).enhance(1.08)
    scale = max(W / img.width, h / img.height)
    nw, nh = int(img.width * scale), int(img.height * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - W) // 2
    top = max(0, (nh - h) // 5)
    return img.crop((left, top, left + W, top + h))


def wrap_lines(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def text_block(
    canvas: Image.Image,
    y: int,
    text: str,
    font: ImageFont.ImageFont,
    *,
    fill=(255, 255, 255, 255),
    center: bool = False,
    max_width: int = MAX_TEXT,
    tracking: int = 10,
    outlined: bool = False,
) -> int:
    """Clean Poppins text. Optional outline only for header on busy sky."""
    draw = ImageDraw.Draw(canvas)
    lines = wrap_lines(draw, text, font, max_width)
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for line in lines:
        tw = od.textlength(line, font=font)
        x = (W - tw) / 2 if center else MARGIN
        if outlined:
            outline = (6, 28, 55, 230)
            for dx, dy in (
                (-3, 0), (3, 0), (0, -3), (0, 3),
                (-2, -2), (2, -2), (-2, 2), (2, 2),
                (-3, -1), (3, -1), (-3, 1), (3, 1),
                (-1, -3), (1, -3), (-1, 3), (1, 3),
            ):
                od.text((x + dx, y + dy), line, font=font, fill=outline)
            od.text((x + 1, y + 2), line, font=font, fill=(0, 0, 0, 110))
        else:
            # subtle drop shadow only
            od.text((x + 1, y + 2), line, font=font, fill=(0, 0, 0, 90))
        od.text((x, y), line, font=font, fill=fill)
        bbox = od.textbbox((0, 0), line, font=font)
        y += (bbox[3] - bbox[1]) + tracking
    canvas.alpha_composite(overlay)
    return y


def paste_deco(canvas: Image.Image, name: str, xy: tuple[int, int], size: int) -> None:
    path = ASSETS / name
    if not path.exists():
        return
    deco = Image.open(path).convert("RGBA")
    deco.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas.alpha_composite(deco, xy)


def solid_panel(canvas: Image.Image, top: int, height: int) -> None:
    """Solid sky-navy panel so text pops (not liquid glass)."""
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rounded_rectangle((40, top, W - 40, top + height), radius=26, fill=(14, 52, 92, 242))
    d.rounded_rectangle((40, top, W - 40, top + height), radius=26, outline=(190, 220, 245, 90), width=2)
    canvas.alpha_composite(overlay)


def measure_block(texts: list[tuple[str, ImageFont.ImageFont, dict]], gap_after: int = 0) -> int:
    temp = Image.new("RGBA", (W, 2000), (0, 0, 0, 0))
    y = 0
    for text, fnt, kwargs in texts:
        y = text_block(temp, y, text, fnt, **kwargs)
        y += gap_after
    return y


def main() -> None:
    data = yaml.safe_load(CONTENT.read_text(encoding="utf-8"))

    # Copy dense sky into assets if needed
    gen_sky = Path(r"C:\Users\regmi\.cursor\projects\c-Users-regmi-OneDrive-Desktop-About-me\assets\sky-dense-clouds.png")
    if gen_sky.exists():
        (ASSETS / "sky-dense-clouds.png").write_bytes(gen_sky.read_bytes())

    title = load_font(56, "bold")
    subtitle = load_font(24, "semibold")
    h1 = load_font(34, "bold")
    h2 = load_font(23, "semibold")
    body = load_font(20, "regular")
    small = load_font(18, "regular")

    estimate_h = 3000
    canvas = load_sky(estimate_h)

    # Scatter more clouds across the page
    cloud_spots = [
        (30, 20, 130), (980, 40, 120), (180, 280, 90), (900, 420, 100),
        (40, 700, 110), (1020, 780, 95), (120, 1100, 100), (950, 1200, 115),
        (60, 1500, 105), (1000, 1600, 90), (500, 200, 70), (700, 950, 80),
    ]
    for x, cy, size in cloud_spots:
        paste_deco(canvas, "cloud.png", (x, cy), size)
    island_spots = [(50, 500, 130), (1000, 1050, 120), (80, 1450, 110)]
    for x, cy, size in island_spots:
        paste_deco(canvas, "island.png" if size > 115 else "island-small.png", (x, cy), size)

    y = 56
    y = text_block(canvas, y, data["name"], title, center=True, tracking=8, outlined=True)
    y += 2
    y = text_block(canvas, y, data["tagline"], subtitle, center=True, fill=(255, 255, 255, 255), tracking=8, outlined=True)
    y += 6
    # Roles line needs extra pop on busy clouds
    roles_font = load_font(22, "semibold")
    y = text_block(
        canvas,
        y,
        data["roles"],
        roles_font,
        center=True,
        fill=(255, 255, 255, 255),
        tracking=8,
        outlined=True,
    )
    y += 26

    # Welcome
    welcome_body = " ".join(data["welcome_body"].split())
    content_h = measure_block([
        (data["welcome_title"], h1, {}),
        (welcome_body, body, {"fill": (245, 250, 255, 255)}),
    ], gap_after=10) + 52
    panel_top = y
    solid_panel(canvas, panel_top, content_h)
    y = panel_top + 26
    y = text_block(canvas, y, data["welcome_title"], h1, tracking=8)
    y += 8
    y = text_block(canvas, y, welcome_body, body, fill=(245, 250, 255, 255), tracking=8)
    y = panel_top + content_h + 22

    # Experience
    parts: list[tuple[str, ImageFont.ImageFont, dict]] = [(data["experience_title"], h1, {})]
    for job in data["experience"]:
        parts.append((job["title"], h2, {}))
        parts.append((" ".join(job["body"].split()), body, {"fill": (245, 250, 255, 255)}))
    # rough measure with gaps
    temp = Image.new("RGBA", (W, 2000), (0, 0, 0, 0))
    ty = 0
    ty = text_block(temp, ty, data["experience_title"], h1, tracking=8)
    ty += 12
    for job in data["experience"]:
        ty = text_block(temp, ty, job["title"], h2, tracking=6)
        ty += 4
        ty = text_block(temp, ty, " ".join(job["body"].split()), body, fill=(245, 250, 255, 255), tracking=7)
        ty += 14
    content_h = ty + 48
    panel_top = y
    solid_panel(canvas, panel_top, content_h)
    y = panel_top + 26
    y = text_block(canvas, y, data["experience_title"], h1, tracking=8)
    y += 12
    for job in data["experience"]:
        y = text_block(canvas, y, job["title"], h2, tracking=6)
        y += 4
        y = text_block(canvas, y, " ".join(job["body"].split()), body, fill=(245, 250, 255, 255), tracking=7)
        y += 14
    y = panel_top + content_h + 22

    # Projects
    col_w = (MAX_TEXT - 36) // 2
    temp = Image.new("RGBA", (W, 1200), (0, 0, 0, 0))
    ty = text_block(temp, 0, data["projects_title"], h1, tracking=8) + 16
    max_col = 0
    for p in data["projects"]:
        ph = 108
        tdraw = ImageDraw.Draw(temp)
        ph += 34
        ph += 26
        ph += len(wrap_lines(tdraw, " ".join(p["body"].split()), body, col_w)) * 28
        max_col = max(max_col, ph)
    content_h = ty + max_col + 40
    panel_top = y
    solid_panel(canvas, panel_top, content_h)
    y = panel_top + 26
    y = text_block(canvas, y, data["projects_title"], h1, tracking=8)
    y += 16
    left_x = MARGIN
    right_x = MARGIN + col_w + 36
    row_y = y

    for idx, p in enumerate(data["projects"]):
        x = left_x if idx == 0 else right_x
        cy = row_y
        logo_path = ASSETS / p["logo"]
        if logo_path.exists():
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((92, 92), Image.Resampling.LANCZOS)
            canvas.alpha_composite(logo, (x + (col_w - logo.width) // 2, cy))
            cy += 104

        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)

        def draw_centered(py: int, text: str, fnt, fill=(255, 255, 255, 255)) -> int:
            tw = od.textlength(text, font=fnt)
            px = x + (col_w - tw) / 2
            od.text((px + 1, py + 2), text, font=fnt, fill=(0, 0, 0, 90))
            od.text((px, py), text, font=fnt, fill=fill)
            bb = od.textbbox((0, 0), text, font=fnt)
            return py + (bb[3] - bb[1]) + 8

        def draw_left(py: int, text: str, fnt, fill=(245, 250, 255, 255)) -> int:
            od.text((x + 1, py + 2), text, font=fnt, fill=(0, 0, 0, 90))
            od.text((x, py), text, font=fnt, fill=fill)
            bb = od.textbbox((0, 0), text, font=fnt)
            return py + (bb[3] - bb[1]) + 7

        cy = draw_centered(cy, p["name"], h2)
        cy = draw_centered(cy, p["stack"], small, fill=(230, 242, 255, 255))
        for line in wrap_lines(od, " ".join(p["body"].split()), body, col_w):
            cy = draw_left(cy, line, body)
        canvas.alpha_composite(overlay)

    y = panel_top + content_h + 22

    # Tech with icons
    icons_path = ASSETS / data.get("tech_icons", "tech-icons.png")
    icons = Image.open(icons_path).convert("RGBA") if icons_path.exists() else None
    icon_h = 0
    if icons is not None:
        # fit to content width, then scale up a bit for presence
        max_w = MAX_TEXT
        scale = min(1.85, max_w / icons.width)
        icons = icons.resize((int(icons.width * scale), int(icons.height * scale)), Image.Resampling.LANCZOS)
        icon_h = icons.height

    temp = Image.new("RGBA", (W, 600), (0, 0, 0, 0))
    ty = text_block(temp, 0, data["tech_title"], h1, tracking=8) + 16 + icon_h
    content_h = ty + 48
    panel_top = y
    solid_panel(canvas, panel_top, content_h)
    y = panel_top + 26
    y = text_block(canvas, y, data["tech_title"], h1, tracking=8)
    y += 14
    if icons is not None:
        ix = (W - icons.width) // 2
        canvas.alpha_composite(icons, (ix, y))
        y += icons.height
    y = panel_top + content_h + 30

    # Extra clouds near bottom
    paste_deco(canvas, "cloud.png", (70, y - 40), 110)
    paste_deco(canvas, "island-small.png", (980, y - 50), 100)
    paste_deco(canvas, "cloud.png", (500, y - 20), 80)

    final_h = min(estimate_h, y + 40)
    final = canvas.crop((0, 0, W, final_h))
    final.convert("RGB").save(OUT, quality=95, optimize=True)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes, {final.size[0]}x{final.size[1]})")


if __name__ == "__main__":
    main()
