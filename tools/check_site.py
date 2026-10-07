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
Плюс: lang="ru", нет style="" (кроме aspect-ratio); в style.css у кнопок .btn скругление
var(--radius-btn) = 12px на всех ширинах, у карточек и ячеек углы прямые (G02); в секциях 4 и 6
под сеткой иллюстраций нет пустой полосы (G01, таск F2): по числам style.css и размерам картинок
высота сетки равна высоте списка на десктопе, а на планшете список и сетка
переносятся друг под друга и строки списка растягиваются до высоты сетки;
в первом экране нет вертикальных линий — ни разметки, ни стилей (G03, таск F3).
Таск F4: весь сайт набран Inter (G05) — Google Fonts подключён ровно строкой из interfaces.md,
в style.css нет других шрифтов, кроме Inter и запасных, заголовки и бейджи — 800 и −0,01em,
README называет Inter; на телефоне (320–767) сетки картинок секций 4 и 6, карточки и кнопки CTA
доходят до правого края контента, сетки — полными рядами по 2, от ~560 px — по 3 (G04):
по числам style.css ширина колонок вычисляется для каждой ширины экрана.
Таск F5 (G06, §9 спеки): в секциях 4 и 6 каждый пункт списка — кнопка, связанная через
aria-controls с картинкой своего номера, с aria-pressed; в style.css есть
@media (prefers-reduced-motion: reduce), которое выключает анимации и перемещения и показывает
скрытое до появления; контент скрывается только под классом html.has-reveal (его ставит main.js —
без JS всё видно); @keyframes меняют только transform и opacity, переходы не трогают размеры.

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

README = ROOT / "README.md"

# G05 (таск F4): строка подключения — из interfaces.md; других шрифтов на сайте нет.
FONT_HREF = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&display=swap"
FONT_NAME = "Inter"
FONT_FALLBACKS = ("arial", "sans-serif")
# H1, H2, H3 и бейджи «50 / мкЗв»: вес 800, межбуквенный −0,01em.
HEADING_SELECTORS = (".hero__title", ".h2", ".card__title", ".compare__title", ".card__badge")
HEADING_WEIGHT = "800"
HEADING_TRACKING = "-0.01em"

# G04 (таск F4): ширины телефона, на которых ряды доходят до правого края контента (±1 px).
PHONE_WIDTHS = (320, 380, 480, 600, 700, 767)
EDGE_TOLERANCE = 1
FACTS_THREE_FROM = 560  # px экрана: уже — сетка 6 картинок по 2 в ряд, шире — по 3

# G06 (таск F5): связка «пункт списка ↔ картинка» и бережная анимация (§9 спеки).
PAIR_SECTIONS = FACTS_SECTIONS
REDUCED_MOTION = "prefers-reduced-motion: reduce"
REVEAL_GATE = "has-reveal"  # класс на <html>, который ставит main.js; без него ничего не скрыто
KEYFRAME_PROPS = {"transform", "opacity"}
LAYOUT_PROPS = re.compile(
    r"^(all|width|height|(min|max)-(width|height)|top|right|bottom|left|inset.*|margin.*|padding.*"
    r"|border|border(-[a-z]+)?-width|font.*|line-height|letter-spacing|(row-|column-)?gap|grid.*|flex.*)$")
TIMING = re.compile(r"^(-?\d*\.?\d+m?s|ease|ease-in|ease-out|ease-in-out|linear|step-start|step-end"
                    r"|(cubic-bezier|steps|var)\(.*\))$")
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

    # --- Стили только в style.css ---
    for n in body.iter():
        style = n.attrs.get("style")
        if style is not None:
            rules = [r.split(":")[0].strip() for r in style.split(";") if r.strip()]
            check(all(r == "aspect-ratio" for r in rules),
                  f"[стили] строка {n.line}: style=\"{style}\" — стили только в style.css")

    check_font(root)
    check_radius(body)
    check_facts(body)
    check_phone_rows(body)
    check_hero_lines(body)
    check_pairs(body)
    check_motion()
    return report()


