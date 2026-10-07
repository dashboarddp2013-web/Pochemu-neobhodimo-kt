#!/usr/bin/env python3
"""Проверка картинок и обвязки публикации сайта «Денталь профи».

Запуск из корня сайта:
    PYTHONIOENCODING=utf-8 python tools/check_assets.py

Код возврата 0 — всё в порядке; иначе печатает найденные проблемы и возвращает 1.
Только стандартная библиотека Python 3.

Что проверяется (таск 01, §6 и §7 спецификации):
  * все картинки из §6 на месте и называются ровно так;
  * пиксельные размеры (читаются из заголовков PNG/JPEG) — 2× от макета;
  * лимиты веса для логотипа, фото первого экрана и фото рук;
  * у иконок, логотипа и фото первого экрана есть альфа-канал и прозрачный фон;
  * на краях иллюстраций нет полос, пятен и штрихов: край сравнивается с рисунком за зоной
    чистки (дальше 8 px от края), а не сам с собой; на стыках тайлов нет швов;
  * в ct-machine.png нет пурпурных пикселей;
  * лёгкие JPEG для телефона (таск F7, §10.8; F9, §11 — плюс safety-plane.jpg): 11 файлов с теми же
    именами, что у PNG, тот же пиксельный размер, каждый ≤ 110 КБ, целый файл (маркеры SOI/EOI),
    качество 82 (по таблице квантования, ±1), а все картинки страницы вместе ≤ 1 МБ (в редакции 3
    на странице только эти JPEG: логотип первого экрана — SVG, фото рук со страницы убрано);
  * превью ссылки в мессенджере и лёгкое фото для телефона (таск F8, G16, G15): og-preview.jpg —
    1200×630, ≤ 150 КБ; xray-hands-1000.jpg — 1000×667 (половина xray-hands.jpg), ≤ 80 КБ; оба — целые JPEG;
  * ролик «КТ в работе» для #planning (таск F10, G22, G15): assets/video/kt-video.mp4 — MP4 1200×800,
    без звуковой дорожки, moov перед mdat (воспроизведение начинается до полной загрузки), ≤ 2,5 МБ;
    кадр-заставка assets/video/kt-video-poster.jpg — целый JPEG 1200×800, входит в вес картинок
    страницы; оба — побайтные копии файлов из корня проекта (если те лежат там);
  * есть .nojekyll, workflow GitHub Pages и README со ссылкой на tools/check_site.py и словом «Inter»
    (таблицы «Что заменить» и якорей-заглушек в редакции 2 нет — их проверка снята);
  * в tools/ и README.md нет зашитого имени папки прогона .autopilot/<дата-…> —
    проверки и сборка работают и после её переименования.
"""
import re
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "assets" / "img"

# Имя папки прогона (вида 2026-10-07-что-то) в путях инструментов не прописывается — она ищется.
RUN_DIR_NAME = re.compile(r"\d{4}-\d{2}-\d{2}-[a-z][\w-]*")
NO_RUN_DIR_FILES = sorted((ROOT / "tools").glob("*.py")) + sorted((ROOT / "tools").glob("*.ps1")) + [ROOT / "README.md"]

# Иллюстрации: размер = 2 × (w, h) прямоугольника макета (§6, captures.json → rect).
ILLUSTRATIONS = {
    "safety-ct.png": (770, 712),
    "safety-plane.png": (772, 712),
    "safety-chest.png": (772, 712),
    "exam-only.png": (770, 712),
    "exam-ct.png": (772, 712),
    "see-01.png": (496, 456),
    "see-02.png": (496, 456),
    "see-03.png": (496, 456),
    "see-04.png": (496, 454),
    "see-05.png": (496, 454),
    "see-06.png": (496, 454),
    "case-01.png": (496, 456),
    "case-02.png": (496, 456),
    "case-03.png": (496, 456),
    "case-04.png": (496, 456),
    "case-05.png": (496, 456),
    "case-06.png": (496, 456),
    "step-1.png": (770, 714),
    "step-2.png": (772, 714),
    "step-3.png": (772, 714),
    "step-4.png": (772, 714),
    "ct-machine.png": (1584, 1280),
}
# Склейки из двух тайлов по вертикали: стык на строке 600 (тайлы по 600 px в 2×).
STACKED = [n for n, (w, h) in ILLUSTRATIONS.items() if h > 600 and n != "ct-machine.png"]

