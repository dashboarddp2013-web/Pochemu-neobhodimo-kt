#!/usr/bin/env python3
"""Проверка страницы сайта «Денталь профи» без браузера.

Запуск из корня сайта:
    PYTHONIOENCODING=utf-8 python tools/check_site.py

Код возврата 0 — всё в порядке; иначе печатает найденные проблемы и возвращает 1.
Только стандартная библиотека Python 3.

Что проверяется (тестовый шов из interfaces.md):
  1. index.html разбирается html.parser без незакрытых и лишних тегов в body;
  2. каждый текст из design/frame1-desktop.json (узлы «p») есть в видимом тексте
     страницы после нормализации пробелов и регистра; для исправлений §8 спеки
     проверяется исправленный вариант (одно «лечения», «Без КТ» — 01–06 по порядку);
  3. у каждого <img> есть непустой alt (или alt="" + aria-hidden="true"), width,
     height, файл существует; ниже первого экрана — loading="lazy";
  4. пункты меню и кнопки ведут на заглушки §7; все ссылки — только якоря,
     ни одного адреса мессенджеров; в начале файла — комментарий «ЗАМЕНИТЬ»;
  5. все 9 id секций на месте и в нужном порядке; ровно один h1; у секций есть h2.
Плюс: lang="ru", шрифт Manrope подключён строкой из interfaces.md, нет style=""
(кроме aspect-ratio); в style.css у кнопок .btn скругление var(--radius-btn) = 12px
на всех ширинах, у карточек и ячеек углы прямые (G02); в секциях 4 и 6 под сеткой
иллюстраций нет пустой полосы (G01, таск F2): по числам style.css и размерам картинок
высота сетки равна высоте списка на десктопе, а на планшете список и сетка
переносятся друг под друга и строки списка растягиваются до высоты сетки;
в первом экране нет вертикальных линий — ни разметки, ни стилей (G03, таск F3).

Эталон текстов ищется, а не прописан: первая по имени .autopilot/*/design/frame1-desktop.json
(папку прогона можно переименовать). Служебной папки .autopilot нет в публичном репозитории —
там сверка текстов с эталоном пропускается (строка «ПРОПУСК: …»), остальные проверки идут как обычно.
"""
import json
import re
import struct
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
STYLE = ROOT / "assets" / "css" / "style.css"
DESKTOP_JSON_GLOB = ".autopilot/*/design/frame1-desktop.json"


def find_desktop_json():
    """Эталон текстов макета из папки прогона (имя папки не важно)."""
    hits = sorted(ROOT.glob(DESKTOP_JSON_GLOB))
    return hits[-1] if hits else None


DESKTOP_JSON = find_desktop_json()

# G02: кнопки скруглены токеном §3, карточки и ячейки — с прямыми углами.
RADIUS_TOKEN = "--radius-btn"
RADIUS_VALUE = "12px"
SQUARE_BLOCKS = ("card", "card__media", "card__img", "facts__cell", "facts__img")

# G01 (таск F2): секции 4 и 6 — список из 6 строк рядом с сеткой 3×2 без пустой полосы под сеткой.
FACTS_SECTIONS = ("see", "cases")
FACTS_TOLERANCE = 8   # px: допуск разницы нижних краёв списка и сетки
FACTS_MIN_LIST = 300  # px: уже — список и сетка друг под другом
TABLET_MEDIA = "@media (max-width: 1199.98px)"
PHONE_MEDIA = "@media (max-width: 767.98px)"

SECTION_IDS = ["top", "safety", "exam", "see", "quality", "cases", "after", "best", "questions"]
MENU_STUBS = ["#uslugi", "#ceny", "#komanda", "#akcii", "#otzyvy", "#pacientam", "#kontakty"]
BUTTON_STUBS = ["#video", "#vopros", "#telegram", "#whatsapp", "#max"]
ALL_STUBS = MENU_STUBS + BUTTON_STUBS
MENU_TEXTS = ["Услуги", "Цены", "Команда", "Акции", "Отзывы", "Пациентам", "Контакты"]

FONT_HREF = "https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700&display=swap"
FORBIDDEN_HOSTS = re.compile(
    r"(t\.me|telegram\.(me|org|dog)|wa\.me|whatsapp\.com|max\.ru|vk\.com|instagram\.com|ok\.ru)",
    re.I,
)