def font_families(value):
    """«'Inter', Arial, sans-serif» → ['inter', 'arial', 'sans-serif']."""
    return [f.strip().strip("'\"").strip().lower() for f in value.split(",") if f.strip()]


def check_font(root):
    """G05 (таск F4): весь сайт набран Inter. Google Fonts подключён ровно строкой из interfaces.md
    (никаких других семейств); в style.css шрифт задаётся только как Inter с запасными Arial и
    sans-serif, body набран Inter; H1, H2, H3 и бейджи — вес 800 и −0,01em на всех ширинах;
    README называет Inter."""
    hrefs = [n.attrs.get("href") or "" for n in root.iter() if n.tag == "link"]
    sheets = [h for h in hrefs if "fonts.googleapis.com/css" in h]
    check(sheets == [FONT_HREF],
          f"[G05] подключение шрифта {sheets or 'не найдено'} — нужна ровно строка из interfaces.md: {FONT_HREF}")
    if not check(STYLE.is_file(), "[G05] нет файла assets/css/style.css"):
        return
    css = STYLE.read_text(encoding="utf-8")
    plain = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    check("@font-face" not in plain and "@import" not in plain,
          "[G05] в style.css @font-face или @import — шрифт подключается только строкой в index.html")
    rules = css_rules(css)
    allowed = {FONT_NAME.lower(), *FONT_FALLBACKS}
    tokens = {}
    for sel, decls in rules:
        for prop, value in decls.items():
            if prop == "font-family" or (prop.startswith("--") and "font" in prop):
                if value.startswith("var(") or value in ("inherit", "initial", "unset"):
                    continue
                extra = [f for f in font_families(value) if f not in allowed]
                check(not extra, f"[G05] «{sel}» {prop}: {value} — кроме Inter, шрифтов быть не должно ({extra})")
                if prop.startswith("--"):
                    tokens[prop] = value
    body_font = [d.get("font-family") for sel, d in rules if sel == "body" and "font-family" in d]
    family = body_font[-1] if body_font else ""
    var = re.fullmatch(r"var\((--[\w-]+)\)", family or "")
    if var:
        family = tokens.get(var.group(1), "")
    check(font_families(family or "")[:1] == [FONT_NAME.lower()],
          f"[G05] body набран не Inter: font-family {body_font or 'не задан'}")

    media_rules = css_rules_media(css)
    narrow = (TABLET_MEDIA, PHONE_MEDIA)
    for selector in HEADING_SELECTORS:
        for prop, want in (("font-weight", HEADING_WEIGHT), ("letter-spacing", HEADING_TRACKING)):
            base = css_value(media_rules, selector, prop, ("",))
            check(base == want, f"[G05] «{selector}» {prop}: {base or 'не задан'}, нужно {want}")
            for media, sel, decls in media_rules:  # планшет и телефон не перебивают
                if prop in decls and selector in [s.strip() for s in sel.split(",")] and media in narrow:
                    check(decls[prop] == want, f"[G05] «{sel}» {media}: {prop} {decls[prop]}, нужно {want}")

    if check(README.is_file(), "[G05] нет README.md"):
        check(FONT_NAME in README.read_text(encoding="utf-8"), "[G05] README не говорит, что шрифт — Inter")


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


def css_length(expr, basis):
    """Длина CSS в px: числа с px и %, 0, + − × ÷, скобки, calc(), min(), max(), clamp().
    Проценты — от basis (ширины контейнера). Иначе ValueError."""
    tokens = re.findall(r"(?:\d+\.?\d*|\.\d+)(?:px|%)?|[a-z]+\(|[()+\-*/,]|\S", expr.strip().lower())
    pos = 0

    def peek():
        return tokens[pos] if pos < len(tokens) else None

    def take(expected=None):
        nonlocal pos
        tok = peek()
        if tok is None or (expected and tok != expected):
            raise ValueError(f"в «{expr}» ожидалось {expected or 'значение'}, найдено {tok}")
        pos += 1
        return tok

    def atom():
        tok = take()
        if tok in ("calc(", "("):
            value = add()
            take(")")
            return value
        if tok in ("min(", "max(", "clamp("):
            args = [add()]
            while peek() == ",":
                take()
                args.append(add())
            take(")")
            if tok == "clamp(":
                return max(args[0], min(args[1], args[2]))
            return min(args) if tok == "min(" else max(args)
        if tok == "-":
            return -atom()
        if tok.endswith("%"):
            return float(tok[:-1]) * basis / 100
        if tok.endswith("px"):
            return float(tok[:-2])
        if re.fullmatch(r"\d+\.?\d*|\.\d+", tok):
            return float(tok)
        raise ValueError(f"в «{expr}» непонятное «{tok}»")

    def mul():
        value = atom()
        while peek() in ("*", "/"):
            op, other = take(), atom()
            value = value * other if op == "*" else value / other
        return value

    def add():
        value = mul()
        while peek() in ("+", "-"):
            op, other = take(), mul()
            value = value + other if op == "+" else value - other
        return value

    result = add()
    if peek() is not None:
        raise ValueError(f"в «{expr}» лишнее «{peek()}»")
    return result


