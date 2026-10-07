#!/usr/bin/env python3
"""Проверка страницы сайта «Денталь профи» без браузера — редакция 2 («Почему необходимо КТ»).

Запуск из корня сайта:
    PYTHONIOENCODING=utf-8 python tools/check_site.py

Код возврата 0 — всё в порядке; иначе печатает строки «ПРОБЛЕМА: …» и возвращает 1.
Только стандартная библиотека Python 3. Эталон текстов — в самом скрипте (TEXTS ниже), это ТЗ
коммерческого директора слово в слово; служебная папка .autopilot для проверки не нужна.

Что проверяется:
  [1]  index.html разбирается html.parser без незакрытых и лишних тегов; lang="ru";
  [2]  <title>, meta description; весь видимый текст страницы — ровно тексты ТЗ в порядке TEXTS:
       ни одного недостающего и ни одного лишнего слова; запрещённых текстов прежней редакции
       (меню, видео, «Без КТ / С КТ», «мкЗв», «Остались вопросы», мессенджеры…) нет ни в тексте,
       ни в title, meta и alt; подписи иллюстраций и шаги «после КТ» стоят у своих картинок;
  [3]  картинки: в каждой секции ровно свои файлы (иллюстрации — .jpg), файл существует, alt
       не пустой, width/height в пропорции файла, ниже первого экрана loading="lazy";
       общий вес картинок страницы ≤ 1 МБ;
  [4]  на странице нет ни одного <a> и <button>, меню, бургера, форм и всплывающих окон;
       в style.css и main.js не осталось меню, кнопок и связки «пункт ↔ картинка»;
  [5]  секции и id — по порядку SECTION_IDS, все <section>, у каждой (кроме первого экрана) h2;
       ровно один h1 — в первом экране;
  [G05] шрифт — Inter (строка подключения из interfaces.md), H1 и H2 — 800 и −0,01em;
  [G06] анимация бережная: prefers-reduced-motion, скрытие только под html.has-reveal (его ставит
       main.js), @keyframes — только transform и opacity, переходы не сдвигают вёрстку;
  [G15] отступы секций 72 / 56 / 32 (десктоп / планшет / телефон), первого экрана на телефоне 24 / 32;
       ряды картинок и пунктов полные на всю ширину: колонки по GRIDS на каждой ширине;
  [G03] в первом экране нет вертикальных линий;
  README: без таблицы «Что заменить», со ссылкой на tools/check_site.py, словом «Inter» и «Пикассо».
"""
import re
import struct
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
STYLE = ROOT / "assets" / "css" / "style.css"
SCRIPT = ROOT / "assets" / "js" / "main.js"
README = ROOT / "README.md"

# ---------------------------------------------------------------- Тексты ТЗ (§10.1–§10.7 спеки)
TITLE = "Почему необходимо КТ — Денталь профи"
SECTION_IDS = ["top", "clarify", "planning", "safety", "howto", "after", "next"]

