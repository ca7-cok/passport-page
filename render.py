#!/usr/bin/env python3
"""Render the passport data page of the Republic of Vespera, a country
that isn't there. One 1024x1024 PNG, fully deterministic: same code,
same bytes. Pure Pillow; fonts are the DejaVu faces installed locally.

The page: navy guilloche ground, gold frame, coat of arms, a dusk
portrait, the holder's data, two entry stamps, a visa stamp, and a
valid ICAO MRZ (check digits computed, not faked).
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")

NAVY = (11, 34, 54)
NAVY2 = (16, 56, 78)
TEAL = (20, 82, 92)
GOLD = (201, 162, 39)
GOLD_LT = (226, 196, 110)
CREAM = (242, 234, 216)
INK = (24, 24, 22)
RED = (176, 48, 48)
BLUE = (31, 78, 121)
PALE = (168, 190, 205)

FONT_DIR = "/usr/share/fonts/truetype/dejavu/"


def font(name, size):
    return ImageFont.truetype(FONT_DIR + name, size)


SERIF_B = lambda s: font("DejaVuSerif-Bold.ttf", s)
SERIF = lambda s: font("DejaVuSerif.ttf", s)
SANS_B = lambda s: font("DejaVuSans-Bold.ttf", s)
SANS = lambda s: font("DejaVuSans.ttf", s)
MONO = lambda s: font("DejaVuSansMono.ttf", s)
MONO_B = lambda s: font("DejaVuSansMono-Bold.ttf", s)


# ------------------------------------------------------------------ mrz
def mrz_cd(s):
    """ICAO 9303 check digit: values 0-9, A-Z = 10-35, '<' = 0; weights 7,3,1."""
    vals = {str(i): i for i in range(10)}
    vals.update({chr(ord("A") + i): 10 + i for i in range(26)})
    vals["<"] = 0
    w = (7, 3, 1)
    return str(sum(vals[c] * w[i % 3] for i, c in enumerate(s)) % 10)


def mrz_lines():
    doc = "VSP260042"
    nat = "VSP"
    dob, sex, exp = "980314", "F", "360601"
    personal = "<" * 14
    line1 = ("P<" + nat + "MARLOWE<<ELARA<JUNE").ljust(44, "<")
    core = (doc + mrz_cd(doc) + nat + dob + mrz_cd(dob) + sex + exp
            + mrz_cd(exp) + personal + mrz_cd(personal))
    line2 = core + mrz_cd(core)
    assert len(line1) == 44 and len(line2) == 44, (line1, line2)
    return line1, line2


# ------------------------------------------------------------------ helpers
def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgrad(d, box, c0, c1):
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0 - 1)
        d.line([(x0, y), (x1, y)], fill=lerp(c0, c1, t))


def text_center(d, cx, y, text, fnt, fill):
    d.text((cx - d.textlength(text, font=fnt) / 2, y), text, font=fnt,
           fill=fill)


def text_right(d, x, y, text, fnt, fill):
    d.text((x - d.textlength(text, font=fnt), y), text, font=fnt, fill=fill)


def ring_text(base, cx, cy, r, text, fnt, fill, start_deg=-90, span=300):
    """Draw text along a circle, one glyph at a time, upright outward."""
    if not text:
        return
    step = span / max(1, len(text))
    for i, ch in enumerate(text):
        ang = math.radians(start_deg + i * step + step / 2)
        glyph = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
        g = ImageDraw.Draw(glyph)
        g.text((20, 20), ch, font=fnt, fill=fill + (255,), anchor="mm")
        rot = glyph.rotate(-(start_deg + i * step + step / 2) - 90,
                           resample=Image.BICUBIC, center=(20, 20))
        px = int(cx + r * math.cos(ang) - 20)
        py = int(cy + r * math.sin(ang) - 20)
        base.alpha_composite(rot, (px, py))


def guilloche(base, cx, cy, r0, r1, step, color, width=1):
    """Concentric hairline circles, faint, for the security ground.
    color is an RGBA tuple, used as given."""
    d = ImageDraw.Draw(base)
    r = r0
    while r <= r1:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color,
                  width=width)
        r += step


def star(d, cx, cy, r, fill, points=5, inner=0.45):
    pts = []
    for i in range(points * 2):
        ang = math.radians(-90 + i * 180 / points)
        rr = r if i % 2 == 0 else r * inner
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=fill)


def compass_rose(base, cx, cy, r, color):
    """Faint watermark rose: long/short points + ring. color is RGBA."""
    d = ImageDraw.Draw(base)
    for k in range(8):
        ang = math.radians(k * 45)
        long = r if k % 2 == 0 else r * 0.55
        tip = (cx + long * math.cos(ang), cy + long * math.sin(ang))
        left = (cx + r * 0.12 * math.cos(ang + math.pi / 2),
                cy + r * 0.12 * math.sin(ang + math.pi / 2))
        right = (cx + r * 0.12 * math.cos(ang - math.pi / 2),
                 cy + r * 0.12 * math.sin(ang - math.pi / 2))
        d.polygon([tip, left, right], fill=color)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color,
              width=2)
    d.ellipse([cx - r * 0.55, cy - r * 0.55, cx + r * 0.55, cy + r * 0.55],
              outline=color, width=1)

# ------------------------------------------------------------------ arms
def coat_of_arms(base, x, y, s):
    """Vespera arms: gold-ringed shield, evening star over three waves."""
    d = ImageDraw.Draw(base)
    # shield outline
    w, h = s, int(s * 1.18)
    pts = [(x, y), (x + w, y), (x + w, y + h * 0.62),
           (x + w / 2, y + h), (x, y + h * 0.62)]
    d.polygon(pts, fill=(13, 46, 66, 255), outline=GOLD + (255,), width=3)
    d.polygon([(x + 5, y + 5), (x + w - 5, y + 5),
               (x + w - 5, y + h * 0.62 - 2),
               (x + w / 2, y + h - 7), (x + 5, y + h * 0.62 - 2)],
              outline=GOLD_LT + (255,), width=1)
    cx, cy = x + w / 2, y + h * 0.34
    star(d, cx, cy, s * 0.20, GOLD + (255,))
    for k, yy in enumerate((0.58, 0.68, 0.78)):
        wy = y + h * yy
        amp = s * 0.10
        xs = [x + 8 + i * (w - 16) / 12 for i in range(13)]
        wave = [(xx, wy + amp * math.sin((xx - x) / w * math.pi * 2 + k))
                for xx in xs]
        d.line(wave, fill=GOLD_LT + (255,), width=2)


def flag(base, x, y, w, h):
    """Vespera ensign: teal / gold / navy bands with a gold star."""
    d = ImageDraw.Draw(base)
    bands = [TEAL, GOLD, NAVY2]
    for i, c in enumerate(bands):
        d.rectangle([x, y + i * h / 3, x + w, y + (i + 1) * h / 3], fill=c)
    d.rectangle([x, y, x + w, y + h], outline=GOLD_LT + (255,), width=1)
    star(d, x + w / 2, y + h / 2, h * 0.30, (242, 234, 216, 255))


# ------------------------------------------------------------------ portrait
def portrait(base, box):
    """Dusk over Port Lumen: gradient sky, low sun, a traveller in
    silhouette with a wide-brim hat, a few early stars."""
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(base)
    sky = [(46, 74, 107), (196, 128, 66), (122, 74, 43)]
    n = y1 - y0
    for yy in range(y0, y1):
        t = (yy - y0) / max(1, n - 1)
        if t < 0.55:
            c = lerp(sky[0], sky[1], t / 0.55)
        else:
            c = lerp(sky[1], sky[2], (t - 0.55) / 0.45)
        d.line([(x0, yy), (x1, yy)], fill=c + (255,))
    # sun and stars
    sx, sy = x0 + (x1 - x0) * 0.68, y0 + (y1 - y0) * 0.42
    d.ellipse([sx - 26, sy - 26, sx + 26, sy + 26], fill=(240, 200, 110, 255))
    for (px, py, r) in [(0.18, 0.14, 2), (0.30, 0.08, 1), (0.52, 0.18, 2),
                        (0.82, 0.10, 1), (0.12, 0.30, 1), (0.88, 0.26, 2)]:
        d.ellipse([x0 + (x1 - x0) * px - r, y0 + (y1 - y0) * py - r,
                   x0 + (x1 - x0) * px + r, y0 + (y1 - y0) * py + r],
                  fill=(255, 255, 255, 220))
    # sea band
    sea_y = y0 + (y1 - y0) * 0.62
    d.rectangle([x0, sea_y, x1, y1], fill=(16, 42, 60, 255))
    for k in range(4):
        yy = sea_y + 14 + k * 18
        d.line([(x0 + 8, yy), (x1 - 8, yy)], fill=(120, 150, 170, 90),
               width=2)
    # traveller silhouette: hat, head, shoulders
    cx = x0 + (x1 - x0) / 2
    hy = y0 + (y1 - y0) * 0.52
    sil = (10, 18, 30, 255)
    d.ellipse([cx - 52, hy - 14, cx + 52, hy + 6], fill=sil)          # brim
    d.pieslice([cx - 30, hy - 46, cx + 30, hy + 2], 180, 360, fill=sil)
    d.ellipse([cx - 24, hy + 2, cx + 24, hy + 40], fill=sil)          # head
    d.polygon([(cx - 78, y1), (cx - 52, hy + 34), (cx + 52, hy + 34),
               (cx + 78, y1)], fill=sil)                             # shoulders
    d.line([(x0, y1 - 1), (x1, y1 - 1)], fill=(10, 18, 30, 255), width=2)


# ------------------------------------------------------------------ stamps
def round_stamp(base, cx, cy, r, ring, inner, color, angle=0):
    """Circular arrival/departure stamp, rotated as a whole."""
    layer = Image.new("RGBA", (r * 2 + 60, r * 2 + 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cc = r + 30
    d.ellipse([30, 30, 30 + 2 * r, 30 + 2 * r], outline=color + (230,),
              width=3)
    d.ellipse([30 + 12, 30 + 12, 30 + 2 * r - 12, 30 + 2 * r - 12],
              outline=color + (230,), width=2)
    ring_text(layer, cc, cc, r - 22, ring, SANS_B(17), color)
    text_center(d, cc, cc - 26, inner, SANS_B(21), color)
    d.line([(cc - 34, cc + 6), (cc + 34, cc + 6)], fill=color + (230,),
           width=2)
    text_center(d, cc, cc + 12, "12 AUG 2026", SANS_B(15), color)
    star(d, cc, cc - 46, 9, color + (230,))
    layer = layer.rotate(angle, resample=Image.BICUBIC, center=(cc, cc))
    base.alpha_composite(layer, (cx - r - 30, cy - r - 30))


def visa_stamp(base, box, angle):
    """Rectangular visa stamp, slightly rotated, red ink."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    layer = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rectangle([20, 20, 20 + w, 20 + h], outline=RED + (225,), width=3)
    d.rectangle([24, 24, 20 + w - 4, 20 + h - 4], outline=RED + (200,),
                width=1)
    text_center(d, 20 + w / 2, 30, "VISA — 90 DAYS", SANS_B(20), RED)
    text_center(d, 20 + w / 2, 56, "MULTIPLE ENTRY", SANS(16), RED)
    text_center(d, 20 + w / 2, 78, "PORT LUMEN • VSP", SANS(16), RED)
    layer = layer.rotate(angle, resample=Image.BICUBIC,
                         center=(20 + w / 2, 20 + h / 2))
    base.alpha_composite(layer, (x0 - 20, y0 - 20))