# §8 спеки: исправления текста макета.
DOUBLED_PHRASE = "тактики лечения лечения врач"
FIXED_PHRASE = "тактики лечения врач"

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "source", "track", "wbr"}
HIDDEN_TAGS = {"head", "script", "style", "template", "noscript", "title"}

problems = []
skipped = []  # пропущенные проверки (нет данных в этой копии) — не ошибка
checks = 0


def fail(msg):
    problems.append(msg)


def check(cond, msg):
    global checks
    checks += 1
    if not cond:
        fail(msg)
    return cond


def norm(text):
    """Нормализация для сравнения: без пробельных символов, нижний регистр."""
    return re.sub(r"\s+", "", text).lower()


class Node:
    def __init__(self, tag, attrs, parent, line):
        self.tag = tag
        self.attrs = dict(attrs)
        self.parent = parent
        self.children = []  # Node или str
        self.line = line

    @property
    def classes(self):
        return (self.attrs.get("class") or "").split()

    def iter(self):
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.iter()

    def ancestors(self):
        node = self.parent
        while node is not None:
            yield node
            node = node.parent

    def text(self):
        parts = []
        for child in self.children:
            parts.append(child if isinstance(child, str) else child.text())
        return "".join(parts)


class TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#document", [], None, 0)
        self.stack = [self.root]
        self.comments = []  # (позиция строки, текст)
        self.errors = []
        self.body_line = None

    def handle_starttag(self, tag, attrs):
        line = self.getpos()[0]
        node = Node(tag, attrs, self.stack[-1], line)
        self.stack[-1].children.append(node)
        if tag == "body":
            self.body_line = line
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        line = self.getpos()[0]
        node = Node(tag, attrs, self.stack[-1], line)
        self.stack[-1].children.append(node)
        in_foreign = any(n.tag in {"svg", "math"} for n in self.stack) or tag in {"svg", "math"}
        if tag not in VOID and not in_foreign:
            self.errors.append(f"строка {line}: <{tag}/> — самозакрытие не-пустого тега")

    def handle_endtag(self, tag):
        line = self.getpos()[0]
        if tag in VOID:
            self.errors.append(f"строка {line}: лишний закрывающий </{tag}>")
            return
        open_tags = [n.tag for n in self.stack[1:]]
        if tag not in open_tags:
            self.errors.append(f"строка {line}: </{tag}> без открывающего тега")
            return
        while self.stack[-1].tag != tag:
            lost = self.stack.pop()
            self.errors.append(
                f"строка {lost.line}: <{lost.tag}> не закрыт (встретился </{tag}> в строке {line})")
        self.stack.pop()

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def handle_comment(self, data):
        self.comments.append((self.getpos()[0], data))


def visible_text(node):
    if isinstance(node, str):
        return node
    if node.tag in HIDDEN_TAGS or "hidden" in node.attrs:
        return ""
    sep = " " if node.tag in {"br", "p", "div", "li", "h1", "h2", "h3", "a", "span"} else ""
    return sep + "".join(visible_text(c) for c in node.children) + sep


def find_all(root, pred):
    return [n for n in root.iter() if pred(n)]


def by_class(root, cls):
    return find_all(root, lambda n: cls in n.classes)