# Края иллюстраций: зона чистки tools/build_assets.py — 8 px у края (блок сжатия захвата);
# эталон — линия за ней (дальше 8 px от края), участки края — по EDGE_SEG px.
EDGE_ZONE = 8
EDGE_REF = EDGE_ZONE + 2
EDGE_SEG = 50
EDGE_TOL = 20.0

# Фото и логотип: (ширина, высота, максимум байт, нужна прозрачность).
PHOTOS = {
    "logo-white.png": (436, 259, 30 * 1000, True),
    "hero-xray.png": (1242, 1641, 700 * 1000, True),
    "xray-hands.jpg": (2000, 1334, 400 * 1000, False),
}

# Иконки мессенджеров: квадрат 62×62 (2×), знак 58×58 с полем 2 px, цвет #4A678D.
ICONS = ["icon-telegram.png", "icon-whatsapp.png", "icon-max.png"]
ICON_SIZE = (62, 62)
ICON_COLOR = (0x4A, 0x67, 0x8D)

# Лёгкие JPEG для страницы (F7, §10.8): те же базовые имена и пиксельные размеры, что у одноимённых
# PNG из ILLUSTRATIONS (размер берётся оттуда, а не из JPEG, который проверяется).
JPEGS = ["step-1.jpg", "step-2.jpg", "step-3.jpg", "exam-ct.jpg", "see-01.jpg", "see-02.jpg",
         "see-03.jpg", "see-04.jpg", "safety-ct.jpg", "safety-plane.jpg", "ct-machine.jpg"]
JPEG_MAX_BYTES = 110 * 1000
# Качество JPEG — 82 (F7; §11: safety-plane.jpg «тем же способом, качество 82»). Оценка — по таблице
# квантования яркости против стандартной таблицы IJG; GDI+ при качестве 82 пишет таблицу IJG 81 — допуск ±1.
JPEG_QUALITY = 82
JPEG_QUALITY_TOL = 1
# Вес картинок страницы (G15 — «быстро через мобильный интернет»): кроме JPEG выше, на странице
# растровый только кадр-заставка ролика (F10; G20 — логотип SVG, G22 — фото рук убрано).
# logo-white.png остаётся для превью. Пути — от assets/.
PAGE_EXTRA = ["video/kt-video-poster.jpg"]
PAGE_MAX_BYTES = 1000 * 1000

# Ролик «КТ в работе» (F10, G22): файл → (ширина, высота, максимум байт). Сделан соседней сессией,
# лежит в корне проекта; в assets/video/ — его побайтные копии (корневые файлы не публикуются).
VIDEO_DIR = ROOT / "assets" / "video"
VIDEO_FILE = "kt-video.mp4"
VIDEO_POSTER = "kt-video-poster.jpg"
VIDEO_SIZE = (1200, 800)
VIDEO_MAX_BYTES = 2500 * 1000  # «≤ 2,5 МБ» — ролик грузится по мобильному интернету

# Превью ссылки (og:image) и лёгкая версия фото рук для телефона (F8): (ширина, высота, максимум байт).
PREVIEW_IMAGES = {
    "og-preview.jpg": (1200, 630, 150 * 1000),
    "xray-hands-1000.jpg": (1000, 667, 80 * 1000),
}

problems = []
checks = 0


def fail(msg):
    problems.append(msg)


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        fail(msg)
    return cond


# ---------------------------------------------------------------- заголовки файлов