H1 = "КТ — следующий шаг к вашему плану лечения"
HEADINGS = {
    "clarify": "Что исследование поможет уточнить",
    "planning": "Как КТ помогает спланировать лечение",
    "safety": "Что важно знать о лучевой нагрузке",
    "howto": "Как пройти исследование",
    "after": "Что будет после КТ",
    "next": "Продолжим подготовку вашего плана лечения",
}
# Подписи иллюстраций «Что исследование поможет уточнить» — у своих картинок, без номеров.
CLARIFY_FIGURES = [
    ("see-01.jpg", "Костная ткань"),
    ("see-03.jpg", "Корни зубов"),
    ("see-04.jpg", "Анатомические образования"),
    ("see-02.jpg", "Очаги воспаления"),
]
HOWTO_ITEMS = [
    ("Где пройти КТ",
     "В диагностическом центре «Пикассо» по направлению, которое вы получили на консультации."),
    ("Сколько времени заложить",
     "Ориентируйтесь примерно на 30 минут на посещение. Точное время уточните при записи."),
    ("Нужна ли подготовка",
     "Как правило, специальная подготовка не требуется. При записи уточните рекомендации "
     "для назначенного исследования."),
    ("Как результаты попадут врачу",
     "«Пикассо» отправляет результаты напрямую в нашу клинику по электронной почте. При посещении "
     "уточните, что исследование выполняется по направлению «Денталь Профи»."),
    ("Если КТ уже есть",
     "Передайте имеющееся исследование координатору. Врач оценит, достаточно ли его для вашей "
     "ситуации и требуется ли дополнительная диагностика."),
]
STEPS = [
    ("step-1.jpg", "1. Получим исследование", "«Пикассо» направит результаты в клинику."),
    ("exam-ct.jpg", "2. Врач изучит данные",
     "Сопоставит КТ с результатами осмотра и подготовит дальнейшие предложения по лечению."),
    ("step-3.jpg", "3. Обсудим следующий этап",
     "Команда клиники свяжется с вами для согласования дальнейших действий."),
]
# Весь видимый текст страницы по порядку: секция → строки.
TEXTS = {
    "top": [
        H1,
        "На консультации врач рекомендовал вам компьютерную томографию, чтобы уточнить важные детали "
        "перед планированием лечения. Исследование поможет оценить то, что невозможно увидеть только "
        "при осмотре, и выбрать дальнейшую тактику с учётом вашей ситуации.",
    ],
    "clarify": [
        HEADINGS["clarify"],
        "В зависимости от задачи лечения врач оценивает состояние костной ткани, корней зубов "
        "и окружающих структур, расположение важных анатомических образований и возможные очаги воспаления.",
        "Результаты КТ дополняют осмотр и помогают обосновать дальнейшие решения.",
        *[caption for _, caption in CLARIFY_FIGURES],
    ],
    "planning": [
        HEADINGS["planning"],
        "Врач сопоставляет исследование с результатами консультации, уточняет особенности вашей ситуации "
        "и определяет возможные варианты лечения. Это помогает заранее обсудить последовательность "
        "действий и важные ограничения.",
    ],
    "safety": [
        HEADINGS["safety"],
        "КТ связано с лучевой нагрузкой, поэтому врач назначает исследование для решения конкретной "
        "диагностической задачи. Доза зависит от области исследования, оборудования и выбранного протокола.",
        "Пройдите исследование по выданному направлению. Если у вас уже есть КТ, сначала передайте его "
        "в клинику: врач проверит, подходит ли оно для текущего планирования.",
    ],
    "howto": [HEADINGS["howto"], *[line for item in HOWTO_ITEMS for line in item]],
    "after": [HEADINGS["after"], *[line for _, title, text in STEPS for line in (title, text)]],
    "next": [
        HEADINGS["next"],
        "Пройдите КТ по выданному направлению — после получения результатов мы сможем перейти "
        "к следующему этапу.",
        "Если что-то мешает пройти исследование или остались вопросы, ответьте координатору в переписке, "
        "из которой вы открыли эту страницу. Мы поможем разобраться.",
    ],
}

# Тексты прежней редакции, которые ТЗ убирает (видимый текст, title, meta, alt).
FORBIDDEN_TEXTS = ["Мы не лечим", "на глаз", "Без КТ", "С КТ", "В каких случаях", "мкЗв", "микрозиверт",
                   "перелета", "перелёта", "грудной клетки", "Остались вопросы", "Смотреть видео", "видео",
                   "Задать вопрос", "Telegram", "WhatsApp", "Max", "Лучшее лечение", "Что позволяет увидеть",
                   "недостаточно обычного осмотра", "Безопасно ли"]
MENU_TEXTS = ["Услуги", "Цены", "Команда", "Акции", "Отзывы", "Пациентам", "Контакты"]

# ---------------------------------------------------------------- Картинки (§10, таск F7 — JPEG)
IMAGES = {
    "top": ["logo-white.png", "step-2.jpg"],
    "clarify": [name for name, _ in CLARIFY_FIGURES],
    "planning": ["xray-hands.jpg"],
    "safety": ["safety-ct.jpg"],
    "howto": [],
    "after": [name for name, _, _ in STEPS],
    "next": ["ct-machine.jpg"],
}
NOT_JPEG_OK = {"logo-white.png"}  # логотип с прозрачным фоном остаётся PNG
IMAGES_BUDGET = 1024 * 1024       # байт: общий вес картинок страницы (§10.8)
RATIO_TOLERANCE = 0.02            # width/height разметки против пропорций файла

# ---------------------------------------------------------------- Нет кнопок, ссылок и меню (§10.9)
FORBIDDEN_TAGS = {"a", "button", "nav", "form", "input", "select", "textarea", "iframe", "dialog",
                  "video", "audio", "embed", "object"}