def main():
    if not INDEX.is_file():
        print(f"ПРОБЛЕМА: нет файла {INDEX.relative_to(ROOT)} — страница не свёрстана")
        print("Итог: 1 проблема")
        return 1

    raw = INDEX.read_text(encoding="utf-8")
    parser = TreeBuilder()
    parser.feed(raw)
    parser.close()
    root = parser.root

    # --- 1. Разбор без незакрытых тегов ---
    for err in parser.errors:
        fail(f"[1] {err}")
    unclosed = [n for n in parser.stack[1:] if n.tag not in {"html", "body"}]
    for n in unclosed:
        fail(f"[1] строка {n.line}: <{n.tag}> не закрыт до конца файла")
    check(not parser.errors and not unclosed, "[1] разметка с ошибками вложенности (см. выше)")
    bodies = find_all(root, lambda n: n.tag == "body")
    check(len(bodies) == 1, f"[1] ожидался один <body>, найдено {len(bodies)}")
    if not bodies:
        return report()
    body = bodies[0]
    html = find_all(root, lambda n: n.tag == "html")
    check(bool(html) and html[0].attrs.get("lang") == "ru", '[a11y] у <html> нет lang="ru"')

    # --- 2. Тексты макета ---
    page_text = norm(visible_text(body))
    if DESKTOP_JSON is None:
        # Публичная копия без служебной .autopilot: сверять тексты не с чем.
        skipped.append(f"[2] эталон текстов макета ({DESKTOP_JSON_GLOB}) есть только в локальной "
                       "копии — проверка текстов пропущена")
    else:
        frame = json.loads(DESKTOP_JSON.read_text(encoding="utf-8"))
        texts = [n[5] for n in frame["nodes"] if n[0] == "p" and n[5].strip()]
        check(len(texts) > 100, f"[2] в эталоне подозрительно мало текстов: {len(texts)}")
        for text in texts:
            text = text.split(" SPANS:")[0]  # служебная разметка размеров спанов
            if DOUBLED_PHRASE in text:
                text = text.replace(DOUBLED_PHRASE, FIXED_PHRASE)  # §8
            check(norm(text) in page_text, f"[2] нет текста макета: «{text[:70]}»")

    # §8 эталона не требует: нет «лечения лечения»; «Без КТ» — 01–06 по порядку, «С КТ» — 01–05.
    check(norm(DOUBLED_PHRASE) not in page_text, "[2] §8: осталось двойное «лечения лечения»")
    for cls, count in (("compare__col--bad", 6), ("compare__col--good", 5)):
        cols = by_class(body, cls)
        if check(len(cols) == 1, f"[2] нужен ровно один .{cls}, найдено {len(cols)}"):
            nums = [norm(c.text()) for c in by_class(cols[0], "compare__circle")]
            want = [f"{i:02d}" for i in range(1, count + 1)]
            check(nums == want, f"[2] §8: номера в .{cls} {nums}, ожидалось {want}")

    # --- 3. Картинки ---
    imgs = find_all(body, lambda n: n.tag == "img")
    check(len(imgs) >= 25, f"[3] картинок на странице {len(imgs)}, ожидалось не меньше 25")
    for img in imgs:
        src = img.attrs.get("src") or ""
        where = f"<img src=\"{src}\"> (строка {img.line})"
        alt = img.attrs.get("alt")
        if alt is None:
            fail(f"[3] {where}: нет alt")
        elif not alt.strip():
            check(img.attrs.get("aria-hidden") == "true",
                  f"[3] {where}: пустой alt без aria-hidden=\"true\"")
        for dim in ("width", "height"):
            val = img.attrs.get(dim) or ""
            check(val.isdigit() and int(val) > 0, f"[3] {where}: нет корректного {dim}")
        check(bool(src) and not re.match(r"^[a-z]+:|^/", src, re.I),
              f"[3] {where}: путь должен быть относительным")
        check((ROOT / src.split("?")[0]).is_file(), f"[3] {where}: файл не найден")
        check("/src/" not in src, f"[3] {where}: исходники assets/img/src/ в вёрстке не используются")
        first_screen = any(a.tag == "header" or a.attrs.get("id") == "top"
                           or "mobile-menu" in a.classes for a in img.ancestors())
        if not first_screen:
            check(img.attrs.get("loading") == "lazy", f"[3] {where}: ниже первого экрана нужен loading=\"lazy\"")

    # --- 4. Ссылки и заглушки §7 ---
    ids = {n.attrs["id"] for n in body.iter() if n.attrs.get("id")}
    links = find_all(body, lambda n: n.tag == "a")
    for a in links:
        href = a.attrs.get("href")
        where = f"<a> «{a.text().strip()[:30]}» (строка {a.line})"
        if not check(href is not None, f"[4] {where}: нет href"):
            continue
        check(not FORBIDDEN_HOSTS.search(href), f"[4] {where}: выдуманный адрес мессенджера {href}")
        if check(href.startswith("#"), f"[4] {where}: внешний адрес {href} — нужны заглушки §7"):
            check(href in ALL_STUBS or href[1:] in ids, f"[4] {where}: якорь {href} никуда не ведёт")
    for tag in find_all(root, lambda n: n.tag in {"link", "script", "img", "iframe", "form"}):
        for attr in ("href", "src", "action"):
            val = tag.attrs.get(attr) or ""
            check(not FORBIDDEN_HOSTS.search(val), f"[4] <{tag.tag} {attr}=\"{val}\">: адрес мессенджера")

    navs = by_class(body, "nav")
    if check(len(navs) >= 1, "[4] нет меню .nav"):
        nav_links = [a for nav in navs for a in find_all(nav, lambda n: n.tag == "a")]
        check([a.attrs.get("href") for a in nav_links] == MENU_STUBS,
              f"[4] ссылки .nav {[a.attrs.get('href') for a in nav_links]}, ожидалось {MENU_STUBS}")
        check([a.text().strip() for a in nav_links] == MENU_TEXTS,
              f"[4] пункты .nav {[a.text().strip() for a in nav_links]}, ожидалось {MENU_TEXTS}")
    menus = by_class(body, "mobile-menu")
    if check(len(menus) == 1, f"[4] нужен один .mobile-menu, найдено {len(menus)}"):
        m_links = [a for a in find_all(menus[0], lambda n: n.tag == "a") if a.attrs.get("href") in MENU_STUBS]
        check([a.attrs.get("href") for a in m_links] == MENU_STUBS,
              f"[4] в .mobile-menu пункты {[a.attrs.get('href') for a in m_links]}, ожидалось {MENU_STUBS}")
    btns = by_class(body, "btn")
    check(sorted(b.attrs.get("href") or "" for b in btns) == sorted(BUTTON_STUBS),
          f"[4] ссылки кнопок .btn {[b.attrs.get('href') for b in btns]}, ожидалось {BUTTON_STUBS}")

    head_comments = [text for line, text in parser.comments
                     if parser.body_line is None or line < parser.body_line]
    replace_block = [c for c in head_comments if "ЗАМЕНИТЬ" in c]
    if check(len(replace_block) == 1, "[4] в начале index.html нет комментария «ЗАМЕНИТЬ»"):
        missing = [s for s in ALL_STUBS if s not in replace_block[0]]
        check(not missing, f"[4] в комментарии «ЗАМЕНИТЬ» нет заглушек: {missing}")

    # --- 5. Секции и заголовки ---
    found = [n.attrs["id"] for n in body.iter() if n.attrs.get("id") in SECTION_IDS]
    check(found == SECTION_IDS, f"[5] id секций {found}, ожидалось {SECTION_IDS}")
    for sid in SECTION_IDS:
        nodes = [n for n in body.iter() if n.attrs.get("id") == sid]
        if nodes:
            check(nodes[0].tag == "section", f"[5] #{sid} должен быть <section>, а не <{nodes[0].tag}>")
            if sid != "top":
                check(bool(find_all(nodes[0], lambda n: n.tag == "h2")), f"[5] в #{sid} нет h2")
    h1 = find_all(body, lambda n: n.tag == "h1")
    check(len(h1) == 1, f"[5] h1 на странице: {len(h1)}, нужен ровно один")

    # --- Шрифт и стили ---
    fonts = [n for n in root.iter() if n.tag == "link" and n.attrs.get("href") == FONT_HREF]
    check(len(fonts) == 1, "[шрифт] нет подключения Manrope строкой из interfaces.md")
    for n in body.iter():
        style = n.attrs.get("style")
        if style is not None:
            rules = [r.split(":")[0].strip() for r in style.split(";") if r.strip()]
            check(all(r == "aspect-ratio" for r in rules),
                  f"[стили] строка {n.line}: style=\"{style}\" — стили только в style.css")

    check_radius(body)
    check_facts(body)
    check_hero_lines(body)
    return report()


