#!/usr/bin/env python3
"""Сборка картинок сайта в assets/img/ (имена и размеры — §6 спецификации).

Что делает:
  * иллюстрации макета: склеивает 2x-тайлы из design/tiles папки прогона (.autopilot/<прогон>/design —
    папка ищется по design/captures.json, имя прогона не прописано) по описанию captures.json
    (обрезка до 2*w, склейка по вертикали); у краёв, где наивная склейка даёт полосу (чужой фон,
    «звон» сжатия), полосные линии заменяет зеркальным продолжением рисунка — остальные края не трогает;
    ct-machine собирает из сетки 2x3 без пурпурной вставки;
  * иконки мессенджеров: квадраты 62x62 из тайла icons-messengers, цвет #4A678D, белое -> прозрачное;
  * фото и логотип: уменьшает исходники assets/img/src через tools/resize.ps1 (System.Drawing),
    PNG затем пережимает без потерь (адаптивные фильтры + zlib 9); там же делается xray-hands-1000.jpg —
    лёгкая версия фото рук для телефона (таск F8, srcset);
  * лёгкие JPEG для мобильного интернета (таск F7; F9 — плюс safety-plane для сравнения доз): из готовых
    PNG иллюстраций делает одноимённые .jpg того же размера (JPEG_NAMES, качество JPEG_QUALITY) тем же
    tools/resize.ps1 (-Step jpeg); PNG остаются на месте;
  * превью ссылки в мессенджере (таск F8): og-preview.jpg 1200x630 — логотип и иллюстрация step-2 на фоне
    страницы (шаг og в tools/resize.ps1, берёт готовые logo-white.png и step-2.png из assets/img).
Исходники в assets/img/src не меняются. Только стандартная библиотека Python + Windows PowerShell 5.1.

Запуск из корня сайта (около полутора минут):
    PYTHONIOENCODING=utf-8 python tools/build_assets.py            # все картинки
    PYTHONIOENCODING=utf-8 python tools/build_assets.py see-01 photos   # выборочно; photos — фото и логотип
    PYTHONIOENCODING=utf-8 python tools/build_assets.py jpeg            # только JPEG из готовых PNG
    PYTHONIOENCODING=utf-8 python tools/build_assets.py og              # только превью og-preview.jpg
    PYTHONIOENCODING=utf-8 python tools/build_assets.py --naive    # склейка без чистки (для проверки проверки)
Потом: PYTHONIOENCODING=utf-8 python tools/check_assets.py
"""
import glob
import json
import os
import statistics
import struct
import subprocess
import sys
import tempfile
import time
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_design():
    """Папка design прогона: любая .autopilot/*/design с captures.json (имя прогона может меняться).
    В публичном репозитории служебной .autopilot нет — тогда пересобирать не из чего: сообщение и код 2."""
    hits = sorted(glob.glob(os.path.join(ROOT, ".autopilot", "*", "design", "captures.json")))
    if not hits:
        print("Пересборка картинок возможна только в локальной копии с папкой .autopilot "
              "(нет .autopilot/*/design/captures.json и тайлов макета) — картинки уже лежат в assets/img.")
        sys.exit(2)
    return os.path.dirname(hits[-1])


DESIGN = find_design()
sys.path.insert(0, DESIGN)
import png  # noqa: E402  (design/png.py — чтение/запись PNG на чистом Python)

OUT = os.path.join(ROOT, "assets", "img")
TILES = os.path.join(DESIGN, "tiles")
RESIZE_PS1 = os.path.join(ROOT, "tools", "resize.ps1")

NAIVE = "--naive" in sys.argv
ONLY = [a for a in sys.argv[1:] if not a.startswith("--")]

# Лёгкие JPEG для страницы (F7, §10.8): базовые имена PNG из assets/img, у JPEG то же имя и тот же размер.
# 82 — нижняя граница диапазона 82–90: на тонких тёмно-синих линиях и плоских фонах артефактов не видно
# (проверено 1:1), а вес 10 файлов вместе ≈ 455 КБ; каждый ≤ 110 КБ (tools/check_assets.py).
# safety-plane (F9, §11) — вторая карточка сравнения доз в «Что важно знать о лучевой нагрузке».
JPEG_NAMES = ["step-1", "step-2", "step-3", "exam-ct", "see-01", "see-02", "see-03", "see-04",
              "safety-ct", "safety-plane", "ct-machine"]
JPEG_QUALITY = 82
# Превью ссылки (F8, G16): 1200x630; 90 — свечение фона без ступенек, вес ≈ 100 КБ при пределе 150 КБ.
OG_QUALITY = 90