RETIRED_BLOCKS = ("nav", "burger", "mobile-menu", "btn", "facts", "compare", "best", "cta", "card")
RETIRED_CLASS = re.compile(r"\.(%s)(?![\w-])|\.(%s)(__|--)" % ("|".join(RETIRED_BLOCKS), "|".join(RETIRED_BLOCKS)))
FORBIDDEN_JS = ("data-menu", "is-menu-open", "aria-expanded", "data-facts", "aria-pressed",
                "setInterval", "alert(", "confirm(", "prompt(", "window.open", "showModal")

# ---------------------------------------------------------------- Шрифт (G05, таск F4)
FONT_HREF = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&display=swap"
FONT_NAME = "Inter"
FONT_FALLBACKS = ("arial", "sans-serif")
HEADING_SELECTORS = (".hero__title", ".h2")  # H1 и H2: вес 800, межбуквенный −0,01em
HEADING_WEIGHT = "800"
HEADING_TRACKING = "-0.01em"

# ---------------------------------------------------------------- Раскладка (§10.8, G15)
TABLET_MEDIA = "@media (max-width: 1199.98px)"
PHONE_MEDIA = "@media (max-width: 767.98px)"
SECTION_PADDING = {"": "72px", TABLET_MEDIA: "56px", PHONE_MEDIA: "32px"}
HERO_PHONE_PADDING = ("24px", "32px")  # сверху, снизу
PHONE_WIDTHS = (320, 380, 480, 600, 700, 767)
TABLET_WIDTHS = (768, 1024, 1199)
DESKTOP_WIDTHS = (1200, 1440, 1710, 1920)
CONTENT_MAX = 1710
# Ряды: блок-сетка → колонок на (телефоне, планшете, десктопе); WIDE — пункт на все колонки.
GRIDS = {"gallery": (2, 4, 4), "howto": (1, 2, 2), "steps": (1, 3, 3)}
WIDE = {"howto": "howto__item--wide"}

# ---------------------------------------------------------------- Анимация (G06, таск F5)
REDUCED_MOTION = "prefers-reduced-motion: reduce"
REVEAL_GATE = "has-reveal"  # класс на <html>, который ставит main.js; без него ничего не скрыто
KEYFRAME_PROPS = {"transform", "opacity"}
LAYOUT_PROPS = re.compile(
    r"^(all|width|height|(min|max)-(width|height)|top|right|bottom|left|inset.*|margin.*|padding.*"
    r"|border|border(-[a-z]+)?-width|font.*|line-height|letter-spacing|(row-|column-)?gap|grid.*|flex.*)$")
TIMING = re.compile(r"^(-?\d*\.?\d+m?s|ease|ease-in|ease-out|ease-in-out|linear|step-start|step-end"
                    r"|(cubic-bezier|steps|var)\(.*\))$")

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "source", "track", "wbr"}
HIDDEN_TAGS = {"head", "script", "style", "template", "noscript", "title"}
INLINE_TAGS = {"span", "b", "i", "em", "strong", "small", "abbr", "sup", "sub", "nobr"}

problems = []
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
    """Нормализация для сравнения: без пробельных символов (и неразрывных), нижний регистр."""
    return re.sub(r"\s+", "", text).lower()


def squash(text):
    """Пробелы (и неразрывные) схлопнуты в один."""
    return " ".join(text.split())


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
        return visible_text(self)


class TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#document", [], None, 0)
        self.stack = [self.root]
        self.comments = []  # (строка, текст)
        self.errors = []

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.stack[-1], self.getpos()[0])
        self.stack[-1].children.append(node)
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
        if tag not in [n.tag for n in self.stack[1:]]:
            self.errors.append(f"строка {line}: </{tag}> без открывающего тега")
            return
        while self.stack[-1].tag != tag:
            lost = self.stack.pop()
            self.errors.append(f"строка {lost.line}: <{lost.tag}> не закрыт (встретился </{tag}> в строке {line})")
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
    sep = "" if node.tag in INLINE_TAGS else " "
    return sep + "".join(visible_text(c) for c in node.children) + sep