def css_decls(block):
    """{свойство: значение} одного блока объявлений (пробелы схлопнуты, нижний регистр)."""
    decls = {}
    for decl in block.split(";"):
        if ":" in decl:
            prop, val = decl.split(":", 1)
            decls[prop.strip().lower()] = " ".join(val.split()).lower()
    return decls


def css_rules(css):
    """[(селектор, {свойство: значение})] — правила style.css, включая вложенные в @media."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return [(" ".join(sel.split()), css_decls(block))
            for sel, block in re.findall(r"([^{}]+)\{([^{}]*)\}", css)]


def css_rules_media(css):
    """[(«@media …» или "", селектор, {свойство: значение})] в порядке файла."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    rules, media, selector, pos = [], [], None, 0
    for m in re.finditer(r"[{}]", css):
        chunk, pos = css[pos:m.start()], m.end()
        if m.group() == "{":
            head = " ".join(chunk.split())
            if head.startswith("@"):
                media.append(head)
            else:
                selector = head
        elif selector is not None:
            rules.append((media[-1] if media else "", selector, css_decls(chunk)))
            selector = None
        elif media:
            media.pop()
    return rules


def selector_classes(selector):
    """Классы последнего (целевого) элемента каждого селектора из списка через запятую."""
    out = []
    for part in selector.split(","):
        target = re.split(r"[\s>+~]+", part.strip())[-1]
        out.append(set(re.findall(r"\.([\w-]+)", target)))
    return out