# ------------------------------------------------------------------ PNG-кодер с адаптивными фильтрами

def encode_png(path, w, h, px, alpha):
    """px — RGBA bytearray. alpha=False пишет RGB (тип 2)."""
    bpp = 4 if alpha else 3
    stride = w * bpp
    if alpha:
        data = px
    else:
        data = bytearray(w * h * 3)
        data[0::3] = px[0::4]
        data[1::3] = px[1::4]
        data[2::3] = px[2::4]
    out = bytearray()
    prev = bytes(stride)
    for y in range(h):
        line = bytes(data[y * stride:(y + 1) * stride])
        cands = []
        # 0 — None
        cands.append((0, line))
        # 1 — Sub
        sub = bytes(line[:bpp]) + bytes((line[i] - line[i - bpp]) & 255 for i in range(bpp, stride))
        cands.append((1, sub))
        # 2 — Up
        up = bytes((a - b) & 255 for a, b in zip(line, prev))
        cands.append((2, up))
        # 3 — Average
        avg = bytearray(stride)
        for i in range(stride):
            left = line[i - bpp] if i >= bpp else 0
            avg[i] = (line[i] - ((left + prev[i]) >> 1)) & 255
        cands.append((3, bytes(avg)))
        # 4 — Paeth
        pae = bytearray(stride)
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            p = a + b - c
            pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
            pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
            pae[i] = (line[i] - pr) & 255
        cands.append((4, bytes(pae)))
        best = min(cands, key=lambda c: sum(v if v < 128 else 256 - v for v in c[1]))
        out.append(best[0])
        out += best[1]
        prev = line

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)

    comp = zlib.compressobj(9, zlib.DEFLATED, 15, 9)
    idat = comp.compress(bytes(out)) + comp.flush()
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6 if alpha else 2, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b""))
    return os.path.getsize(path)


# ------------------------------------------------------------------ помощники по пикселям

def get_line(img, axis, idx):
    w, h, px = img
    if axis == "row":
        return bytes(px[idx * w * 4:(idx + 1) * w * 4])
    return bytes(b for y in range(h) for b in px[(y * w + idx) * 4:(y * w + idx) * 4 + 4])


def line_diff(a, b):
    n = len(a) // 4
    return sum(abs(a[i] - b[i]) + abs(a[i + 1] - b[i + 1]) + abs(a[i + 2] - b[i + 2])
               for i in range(0, len(a), 4)) / max(1, n)


# Чистка краёв. Захват макета сжат блоками 8 px, поэтому полоса у края (1–2 px чужого фона и «звон»
# сжатия рядом) живёт в зоне EDGE_ZONE. Линия считается полосной, если отличается от соседней
# заметно сильнее, чем соседние линии отличаются друг от друга за зоной (дальше EDGE_ZONE px от края).
EDGE_ZONE = 8
EDGE_MAX_DEPTH = 4     # чистим не глубже половины зоны
EDGE_SEG = 50          # край проверяется участками: полоса бывает не по всей длине
EDGE_FLOOR = 6.0       # меньше этой разницы линий глаз не видит
EDGE_FACTOR = 2.5      # во сколько раз скачок у края больше обычного за зоной
EDGE_SHARE = 0.25      # полоса склейки идёт вдоль края, а не одним пятном у рисунка
EDGE_WHOLE_FLOOR = 8.0  # ...или крайняя линия выделяется по всей длине края


def edge_lines(img, axis, at, count):
    return [get_line(img, axis, at(k)) for k in range(count)]


def stripe_depths(lines):
    """Глубина полосы по участкам края EDGE_SEG (0 — участок чистый). lines[0] — линия у самого края.

    Глубина участка — число линий подряд от края, у которых скачок к следующей больше
    max(EDGE_FLOOR, EDGE_FACTOR × медиана скачков за зоной). Край чистится, только если полоса
    идёт вдоль него — хотя бы на EDGE_SHARE участков — или крайняя линия выделяется по всей
    длине; иначе это контур рисунка у края, и все глубины — 0.
    """
    n = len(lines[0]) // 4

    def depth_of(part):
        d = [line_diff(part[k], part[k + 1]) for k in range(len(part) - 1)]
        limit = max(EDGE_FLOOR, EDGE_FACTOR * statistics.median(d[EDGE_ZONE + 1:]))
        k = 0
        while k < EDGE_MAX_DEPTH and d[k] > limit:
            k += 1
        return k

    depths = [depth_of([ln[s * 4:(s + EDGE_SEG) * 4] for ln in lines]) for s in range(0, n, EDGE_SEG)]
    d = [line_diff(lines[k], lines[k + 1]) for k in range(len(lines) - 1)]
    whole = d[0] > max(EDGE_WHOLE_FLOOR, EDGE_FACTOR * statistics.median(d[EDGE_ZONE + 1:]))
    striped = sum(1 for k in depths if k) >= EDGE_SHARE * len(depths)
    if not (striped or whole):
        return [0] * len(depths)
    if not any(depths):
        return [1] * len(depths)
    return depths