def stray_text(node, inside=False):
    """Видимый текст вне секций SECTION_IDS."""
    if isinstance(node, str):
        return "" if inside else node
    if node.tag in HIDDEN_TAGS or "hidden" in node.attrs:
        return ""
    inside = inside or (node.tag == "section" and node.attrs.get("id") in SECTION_IDS)
    return "".join(stray_text(c, inside) for c in node.children)


def find_all(root, pred):
    return [n for n in root.iter() if pred(n)]


def by_class(root, cls):
    return find_all(root, lambda n: cls in n.classes)


def by_id(root, ident):
    hits = [n for n in root.iter() if n.attrs.get("id") == ident]
    return hits[0] if hits else None


def basename(src):
    return (src or "").split("?")[0].rsplit("/", 1)[-1]


def words_re(phrase):
    """Фраза целыми словами, без учёта регистра и вида пробелов."""
    return re.compile(r"(?<!\w)" + r"\s+".join(map(re.escape, phrase.split())) + r"(?!\w)", re.I)


# ======================================================================== main

def main():
    if not INDEX.is_file():
        print("ПРОБЛЕМА: нет файла index.html — страница не свёрстана")
        print("Итог: 1 проблема")
        return 1

    raw = INDEX.read_text(encoding="utf-8")
    parser = TreeBuilder()
    parser.feed(raw)
    parser.close()
    root = parser.root

    # --- [1] Разбор без незакрытых тегов ---
    for err in parser.errors:
        fail(f"[1] {err}")
    unclosed = [n for n in parser.stack[1:] if n.tag not in {"html", "body"}]
    for n in unclosed:
        fail(f"[1] строка {n.line}: <{n.tag}> не закрыт до конца файла")
    check(not parser.errors and not unclosed, "[1] разметка с ошибками вложенности (см. выше)")
    bodies = find_all(root, lambda n: n.tag == "body")
    if not check(len(bodies) == 1, f"[1] ожидался один <body>, найдено {len(bodies)}"):
        return report()
    body = bodies[0]
    html = find_all(root, lambda n: n.tag == "html")
    check(bool(html) and html[0].attrs.get("lang") == "ru", '[1] у <html> нет lang="ru"')

    check_sections(body)
    check_texts(root, body, raw)
    check_images(body)
    check_no_controls(root, body, raw)

    # --- Стили только в style.css ---
    for n in body.iter():
        style = n.attrs.get("style")
        if style is not None:
            rules = [r.split(":")[0].strip() for r in style.split(";") if r.strip()]
            check(all(r == "aspect-ratio" for r in rules),
                  f"[стили] строка {n.line}: style=\"{style}\" — стили только в style.css")

    check_font(root)
    check_layout(body)
    check_hero_lines(body)
    check_motion()
    check_readme()
    return report()


# ======================================================================== [5] секции

def check_sections(body):
    found = [n.attrs["id"] for n in body.iter() if n.tag == "section" and n.attrs.get("id")]
    check(found == SECTION_IDS, f"[5] секции {found}, ожидалось {SECTION_IDS}")
    for sid in SECTION_IDS:
        node = by_id(body, sid)
        if not check(node is not None, f"[5] нет секции #{sid}"):
            continue
        check(node.tag == "section", f"[5] #{sid} должен быть <section>, а не <{node.tag}>")
        h2 = find_all(node, lambda n: n.tag == "h2")
        if sid == "top":
            check(not h2, "[5] в первом экране не должно быть h2")
        else:
            check(len(h2) == 1, f"[5] в #{sid} нужен ровно один h2, найдено {len(h2)}")
            if h2:
                check(norm(h2[0].text()) == norm(HEADINGS[sid]),
                      f"[5] h2 в #{sid}: «{squash(h2[0].text())}», нужно «{HEADINGS[sid]}»")
    h1 = find_all(body, lambda n: n.tag == "h1")
    if check(len(h1) == 1, f"[5] h1 на странице: {len(h1)}, нужен ровно один"):
        check(any(a.attrs.get("id") == "top" for a in h1[0].ancestors()), "[5] h1 должен быть в первом экране #top")
        check(norm(h1[0].text()) == norm(H1), f"[5] h1: «{squash(h1[0].text())}», нужно «{H1}»")


# ======================================================================== [2] тексты