def check_radius(body):
    """G02: «Смотреть видео» и четыре кнопки CTA скруглены var(--radius-btn) = 12px на всех ширинах;
    фокусная обводка не отключена; у карточек и ячеек углы прямые."""
    if not check(STYLE.is_file(), "[G02] нет файла assets/css/style.css"):
        return
    rules = css_rules(STYLE.read_text(encoding="utf-8"))
    tokens = [d.get(RADIUS_TOKEN) for sel, d in rules if sel == ":root" and RADIUS_TOKEN in d]
    check(tokens == [RADIUS_VALUE],
          f"[G02] в :root нужен токен {RADIUS_TOKEN}: {RADIUS_VALUE}, найдено {tokens or 'ничего'}")
    want = f"var({RADIUS_TOKEN})"
    base = [d.get("border-radius") for sel, d in rules if {"btn"} in selector_classes(sel)]
    check(want in base, f"[G02] у .btn нет border-radius: {want} (найдено {base or 'ничего'})")
    for sel, d in rules:
        targets = selector_classes(sel)
        radius = d.get("border-radius")
        if any(any(c == "btn" or c.startswith("btn--") for c in t) for t in targets):
            check(radius in (None, want), f"[G02] «{sel}»: border-radius {radius} вместо {want}")
            check(d.get("outline") not in ("none", "0"), f"[G02] «{sel}»: фокусная обводка отключена")
        if any(t & set(SQUARE_BLOCKS) for t in targets):
            check(radius in (None, "0", "0px"), f"[G02] «{sel}»: у карточек и ячеек углы прямые, а не {radius}")
    # Кнопки G02 на странице: «Смотреть видео» и четыре кнопки CTA — все с классом btn.
    btn_hrefs = sorted(n.attrs.get("href") for n in by_class(body, "btn"))
    check(btn_hrefs == sorted(BUTTON_STUBS), f"[G02] кнопки .btn: {btn_hrefs}, ожидалось {sorted(BUTTON_STUBS)}")


def check_hero_lines(body):
    """G03 (таск F3): в первом экране нет вертикальных линий (декоративная сетка макета).
    Разметка: внутри #top нет элементов с «line» в классе; стили: ни одного правила про
    линии первого экрана и нет токена --hero-line (линии удалены, а не спрятаны)."""
    tops = [n for n in body.iter() if n.attrs.get("id") == "top"]
    if check(len(tops) == 1, "[G03] нет секции #top"):
        lines = [n for n in tops[0].iter() if n is not tops[0] and any("line" in c for c in n.classes)]
        check(not lines, "[G03] в первом экране остались линии: "
                         f"{[(n.tag, ' '.join(n.classes), n.line) for n in lines]}")
    if not STYLE.is_file():
        return
    rules = css_rules(STYLE.read_text(encoding="utf-8"))
    for sel, decls in rules:
        check(not re.search(r"\.hero[\w-]*line", sel), f"[G03] в style.css остались правила линий первого экрана: «{sel}»")
        if ".hero" in sel:
            check(px(decls.get("width")) != 1.0,
                  f"[G03] «{sel}»: ширина 1px — похоже на вертикальную линию в первом экране")
        if sel == ":root":
            check("--hero-line" not in decls, "[G03] в :root остался токен --hero-line")