def put_span(img, axis, idx, line, start, stop):
    """Записать в линию idx пиксели start..stop-1 из line (полная линия в байтах RGBA)."""
    w, h, px = img
    if axis == "row":
        px[(idx * w + start) * 4:(idx * w + stop) * 4] = line[start * 4:stop * 4]
    else:
        for y in range(start, stop):
            px[(y * w + idx) * 4:(y * w + idx) * 4 + 4] = line[y * 4:y * 4 + 4]


def fix_edges(img):
    """На участках с полосой (stripe_depths) полосные линии заменяются зеркальным продолжением
    рисунка: k-я от края линия ← (2·depth − k)-я. Фактура и контуры продолжаются, без штрихов-копий;
    участки и края без полосы не меняются. Возвращает {сторона: (наибольшая глубина, участков)}."""
    w, h, _ = img
    done = {}
    for side, axis, at, length in (("right", "col", lambda k: w - 1 - k, h), ("bottom", "row", lambda k: h - 1 - k, w),
                                   ("left", "col", lambda k: k, h), ("top", "row", lambda k: k, w)):
        lines = edge_lines(img, axis, at, 2 * EDGE_ZONE + 6)
        depths = stripe_depths(lines)
        for i, depth in enumerate(depths):
            start, stop = i * EDGE_SEG, min(length, (i + 1) * EDGE_SEG)
            for k in range(depth):
                put_span(img, axis, at(k), lines[2 * depth - k], start, stop)
        done[side] = (max(depths), sum(1 for d in depths if d))
    return done


def report_edges(name, done):
    cleaned = ", ".join("%s до %d px на %d уч." % (side, d, n) for side, (d, n) in done.items() if d)
    print("  %s: края — %s" % (name, cleaned or "без полос"))


def opaque(img):
    w, h, px = img
    px[3::4] = b"\xff" * (w * h)
    return img


def load_tile(name):
    return opaque(png.read(os.path.join(TILES, name)))


# ------------------------------------------------------------------ сборка

def build_stack(item):
    W, H = 2 * item["rect"][2], 2 * item["rect"][3]
    tiles = [load_tile(t) for t in item["tiles"]]
    out = png.blank(W, H)
    y = 0
    for t in tiles:
        png.paste(out, png.crop(t, 0, 0, W, t[1]), 0, y)
        y += t[1]
    assert y == H, (item["name"], y, H)
    if not NAIVE:
        report_edges(item["name"], fix_edges(out))
    return out


