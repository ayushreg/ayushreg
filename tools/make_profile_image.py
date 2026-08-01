"""
Build one tall sky-themed profile image from content/profile.yaml.

Apple-inspired liquid glass panels + crisp dark typography.

Usage:
  python tools/make_profile_image.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import yaml

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
CONTENT = ROOT / "content" / "profile.yaml"
OUT = ASSETS / "profile.png"

W = 1200
MARGIN = 78
MAX_TEXT = W - MARGIN * 2
PAD_X = 40  # panel inset from canvas edge
RADIUS = 28

# Apple-like ink on light glass
INK = (18, 28, 48, 255)
INK_SECONDARY = (45, 62, 90, 255)
INK_MUTED = (70, 90, 120, 255)


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
    img = ImageEnhance.Brightness(img).enhance(1.06)
    img = ImageEnhance.Color(img).enhance(1.1)
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
    fill=INK,
    center: bool = False,
    max_width: int = MAX_TEXT,
    tracking: int = 9,
) -> int:
    """Crisp text - no fat outlines. Tiny soft shadow only."""
    draw = ImageDraw.Draw(canvas)
    lines = wrap_lines(draw, text, font, max_width)
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for line in lines:
        tw = od.textlength(line, font=font)
        x = (W - tw) / 2 if center else MARGIN
        od.text((x, y + 1), line, font=font, fill=(255, 255, 255, 70))  # light under-glow
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


def rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    return mask


def liquid_glass_panel(canvas: Image.Image, top: int, height: int, radius: int = RADIUS) -> None:
    """
    Apple-like liquid glass:
    - blurred backdrop of the sky behind the panel
    - frosted light tint
    - specular top highlight
    - soft rim + drop shadow
    Text drawn AFTER this stays crisp on top.
    """
    left, right = PAD_X, W - PAD_X
    width = right - left
    # soft drop shadow
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((left + 4, top + 8, right + 4, top + height + 8), radius=radius, fill=(10, 30, 55, 55))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    canvas.alpha_composite(shadow)

    # crop + blur the sky under the panel for frost
    y0 = max(0, top)
    y1 = min(canvas.height, top + height)
    region = canvas.crop((left, y0, right, y1)).filter(ImageFilter.GaussianBlur(18))
    # brighten frost slightly
    region = ImageEnhance.Brightness(region).enhance(1.12)
    region = ImageEnhance.Contrast(region).enhance(0.92)

    frost = Image.new("RGBA", region.size, (0, 0, 0, 0))
    # stronger frost so dark text stays Apple-crisp on bright clouds
    tint = Image.new("RGBA", region.size, (242, 248, 255, 188))
    frost = Image.alpha_composite(region.convert("RGBA"), tint)
    frost = Image.alpha_composite(frost, Image.new("RGBA", region.size, (190, 215, 240, 40)))

    mask = rounded_mask(frost.size, radius)
    panel = Image.new("RGBA", frost.size, (0, 0, 0, 0))
    panel.paste(frost, (0, 0), mask)

    # specular highlight strip at top (Apple shine)
    shine = Image.new("RGBA", frost.size, (0, 0, 0, 0))
    sh = ImageDraw.Draw(shine)
    sh.rounded_rectangle((0, 0, frost.size[0] - 1, max(40, frost.size[1] // 4)), radius=radius, fill=(255, 255, 255, 55))
    shine = shine.filter(ImageFilter.GaussianBlur(8))
    panel = Image.alpha_composite(panel, Image.composite(shine, Image.new("RGBA", frost.size, (0, 0, 0, 0)), mask))

    # crisp rim light
    rim = Image.new("RGBA", frost.size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(rim)
    rd.rounded_rectangle((1, 1, frost.size[0] - 2, frost.size[1] - 2), radius=radius - 1, outline=(255, 255, 255, 170), width=2)
    rd.rounded_rectangle((2, 2, frost.size[0] - 3, frost.size[1] - 3), radius=radius - 2, outline=(180, 210, 240, 70), width=1)
    panel = Image.alpha_composite(panel, rim)

    canvas.alpha_composite(panel, (left, y0))


def main() -> None:
    data = yaml.safe_load(CONTENT.read_text(encoding="utf-8"))

    gen_sky = Path(r"C:\Users\regmi\.cursor\projects\c-Users-regmi-OneDrive-Desktop-About-me\assets\sky-dense-clouds.png")
    if gen_sky.exists():
        (ASSETS / "sky-dense-clouds.png").write_bytes(gen_sky.read_bytes())

    title = load_font(54, "bold")
    subtitle = load_font(23, "semibold")
    roles_f = load_font(22, "semibold")
    h1 = load_font(32, "bold")
    h2 = load_font(22, "semibold")
    body = load_font(19, "regular")
    small = load_font(17, "regular")

    estimate_h = 3200
    canvas = load_sky(estimate_h)

    cloud_spots = [
        (30, 20, 130), (980, 40, 120), (180, 280, 90), (900, 420, 100),
        (40, 700, 110), (1020, 780, 95), (120, 1100, 100), (950, 1200, 115),
        (60, 1500, 105), (1000, 1600, 90), (500, 200, 70), (700, 950, 80),
    ]
    for x, cy, size in cloud_spots:
        paste_deco(canvas, "cloud.png", (x, cy), size)
    for x, cy, size in [(50, 500, 130), (1000, 1050, 120), (80, 1450, 110)]:
        paste_deco(canvas, "island.png" if size > 115 else "island-small.png", (x, cy), size)

    # ----- Header on liquid glass so roles are readable -----
    header_top = 40
    # measure header
    temp = Image.new("RGBA", (W, 400), (0, 0, 0, 0))
    ty = 0
    ty = text_block(temp, ty, data["name"], title, center=True, fill=INK, tracking=6)
    ty += 4
    ty = text_block(temp, ty, data["tagline"], subtitle, center=True, fill=INK_SECONDARY, tracking=6)
    ty += 6
    ty = text_block(temp, ty, data["roles"], roles_f, center=True, fill=INK, tracking=6)
    header_h = ty + 44
    liquid_glass_panel(canvas, header_top, header_h)
    y = header_top + 22
    y = text_block(canvas, y, data["name"], title, center=True, fill=INK, tracking=6)
    y += 4
    y = text_block(canvas, y, data["tagline"], subtitle, center=True, fill=INK_SECONDARY, tracking=6)
    y += 6
    y = text_block(canvas, y, data["roles"], roles_f, center=True, fill=INK, tracking=6)
    y = header_top + header_h + 22

    # ----- Welcome -----
    welcome_body = " ".join(data["welcome_body"].split())
    temp = Image.new("RGBA", (W, 500), (0, 0, 0, 0))
    ty = 0
    ty = text_block(temp, ty, data["welcome_title"], h1, fill=INK, tracking=7)
    ty += 8
    ty = text_block(temp, ty, welcome_body, body, fill=INK_SECONDARY, tracking=7)
    content_h = ty + 48
    panel_top = y
    liquid_glass_panel(canvas, panel_top, content_h)
    y = panel_top + 24
    y = text_block(canvas, y, data["welcome_title"], h1, fill=INK, tracking=7)
    y += 8
    y = text_block(canvas, y, welcome_body, body, fill=INK_SECONDARY, tracking=7)
    y = panel_top + content_h + 20

    # ----- Experience -----
    temp = Image.new("RGBA", (W, 2000), (0, 0, 0, 0))
    ty = 0
    ty = text_block(temp, ty, data["experience_title"], h1, fill=INK, tracking=7)
    ty += 12
    for job in data["experience"]:
        ty = text_block(temp, ty, job["title"], h2, fill=INK, tracking=5)
        ty += 3
        ty = text_block(temp, ty, " ".join(job["body"].split()), body, fill=INK_SECONDARY, tracking=6)
        ty += 12
    content_h = ty + 44
    panel_top = y
    liquid_glass_panel(canvas, panel_top, content_h)
    y = panel_top + 24
    y = text_block(canvas, y, data["experience_title"], h1, fill=INK, tracking=7)
    y += 12
    for job in data["experience"]:
        y = text_block(canvas, y, job["title"], h2, fill=INK, tracking=5)
        y += 3
        y = text_block(canvas, y, " ".join(job["body"].split()), body, fill=INK_SECONDARY, tracking=6)
        y += 12
    y = panel_top + content_h + 20

    # ----- Projects -----
    col_w = (MAX_TEXT - 36) // 2
    temp = Image.new("RGBA", (W, 1200), (0, 0, 0, 0))
    ty = text_block(temp, 0, data["projects_title"], h1, fill=INK, tracking=7) + 14
    max_col = 0
    tdraw = ImageDraw.Draw(temp)
    for p in data["projects"]:
        ph = 108 + 34 + 26
        ph += len(wrap_lines(tdraw, " ".join(p["body"].split()), body, col_w)) * 28
        max_col = max(max_col, ph)
    content_h = ty + max_col + 36
    panel_top = y
    liquid_glass_panel(canvas, panel_top, content_h)
    y = panel_top + 24
    y = text_block(canvas, y, data["projects_title"], h1, fill=INK, tracking=7)
    y += 14
    left_x = MARGIN
    right_x = MARGIN + col_w + 36
    row_y = y

    for idx, p in enumerate(data["projects"]):
        x = left_x if idx == 0 else right_x
        cy = row_y
        logo_path = ASSETS / p["logo"]
        if logo_path.exists():
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((88, 88), Image.Resampling.LANCZOS)
            canvas.alpha_composite(logo, (x + (col_w - logo.width) // 2, cy))
            cy += 100

        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)

        def draw_centered(py: int, text: str, fnt, fill=INK) -> int:
            tw = od.textlength(text, font=fnt)
            px = x + (col_w - tw) / 2
            od.text((px, py + 1), text, font=fnt, fill=(255, 255, 255, 60))
            od.text((px, py), text, font=fnt, fill=fill)
            bb = od.textbbox((0, 0), text, font=fnt)
            return py + (bb[3] - bb[1]) + 7

        def draw_left(py: int, text: str, fnt, fill=INK_SECONDARY) -> int:
            od.text((x, py + 1), text, font=fnt, fill=(255, 255, 255, 50))
            od.text((x, py), text, font=fnt, fill=fill)
            bb = od.textbbox((0, 0), text, font=fnt)
            return py + (bb[3] - bb[1]) + 6

        cy = draw_centered(cy, p["name"], h2, INK)
        cy = draw_centered(cy, p["stack"], small, INK_MUTED)
        for line in wrap_lines(od, " ".join(p["body"].split()), body, col_w):
            cy = draw_left(cy, line, body, INK_SECONDARY)
        canvas.alpha_composite(overlay)

    y = panel_top + content_h + 20

    # ----- Tech icons -----
    icons_path = ASSETS / data.get("tech_icons", "tech-icons.png")
    icons = Image.open(icons_path).convert("RGBA") if icons_path.exists() else None
    icon_h = 0
    if icons is not None:
        max_w = MAX_TEXT
        scale = min(1.85, max_w / icons.width)
        icons = icons.resize((int(icons.width * scale), int(icons.height * scale)), Image.Resampling.LANCZOS)
        icon_h = icons.height

    temp = Image.new("RGBA", (W, 600), (0, 0, 0, 0))
    ty = text_block(temp, 0, data["tech_title"], h1, fill=INK, tracking=7) + 14 + icon_h
    content_h = ty + 44
    panel_top = y
    liquid_glass_panel(canvas, panel_top, content_h)
    y = panel_top + 24
    y = text_block(canvas, y, data["tech_title"], h1, fill=INK, tracking=7)
    y += 12
    if icons is not None:
        ix = (W - icons.width) // 2
        canvas.alpha_composite(icons, (ix, y))
        y += icons.height
    y = panel_top + content_h + 28

    paste_deco(canvas, "cloud.png", (70, y - 40), 110)
    paste_deco(canvas, "island-small.png", (980, y - 50), 100)
    paste_deco(canvas, "cloud.png", (500, y - 20), 80)

    final_h = min(estimate_h, y + 40)
    final = canvas.crop((0, 0, W, final_h))
    final.convert("RGB").save(OUT, quality=95, optimize=True)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes, {final.size[0]}x{final.size[1]})")


if __name__ == "__main__":
    main()