def css_value(rules, selector, prop, medias):
    """Значение свойства у селектора (точно, в т. ч. внутри списка через запятую) — последнее
    по порядку файла среди правил, чьё @media входит в medias ("" — правила без @media)."""
    value = None
    for media, sel, decls in rules:
        if media in medias and prop in decls and selector in [s.strip() for s in sel.split(",")]:
            value = decls[prop]
    return value


def px(value):
    """«28px» → 28.0, иначе None."""
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)px", (value or "").strip())
    return float(m.group(1)) if m else None


def flex_parts(value):
    """Свойство flex → (grow, shrink, basis); не задано → значения по умолчанию (0, 1, auto)."""
    if value is None:
        return 0.0, 1.0, "auto"
    if value in ("none", "auto"):
        grow = 0.0 if value == "none" else 1.0
        return grow, grow, "auto"
    tokens = value.split()
    try:
        if len(tokens) == 3:
            return float(tokens[0]), float(tokens[1]), tokens[2]
        if len(tokens) == 2 and px(tokens[1]) is None and tokens[1] != "auto":
            return float(tokens[0]), float(tokens[1]), "0%"
        if len(tokens) == 2:
            return float(tokens[0]), 1.0, tokens[1]
        return (1.0, 1.0, tokens[0]) if px(tokens[0]) is not None else (float(tokens[0]), 1.0, "0%")
    except ValueError:
        return 0.0, 1.0, "auto"


def png_size(path):
    """(ширина, высота) PNG по заголовку IHDR или None."""
    try:
        head = path.read_bytes()[:24]
    except OSError:
        return None
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def facts_grid_height(ratios, width, columns, gap):
    """Высота сетки ячеек шириной width: картинки по ширине ячейки, высота — по пропорциям файла."""
    cell = (width - gap * (columns - 1)) / columns
    rows = [ratios[i:i + columns] for i in range(0, len(ratios), columns)]
    return sum(cell * max(row) for row in rows) + gap * (len(rows) - 1)