def check_texts(root, body, raw):
    titles = find_all(root, lambda n: n.tag == "title")
    title = squash("".join(c for c in titles[0].children if isinstance(c, str))) if titles else ""
    check(title == TITLE, f"[2] <title> «{title}», нужно «{TITLE}»")
    joined = norm("".join(t for texts in TEXTS.values() for t in texts))
    metas = {(m.attrs.get("name") or m.attrs.get("property") or ""): m.attrs.get("content") or ""
             for m in find_all(root, lambda n: n.tag == "meta")}
    desc = metas.get("description", "")
    if check(bool(desc.strip()), "[2] нет meta description"):
        check(norm(desc) in joined, f"[2] meta description «{desc[:60]}…» — не текст ТЗ")

    # Весь видимый текст — ровно тексты ТЗ по порядку секций: ничего не пропущено и ничего лишнего.
    for sid, texts in TEXTS.items():
        section = by_id(body, sid)
        if section is None:
            continue  # пропавшую секцию ловит [5]
        page = norm(section.text())
        pos = 0
        for text in texts:
            want = norm(text)
            at = page.find(want, pos)
            if at < 0:
                where = " (есть, но не на своём месте)" if want in page else ""
                fail(f"[2] #{sid}: нет текста ТЗ «{text[:70]}»{where}")
                continue
            check(at == pos, f"[2] #{sid}: лишний текст «{page[pos:at][:70]}» перед «{text[:40]}»")
            pos = at + len(want)
        check(pos >= len(page), f"[2] #{sid}: лишний текст в конце секции «{page[pos:][:70]}»")
    outside = norm(stray_text(body))
    check(not outside, f"[2] видимый текст вне секций: «{outside[:70]}»")

    # Запрещённые тексты прежней редакции — нигде: ни в тексте, ни в title, meta, alt.
    spots = [("текст", squash(body.text())), ("title", title)]
    spots += [(f"meta {k}", v) for k, v in metas.items()]
    spots += [(f"alt {basename(i.attrs.get('src'))}", i.attrs.get("alt") or "")
              for i in find_all(body, lambda n: n.tag == "img")]
    allowed = squash(" ".join(t for texts in TEXTS.values() for t in texts))
    for phrase in FORBIDDEN_TEXTS + MENU_TEXTS:
        pattern = words_re(phrase)
        if pattern.search(allowed):
            # Слова есть внутри текста ТЗ («Команда клиники…», «…или остались вопросы») — запрещены
            # только отдельным элементом: пункт меню, заголовок «Остались вопросы?».
            for n in body.iter():
                if squash(n.text()).rstrip("?!.:").lower() == phrase.lower():
                    fail(f"[2] остался элемент прежней редакции «{phrase}» (<{n.tag}>, строка {n.line})")
            continue
        for where, text in spots:
            check(not pattern.search(text), f"[2] {where}: остался текст прежней редакции «{phrase}»")
    check("видео" not in raw.lower(), "[2] в index.html осталось упоминание видео")
    check("ЗАМЕНИТЬ" not in raw, "[2] в index.html остался блок «ЗАМЕНИТЬ» — заглушек в редакции 2 нет")

    # Подписи иллюстраций — у своих картинок, без номеров «01–04».
    clarify = by_id(body, "clarify")
    if clarify is not None:
        figures = find_all(clarify, lambda n: n.tag == "figure")
        got = []
        for fig in figures:
            imgs = find_all(fig, lambda n: n.tag == "img")
            caps = find_all(fig, lambda n: n.tag == "figcaption")
            got.append((basename(imgs[0].attrs.get("src")) if imgs else None,
                        squash(caps[0].text()) if caps else None))
        check(got == CLARIFY_FIGURES, f"[2] #clarify: пары картинка—подпись {got}, ожидалось {CLARIFY_FIGURES}")
        check(not re.search(r"(?<!\d)0[1-9](?!\d)", squash(clarify.text())),
              "[2] #clarify: у иллюстраций не должно быть номеров «01–04»")
    after = by_id(body, "after")
    if after is not None:
        got = []
        for item in find_all(after, lambda n: n.tag == "li"):
            imgs = find_all(item, lambda n: n.tag == "img")
            heads = find_all(item, lambda n: n.tag == "h3")
            paras = find_all(item, lambda n: n.tag == "p")
            got.append((basename(imgs[0].attrs.get("src")) if imgs else None,
                        squash(heads[0].text()) if heads else None,
                        squash(paras[0].text()) if paras else None))
        check(got == STEPS, f"[2] #after: шаги (картинка, заголовок, текст) {got}, ожидалось {STEPS}")
    howto = by_id(body, "howto")
    if howto is not None:
        got = [(squash(h.text()), squash(p.text()))
               for item in find_all(howto, lambda n: n.tag == "li")
               for h in find_all(item, lambda n: n.tag == "h3")[:1]
               for p in find_all(item, lambda n: n.tag == "p")[:1]]
        check(got == HOWTO_ITEMS, f"[2] #howto: пункты (заголовок, текст) {got}, ожидалось {HOWTO_ITEMS}")