def split_top(value, sep):
    """Разбить по sep (запятая или пробел) только на верхнем уровне скобок."""
    parts, depth, cur = [], 0, ""
    for ch in value:
        depth += (ch == "(") - (ch == ")")
        if depth == 0 and (ch == sep or (sep == " " and ch.isspace())):
            if cur.strip():
                parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur.strip())
    return parts


def grid_columns(template, width, gap):
    """Колонки grid-template-columns при ширине сетки width и межколоннике gap:
    [(минимум в px, максимум — px или None для fr)]. repeat(auto-fill|auto-fit, …) считается,
    как в браузере: столько колонок минимальной ширины, сколько помещается (не меньше одной)."""
    def track(spec):
        if spec.startswith("minmax(") and spec.endswith(")"):
            low, high = split_top(spec[7:-1], ",")
        else:
            low = high = spec
        low_px = None if low.endswith("fr") or low == "auto" else css_length(low, width)
        high_px = None if high.endswith("fr") else css_length(high, width)
        return low_px, high_px

    columns = []
    for part in split_top(template, " "):
        if part.startswith("repeat(") and part.endswith(")"):
            count, spec = split_top(part[7:-1], ",")
            low, high = track(spec)
            if count in ("auto-fill", "auto-fit"):
                size = low if low is not None else high
                if size is None:
                    raise ValueError(f"repeat({count}) без определённой ширины колонки: {spec}")
                count = max(1, int((width + gap + 1e-6) // (size + gap)))
            columns += [(low or 0.0, high)] * int(count)
        else:
            low, high = track(part)
            columns.append((low or 0.0, high))
    return columns


def cascade(rules, classes, prop, medias):
    """Значение prop у элемента с классами classes: последнее по порядку файла среди правил
    с простыми селекторами «.класс» (одинаковая специфичность) из medias."""
    value = None
    wanted = {"." + c for c in classes}
    for media, sel, decls in rules:
        if media in medias and prop in decls and wanted & {s.strip() for s in sel.split(",")}:
            value = decls[prop]
    return value


def column_gap(rules, classes, medias):
    """Межколонник: column-gap или вторая часть gap — что задано позже."""
    value = None
    wanted = {"." + c for c in classes}
    for media, sel, decls in rules:
        if media in medias and wanted & {s.strip() for s in sel.split(",")}:
            if "gap" in decls:
                parts = decls["gap"].split()
                value = parts[1] if len(parts) > 1 else parts[0]
            if "column-gap" in decls:
                value = decls["column-gap"]
    return px(value) if value else 0.0


def row_fill(rules, classes, width, label):
    """Ряд сетки при ширине width: колонки, пусто справа (px) и переполнение (px)."""
    phone = ("", TABLET_MEDIA, PHONE_MEDIA)
    template = cascade(rules, classes, "grid-template-columns", phone) or ""
    gap = column_gap(rules, classes, phone)
    try:
        columns = grid_columns(template, width, gap)
    except ValueError as err:
        fail(f"[G04] {label}: grid-template-columns «{template}» не разобрать — {err}")
        return None
    gaps = gap * (len(columns) - 1)
    mins = sum(low for low, _ in columns) + gaps
    if any(high is None for _, high in columns):
        used = max(width, mins)  # колонки fr забирают всю свободную ширину
    else:
        free = (width - gaps) / len(columns)
        used = sum(max(low, min(high, free)) for low, high in columns) + gaps
    return len(columns), width - used, template


def check_phone_rows(body):
    """G04 (таск F4): на телефоне (320–767) ряды доходят до правого края контента (±1 px).
    Сетки 6 картинок секций 4 и 6 — на всю строку под списком, полными рядами: по 2 в ряд,
    от ~560 px — по 3; карточки секций 2, 3, 7 и кнопки CTA (2×2) — тоже на всю ширину.
    Ширина колонок вычисляется по grid-template-columns из style.css для каждой ширины экрана."""
    if not STYLE.is_file():
        return
    rules = css_rules_media(STYLE.read_text(encoding="utf-8"))
    phone = ("", TABLET_MEDIA, PHONE_MEDIA)
    pad = px(cascade(rules, ["container"], "padding-left", phone)) or 0.0
    pad_r = px(cascade(rules, ["container"], "padding-right", phone)) or 0.0

    # Сетка фактов — отдельной строкой flex-контейнера .facts и растянута на всю строку.
    grid_width = cascade(rules, ["facts__grid"], "width", phone)
    grow, _, grid_basis = flex_parts(cascade(rules, ["facts__grid"], "flex", phone))
    list_basis = px(flex_parts(cascade(rules, ["facts__list"], "flex", phone))[2]) or 0.0
    facts_gap = column_gap(rules, ["facts"], phone)
    check(grid_width in (None, "auto", "100%") and grow > 0,
          f"[G04] телефон: .facts__grid width {grid_width}, flex-grow {grow} — сетка не тянется на всю строку")
    check(cascade(rules, ["facts__grid"], "max-width", phone) in (None, "none", "100%"),
          "[G04] телефон: у .facts__grid ограничена max-width — справа останется пусто")
    check(cascade(rules, ["facts"], "flex-wrap", phone) == "wrap",
          "[G04] телефон: у .facts нет flex-wrap: wrap — сетка не встаёт под список")

    rows = [(["facts__grid"], "сетка картинок секций 4 и 6", True)]
    for node in by_class(body, "cards"):
        rows.append((node.classes, "карточки ." + " .".join(node.classes), False))
    rows.append((["cta__buttons"], "кнопки CTA", False))
    for screen in PHONE_WIDTHS:
        width = screen - pad - pad_r
        basis = px(grid_basis)
        check(basis is None or list_basis + facts_gap + basis > width,
              f"[G04] {screen} px: сетка картинок встаёт рядом со списком, а не под ним")
        for classes, label, is_facts in rows:
            filled = row_fill(rules, classes, width, label)
            if filled is None:
                continue
            count, empty, template = filled
            check(abs(empty) <= EDGE_TOLERANCE,
                  f"[G04] {screen} px, {label}: справа пусто {empty:.0f} px "
                  f"(контент {width:.0f} px, колонки «{template}»)" if empty > 0 else
                  f"[G04] {screen} px, {label}: ряд шире контента на {-empty:.0f} px")
            if is_facts:
                want = 2 if screen < FACTS_THREE_FROM else 3
                check(count == want,
                      f"[G04] {screen} px, {label}: {count} в ряд, нужно {want} (6 картинок — полные ряды)")
            elif "cta__buttons" in classes:
                check(count == 2, f"[G04] {screen} px, кнопки CTA: {count} в ряд, нужно 2 (сетка 2×2)")


def check_pairs(body):
    """G06 (таск F5): в секциях 4 и 6 каждый пункт списка — одна кнопка (<button type="button">
    или role="button" + tabindex="0"), связанная с картинкой своего номера: aria-controls → id
    ячейки .facts__cell этой же секции с тем же номером; в разметке aria-pressed="false";
    шесть пунктов ведут на шесть разных картинок."""
    for sid in PAIR_SECTIONS:
        sec = [n for n in body.iter() if n.attrs.get("id") == sid]
        if not sec:
            continue  # пропавшую секцию ловит [5]
        cells = {c.attrs["id"]: norm("".join(n.text() for n in by_class(c, "facts__cell-num")))
                 for c in by_class(sec[0], "facts__cell") if c.attrs.get("id")}
        targets = []
        for item in by_class(sec[0], "facts__item"):
            num = norm("".join(n.text() for n in by_class(item, "facts__num")))
            where = f"[G06] #{sid}, пункт {num}"
            controls = [n for n in item.iter() if n is not item and (
                n.tag == "button" or (n.attrs.get("role") == "button" and n.attrs.get("tabindex") == "0"))]
            if not check(len(controls) == 1, f"{where}: нужна одна кнопка (button или role=\"button\" "
                                             f"+ tabindex=\"0\"), найдено {len(controls)}"):
                continue
            ctrl = controls[0]
            if ctrl.tag == "button":
                check(ctrl.attrs.get("type") == "button", f'{where}: у <button> нужен type="button"')
            check(ctrl.attrs.get("aria-pressed") == "false", f'{where}: нет aria-pressed="false"')
            target = ctrl.attrs.get("aria-controls")
            targets.append(target)
            if check(target is not None and target in cells,
                     f"{where}: aria-controls «{target}» не ведёт на картинку .facts__cell этой секции"):
                check(cells[target] == num, f"{where}: aria-controls ведёт на картинку {cells[target]}, а не {num}")
        check(len(targets) == 6 and len(set(targets)) == 6,
              f"[G06] #{sid}: пункты должны вести на 6 разных картинок, ведут на {targets}")


def transition_names(value, prop):
    """Свойства, которые меняет transition / transition-property (без времени и кривых)."""
    names = []
    for part in split_top(value, ","):
        if prop == "transition-property":
            names.append(part)
            continue
        name = next((t for t in split_top(part, " ") if not TIMING.match(t)), "all")
        if name != "none":
            names.append(name)
    return names


def check_motion():
    """G06 (таск F5, §9 спеки): анимация бережная. В style.css есть
    @media (prefers-reduced-motion: reduce): animation: none, transform: none и opacity: 1 у
    скрытого до появления. Скрывать контент (opacity: 0, visibility: hidden — кроме ::before/::after)
    можно только под классом .has-reveal, который ставит JS, — без JS всё видно сразу.
    @keyframes меняют только transform и opacity; переходы не трогают размеры и отступы."""
    if not STYLE.is_file():
        return
    rules = css_rules_media(STYLE.read_text(encoding="utf-8"))
    reduced = [(sel, d) for media, sel, d in rules if REDUCED_MOTION in media]
    if check(bool(reduced), f"[G06] в style.css нет @media ({REDUCED_MOTION})"):
        check(any("none" in (d.get("animation"), d.get("animation-name")) for _, d in reduced),
              f"[G06] @media ({REDUCED_MOTION}) не выключает анимации (animation: none)")
        check(any(d.get("transform") == "none" for _, d in reduced),
              f"[G06] @media ({REDUCED_MOTION}) не выключает перемещения (transform: none)")
        check(any(f".{REVEAL_GATE}" in sel and d.get("opacity") == "1" for sel, d in reduced),
              f"[G06] @media ({REDUCED_MOTION}) не показывает скрытое до появления (.{REVEAL_GATE} … opacity: 1)")
    for media, sel, d in rules:
        if media.startswith("@keyframes"):
            extra = sorted(set(d) - KEYFRAME_PROPS)
            check(not extra, f"[G06] {media} «{sel}»: анимируются {extra} — можно только transform и opacity")
            continue
        if REDUCED_MOTION in media or media == "@media print":
            continue
        if (d.get("opacity") == "0" or d.get("visibility") == "hidden") and "::" not in sel:
            check(all(f".{REVEAL_GATE}" in part for part in sel.split(",")),
                  f"[G06] «{sel}» прячет контент без класса .{REVEAL_GATE} — без JS он не появится")
        for prop in ("transition", "transition-property"):
            for name in transition_names(d.get(prop) or "", prop):
                check(not LAYOUT_PROPS.match(name),
                      f"[G06] «{sel}» {prop}: {name} — переход сдвигает вёрстку")


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
