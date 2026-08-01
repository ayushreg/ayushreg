"""
Build one tall sky-themed profile image from content/profile.yaml.

Usage:
  python tools/make_profile_image.py
"""
from __future__ import annotations

from pathlib import Path
import textwrap

from PIL import Image, ImageDraw, ImageFont
import yaml

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
CONTENT = ROOT / "content" / "profile.yaml"
OUT = ASSETS / "profile.png"

W = 1200
MARGIN = 72
MAX_TEXT = W - MARGIN * 2


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibrib.ttf" if bold else r"C:\Windows\Fonts\calibri.ttf",
    ]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def fit_strip(bg: Image.Image, h: int) -> Image.Image:
    img = bg.convert("RGBA")
    scale = max(W / img.width, h / img.height)
    nw, nh = int(img.width * scale), int(img.height * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - W) // 2
    top = max(0, (nh - h) // 4)
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
    shadow=(10, 25, 45, 180),
    center: bool = False,
    max_width: int = MAX_TEXT,
) -> int:
    draw = ImageDraw.Draw(canvas)
    lines = wrap_lines(draw, text, font, max_width)
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for line in lines:
        tw = od.textlength(line, font=font)
        x = (W - tw) / 2 if center else MARGIN
        for dx, dy in ((2, 2), (1, 1), (0, 2)):
            od.text((x + dx, y + dy), line, font=font, fill=shadow)
        od.text((x, y), line, font=font, fill=fill)
        bbox = od.textbbox((0, 0), line, font=font)
        y += (bbox[3] - bbox[1]) + 8
    canvas.alpha_composite(overlay)
    return y


def paste_deco(canvas: Image.Image, name: str, xy: tuple[int, int], size: int) -> None:
    path = ASSETS / name
    if not path.exists():
        return
    deco = Image.open(path).convert("RGBA")
    deco.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas.alpha_composite(deco, xy)


def section_scrim(canvas: Image.Image, y0: int, y1: int, alpha: int = 55) -> None:
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rounded_rectangle((40, y0, W - 40, y1), radius=22, fill=(12, 35, 65, alpha))
    canvas.alpha_composite(overlay)