# ======================================================================== [3] картинки

def image_size(path):
    """(ширина, высота) PNG или JPEG по заголовку файла; иначе None."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker == 0xFF or marker == 0x01 or 0xD0 <= marker <= 0xD8:
            i += 2 if marker != 0xFF else 1
            continue
        length = struct.unpack(">H", data[i + 2:i + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            height, width = struct.unpack(">HH", data[i + 5:i + 9])
            return width, height
        i += 2 + length
    return None


def check_images(body):
    imgs = find_all(body, lambda n: n.tag == "img")
    seen = []
    for sid, want in IMAGES.items():
        section = by_id(body, sid)
        if section is None:
            continue
        got = [basename(i.attrs.get("src")) for i in find_all(section, lambda n: n.tag == "img")]
        check(got == want, f"[3] картинки в #{sid}: {got}, ожидалось {want}")
        seen += find_all(section, lambda n: n.tag == "img")
    stray = [basename(i.attrs.get("src")) for i in imgs if i not in seen]
    check(not stray, f"[3] картинки вне секций: {stray}")

    total, missing = 0, []
    for img in imgs:
        src = img.attrs.get("src") or ""
        name = basename(src)
        where = f"<img src=\"{src}\"> (строка {img.line})"
        check(bool((img.attrs.get("alt") or "").strip()), f"[3] {where}: нужен осмысленный alt")
        dims = []
        for dim in ("width", "height"):
            val = img.attrs.get(dim) or ""
            if check(val.isdigit() and int(val) > 0, f"[3] {where}: нет корректного {dim}"):
                dims.append(int(val))
        check(bool(src) and not re.match(r"^[a-z]+:|^/", src, re.I), f"[3] {where}: путь должен быть относительным")
        check(src.startswith("assets/img/") and "/src/" not in src,
              f"[3] {where}: картинки — только из assets/img/ (не исходники assets/img/src/)")
        check(name in NOT_JPEG_OK or name.endswith(".jpg"), f"[3] {where}: иллюстрации — оптимизированные .jpg")
        path = ROOT / src.split("?")[0]
        if not check(path.is_file(), f"[3] {where}: файл не найден"):
            missing.append(name)
            continue
        total += path.stat().st_size
        size = image_size(path)
        if check(size is not None, f"[3] {where}: не PNG и не JPEG") and len(dims) == 2:
            ratio, file_ratio = dims[0] / dims[1], size[0] / size[1]
            check(abs(ratio / file_ratio - 1) <= RATIO_TOLERANCE,
                  f"[3] {where}: width/height {dims[0]}×{dims[1]} не в пропорции файла {size[0]}×{size[1]}")
            check(size[0] >= 1.9 * dims[0], f"[3] {where}: файл {size[0]} px — меньше 2× от width {dims[0]}")
        first_screen = any(a.attrs.get("id") == "top" for a in img.ancestors())
        if first_screen:
            check(img.attrs.get("loading") != "lazy", f"[3] {where}: в первом экране без loading=\"lazy\"")
        else:
            check(img.attrs.get("loading") == "lazy", f"[3] {where}: ниже первого экрана нужен loading=\"lazy\"")
    if not missing:
        check(total <= IMAGES_BUDGET,
              f"[3] картинки страницы весят {total / 1024:.0f} КБ — больше {IMAGES_BUDGET // 1024} КБ")


# ======================================================================== [4] ни кнопок, ни ссылок

def check_no_controls(root, body, raw):
    for n in body.iter():
        if n.tag in FORBIDDEN_TAGS:
            fail(f"[4] строка {n.line}: <{n.tag}> — в редакции 2 нет ни ссылок, ни кнопок, ни форм")
        role = n.attrs.get("role") or ""
        check(role not in ("button", "link", "dialog", "navigation", "menu"),
              f"[4] строка {n.line}: role=\"{role}\" — интерактивных элементов нет")
        check("tabindex" not in n.attrs and "onclick" not in n.attrs,
              f"[4] строка {n.line}: tabindex/onclick — интерактивных элементов нет")
        retired = [c for c in n.classes if RETIRED_CLASS.search("." + c)]
        check(not retired, f"[4] строка {n.line}: класс прежней редакции {retired}")
        if n.tag == "header":
            check(any(a.attrs.get("id") == "top" for a in n.ancestors()),
                  f"[4] строка {n.line}: шапка вне первого экрана — меню в редакции 2 нет")
    for path, label in ((STYLE, "style.css"), (SCRIPT, "main.js")):
        if not check(path.is_file(), f"[4] нет файла {label}"):
            continue
        text = re.sub(r"/\*.*?\*/|(?<![:\w])//[^\n]*", "", path.read_text(encoding="utf-8"), flags=re.S)
        retired = sorted({m.group(0) for m in RETIRED_CLASS.finditer(text)})
        check(not retired, f"[4] {label}: остались классы прежней редакции (меню, кнопки, списки): {retired[:12]}")
        if path == SCRIPT:
            for needle in FORBIDDEN_JS:
                check(needle not in text, f"[4] main.js: «{needle}» — меню, связка пунктов и всплывающих окон нет")


# ======================================================================== [G05] шрифт

def font_families(value):
    """«'Inter', Arial, sans-serif» → ['inter', 'arial', 'sans-serif']."""
    return [f.strip().strip("'\"").strip().lower() for f in value.split(",") if f.strip()]


def check_font(root):
    """G05: Google Fonts подключён ровно строкой из interfaces.md; в style.css шрифт — только Inter
    с запасными Arial и sans-serif, body набран Inter; H1 и H2 — 800 и −0,01em на всех ширинах."""
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
    for selector in HEADING_SELECTORS:
        for prop, want in (("font-weight", HEADING_WEIGHT), ("letter-spacing", HEADING_TRACKING)):
            base = css_value(media_rules, selector, prop, ("",))
            check(base == want, f"[G05] «{selector}» {prop}: {base or 'не задан'}, нужно {want}")
            for media, sel, decls in media_rules:  # планшет и телефон не перебивают
                if prop in decls and selector in [s.strip() for s in sel.split(",")] and media:
                    check(decls[prop] == want, f"[G05] «{sel}» {media}: {prop} {decls[prop]}, нужно {want}")


# ======================================================================== CSS-разбор

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


# ======================================================================== [G15] раскладка

def check_layout(body):
    """§10.8: отступы секций 72 / 56 / 32, первого экрана на телефоне 24 / 32. Ряды полные и на всю
    ширину: колонки сеток GRIDS по grid-template-columns из style.css на каждой ширине; сумма
    пунктов (широкий пункт — на все колонки) делится на число колонок; колонки fr — без пустого
    места справа."""
    if not STYLE.is_file():
        return
    rules = css_rules_media(STYLE.read_text(encoding="utf-8"))
    for media, want in SECTION_PADDING.items():
        for prop in ("padding-top", "padding-bottom"):
            got = css_value(rules, ".section", prop, (media,))
            check(got == want, f"[G15] .section {media or 'десктоп'}: {prop} {got}, нужно {want}")
    phone = ("", TABLET_MEDIA, PHONE_MEDIA)
    for prop, want in zip(("padding-top", "padding-bottom"), HERO_PHONE_PADDING):
        got = cascade(rules, ["hero"], prop, phone)
        check(got == want, f"[G15] .hero на телефоне: {prop} {got}, нужно {want}")

    ranges = [("телефон", PHONE_WIDTHS, phone, 0), ("планшет", TABLET_WIDTHS, ("", TABLET_MEDIA), 1),
              ("десктоп", DESKTOP_WIDTHS, ("",), 2)]
    for block, counts in GRIDS.items():
        nodes = by_class(body, block)
        if not check(len(nodes) == 1, f"[G15] нужен ровно один .{block}, найдено {len(nodes)}"):
            continue
        items = [c for c in nodes[0].children if isinstance(c, Node)]
        wide_cls = WIDE.get(block)
        wide_items = [i for i in items if wide_cls and wide_cls in i.classes]
        for label, widths, medias, idx in ranges:
            pad = (px(cascade(rules, ["container"], "padding-left", medias)) or 0.0) + \
                  (px(cascade(rules, ["container"], "padding-right", medias)) or 0.0)
            template = cascade(rules, [block], "grid-template-columns", medias) or ""
            gap = column_gap(rules, [block], medias)
            span = cascade(rules, [wide_cls], "grid-column", medias) if wide_cls else None
            for screen in widths:
                width = min(screen, CONTENT_MAX) - pad
                try:
                    columns = grid_columns(template, width, gap) if template else [(0.0, None)]
                except ValueError as err:
                    fail(f"[G15] .{block}: grid-template-columns «{template}» не разобрать — {err}")
                    break
                count = len(columns)
                if not check(count == counts[idx], f"[G15] {label} {screen} px, .{block}: {count} в ряд, "
                                                   f"нужно {counts[idx]}"):
                    break
                check(all(high is None for _, high in columns),
                      f"[G15] {label} {screen} px, .{block}: колонки не fr — справа останется пусто")
                spans_all = span in ("1 / -1", "1/-1", f"span {count}")
                cells = len(items) - len(wide_items) + len(wide_items) * (count if spans_all else 1)
                check(cells % count == 0,
                      f"[G15] {label} {screen} px, .{block}: {len(items)} пунктов в {count} колонки — неполный ряд"
                      + (f" (у .{wide_cls} нужно grid-column: 1 / -1)" if wide_cls else ""))


# ======================================================================== [G03] без линий

def check_hero_lines(body):
    """G03: в первом экране нет вертикальных линий — ни разметки с «line» в классе, ни стилей."""
    top = by_id(body, "top")
    if top is not None:
        lines = [n for n in top.iter() if n is not top and any("line" in c for c in n.classes)]
        check(not lines, f"[G03] в первом экране остались линии: {[(n.tag, ' '.join(n.classes)) for n in lines]}")
    if not STYLE.is_file():
        return
    for sel, decls in css_rules(STYLE.read_text(encoding="utf-8")):
        check(not re.search(r"\.hero[\w-]*line", sel), f"[G03] в style.css правила линий первого экрана: «{sel}»")
        if ".hero" in sel:
            check(px(decls.get("width")) != 1.0, f"[G03] «{sel}»: ширина 1px — похоже на вертикальную линию")
        if sel == ":root":
            check("--hero-line" not in decls, "[G03] в :root остался токен --hero-line")


# ======================================================================== [G06] анимация

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
    """G06 (§9 спеки): в style.css есть @media (prefers-reduced-motion: reduce) — animation: none,
    transform: none и opacity: 1 у скрытого до появления. Скрывать контент можно только под классом
    .has-reveal, который ставит main.js (с IntersectionObserver и учётом «уменьшить движение») —
    без JS всё видно сразу. @keyframes меняют только transform и opacity; переходы не трогают размеры."""
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
                check(not LAYOUT_PROPS.match(name), f"[G06] «{sel}» {prop}: {name} — переход сдвигает вёрстку")
    if check(SCRIPT.is_file(), "[G06] нет assets/js/main.js"):
        js = SCRIPT.read_text(encoding="utf-8")
        for needle in ("IntersectionObserver", REVEAL_GATE, "prefers-reduced-motion"):
            check(needle in js, f"[G06] main.js: нет «{needle}» — появление при прокрутке не бережное")


# ======================================================================== README

def check_readme():
    if not check(README.is_file(), "[README] нет README.md"):
        return
    text = README.read_text(encoding="utf-8")
    check("Что заменить" not in text, "[README] осталась таблица «Что заменить» — заглушек в редакции 2 нет")
    for anchor in ("#telegram", "#whatsapp", "#max", "#vopros", "#video", "#uslugi"):
        check(anchor not in text, f"[README] осталась заглушка {anchor}")
    for needle in ("tools/check_site.py", FONT_NAME, "Пикассо"):
        check(needle in text, f"[README] нет «{needle}»")


def report():
    for p in problems:
        print("ПРОБЛЕМА:", p)
    if problems:
        print(f"Итог: {len(problems)} проблем(ы) из {checks} проверок")
        return 1
    print(f"OK: {checks} проверок, проблем нет")
    return 0


if __name__ == "__main__":
    sys.exit(main())
