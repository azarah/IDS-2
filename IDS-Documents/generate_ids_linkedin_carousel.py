#!/usr/bin/env python3
"""
Generates PNG carousel frames for LinkedIn (1080×1080) —
Zarah Sharda · Creative Direction × IDS Invoice Application case study.
Run from repo root or any cwd; resolves paths relative to this file's folder.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

# IDS photography (prefer repo root duplicate if present)
BABY = ROOT / "IDS-holding baby.png"
if not BABY.exists():
    BABY = HERE / "IDS-holding baby.png"
TELE = HERE / "IDS-Telephoneservice.png"

OUT_DIR = ROOT / "IDS-LinkedIn-Assets"
SIZE = (1080, 1080)
FOOTER = "Zarah Sharda · Creative Direction"
CASELINE = "Case study · Individualized Doula Services (IDS)"


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def _fonts() -> tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
    bold_candidates = (
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\calibrib.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
    )
    body_candidates = (
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    )
    bold_path = next((p for p in bold_candidates if Path(p).exists()), bold_candidates[-1])
    body_path = next((p for p in body_candidates if Path(p).exists()), body_candidates[-1])
    title = _font(bold_path, 52)
    sub = _font(body_path, 34)
    small = _font(body_path, 26)
    return title, sub, small


def _draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    font: ImageFont.FreeTypeFont,
    fill,
    width_chars: int = 42,
    line_spacing: int = 8,
) -> int:
    x, y = xy
    lines = []
    for block in text.split("\n"):
        if not block.strip():
            lines.append("")
            continue
        lines.extend(textwrap.wrap(block, width=width_chars) or [""])
    y_cursor = y
    for line in lines:
        draw.text((x, y_cursor), line, font=font, fill=fill)
        bbox = draw.textbbox((x, y_cursor), line, font=font)
        y_cursor = (bbox[3] - bbox[1]) + line_spacing + y_cursor
    return y_cursor


def slide_cover(ftitle, fbody, fsmall) -> Image.Image:
    im = Image.new("RGB", SIZE, "#1a1714")
    if BABY.exists():
        photo = Image.open(BABY).convert("RGB")
        sx = max(SIZE[0] / photo.width, SIZE[1] / photo.height)
        nw, nh = int(photo.width * sx), int(photo.height * sx)
        photo = photo.resize((nw, nh), Image.Resampling.LANCZOS)
        left = (nw - SIZE[0]) // 2
        top = (nh - SIZE[1]) // 2
        photo = photo.crop((left, top, left + SIZE[0], top + SIZE[1]))
        base = photo.convert("RGBA")
        overlay = Image.new("RGBA", SIZE, (26, 23, 20, 205))
        im = Image.alpha_composite(base, overlay).convert("RGB")
    draw = ImageDraw.Draw(im)
    draw.rectangle((0, 0, SIZE[0], 12), fill="#c4983c")
    _draw_wrapped(draw, CASELINE.upper(), (64, 72), fsmall, "#e8dfd0", width_chars=52)
    _draw_wrapped(
        draw,
        "Funding the next layer\nof maternal care infrastructure",
        (64, 160),
        ftitle,
        "#faf7f2",
        width_chars=22,
        line_spacing=12,
    )
    _draw_wrapped(
        draw,
        "Transparent billing ops for doula-led practices —\na disciplined Python MVP.",
        (64, 420),
        fbody,
        "#d4c4b0",
        width_chars=46,
        line_spacing=10,
    )
    draw.text((64, SIZE[1] - 120), FOOTER, font=fsmall, fill="#a89888")
    return im


def slide_editorial(bg: str, title: str, body: str, ftitle, fbody, fsmall, accent_ok: bool = True) -> Image.Image:
    im = Image.new("RGB", SIZE, bg)
    draw = ImageDraw.Draw(im)
    if accent_ok:
        draw.rectangle((0, 0, SIZE[0], 10), fill="#c4983c")
    _draw_wrapped(draw, title, (72, 80), ftitle, "#1a1714", width_chars=34, line_spacing=14)
    _draw_wrapped(draw, body, (72, 260), fbody, "#3d3530", width_chars=42, line_spacing=14)
    draw.text((72, SIZE[1] - 96), FOOTER, font=fsmall, fill="#7a7068")
    return im


def slide_split_visual(ftitle, fbody, fsmall) -> Image.Image:
    """Phone service visual + headline for ‘remote base + hourly visits’ story."""
    im = Image.new("RGB", SIZE, "#f5f1eb")
    draw = ImageDraw.Draw(im)
    draw.rectangle((0, 540, SIZE[0], SIZE[1]), fill="#eae3d8")
    if TELE.exists():
        pic = Image.open(TELE).convert("RGB")
        pic.thumbnail((SIZE[0], 540))
        x = (SIZE[0] - pic.width) // 2
        im.paste(pic, (x, 0))
    draw.rectangle((0, 536, SIZE[0], 544), fill="#c4983c")
    _draw_wrapped(
        draw,
        "Operational clarity,\nhuman tone",
        (72, 580),
        ftitle,
        "#1a1714",
        width_chars=26,
        line_spacing=12,
    )
    txt = (
        "IDS separates telephone (flat-rate) support from hourly hospital and home visits, mileage, "
        "and overnight items — surfaced as a respectful, legible invoice families can reconcile."
    )
    _draw_wrapped(draw, txt, (72, 720), fbody, "#423930", width_chars=44)
    draw.text((72, SIZE[1] - 88), FOOTER, font=fsmall, fill="#8a8278")
    return im


def slide_cta(ftitle, fbody, fsmall) -> Image.Image:
    im = Image.new("RGB", SIZE, "#1a1714")
    draw = ImageDraw.Draw(im)
    draw.rectangle((0, 0, SIZE[0], 10), fill="#c4983c")
    _draw_wrapped(draw, "Open to aligned capital\n& strategic partners", (72, 100), ftitle, "#faf7f2", width_chars=28)
    body = (
        "We articulate product narrative, visual systems, and launch collateral for ventures where care "
        "meets critical operations.\n\n"
        "→ DM for IDS technical appendix, investor one-pager, or creative partnership."
    )
    _draw_wrapped(draw, body, (72, 420), fbody, "#cfc3b6", width_chars=42)
    draw.text((72, SIZE[1] - 120), FOOTER, font=fsmall, fill="#9a8b7e")
    draw.text((72, SIZE[1] - 80), CASELINE, font=fsmall, fill="#6d635a")
    return im


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ftitle, fbody, fsmall = _fonts()
    specs: list[tuple[str, Image.Image]] = [
        ("zs_ids_li_01_cover.png", slide_cover(ftitle, fbody, fsmall)),
        (
            "zs_ids_li_02_why_now.png",
            slide_editorial(
                "#faf7f2",
                "Why this category",
                (
                    "Maternal health workloads run on fragmented billing: flat remote retainers collide with hourly "
                    "bedside visits, mileage, and add-ons.\n\n"
                    "Illinois practices are navigating expanding payer pathways for doulas; operational rigor builds "
                    "trust with families and auditors alike."
                ),
                ftitle,
                fbody,
                fsmall,
            ),
        ),
        (
            "zs_ids_li_03_the_build.png",
            slide_editorial(
                "#eae3d8",
                "The build (investable MVP)",
                (
                    "IDS Invoice Application — single-file Python, standard library. "
                    "File-backed truth for rates & rosters; Client, Doula, and Admin journeys; "
                    "Decimal currency; optional exported invoice artifacts.\n\n"
                    "No mandatory server footprint today — deliberate runway for HIPAA-aware hosting & integrations."
                ),
                ftitle,
                fbody,
                fsmall,
            ),
        ),
        ("zs_ids_li_04_ops_story.png", slide_split_visual(ftitle, fbody, fsmall)),
        ("zs_ids_li_05_cta.png", slide_cta(ftitle, fbody, fsmall)),
    ]
    for name, img in specs:
        path = OUT_DIR / name
        img.save(path, "PNG", optimize=True)
        print(path)


if __name__ == "__main__":
    main()