# ------------------------------------------------------------------ page
def field(d, x, y, label, value, vfnt, w, fill=CREAM):
    d.text((x, y), label, font=SANS_B(14), fill=GOLD_LT)
    d.text((x, y + 20), value, font=vfnt, fill=fill)
    d.line([(x, y + 52), (x + w, y + 52)], fill=(120, 140, 155, 90), width=1)


def render():
    img = Image.new("RGBA", (W, H), NAVY + (255,))
    d = ImageDraw.Draw(img)
    vgrad(d, (0, 0, W, H), (10, 32, 50), (16, 56, 78))
    # faint watermark rose behind everything
    rose = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    compass_rose(rose, 512, 470, 300, (140, 175, 195, 14))
    img.alpha_composite(rose)
    guilloche(img, 512, 470, 330, 560, 7, (150, 185, 205, 10))
    guilloche(img, 90, 950, 60, 260, 9, (150, 185, 205, 8))
    d = ImageDraw.Draw(img)

    # gold frame
    d.rectangle([28, 28, W - 28, H - 28], outline=GOLD + (255,), width=3)
    d.rectangle([36, 36, W - 36, H - 36], outline=GOLD_LT + (255,), width=1)

    # ---- header ------------------------------------------------------
    coat_of_arms(img, 62, 58, 96)
    d = ImageDraw.Draw(img)
    text_center(d, 560, 66, "REPUBLIC OF VESPERA", SERIF_B(42), CREAM)
    text_center(d, 560, 118, "P A S S P O R T", SANS_B(21), GOLD_LT)
    flag(img, 868, 64, 96, 54)
    d.text((868, 124), "VSP", font=SANS_B(15), fill=GOLD_LT)
    d.line([(60, 168), (964, 168)], fill=GOLD + (255,), width=2)

    # ---- portrait ----------------------------------------------------
    px0, py0, px1, py1 = 60, 192, 330, 552
    portrait(img, (px0, py0, px1, py1))
    d = ImageDraw.Draw(img)
    d.rectangle([px0, py0, px1, py1], outline=GOLD + (255,), width=3)
    d.rectangle([px0 + 96, py1 - 30, px1 - 96, py1 - 8],
                fill=(11, 34, 54, 220))
    text_center(d, (px0 + px1) / 2, py1 - 28, "PHOTOGRAPH", SANS_B(13),
                CREAM)

    # ---- data fields ---------------------------------------------------
    fx, fw = 360, 604
    y = 196
    field(d, fx, y, "TYPE", "P", SANS_B(26), 60)
    field(d, fx + 120, y, "COUNTRY CODE", "VSP", SANS_B(26), 150)
    field(d, fx + 330, y, "PASSPORT No.", "VSP260042", SANS_B(26), 200)
    y += 76
    field(d, fx, y, "SURNAME", "MARLOWE", SERIF_B(27), 260)
    field(d, fx + 330, y, "GIVEN NAMES", "ELARA JUNE", SERIF_B(27), 274)
    y += 76
    field(d, fx, y, "NATIONALITY", "VESPERAN", SANS_B(24), 200)
    field(d, fx + 250, y, "SEX", "F", SANS_B(24), 50)
    field(d, fx + 360, y, "DATE OF BIRTH", "14 MAR 1998", SANS_B(24), 220)
    y += 76
    field(d, fx, y, "PLACE OF BIRTH", "PORT LUMEN", SANS_B(24), 240)
    field(d, fx + 280, y, "DATE OF ISSUE", "02 JUN 2026", SANS_B(20), 140)
    field(d, fx + 450, y, "DATE OF EXPIRY", "01 JUN 2036", SANS_B(20), 154)
    y += 76
    field(d, fx, y, "AUTHORITY", "MINISTRY OF TIDES", SANS_B(24), 330)

    # signature squiggle under the photograph + e-passport chip
    sx0, sy = 60, 612
    d.text((sx0, 576), "HOLDER'S SIGNATURE", font=SANS_B(14),
           fill=GOLD_LT)
    pts = []
    for i in range(41):
        t = i / 40
        pts.append((sx0 + 10 + t * 220,
                    sy - 12 + 12 * math.sin(t * math.pi * 3.2)
                    * (1 - t * 0.4) - 8 * t))
    d.line(pts, fill=INK + (255,), width=2)
    d.line([(sx0, sy + 12), (sx0 + 240, sy + 12)],
           fill=(120, 140, 155, 90), width=1)
    chip_cx, chip_cy = 900, 518
    d.ellipse([chip_cx - 24, chip_cy - 24, chip_cx + 24, chip_cy + 24],
              outline=GOLD + (255,), width=2)
    for k in range(3):
        yy = chip_cy - 10 + k * 10
        d.line([(chip_cx - 15, yy), (chip_cx + 15, yy)],
               fill=GOLD_LT + (255,), width=2)

    # ---- stamps --------------------------------------------------------
    round_stamp(img, 880, 600, 64, "PORT LUMEN • ARRIVAL • ", "VESPERA",
                RED, angle=-14)
    round_stamp(img, 700, 636, 58, "VESPERA • DEPARTURE • ", "VSP",
                BLUE, angle=11)
    visa_stamp(img, (384, 596, 664, 700), angle=-8)

    # ---- machine readable zone -----------------------------------------
    d = ImageDraw.Draw(img)
    d.rectangle([60, 716, 964, 852], fill=CREAM + (255,))
    d.rectangle([60, 716, 964, 852], outline=GOLD + (255,), width=2)
    l1, l2 = mrz_lines()
    d.text((78, 734), l1, font=MONO(22), fill=INK)
    d.text((78, 780), l2, font=MONO(22), fill=INK)

    # ---- footer ----------------------------------------------------------
    d.text((60, 872), "This document is the property of the Republic of "
           "Vespera and must be surrendered on demand.",
           font=SANS(15), fill=PALE)
    d.text((60, 894), "Ce document est la propriété de la République de "
           "Vespera.", font=SANS(15), fill=PALE)
    micro = ("REPUBLIC OF VESPERA • MINISTRY OF TIDES • PORT LUMEN • " * 3)
    mf = SANS(10)
    while d.textlength(micro, font=mf) > 890 and len(micro) > 10:
        micro = micro[:-1]
    # never end mid-word: cut back to the last bullet separator
    cut = micro.rfind("• ")
    if cut > 60:
        micro = micro[:cut + 2]
    d.text((60, 922), micro, font=mf, fill=(110, 130, 145))
    d.text((60, 946), "Specimen of a country that isn't there — drawn "
           "entirely in code.", font=SANS(13), fill=GOLD_LT)

    img.convert("RGB").save(OUT, optimize=True)
    print(f"wrote {OUT} {img.size}")


if __name__ == "__main__":
    render()