def build_ct(item):
    W, H = 2 * item["rect"][2], 2 * item["rect"][3]
    half = W // 2
    (tl, tr), (ml, mr) = [[load_tile(t) for t in row] for row in item["tiles"]]
    pk = load_tile(item["lastRowPacked"])
    out = png.blank(W, H)
    png.paste(out, tl, 0, 0)
    png.paste(out, tr, half, 0)
    png.paste(out, ml, 0, 600)
    png.paste(out, mr, half, 600)
    png.paste(out, png.crop(pk, 0, 0, half, 80), 0, 1200)
    png.paste(out, png.crop(pk, 0, 100, half, 80), half, 1200)
    if NAIVE:
        return out
    w, h, px = out

    def pix(x, y):
        return px[(y * w + x) * 4:(y * w + x) * 4 + 4]

    def put(x, y, c):
        px[(y * w + x) * 4:(y * w + x) * 4 + 4] = c

    # левая нижняя полоса: строка 79 упакованного тайла задета пурпуром — повторяем строку выше
    for x in range(half):
        put(x, 1279, pix(x, 1278))
    # правая нижняя полоса: строка 100 упакованного тайла задета пурпуром — берём строку 1199 (стык)
    for x in range(half, W):
        put(x, 1200, pix(x, 1199))
    # «звон» сжатия под пурпурной полосой (строки 101–125 тайла): тёмный фон приводим
    # к ближайшему из двух чистых цветов заливки (фон и светлая деталь), светлые линии не трогаем
    flat = [bytes((15, 41, 78, 255)), bytes((16, 49, 90, 255))]
    for y in range(1201, 1226):
        for x in range(half, W):
            c = pix(x, y)
            if sum(c[:3]) >= 250:
                continue
            dist = [sum(abs(c[i] - f[i]) for i in range(3)) for f in flat]
            k = 0 if dist[0] <= dist[1] else 1
            if dist[k] < 40:
                put(x, y, flat[k])
    # контроль: пурпурных пикселей не осталось
    for k in range(0, len(px), 4):
        r, g, b = px[k], px[k + 1], px[k + 2]
        if r > g + 8 and b > g + 8:
            y, x = divmod(k // 4, w)
            # заменяем пикселем сверху
            px[k:k + 4] = pix(x, y - 1)
    report_edges(item["name"], fix_edges(out))
    return out


def build_icons(item):
    tile = load_tile(item["tile"])
    C = (0x4A, 0x67, 0x8D)
    dc = [255 - c for c in C]
    norm = sum(v * v for v in dc)
    res = {}
    for name, x0 in (("icon-telegram", 0), ("icon-whatsapp", 80), ("icon-max", 160)):
        sq = png.crop(tile, x0, 0, 62, 62)
        w, h, px = sq
        out = bytearray(w * h * 4)
        for y in range(h):
            for x in range(w):
                k = (y * w + x) * 4
                a = sum((255 - px[k + i]) * dc[i] for i in range(3)) / norm
                a = (a - 0.08) / (0.92 - 0.08)
                a = 0.0 if a < 0 else (1.0 if a > 1 else a)
                if x < 2 or y < 2 or x >= w - 2 or y >= h - 2:
                    a = 0.0
                out[k:k + 3] = bytes(C)
                out[k + 3] = int(round(a * 255))
        res[name] = (w, h, out)
    return res


def premultiply_clean(img):
    """У полностью прозрачных пикселей обнуляем цвет — меньше вес, без «мусора»."""
    w, h, px = img
    for k in range(0, len(px), 4):
        if px[k + 3] == 0:
            px[k:k + 3] = b"\x00\x00\x00"
    return img


def build_photos():
    """Фото и логотип: уменьшение System.Drawing (tools/resize.ps1), затем PNG пережимаем без потерь."""
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", RESIZE_PS1,
                        "-OutDir", tmp], check=True)
        for name in ("hero-xray", "logo-white"):
            img = premultiply_clean(png.read(os.path.join(tmp, "gdi-%s.png" % name)))
            size = encode_png(os.path.join(OUT, name + ".png"), *img, alpha=True)
            print(name, img[0], img[1], size)


def build_jpegs(names):
    """Лёгкие JPEG из готовых PNG assets/img (System.Drawing через tools/resize.ps1, шаг jpeg)."""
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", RESIZE_PS1,
                    "-Step", "jpeg", "-Jpeg", ",".join(names), "-JpegQuality", str(JPEG_QUALITY)], check=True)


def build_og():
    """Превью ссылки для мессенджеров assets/img/og-preview.jpg (System.Drawing через tools/resize.ps1, шаг og)."""
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", RESIZE_PS1,
                    "-Step", "og", "-OgQuality", str(OG_QUALITY)], check=True)


def main():
    d = json.load(open(os.path.join(DESIGN, "captures.json"), encoding="utf-8"))
    for item in d["items"]:
        name = item["name"]
        if ONLY and name not in ONLY:
            continue
        t0 = time.time()
        if name == "icons-messengers":
            for n, (w, h, px) in build_icons(item).items():
                size = encode_png(os.path.join(OUT, n + ".png"), w, h, px, alpha=True)
                print(n, w, h, size)
            continue
        img = build_ct(item) if name == "ct-machine" else build_stack(item)
        w, h, px = img
        size = encode_png(os.path.join(OUT, name + ".png"), w, h, px, alpha=False)
        print(name, w, h, size, "%.1fs" % (time.time() - t0))

    if not ONLY or "photos" in ONLY:
        build_photos()

    # JPEG делаются из PNG, поэтому — после них; при выборочной сборке — только для выбранных (или все по «jpeg»)
    jpegs = [n for n in JPEG_NAMES if not ONLY or "jpeg" in ONLY or n in ONLY]
    if jpegs:
        build_jpegs(jpegs)

    # Превью берёт готовые logo-white.png и step-2.png — поэтому в самом конце; при выборочной сборке —
    # по «og» и когда пересобраны его исходники (photos, step-2).
    if not ONLY or any(n in ONLY for n in ("og", "photos", "step-2")):
        build_og()


if __name__ == "__main__":
    main()
