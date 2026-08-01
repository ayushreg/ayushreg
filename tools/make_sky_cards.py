"""Render sky-background content cards with text overlaid."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(r"C:\Users\regmi\OneDrive\Desktop\About me\ayushreg-profile\assets")
GEN = Path(r"C:\Users\regmi\.cursor\projects\c-Users-regmi-OneDrive-Desktop-About-me\assets")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibrib.ttf" if bold else r"C:\Windows\Fonts\calibri.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def fit_bg(src: Image.Image, w: int, h: int) -> Image.Image:
    img = src.convert("RGBA")
    scale = max(w / img.width, h / img.height)
    nw, nh = int(img.width * scale), int(img.height * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - w) // 2
    top = max(0, (nh - h) // 3)
    return img.crop((left, top, left + w, top + h))


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=fnt) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_text(
    base: Image.Image,
    xy: tuple[int, int],
    text: str,
    fnt: ImageFont.ImageFont,
    fill=(255, 255, 255, 255),
    shadow=(20, 40, 70, 140),
) -> None:
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    x, y = xy
    # soft shadow
    for dx, dy in ((2, 2), (1, 1), (0, 2), (2, 0)):
        d.text((x + dx, y + dy), text, font=fnt, fill=shadow)
    d.text((x, y), text, font=fnt, fill=fill)
    base.alpha_composite(overlay)


def paste_deco(base: Image.Image, deco_path: Path, xy: tuple[int, int], size: int, opacity: float = 0.95) -> None:
    if not deco_path.exists():
        return
    deco = Image.open(deco_path).convert("RGBA")
    deco.thumbnail((size, size), Image.Resampling.LANCZOS)
    if opacity < 1:
        a = deco.split()[-1].point(lambda p: int(p * opacity))
        deco.putalpha(a)
    base.alpha_composite(deco, xy)


def make_experience(bg: Image.Image) -> Image.Image:
    W, H = 1200, 720
    card = fit_bg(bg, W, H)

    # subtle dark veil for readability in the text band
    veil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(veil)
    vd.rounded_rectangle((48, 48, W - 48, H - 48), radius=28, fill=(15, 40, 70, 42))
    card = Image.alpha_composite(card, veil)

    # decorations
    paste_deco(card, ROOT / "island.png", (70, 520), 150, 0.92)
    paste_deco(card, ROOT / "cloud.png", (980, 70), 140, 0.9)
    paste_deco(card, ROOT / "island-small.png", (1000, 520), 120, 0.9)

    draw = ImageDraw.Draw(card)
    title_f = font(44, bold=True)
    role_f = font(26, bold=True)
    body_f = font(22, bold=False)

    draw_text(card, (90, 80), "Experience", title_f)

    jobs = [
        (
            "Argo Data  ·  Software Engineering Intern",
            "Building a React app so engineers can create, edit, compare, and run tests in one place, and moving tests from Excel to XML so Git can review them cleanly.",
        ),
        (
            "OneKit  ·  Software Engineering Intern",
            "Owned the email marketing tool in a desktop app for small-business owners: campaigns, A/B testing, and engagement tracking.",
        ),
        (
            "AI Squads  ·  TA Lead & Software Engineer",
            "Help teach thousands of students building AI products, and ship website fixes when something blocks them from submitting work.",
        ),
    ]

    y = 160
    max_w = 900
    for role, body in jobs:
        draw_text(card, (90, y), role, role_f, fill=(255, 255, 255, 255))
        y += 42
        for line in wrap(draw, body, body_f, max_w):
            draw_text(card, (90, y), line, body_f, fill=(235, 245, 255, 245), shadow=(20, 40, 70, 110))
            y += 30
        y += 28

    return card


def make_about(bg: Image.Image) -> Image.Image:
    W, H = 1200, 360
    card = fit_bg(bg, W, H)
    veil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(veil)
    vd.rounded_rectangle((40, 36, W - 40, H - 36), radius=24, fill=(15, 40, 70, 38))
    card = Image.alpha_composite(card, veil)

    paste_deco(card, ROOT / "cloud.png", (40, 40), 110, 0.9)
    paste_deco(card, ROOT / "island-small.png", (1020, 180), 110, 0.92)

    draw = ImageDraw.Draw(card)
    title_f = font(36, bold=True)
    body_f = font(24, bold=False)

    draw_text(card, (180, 70), "Hey, I'm Ayush. Welcome in.", title_f)
    body = (
        "I'm a FastTrack CS student at UT Dallas (graduating 2028). "
        "I intern at Argo Data, teach at AI Squads, and build AutoTok on the side."
    )
    y = 140
    for line in wrap(draw, body, body_f, 780):
        draw_text(card, (180, y), line, body_f, fill=(235, 245, 255, 245), shadow=(20, 40, 70, 110))
        y += 34

    return card


def main() -> None:
    bg_path = GEN / "sky-panel-bg.png"
    if not bg_path.exists():
        raise SystemExit(f"missing {bg_path}")
    bg = Image.open(bg_path).convert("RGBA")

    about = make_about(bg)
    about.convert("RGB").save(ROOT / "about-card.png", quality=95, optimize=True)
    print("wrote about-card.png", (ROOT / "about-card.png").stat().st_size)

    exp = make_experience(bg)
    exp.convert("RGB").save(ROOT / "experience-card.png", quality=95, optimize=True)
    print("wrote experience-card.png", (ROOT / "experience-card.png").stat().st_size)


if __name__ == "__main__":
    main()