def png_header(path):
    """(ширина, высота, глубина, тип цвета, есть tRNS) из заголовка PNG."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h, depth, ctype = struct.unpack(">IIBB", data[16:26])
    trns = b"tRNS" in data[:data.find(b"IDAT")] if b"IDAT" in data else False
    return w, h, depth, ctype, trns


# Стандартная таблица квантования яркости (JPEG, приложение K) в естественном порядке и порядок зигзага.
IJG_LUMA = [16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55, 14, 13, 16, 24, 40, 57, 69, 56,
            14, 17, 22, 29, 51, 87, 80, 62, 18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92,
            49, 64, 78, 87, 103, 121, 120, 101, 72, 92, 95, 98, 112, 100, 103, 99]
ZIGZAG = [0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5, 12, 19, 26, 33, 40, 48, 41, 34, 27, 20, 13, 6,
          7, 14, 21, 28, 35, 42, 49, 56, 57, 50, 43, 36, 29, 22, 15, 23, 30, 37, 44, 51, 58, 59, 52, 45, 38, 31,
          39, 46, 53, 60, 61, 54, 47, 55, 62, 63]


def jpeg_quality(path):
    """Качество JPEG по шкале IJG (1–100): ближайшая масштабированная стандартная таблица к таблице
    квантования яркости файла (DQT, таблица 0). None — таблицы нет или она 16-битная."""
    data = path.read_bytes()
    i = 2
    while i + 4 <= len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        length = struct.unpack(">H", data[i + 2:i + 4])[0]
        if marker == 0xDA:
            break
        if marker == 0xDB:
            seg, j = data[i + 4:i + 2 + length], 0
            while j < len(seg):
                precision, table = seg[j] >> 4, seg[j] & 15
                size = 128 if precision else 64
                values = list(seg[j + 1:j + 1 + size])
                j += 1 + size
                if table == 0 and not precision:
                    natural = [0] * 64
                    for k, v in enumerate(values):
                        natural[ZIGZAG[k]] = v

                    def distance(q):
                        scale = 5000 // q if q < 50 else 200 - 2 * q
                        return sum(abs(min(255, max(1, (base * scale + 50) // 100)) - v)
                                   for base, v in zip(IJG_LUMA, natural))
                    return min(range(1, 101), key=distance)
        i += 2 + length
    return None


def jpeg_size(path):
    """(ширина, высота) из маркера SOFn JPEG."""
    data = path.read_bytes()
    if data[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 4 <= len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        length = struct.unpack(">H", data[i + 2:i + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        i += 2 + length
    return None


# ---------------------------------------------------------------- декодер PNG

def png_decode(path):
    """Распаковывает 8-битный PNG без чересстрочности.

    Возвращает (w, h, ch, pixels), где ch = 3 (RGB) или 4 (RGBA), pixels — bytearray.
    """
    data = path.read_bytes()
    pos, idat, palette, trns = 8, [], None, None
    w = h = ctype = depth = inter = None
    while pos < len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8])
        chunk = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, ctype, _, _, inter = struct.unpack(">IIBBBBB", chunk)
        elif typ == b"PLTE":
            palette = chunk
        elif typ == b"tRNS":
            trns = chunk
        elif typ == b"IDAT":
            idat.append(chunk)
        elif typ == b"IEND":
            break
        pos += 12 + ln
    if depth != 8 or inter != 0 or ctype not in (0, 2, 3, 4, 6):
        raise ValueError("неподдерживаемый PNG: глубина %s, тип %s, interlace %s" % (depth, ctype, inter))
    bpp = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(b"".join(idat))
    stride = w * bpp
    out = bytearray(stride * h)
    prev = bytearray(stride)
    i = 0
    for y in range(h):
        f = raw[i]
        i += 1
        line = bytearray(raw[i:i + stride])
        i += stride
        if f == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 255
        elif f == 2:
            line = bytearray((a + b) & 255 for a, b in zip(line, prev))
        elif f == 3:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if (pa <= pb and pa <= pc) else (b if pb <= pc else c))) & 255
        out[y * stride:(y + 1) * stride] = line
        prev = line
    if ctype in (2, 6):
        return w, h, bpp, out
    # серый и палитра — разворачиваем в RGB/RGBA
    has_alpha = ctype == 4 or trns is not None
    ch = 4 if has_alpha else 3
    res = bytearray(w * h * ch)
    for k in range(w * h):
        if ctype == 3:
            idx = out[k]
            rgb = palette[idx * 3:idx * 3 + 3]
            a = trns[idx] if (trns is not None and idx < len(trns)) else 255
        elif ctype == 0:
            rgb = bytes((out[k],)) * 3
            a = 255
        else:
            rgb = bytes((out[k * 2],)) * 3
            a = out[k * 2 + 1]
        res[k * ch:k * ch + 3] = rgb
        if has_alpha:
            res[k * ch + 3] = a
    return w, h, ch, res


# ---------------------------------------------------------------- сравнение строк и столбцов

def line_px(img, axis, idx, start=0, stop=None):
    """Пиксели (RGB) строки (axis='row') или столбца (axis='col') с номером idx."""
    w, h, ch, px = img
    if axis == "row":
        stop = w if stop is None else stop
        base = idx * w
        return [tuple(px[(base + x) * ch:(base + x) * ch + 3]) for x in range(start, stop)]
    stop = h if stop is None else stop
    return [tuple(px[(y * w + idx) * ch:(y * w + idx) * ch + 3]) for y in range(start, stop)]


def mean_diff(a, b):
    """Средняя по пикселям сумма |ΔR|+|ΔG|+|ΔB|."""
    return sum(abs(p[0] - q[0]) + abs(p[1] - q[1]) + abs(p[2] - q[2]) for p, q in zip(a, b)) / max(1, len(a))


def along_diff(line):
    """Средняя разность соседних пикселей вдоль линии (насколько «живой» рисунок вдоль края)."""
    return sum(abs(p[0] - q[0]) + abs(p[1] - q[1]) + abs(p[2] - q[2])
               for p, q in zip(line, line[1:])) / max(1, len(line) - 1)


def check_edges(name, img):
    """Края иллюстрации сверяются с рисунком ЗА зоной чистки (EDGE_ZONE px от края), а не сами с собой.

    Для каждой стороны и каждого участка края длиной EDGE_SEG:
    1) полоса: крайняя (или вторая) линия отличается от линии EDGE_REF (за зоной) сильнее,
       чем линия ещё на EDGE_REF глубже, и сильнее, чем линия на два шага ближе к рисунку, —
       то есть цвет у самого края взялся не из рисунка (чужой фон, «звон» сжатия, заливка).
       Полоса склейки тянется вдоль края, поэтому ошибка — два участка подряд; одиночный участок —
       это контур рисунка, подошедший к краю;
    2) штрихи и пятна-копии: у края три линии подряд — копии друг друга, хотя за зоной рисунок
       фактурный и меняется поперёк края (так выглядит «размазанная» копия одной линии).
    """
    w, h, ch, px = img
    sides = {
        "правый край": ("col", lambda k: w - 1 - k, h),
        "нижний край": ("row", lambda k: h - 1 - k, w),
        "левый край": ("col", lambda k: k, h),
        "верхний край": ("row", lambda k: k, w),
    }
    ref = EDGE_REF
    for side, (axis, at, n) in sides.items():
        lines = [line_px(img, axis, at(k)) for k in range(2 * ref + 1)]
        # участки по EDGE_SEG px; короткий хвост у угла присоединяется к предыдущему участку
        starts = list(range(0, n, EDGE_SEG))
        if len(starts) > 1 and n - starts[-1] < EDGE_SEG // 2:
            starts.pop()
        stripes = []
        for s, e in zip(starts, starts[1:] + [n]):
            seg = [ln[s:e] for ln in lines]
            where = "%s: %s, участок %d–%d" % (name, side, s, e)
            deeper = mean_diff(seg[2 * ref], seg[ref])
            bad = None
            for k in (0, 1):
                out = mean_diff(seg[k], seg[ref])
                inner = mean_diff(seg[k + 2], seg[ref])
                if out > max(EDGE_TOL, 3.0 * deeper, 2.0 * inner + EDGE_TOL / 2):
                    bad = ("%s — линия %d от края не похожа на рисунок за зоной (%.1f; глубже %.1f; "
                           "ближе к рисунку %.1f): полоса" % (where, k, out, deeper, inner))
                    break
            stripes.append(bad)
            perp = [mean_diff(seg[k], seg[k + 1]) for k in range(2 * ref)]
            zone_copy = sorted(perp[:3])[1]                     # медиана трёх крайних пар
            beyond_perp = sorted(perp[ref:2 * ref])[ref // 2]    # медиана за зоной
            beyond_along = sum(along_diff(seg[k]) for k in range(ref, 2 * ref)) / ref
            textured = beyond_perp >= 1.0 and beyond_perp >= 0.4 * beyond_along
            ok(not (textured and zone_copy <= 0.5 and along_diff(seg[0]) >= 2.0),
               "%s — у края штрихи: линии-копии (%.2f) при фактуре за зоной (%.2f)" % (where, zone_copy, beyond_perp))
        for i, bad in enumerate(stripes):
            neighbour = (i > 0 and stripes[i - 1]) or (i + 1 < len(stripes) and stripes[i + 1])
            ok(not (bad and neighbour), "%s (и на соседнем участке)" % bad)


def check_seam(name, lines, where):
    """lines — 6 линий подряд, стык между 3-й и 4-й (индексы 2 и 3).

    1) сдвиг/ступенька: переход на стыке не резче соседних;
    2) полоса: линия у стыка не выделяется сразу из обеих соседних,
       если соседи через неё похожи друг на друга (тёмная/цветная линия на стыке).
    """
    d = [mean_diff(lines[k], lines[k + 1]) for k in range(5)]
    ok(d[2] <= max(10.0, 3.0 * max(d[1], d[3])),
       "%s: шов на стыке %s: %.1f при соседних %.1f/%.1f" % (name, where, d[2], d[1], d[3]))
    for k in (2, 3):
        skip = mean_diff(lines[k - 1], lines[k + 1])
        ok(min(d[k - 1], d[k]) <= max(10.0, 2.5 * skip),
           "%s: полоса на стыке %s (линия %d из 6): %.1f/%.1f при %.1f через неё" % (name, where, k + 1, d[k - 1], d[k], skip))


def check_row_seam(name, img, y, x0=0, x1=None):
    """Строка y — первая строка нижнего тайла."""
    lines = [line_px(img, "row", k, x0, x1) for k in range(y - 3, y + 3)]
    check_seam(name, lines, "строк %d/%d (x %d–%s)" % (y - 1, y, x0, x1 if x1 is not None else img[0]))


def check_col_seam(name, img, x):
    lines = [line_px(img, "col", k) for k in range(x - 3, x + 3)]
    check_seam(name, lines, "столбцов %d/%d" % (x - 1, x))


def count_magenta(img):
    """Пиксели с пурпурным оттенком: красный и синий заметно выше зелёного."""
    w, h, ch, px = img
    n = 0
    for k in range(0, w * h * ch, ch):
        r, g, b = px[k], px[k + 1], px[k + 2]
        if r > g + 8 and b > g + 8:
            n += 1
    return n


# ---------------------------------------------------------------- проверки

def check_images():
    names = list(ILLUSTRATIONS) + list(PHOTOS) + ICONS
    for name in names:
        ok((IMG / name).is_file(), "нет файла assets/img/%s" % name)

    for name, (ew, eh) in ILLUSTRATIONS.items():
        path = IMG / name
        if not path.is_file():
            continue
        hdr = png_header(path)
        if not ok(hdr is not None, "%s — не PNG" % name):
            continue
        ok((hdr[0], hdr[1]) == (ew, eh), "%s: размер %d×%d, нужен %d×%d" % (name, hdr[0], hdr[1], ew, eh))
        if (hdr[0], hdr[1]) != (ew, eh):
            continue
        img = png_decode(path)
        check_edges(name, img)
        if name in STACKED:
            check_row_seam(name, img, 600)
        if name == "ct-machine.png":
            n = count_magenta(img)
            ok(n == 0, "ct-machine.png: %d пурпурных пикселей" % n)
            half = ew // 2
            for y in (600, 1200):
                check_row_seam(name, img, y, 0, half)
                check_row_seam(name, img, y, half, ew)
            check_col_seam(name, img, half)

    for name, (ew, eh, max_bytes, need_alpha) in PHOTOS.items():
        path = IMG / name
        if not path.is_file():
            continue
        size = path.stat().st_size
        ok(size <= max_bytes, "%s: %d байт, предел %d" % (name, size, max_bytes))
        if name.endswith(".jpg"):
            dims = jpeg_size(path)
            if ok(dims is not None, "%s — не JPEG" % name):
                ok(dims == (ew, eh), "%s: размер %d×%d, нужен %d×%d" % (name, dims[0], dims[1], ew, eh))
            continue
        hdr = png_header(path)
        if not ok(hdr is not None, "%s — не PNG" % name):
            continue
        ok((hdr[0], hdr[1]) == (ew, eh), "%s: размер %d×%d, нужен %d×%d" % (name, hdr[0], hdr[1], ew, eh))
        if need_alpha:
            ok(hdr[3] in (4, 6) or hdr[4], "%s: нет альфа-канала" % name)
            img = png_decode(path)
            w, h, ch, px = img
            if ok(ch == 4, "%s: нет альфа-канала после распаковки" % name):
                alphas = px[3::4]
                clear = alphas.count(0)
                # в исходнике фото первого экрана непрозрачные пиксели имеют альфу 254
                solid = sum(1 for a in alphas if a >= 250)
                ok(clear >= w * h * 0.2, "%s: прозрачного фона почти нет (%d пикс.)" % (name, clear))
                ok(solid >= w * h * 0.02, "%s: почти нет непрозрачных пикселей (%d)" % (name, solid))
                if name == "hero-xray.png":
                    corners = [px[(y * w + x) * 4 + 3] for x, y in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
                    ok(max(corners) == 0, "%s: углы не прозрачные (альфа %s)" % (name, corners))

    for name in ICONS:
        path = IMG / name
        if not path.is_file():
            continue
        hdr = png_header(path)
        if not ok(hdr is not None, "%s — не PNG" % name):
            continue
        ok((hdr[0], hdr[1]) == ICON_SIZE, "%s: размер %d×%d, нужен %d×%d" % ((name,) + hdr[:2] + ICON_SIZE))
        if not ok(hdr[3] in (4, 6) or hdr[4], "%s: нет альфа-канала" % name):
            continue
        w, h, ch, px = png_decode(path)
        if not ok(ch == 4, "%s: нет альфа-канала после распаковки" % name):
            continue
        alpha = lambda x, y: px[(y * w + x) * 4 + 3]
        border = [alpha(x, y) for y in range(h) for x in range(w)
                  if x < 2 or y < 2 or x >= w - 2 or y >= h - 2]
        ok(max(border) == 0, "%s: поле 2 px вокруг знака не прозрачное (макс. альфа %d)" % (name, max(border)))
        opaque = [(x, y) for y in range(h) for x in range(w) if alpha(x, y) >= 250]
        ok(len(opaque) >= w * h * 0.25, "%s: мало непрозрачных пикселей (%d)" % (name, len(opaque)))
        bad = 0
        for y in range(h):
            for x in range(w):
                k = (y * w + x) * 4
                if px[k + 3] >= 128 and any(abs(px[k + c] - ICON_COLOR[c]) > 6 for c in range(3)):
                    bad += 1
        ok(bad == 0, "%s: %d пикселей знака не цвета #4A678D" % (name, bad))
        inner_clear = sum(1 for y in range(8, h - 8) for x in range(8, w - 8) if alpha(x, y) < 20)
        ok(inner_clear >= 40, "%s: внутри знака нет прозрачных (белых) деталей" % name)


def check_jpegs():
    """Лёгкие JPEG: есть, размер как у PNG, вес ≤ JPEG_MAX_BYTES, файл не оборван, качество JPEG_QUALITY;
    сумма по странице ≤ PAGE_MAX_BYTES."""
    total, complete = 0, True
    for name in JPEGS:
        path = IMG / name
        if not ok(path.is_file(), "нет файла assets/img/%s" % name):
            complete = False
            continue
        data = path.read_bytes()
        total += len(data)
        ok(len(data) <= JPEG_MAX_BYTES, "%s: %d байт, предел %d" % (name, len(data), JPEG_MAX_BYTES))
        ok(data[:2] == b"\xff\xd8" and data[-2:] == b"\xff\xd9", "%s — не целый JPEG (нет маркера SOI или EOI)" % name)
        quality = jpeg_quality(path)
        ok(quality is not None and abs(quality - JPEG_QUALITY) <= JPEG_QUALITY_TOL,
           "%s: качество JPEG %s, нужно %d (±%d)" % (name, quality, JPEG_QUALITY, JPEG_QUALITY_TOL))
        want = ILLUSTRATIONS[name[:-4] + ".png"]
        dims = jpeg_size(path)
        if ok(dims is not None, "%s — не JPEG" % name):
            ok(dims == want, "%s: размер %d×%d, нужен %d×%d (как у %s.png)" % ((name,) + dims + want + (name[:-4],)))
    for name in PAGE_EXTRA:
        path = ROOT / "assets" / name
        if path.is_file():
            total += path.stat().st_size
        else:
            complete = False
    if complete:
        ok(total <= PAGE_MAX_BYTES, "картинки страницы весят %d байт, предел %d" % (total, PAGE_MAX_BYTES))


def check_preview_images():
    """Два новых файла F8: есть, JPEG целый, размер в пикселях точный, вес в пределах."""
    for name, (ew, eh, max_bytes) in PREVIEW_IMAGES.items():
        path = IMG / name
        if not ok(path.is_file(), "нет файла assets/img/%s" % name):
            continue
        data = path.read_bytes()
        ok(len(data) <= max_bytes, "%s: %d байт, предел %d" % (name, len(data), max_bytes))
        ok(data[:2] == b"\xff\xd8" and data[-2:] == b"\xff\xd9", "%s — не целый JPEG (нет маркера SOI или EOI)" % name)
        dims = jpeg_size(path)
        if ok(dims is not None, "%s — не JPEG" % name):
            ok(dims == (ew, eh), "%s: размер %d×%d, нужен %d×%d" % (name, dims[0], dims[1], ew, eh))


def mp4_boxes(data, start=0, end=None):
    """[(тип, начало содержимого, конец)] боксов MP4 одного уровня в data[start:end]."""
    end = len(data) if end is None else end
    boxes, i = [], start
    while i + 8 <= end:
        size, kind = struct.unpack(">I4s", data[i:i + 8])
        head = 8
        if size == 1:
            size, head = struct.unpack(">Q", data[i + 8:i + 16])[0], 16
        elif size == 0:
            size = end - i
        if size < head or i + size > end:
            break
        boxes.append((kind.decode("latin-1"), i + head, i + size))
        i += size
    return boxes


def mp4_tracks(data, moov):
    """[(тип дорожки из hdlr — 'vide', 'soun'…, (ширина, высота) из tkhd)] в боксе moov."""
    tracks = []
    for kind, s, e in mp4_boxes(data, moov[1], moov[2]):
        if kind != "trak":
            continue
        handler, size = None, None
        for sub, ss, se in mp4_boxes(data, s, e):
            if sub == "tkhd":
                w, h = struct.unpack(">II", data[se - 8:se])
                size = (w >> 16, h >> 16)
            elif sub == "mdia":
                for leaf, ls, le in mp4_boxes(data, ss, se):
                    if leaf == "hdlr":
                        handler = data[ls + 8:ls + 12].decode("latin-1")
        tracks.append((handler, size))
    return tracks


def check_video():
    """F10: ролик и кадр-заставка в assets/video/ — копии файлов из корня, лёгкие и годные для потока."""
    video, poster = VIDEO_DIR / VIDEO_FILE, VIDEO_DIR / VIDEO_POSTER
    if ok(video.is_file(), "нет файла assets/video/%s" % VIDEO_FILE):
        data = video.read_bytes()
        ok(len(data) <= VIDEO_MAX_BYTES, "%s: %d байт, предел %d (2,5 МБ)" % (VIDEO_FILE, len(data), VIDEO_MAX_BYTES))
        top = mp4_boxes(data)
        kinds = [k for k, _, _ in top]
        if ok(kinds[:1] == ["ftyp"] and "moov" in kinds and "mdat" in kinds,
              "%s — не MP4 (боксы верхнего уровня %s)" % (VIDEO_FILE, kinds[:6])):
            ok(kinds.index("moov") < kinds.index("mdat"),
               "%s: moov после mdat — ролик не начнёт играть, пока не скачается целиком (нужен faststart)" % VIDEO_FILE)
            tracks = mp4_tracks(data, top[kinds.index("moov")])
            ok([t for t, _ in tracks] == ["vide"],
               "%s: дорожки %s — нужна одна видеодорожка без звука" % (VIDEO_FILE, [t for t, _ in tracks]))
            sizes = [s for t, s in tracks if t == "vide"]
            ok(sizes == [VIDEO_SIZE], "%s: размер кадра %s, нужен %d×%d" % ((VIDEO_FILE, sizes) + VIDEO_SIZE))
    if ok(poster.is_file(), "нет кадра-заставки assets/video/%s" % VIDEO_POSTER):
        data = poster.read_bytes()
        ok(data[:2] == b"\xff\xd8" and data[-2:] == b"\xff\xd9", "%s — не целый JPEG (нет маркера SOI или EOI)" % VIDEO_POSTER)
        dims = jpeg_size(poster)
        ok(dims == VIDEO_SIZE, "%s: размер %s, нужен %d×%d — как у ролика" % ((VIDEO_POSTER, dims) + VIDEO_SIZE))
    for path in (video, poster):
        source = ROOT / path.name
        if path.is_file() and source.is_file():
            ok(path.read_bytes() == source.read_bytes(),
               "assets/video/%s — не побайтная копия %s из корня проекта" % (path.name, path.name))


def check_publishing():
    ok((ROOT / ".nojekyll").is_file(), "нет .nojekyll в корне")

    wf = ROOT / ".github" / "workflows" / "pages.yml"
    if ok(wf.is_file(), "нет .github/workflows/pages.yml"):
        text = wf.read_text(encoding="utf-8")
        for needle, why in [
            ("workflow_dispatch", "ручной запуск"),
            ("branches:", "ветка для push"),
            ("main", "ветка main"),
            ("pages: write", "право pages: write"),
            ("id-token: write", "право id-token: write"),
            ("actions/checkout@", "actions/checkout"),
            ("actions/configure-pages@", "actions/configure-pages"),
            ("actions/upload-pages-artifact@", "actions/upload-pages-artifact"),
            ("actions/deploy-pages@", "actions/deploy-pages"),
            ("index.html", "index.html в артефакте"),
            (".nojekyll", ".nojekyll в артефакте"),
            ("assets", "assets/ в артефакте"),
            ("assets/img/src", "исключение исходников assets/img/src"),
        ]:
            ok(needle in text, "pages.yml: нет «%s» (%s)" % (needle, why))
        ok("push:" in text, "pages.yml: нет запуска на push")

    readme = ROOT / "README.md"
    if ok(readme.is_file(), "нет README.md"):
        text = readme.read_text(encoding="utf-8")
        for needle in ["tools/check_site.py", "Inter"]:
            ok(needle in text, "README.md: нет «%s»" % needle)

    for path in NO_RUN_DIR_FILES:
        if path.is_file():
            hits = sorted(set(RUN_DIR_NAME.findall(path.read_text(encoding="utf-8"))))
            ok(not hits, "%s: зашито имя папки прогона %s — её нужно искать (.autopilot/*/design)"
               % (path.relative_to(ROOT).as_posix(), ", ".join(hits)))


def main():
    check_images()
    check_jpegs()
    check_preview_images()
    check_video()
    check_publishing()
    if problems:
        print("Найдено проблем: %d (проверок: %d)" % (len(problems), checks))
        for p in problems:
            print("  - " + p)
        return 1
    print("Всё в порядке: %d проверок пройдено." % checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
