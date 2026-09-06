# -*- coding: utf-8 -*-
"""
Рисует иконку приложения без сторонних библиотек.
Запуск:  python3 make_icon.py   →  hush.icns (и hush.png)

На иконке — рыба <>< из трёх шевронов. Знак хозяина.
Рисуется геометрией, а не шрифтом, поэтому одинакова на любой машине.
"""

import math
import os
import struct
import subprocess
import zlib

S = 1024                      # сторона картинки
BG = (0x16, 0x18, 0x1B)       # плитка
EDGE = (0x2A, 0x2E, 0x35)     # кромка
INK = (0x7A, 0x5C, 0xFF)      # рыба
INK2 = (0x9C, 0x86, 0xFF)     # рыба, светлее


def rounded(x, y, w, h, r):
    """Точка (x, y) внутри скруглённого прямоугольника?"""
    cx = min(max(x, r), w - r)
    cy = min(max(y, r), h - r)
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def dist_to_segment(px, py, x1, y1, x2, y2):
    """Расстояние от точки до отрезка."""
    dx, dy = x2 - x1, y2 - y1
    ln = dx * dx + dy * dy
    if ln == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / ln))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def chevron(cx, cy, dx, dy, left):
    """Два отрезка углом.  left=True → «<», иначе «>»."""
    tip = cx - dx if left else cx + dx
    back = cx + dx if left else cx - dx
    return [(back, cy - dy, tip, cy), (tip, cy, back, cy + dy)]


def build():
    px = bytearray(S * S * 4)
    pad = int(S * 0.06)
    side = S - pad * 2
    radius = int(side * 0.235)          # как у иконок macOS

    # <><  — голова, тело, хвост. Рыба смотрит влево.
    dx, dy = 0.085 * side, 0.150 * side
    cy = 0.5 * side
    strokes = (
        [(s, INK2) for s in chevron(0.285 * side, cy, dx, dy, True)]
        + [(s, INK) for s in chevron(0.500 * side, cy, dx, dy, False)]
        + [(s, INK) for s in chevron(0.715 * side, cy, dx, dy, True)]
    )
    half = 0.030 * side                 # полтолщины линии
    aa = 1.6                            # мягкость края

    for y in range(S):
        for x in range(S):
            i = (y * S + x) * 4
            lx, ly = x - pad, y - pad
            if not (0 <= lx <= side and 0 <= ly <= side):
                continue
            if not rounded(lx, ly, side, side, radius):
                continue

            inner = rounded(lx - 3, ly - 3, side - 6, side - 6, radius - 3)
            r, g, b = BG if inner else EDGE

            # ближайший штрих рыбы
            best, colour = 1e9, INK
            for (x1, y1, x2, y2), c in strokes:
                d = dist_to_segment(lx, ly, x1, y1, x2, y2)
                if d < best:
                    best, colour = d, c

            if best <= half + aa:
                k = 1.0 if best <= half - aa else \
                    (half + aa - best) / (2 * aa)
                k = max(0.0, min(1.0, k))
                r = round(r + (colour[0] - r) * k)
                g = round(g + (colour[1] - g) * k)
                b = round(b + (colour[2] - b) * k)

            px[i:i + 4] = bytes((r, g, b, 255))
    return px


def write_png(path, px):
    raw = b"".join(b"\x00" + bytes(px[y * S * 4:(y + 1) * S * 4])
                   for y in range(S))

    def chunk(tag, data):
        c = tag + data
        return (struct.pack(">I", len(data)) + c
                + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF))

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", S, S, 8, 6, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(raw, 9)))
        f.write(chunk(b"IEND", b""))


def make_icns(png, out="hush.icns"):
    """Собираем .icns стандартными утилитами macOS."""
    iconset = "hush.iconset"
    os.makedirs(iconset, exist_ok=True)
    for s in (16, 32, 128, 256, 512):
        for scale, suffix in ((1, ""), (2, "@2x")):
            name = f"{iconset}/icon_{s}x{s}{suffix}.png"
            subprocess.run(["sips", "-z", str(s * scale), str(s * scale),
                            png, "--out", name],
                           capture_output=True, check=True)
    subprocess.run(["iconutil", "-c", "icns", iconset, "-o", out], check=True)
    subprocess.run(["rm", "-rf", iconset])
    return out


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    write_png("hush.png", build())
    print("hush.png written")
    print(make_icns("hush.png"), "written")