def main() -> None:
    data = yaml.safe_load(CONTENT.read_text(encoding="utf-8"))

    bg_path = ASSETS / "sky-panel-bg.png"
    if not bg_path.exists():
        raise SystemExit(f"Missing {bg_path}")
    bg = Image.open(bg_path).convert("RGBA")

    # Build on a tall sky canvas by tiling/fitting strips
    # Estimate height first with a dry run using a temp image
    estimate_h = 3200
    canvas = fit_strip(bg, estimate_h)

    # Soft overall readability veil (light, keeps sky visible)
    veil = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    vd = ImageDraw.Draw(veil)
    vd.rectangle((0, 0, W, estimate_h), fill=(8, 30, 55, 28))
    canvas.alpha_composite(veil)

    title = load_font(58, bold=True)
    subtitle = load_font(26, bold=False)
    h1 = load_font(38, bold=True)
    h2 = load_font(26, bold=True)
    body = load_font(22, bold=False)
    small = load_font(20, bold=False)

    y = 70
    y = text_block(canvas, y, data["name"], title, center=True)
    y += 6
    y = text_block(canvas, y, data["tagline"], subtitle, center=True, fill=(235, 246, 255, 255))
    y += 2
    y = text_block(canvas, y, data["roles"], small, center=True, fill=(220, 236, 250, 255))
    y += 18

    paste_deco(canvas, "cloud.png", (60, 40), 110)
    paste_deco(canvas, "island-small.png", (1020, 50), 110)

    # Welcome
    sec_top = y
    y += 24
    y = text_block(canvas, y, data["welcome_title"], h1)
    y += 8
    y = text_block(canvas, y, " ".join(data["welcome_body"].split()), body, fill=(240, 248, 255, 255))
    y += 20
    section_scrim(canvas, sec_top, y + 10, alpha=48)
    # redraw text above scrim by compositing order issue - scrim was after text so it covers text!
    # Fix: draw scrim BEFORE text. Rebuild this section properly below.

    # Because scrim-after-text darkens text badly, regenerate cleanly with ordered drawing.
    canvas = fit_strip(bg, estimate_h)
    canvas.alpha_composite(Image.new("RGBA", canvas.size, (8, 30, 55, 22)))

    y = 60
    paste_deco(canvas, "cloud.png", (50, 30), 120)
    paste_deco(canvas, "island.png", (980, 20), 140)

    y = text_block(canvas, y, data["name"], title, center=True)
    y += 4
    y = text_block(canvas, y, data["tagline"], subtitle, center=True, fill=(245, 250, 255, 255))
    y += 2
    y = text_block(canvas, y, data["roles"], small, center=True, fill=(230, 242, 255, 255))
    y += 28

    def begin_section(pad: int = 18) -> int:
        return y + pad

    def end_section(top: int, bottom: int) -> None:
        # draw scrim behind by inserting under - easier: draw rounded panel first next time
        pass

    # Helper: draw a panel then content inside
    def panel(top: int, height: int, alpha: int = 58) -> None:
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        d.rounded_rectangle((36, top, W - 36, top + height), radius=24, fill=(10, 32, 58, alpha))
        # thin bright edge for definition on sky
        d.rounded_rectangle((36, top, W - 36, top + height), radius=24, outline=(255, 255, 255, 55), width=2)
        canvas.alpha_composite(overlay)

    # Welcome panel
    panel_top = y
    inner_y = y + 28
    # measure content height roughly
    temp = Image.new("RGBA", (W, 400), (0, 0, 0, 0))
    ty = 0
    ty = text_block(temp, ty, data["welcome_title"], h1)
    ty += 8
    ty = text_block(temp, ty, " ".join(data["welcome_body"].split()), body)
    panel_h = ty + 56
    panel(panel_top, panel_h, alpha=62)
    y = panel_top + 28
    y = text_block(canvas, y, data["welcome_title"], h1)
    y += 8
    y = text_block(canvas, y, " ".join(data["welcome_body"].split()), body, fill=(245, 250, 255, 255))
    y = panel_top + panel_h + 24

    paste_deco(canvas, "cloud.png", (1000, y - 10), 90)

    # Experience panel
    panel_top = y
    temp = Image.new("RGBA", (W, 1200), (0, 0, 0, 0))
    ty = 0
    ty = text_block(temp, ty, data["experience_title"], h1)
    ty += 14
    for job in data["experience"]:
        ty = text_block(temp, ty, job["title"], h2)
        ty += 4
        ty = text_block(temp, ty, " ".join(job["body"].split()), body, fill=(245, 250, 255, 255))
        ty += 16
    panel_h = ty + 56
    panel(panel_top, panel_h, alpha=64)
    y = panel_top + 28
    y = text_block(canvas, y, data["experience_title"], h1)
    y += 14
    for job in data["experience"]:
        y = text_block(canvas, y, job["title"], h2)
        y += 4
        y = text_block(canvas, y, " ".join(job["body"].split()), body, fill=(245, 250, 255, 255))
        y += 16
    y = panel_top + panel_h + 24

    paste_deco(canvas, "island-small.png", (70, y - 20), 100)

    # Projects panel
    panel_top = y
    # two-column layout
    col_w = (MAX_TEXT - 40) // 2
    temp = Image.new("RGBA", (W, 900), (0, 0, 0, 0))
    ty = 0
    ty = text_block(temp, ty, data["projects_title"], h1)
    ty += 20
    # estimate project card height
    proj_body_h = 0
    for p in data["projects"]:
        ph = 0
        ph += 100  # logo
        ph += 36  # name
        ph += 28  # stack
        # body lines
        tdraw = ImageDraw.Draw(temp)
        lines = wrap_lines(tdraw, " ".join(p["body"].split()), body, col_w)
        ph += len(lines) * 30
        proj_body_h = max(proj_body_h, ph)
    panel_h = ty + proj_body_h + 70
    panel(panel_top, panel_h, alpha=64)
    y = panel_top + 28
    y = text_block(canvas, y, data["projects_title"], h1)
    y += 18

    left_x = MARGIN
    right_x = MARGIN + col_w + 40
    row_y = y

    for idx, p in enumerate(data["projects"]):
        x = left_x if idx == 0 else right_x
        cy = row_y
        logo_path = ASSETS / p["logo"]
        if logo_path.exists():
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((96, 96), Image.Resampling.LANCZOS)
            canvas.alpha_composite(logo, (x + (col_w - logo.width) // 2, cy))
            cy += 110

        # centered-ish column text by manual x
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)

        def draw_at(px: int, py: int, text: str, fnt, fill=(255, 255, 255, 255)) -> int:
            for dx, dy in ((2, 2), (1, 1)):
                od.text((px + dx, py + dy), text, font=fnt, fill=(10, 25, 45, 170))
            od.text((px, py), text, font=fnt, fill=fill)
            bb = od.textbbox((0, 0), text, font=fnt)
            return py + (bb[3] - bb[1]) + 8

        # name centered in column
        tw = od.textlength(p["name"], font=h2)
        cy = draw_at(x + int((col_w - tw) / 2), cy, p["name"], h2)
        tw = od.textlength(p["stack"], font=small)
        cy = draw_at(x + int((col_w - tw) / 2), cy, p["stack"], small, fill=(230, 242, 255, 255))
        for line in wrap_lines(od, " ".join(p["body"].split()), body, col_w):
            cy = draw_at(x, cy, line, body, fill=(245, 250, 255, 255))
        canvas.alpha_composite(overlay)

    y = panel_top + panel_h + 24

    # Tech panel
    panel_top = y
    temp = Image.new("RGBA", (W, 500), (0, 0, 0, 0))
    ty = 0
    ty = text_block(temp, ty, data["tech_title"], h1)
    ty += 12
    for line in (data["tech_line_1"], data["tech_line_2"], data["tech_line_3"]):
        ty = text_block(temp, ty, line, body, center=True, fill=(245, 250, 255, 255))
        ty += 6
    panel_h = ty + 56
    panel(panel_top, panel_h, alpha=62)
    y = panel_top + 28
    y = text_block(canvas, y, data["tech_title"], h1)
    y += 12
    for line in (data["tech_line_1"], data["tech_line_2"], data["tech_line_3"]):
        y = text_block(canvas, y, line, body, center=True, fill=(245, 250, 255, 255))
        y += 6
    y = panel_top + panel_h + 24

    paste_deco(canvas, "cloud.png", (80, y - 10), 95)
    paste_deco(canvas, "island.png", (980, y - 20), 120)

    # Connect panel
    panel_top = y
    temp = Image.new("RGBA", (W, 400), (0, 0, 0, 0))
    ty = 0
    ty = text_block(temp, ty, data["connect_title"], h1, center=True)
    ty += 8
    ty = text_block(temp, ty, data["connect_body"], body, center=True, fill=(245, 250, 255, 255))
    ty += 8
    ty = text_block(temp, ty, data["connect_links"], subtitle, center=True, fill=(230, 242, 255, 255))
    panel_h = ty + 56
    panel(panel_top, panel_h, alpha=62)
    y = panel_top + 28
    y = text_block(canvas, y, data["connect_title"], h1, center=True)
    y += 8
    y = text_block(canvas, y, data["connect_body"], body, center=True, fill=(245, 250, 255, 255))
    y += 8
    y = text_block(canvas, y, data["connect_links"], subtitle, center=True, fill=(230, 242, 255, 255))
    y = panel_top + panel_h + 40

    # Crop to used height
    final_h = min(estimate_h, y + 20)
    final = canvas.crop((0, 0, W, final_h))
    final.convert("RGB").save(OUT, quality=95, optimize=True)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes, {final.size[0]}x{final.size[1]})")


if __name__ == "__main__":
    main()