def check_facts(body):
    """G01 (таск F2): в секциях 4 и 6 под сеткой иллюстраций 3×2 нет пустой полосы.
    Десктоп: высота списка постоянна (строки фиксированной высоты), значит у сетки постоянная
    ширина в px, при которой две строки ячеек с зазором дают ту же высоту (±8 px).
    Планшет: сетка постоянной ширины рядом со списком не уже 300 px, иначе перенос друг под
    друга (flex-wrap); рядом строки списка растягиваются до высоты сетки, а естественная высота
    списка (пункт — не больше двух строк текста) её не превышает больше чем на 8 px."""
    if not STYLE.is_file():
        return
    rules = css_rules_media(STYLE.read_text(encoding="utf-8"))
    desktop, tablet = ("",), ("", TABLET_MEDIA)

    def val(selector, prop, medias):
        return css_value(rules, selector, prop, medias)

    # Пропорции ячеек — из самих файлов: высота ячейки = высота картинки по ширине ячейки.
    sections, items = {}, set()
    for sid in FACTS_SECTIONS:
        sec = [n for n in body.iter() if n.attrs.get("id") == sid]
        grids = by_class(sec[0], "facts__grid") if sec else []
        if not check(len(grids) == 1, f"[G01] в #{sid} нужна ровно одна .facts__grid"):
            continue
        items.add(len(by_class(sec[0], "facts__item")))
        ratios = []
        for img in by_class(grids[0], "facts__img"):
            size = png_size(ROOT / (img.attrs.get("src") or ""))
            if check(size is not None, f"[G01] #{sid}: {img.attrs.get('src')} — не PNG"):
                ratios.append(size[1] / size[0])
        if check(len(ratios) == 6, f"[G01] в #{sid} ячеек с картинкой {len(ratios)}, ожидалось 6"):
            sections[sid] = ratios
    if not check(items == {6}, f"[G01] в списках секций 4 и 6 должно быть по 6 пунктов, найдено {sorted(items)}"):
        return
    rows = 6
    cols = re.search(r"repeat\((\d+)", val(".facts__grid", "grid-template-columns", desktop) or "")
    gap = px(val(".facts__grid", "gap", desktop))
    if not check(bool(cols) and gap is not None,
                 "[G01] у .facts__grid нет grid-template-columns: repeat(N, …) и gap в px"):
        return
    columns = int(cols.group(1))

    # --- Десктоп ---
    grow, _, basis = flex_parts(val(".facts__grid", "flex", desktop))
    grid_w = px(val(".facts__grid", "width", desktop)) or px(basis)
    item_h = px(val(".facts__item", "height", desktop))
    last_h = px(val(".facts__item:last-child", "height", desktop)) or item_h
    if check(grid_w is not None and grow == 0,
             "[G01] десктоп: у .facts__grid нет постоянной ширины в px (width или flex: none + basis) — "
             "сетка сужается вместе с экраном, а список из строк постоянной высоты нет: под сеткой пустая полоса"):
        if check(item_h is not None, "[G01] десктоп: у .facts__item нет постоянной высоты в px"):
            list_h = item_h * (rows - 1) + last_h
            for sid, ratios in sections.items():
                grid_h = facts_grid_height(ratios, grid_w, columns, gap)
                check(abs(list_h - grid_h) <= FACTS_TOLERANCE,
                      f"[G01] десктоп, #{sid}: список {list_h:.1f} px, сетка {grid_h:.1f} px "
                      f"(ширина {grid_w:.0f}) — разница больше {FACTS_TOLERANCE} px")

    # --- Планшет ---
    check(val(".facts", "display", tablet) == "flex" and val(".facts", "flex-wrap", tablet) == "wrap",
          "[G01] планшет: у .facts нет display: flex + flex-wrap: wrap — на узком планшете "
          "список и сетка не встают друг под друга")
    list_basis = px(flex_parts(val(".facts__list", "flex", tablet))[2])
    check(list_basis is not None and list_basis >= FACTS_MIN_LIST,
          f"[G01] планшет: flex-basis .facts__list {list_basis} — нужно не меньше {FACTS_MIN_LIST} px")
    grid_basis = px(flex_parts(val(".facts__grid", "flex", tablet))[2])
    if not check(grid_basis is not None, "[G01] планшет: у .facts__grid нет flex-basis в px"):
        return
    check(val(".facts", "align-items", tablet) in ("stretch", "normal"),
          "[G01] планшет: у .facts нет align-items: stretch — список не тянется до высоты сетки")
    check(val(".facts__list", "display", tablet) == "flex"
          and val(".facts__list", "flex-direction", tablet) == "column",
          "[G01] планшет: .facts__list не flex-колонка — строки не растягиваются до высоты сетки")
    check(flex_parts(val(".facts__item", "flex", tablet))[0] > 0
          and val(".facts__item", "height", tablet) in (None, "auto"),
          "[G01] планшет: строки .facts__item не растягиваются (нужны flex-grow > 0 и height: auto)")
    # Оценка сверху естественной высоты строки: рамка 1 px + поля + две строки текста
    # + 4 px на выравнивание номера и текста по базовой линии.
    min_h = px(val(".facts__item", "min-height", tablet)) or 0
    pad = px((val(".facts__item", "padding", tablet) or "0px").split()[0]) or 0
    line = max(px(val(".facts__text", "line-height", tablet)) or 0,
               px(val(".facts__num", "line-height", tablet)) or 0)
    row = max(min_h, 1 + 2 * pad + 2 * line + 4)
    last_row = max(px(val(".facts__item:last-child", "min-height", tablet)) or min_h, row + 1)
    list_h = row * (rows - 1) + last_row
    for sid, ratios in sections.items():
        grid_h = facts_grid_height(ratios, grid_basis, columns, gap)
        check(list_h - grid_h <= FACTS_TOLERANCE,
              f"[G01] планшет, #{sid}: список до {list_h:.1f} px выше сетки {grid_h:.1f} px "
              f"(ширина {grid_basis:.0f}) больше чем на {FACTS_TOLERANCE} px — под сеткой полоса")


def report():
    for s in skipped:
        print("ПРОПУСК:", s)
    for p in problems:
        print("ПРОБЛЕМА:", p)
    if problems:
        print(f"Итог: {len(problems)} проблем(ы) из {checks} проверок")
        return 1
    print(f"OK: {checks} проверок, проблем нет")
    return 0


if __name__ == "__main__":
    sys.exit(main())
