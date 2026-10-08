#!/usr/bin/env python3
"""Проверка страницы сайта «Денталь профи» без браузера — редакция 4 («Почему необходимо КТ»).

Запуск из корня сайта:
    PYTHONIOENCODING=utf-8 python tools/check_site.py

Код возврата 0 — всё в порядке; иначе печатает строки «ПРОБЛЕМА: …» и возвращает 1.
Только стандартная библиотека Python 3. Эталон текстов — в самом скрипте (TEXTS ниже), это ТЗ
коммерческого директора с правками редакций 3 и 4 (§11, §12 спеки) слово в слово; служебная папка
.autopilot для проверки не нужна.

Что проверяется:
  [1]  index.html разбирается html.parser без незакрытых и лишних тегов; lang="ru";
  [2]  <title>, meta description; весь видимый текст страницы — ровно тексты ТЗ в порядке TEXTS:
       ни одного недостающего и ни одного лишнего слова; запрещённых текстов прежней редакции
       (меню, видео, «Без КТ / С КТ», «мкЗв», «Остались вопросы», мессенджеры…) нет ни в тексте,
       ни в title, meta и alt; подписи иллюстраций и шаги «после КТ» стоят у своих картинок;
  [3]  картинки: в каждой секции ровно свои файлы (все — .jpg, PNG-логотипа больше нет), файл
       существует, alt не пустой, width/height в пропорции файла, ниже первого экрана loading="lazy";
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
  [G16] превью ссылки в мессенджере: og:image (абсолютный адрес, 1200×630), og:url, og:type, og:locale,
        twitter:card, прежние og:title и og:description; файл картинки на месте;
  [G17, G24–G26, G32, G33] тексты редакций 3 и 4 — в TEXTS; убранные формулировки
        (RETIRED_TEXTS) нигде не встречаются — ни в тексте, ни в title, meta, alt; «мкЗв» нет и в index.html;
        абзацы #safety — оба прежних (уточнение заказчика: текст блока не сокращать, G28 не вводится);
  [G29–G31] #safety: слева H2 и абзацы, справа две карточки без чисел (картинка + подпись); на десктопе
        колонка текста ≈ 40 %, ряд карточек до правого края контента, карточка ≤ 480 px; на планшете —
        текст сверху, карточки 2 в ряд; на телефоне — столбиком, с ≈ 600 px — 2 в ряд;
        на картинке с самолётом — пунктирный маршрут (inline SVG, aria-hidden) с точками и живыми
        подписями «Москва» (слева) и «Нью-Йорк» (справа) в верхней части картинки, подпись ≥ 12 px;
        маршрут прокладывается ≈ 1 с при появлении карточки, скрытое — только под html.has-reveal;
  [G20] логотип первого экрана — SVG из logo-intro.html (знак, «Денталь Профи», подпись; геометрия
        путей совпадает с файлом-источником, если он лежит в корне), без PNG, демо-элементов, шрифтов
        Golos Text / IBM Plex Mono и перехвата клавиш; ширина ≈ 230 px на десктопе и ≈ 120 px ниже 1200;
        подпись «центр восстановления улыбок» не мельче 10 px: на десктопе её высота ≥ 10 px, ниже 1200
        она скрыта (D05); скрытое до анимации — только под классом html.has-logo-intro (ставит main.js);
  [G21] H1 — посередине между прежним H1 (60/66 и 32/40) и H2 (40/44 и 24/30): 50/55 и 28/35;
  [G22] в #planning — ролик <video muted loop playsinline preload="none"> с кадром-заставкой (poster),
        без autoplay, controls и src (адрес — в data-src, подставляет main.js при подходе блока к экрану,
        rootMargin ≈ 300 px; при «уменьшить движение» и saveData ролик не грузится), aria-label;
        файлы ролика и заставки на месте; карточка 3:2 со скруглением 16 px и тёмным фоном, на телефоне —
        на всю ширину под текстом; exam-ct.jpg — только в шаге «Врач изучит данные»; фото рук нет;
  [G23] у текста нет анимации появления: ни CSS-анимации, ни появления из main.js не касаются
        элементов с текстом (подписи маршрута — часть картинки); въезд первого экрана ≤ 0,6 с;
  [G27] картинки и карточки (#clarify, #safety, карточка #planning, #after) заметно всплывают:
        translateY ≈ 28 px → 0 и opacity, ≈ 0,7 с, в ряду по очереди (шаг ≈ 90 мс); срабатывает в зоне
        видимости — rootMargin снизу от −15 % до 0 (не заранее, за краем экрана), порог ≤ 0,5;
        при наведении мышью — подъём 4–6 px;
  README: без таблицы «Что заменить» и цифр дозы, со ссылкой на tools/check_site.py, словами «Inter»
       и «Пикассо», с папкой ролика assets/video/.
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

# ---------------------------------------------------------------- Тексты ТЗ (§10.1–§10.7, правки §11 спеки)
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
    ("see-04.jpg", "Пазухи и нервные каналы"),
    ("see-02.jpg", "Очаги воспаления"),
]
HOWTO_ITEMS = [
    ("Где пройти КТ",
     "В диагностическом центре «Пикассо» по направлению, которое вы получили на консультации."),
    ("Сколько времени заложить",
     "Ориентируйтесь примерно на 30 минут на посещение. Согласуйте точное время при записи."),
    ("Нужна ли подготовка",
     "Как правило, специальная подготовка не требуется. При записи уточните, что необходимо иметь "
     "с собой."),
    ("Как результаты попадут врачу",
     "«Пикассо» отправляет результаты напрямую в нашу клинику по электронной почте. При посещении "
     "скажите, что исследование выполняется по направлению «Денталь Профи»."),
]  # G17: пункта «Если КТ уже есть» нет; G32: три правки редакции 4
# G26: в первом экране — одно предложение.
HERO_TEXT = ("На консультации врач рекомендовал вам компьютерную томографию, чтобы уточнить важные детали "
             "перед планированием лечения.")
# Абзацы #safety — оба прежних без изменений (уточнение заказчика к редакции 4: текст блока не сокращать,
# фраза G28 «…но у современных томографов она небольшая» не вводится); всё ниже них — по §12.
SAFETY_LEADS = [
    "КТ связано с лучевой нагрузкой, поэтому врач назначает исследование для решения конкретной "
    "диагностической задачи. Доза зависит от области исследования, оборудования и выбранного протокола.",
    "У современных томографов для зубов доза небольшая — она сопоставима с дозой, которую человек "
    "получает в дальнем перелёте на самолёте.",
]
SAFETY_SHORT_LEAD = "но у современных томографов она небольшая"  # фраза G28 — на странице её нет
# G29: две карточки #safety без чисел — (картинка, подпись).
SAFETY_CARDS = [
    ("safety-ct.jpg", "Компьютерный томограф"),
    ("safety-plane.jpg", "Перелёт Москва — Нью-Йорк"),
]
# G30: маршрут на картинке с самолётом — подписи точек слева направо.
ROUTE_IMAGE = "safety-plane.jpg"
ROUTE_POINTS = ("Москва", "Нью-Йорк")
STEPS = [
    ("step-1.jpg", "1. Получим исследование", "«Пикассо» направит результаты в клинику."),
    ("exam-ct.jpg", "2. Врач изучит данные",
     "Сопоставит КТ с результатами осмотра и подготовит дальнейшие предложения по лечению."),
    ("step-3.jpg", "3. Обсудим следующий этап",
     "Команда клиники свяжется с вами для согласования дальнейших действий."),
]
# Весь видимый текст страницы по порядку: секция → строки.
TEXTS = {
    "top": [H1, HERO_TEXT],
    "clarify": [
        HEADINGS["clarify"],
        "В зависимости от задачи лечения врач оценивает состояние костной ткани, корней зубов "
        "и окружающих структур, расположение пазух и нервных каналов и возможные очаги воспаления.",
        "Результаты КТ дополняют осмотр и помогают уточнить план лечения.",
        *[caption for _, caption in CLARIFY_FIGURES],
    ],
    "planning": [
        HEADINGS["planning"],
        "Врач сопоставляет исследование с результатами консультации, уточняет особенности вашей ситуации "
        "и определяет возможные варианты лечения. Это помогает заранее обсудить последовательность "
        "действий и особенности, которые нужно учесть при лечении.",
    ],
    "safety": [
        HEADINGS["safety"],
        *SAFETY_LEADS,
        # подписи маршрута — на картинке с самолётом, перед подписью её карточки
        *[line for name, caption in SAFETY_CARDS
          for line in ((*ROUTE_POINTS, caption) if name == ROUTE_IMAGE else (caption,))],
    ],
    "howto": [HEADINGS["howto"], *[line for item in HOWTO_ITEMS for line in item]],
    "after": [HEADINGS["after"], *[line for _, title, text in STEPS for line in (title, text)]],
    "next": [
        HEADINGS["next"],
        "Пройдите КТ по выданному направлению. После получения результатов врач сможет уточнить план "
        "лечения, а мы свяжемся с вами, чтобы согласовать дальнейшие действия.",
        "Если у вас возникли какие-то вопросы, ответьте координатору в переписке. Мы поможем разобраться.",
    ],  # G33
}

# Тексты прежних редакций, которые ТЗ убирает (видимый текст, title, meta, alt). «мкЗв» и перелёт
# вернулись в редакции 3 (G19) — уже с числами из §11, поэтому их больше нет в этом списке.
FORBIDDEN_TEXTS = ["Мы не лечим", "на глаз", "Без КТ", "С КТ", "В каких случаях", "микрозиверт",
                   "3 часа", "грудной клетки", "Остались вопросы", "Смотреть видео", "видео",
                   "Задать вопрос", "Telegram", "WhatsApp", "Max", "Лучшее лечение", "Что позволяет увидеть",
                   "недостаточно обычного осмотра", "Безопасно ли"]
# Формулировки редакции 2, которые редакция 3 убирает или заменяет (§11: G17, G18, G24, G25).
RETIRED_TEXTS = ["Если КТ уже есть", "Передайте имеющееся исследование координатору", "Если у вас уже есть КТ",
                 "Пройдите исследование по выданному направлению", "подходит ли оно для текущего планирования",
                 "анатомических образований", "Анатомические образования", "обосновать дальнейшие решения",
                 "важные ограничения", "мы сможем перейти к следующему этапу",
                 "20–100", "КТ зубов на современном аппарате",  # D05: прежние число и подпись КТ
                 # редакция 4 (§12: G26, G29, G32, G33) — цифр дозы и пояснений к ним больше нет;
                 # абзацы #safety «…Доза зависит от области…» и «…сопоставима с дозой…» остаются (уточнение)
                 "Исследование поможет оценить", SAFETY_SHORT_LEAD,
                 "Для сравнения", "Типичные значения", "мкЗв", "20–200", "50–80", "КТ зубов — доза зависит",
                 "Точное время уточните", "рекомендации для назначенного исследования",
                 "уточните, что исследование выполняется", "Если что-то мешает пройти исследование"]
DOSE_UNIT = "мкЗв"  # G29: единицы дозы нет нигде в index.html — ни в тексте, ни в комментариях
MENU_TEXTS = ["Услуги", "Цены", "Команда", "Акции", "Отзывы", "Пациентам", "Контакты"]

# ---------------------------------------------------------------- Картинки (§10, таск F7 — JPEG)
IMAGES = {
    "top": ["step-2.jpg"],  # G20: логотип — SVG в разметке, не картинка
    "clarify": [name for name, _ in CLARIFY_FIGURES],
    "planning": [],  # G22: вместо картинки — ролик (<video>, VIDEO_* ниже)
    "safety": [name for name, _ in SAFETY_CARDS],
    "howto": [],
    "after": [name for name, _, _ in STEPS],
    "next": ["ct-machine.jpg"],
}
NOT_JPEG_OK = set()  # все картинки страницы — JPEG; PNG-логотип остался только в превью ссылки
IMAGES_BUDGET = 1024 * 1024       # байт: общий вес картинок страницы (§10.8), с кадром-заставкой ролика
RATIO_TOLERANCE = 0.02            # width/height разметки против пропорций файла

# ---------------------------------------------------------------- Превью ссылки (F8, G16)
PAGE_URL = "https://dashboarddp2013-web.github.io/Pochemu-neobhodimo-kt/"
OG_IMAGE_NAME = "og-preview.jpg"
OG_TAGS = {  # <meta property="…" content="…">
    "og:type": "website",
    "og:title": TITLE,
    "og:url": PAGE_URL,
    "og:locale": "ru_RU",
    "og:image": PAGE_URL + "assets/img/" + OG_IMAGE_NAME,
    "og:image:width": "1200",
    "og:image:height": "630",
}
TWITTER_TAGS = {"twitter:card": "summary_large_image"}  # <meta name="…" content="…">

# ---------------------------------------------------------------- #planning: ролик (G22, §11, таск F10)
PLANNING_RETIRED = "xray-hands"          # фото рук со снимком — со страницы убрано
PLANNING_RATIO = "3 / 2"                 # пропорции ролика 1200×800
PLANNING_RADIUS = "16px"                 # карточка со скруглением 16 px (как в первом экране)
PLANNING_DARK_MAX = 0.03                 # относительная яркость фона карточки — тёмный, под цвет ролика
VIDEO_SRC = "assets/video/kt-video.mp4"            # в data-src: адрес подставляет main.js
VIDEO_POSTER = "assets/video/kt-video-poster.jpg"  # кадр-заставка — виден до загрузки и без JS
VIDEO_LABEL = "Видео: 3D-модель черепа и срезы КТ"  # aria-label (подпись для скринридера)
VIDEO_FLAGS = ("muted", "loop", "playsinline")     # «живая картинка»: без звука, по кругу, без полноэкрана
VIDEO_BANNED = ("autoplay", "controls", "src")     # ни загрузки на старте, ни кнопок
VIDEO_MARGIN_PX = (200, 400)             # rootMargin загрузки в px — «≈ 300 px до экрана»
EXAM_CT = "exam-ct.jpg"                  # 3D-реконструкция — только в шаге «Врач изучит данные»

# ---------------------------------------------------------------- Логотип (G20, §11)
LOGO_SOURCE = "logo-intro.html"          # готовая анимация в корне проекта; файл не меняется
LOGO_LABEL = "Денталь Профи"             # доступное имя логотипа (role="img" + aria-label)
# viewBox трёх частей логотипа из logo-intro.html → (часть, сколько в ней <path>)
LOGO_PARTS = {
    "568.6 -13.4 876.3 889.7": ("знак", 3 + 6 + 6),   # 3 контура clipPath, 6 искр, 6 линий
    "0 946.6 2010.9 254.2": ("надпись «Денталь Профи»", 12),
    "140.5 1274.3 1725.9 105": ("подпись «центр восстановления улыбок»", 25),
}
LOGO_WIDTH = {"десктоп": 230, "телефон": 120}  # px, ширина знака с надписью (≈, допуск LOGO_TOL; D05)
LOGO_TOL = 5
LOGO_MOTTO_BOX = "140.5 1274.3 1725.9 105"  # viewBox подписи: высота SVG = ширина × 105 / 1725,9
LOGO_MOTTO_MIN_PX = 10                   # D05: подпись не мельче 10 px — иначе не показывается
LOGO_GATE = "has-logo-intro"             # класс на <html>, который ставит main.js на время анимации
LOGO_DEMO_FONTS = ("Golos", "IBM Plex", "IBM+Plex")
LOGO_DEMO_CLASSES = {"orb", "dim", "kicker", "bar", "lockup", "sr"}
LOGO_DEMO_IDS = {"replay", "slow"}
STROKE_HIDING = ("stroke-dashoffset", "stroke-dasharray")  # прячут линии знака до прорисовки

# ---------------------------------------------------------------- H1 (G21, §11)
# Прежний H1 (§4) и H2 (§10.8) — (кегль, интерлиньяж); новый H1 — среднее, интерлиньяж пропорционально.
H1_PREV = {"": (60, 66), "@media (max-width: 1199.98px)": (32, 40)}
H2_SPEC = {"": (40, 44), "@media (max-width: 1199.98px)": (24, 30)}

# ---------------------------------------------------------------- Текст без появления (G23, §11)
HERO_ENTRANCE_MAX_S = 0.6  # въезд первого экрана (кроме логотипа), с

# ---------------------------------------------------------------- Всплывание картинок (G27, §12)
REVEAL_SHIFT_PX = (24, 32)       # translateY при появлении, px (≈ 28)
REVEAL_S = (0.6, 0.8)            # длительность всплывания, с (≈ 0,7)
REVEAL_STEP_MS = (70, 110)       # шаг очереди в ряду, мс (≈ 90)
REVEAL_MARGIN_PCT = (-15, 0)     # rootMargin снизу, %: срабатывает в экране, а не за его краем
REVEAL_MAX_THRESHOLD = 0.5       # не позже, чем картинка видна наполовину
HOVER_LIFT_PX = (4, 6)           # «парящий» подъём при наведении мышью
# Что всплывает: секция → класс картинки или карточки (элемент без текста, кроме подписей маршрута).
REVEAL_TARGETS = {"clarify": "gallery__img", "planning": "planning__card", "safety": "dose__media",
                  "after": "steps__img"}

# ---------------------------------------------------------------- #safety: раскладка и маршрут (G30, G31)
SAFETY_TEXT_SHARE = (0.35, 0.45)  # десктоп: доля колонки текста (≈ 40 %), карточки — остальное
SAFETY_CARD_MAX = 480             # px, карточка на десктопе и телефоне не шире
# Телефон: карточка ≤ 480 px и в столбце, и по 2 в ряд; ряд уже контента — по центру (ревью F11).
SAFETY_PHONE_WIDTHS = (320, 380, 480, 520, 560, 590, 600, 700, 767)
# Телефон: столбиком, пока карточка в ряду вышла бы уже ≈ 280 px (подписи маршрута ≥ 12 px не уместились
# бы в небе над самолётом); дальше — 2 в ряд.
DOSE_PHONE = {320: 1, 380: 1, 480: 1, 600: 2, 700: 2, 767: 2}
ROUTE_CLASS = "route"             # блок маршрута поверх картинки; его подписи — часть картинки
ROUTE_LABEL_MIN_PX = 13           # подпись точки не мельче (ревью F11)
ROUTE_LABEL_WEIGHT = 600          # и не тоньше
ROUTE_SKY_PCT = 30                # точки — в верхней части картинки: небо (самолёт начинается ниже 37 %)
ROUTE_DRAW_S = (0.8, 1.2)         # пунктир «прокладывается» ≈ 1 с
ROUTE_STROKE = ("#0e294b", "2px")  # --navy, пунктир 2 px

# ---------------------------------------------------------------- Нет кнопок, ссылок и меню (§10.9)
FORBIDDEN_TAGS = {"a", "button", "nav", "form", "input", "select", "textarea", "iframe", "dialog",
                  "audio", "embed", "object"}  # <video> — один, в #planning (check_planning_video)
RETIRED_BLOCKS = ("nav", "burger", "mobile-menu", "btn", "facts", "compare", "best", "cta", "card")
RETIRED_CLASS = re.compile(r"\.(%s)(?![\w-])|\.(%s)(__|--)" % ("|".join(RETIRED_BLOCKS), "|".join(RETIRED_BLOCKS)))
FORBIDDEN_JS = ("data-menu", "is-menu-open", "aria-expanded", "data-facts", "aria-pressed",
                "setInterval", "alert(", "confirm(", "prompt(", "window.open", "showModal",
                "keydown", "keyup", "keypress")  # G20: клавиши R / пробел из демо не переносятся

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
GRIDS = {"gallery": (2, 4, 4), "howto": (1, 2, 2), "steps": (1, 3, 3), "dose": (DOSE_PHONE, 2, 2)}
WIDE = {}  # G17: в «Как пройти исследование» 4 пункта — сетка 2×2 без широкого пятого

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
    check_preview(root)
    check_planning_video(body, raw)
    check_safety(body)
    check_logo(root, body, raw)
    check_no_controls(root, body, raw)

    # --- Стили только в style.css ---
    for n in body.iter():
        style = n.attrs.get("style")
        if style is not None:
            rules = [r.split(":")[0].strip() for r in style.split(";") if r.strip()]
            check(all(r == "aspect-ratio" for r in rules),
                  f"[стили] строка {n.line}: style=\"{style}\" — стили только в style.css")

    check_font(root)
    check_hero_title()
    check_layout(body)
    check_hero_lines(body)
    check_motion()
    check_text_motion(body)
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
    for phrase in FORBIDDEN_TEXTS + MENU_TEXTS + RETIRED_TEXTS:
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
    # «Видео» — только в подписи ролика для скринридера; кнопки «Смотреть видео» и прочих упоминаний нет.
    check("видео" not in raw.replace(VIDEO_LABEL, "").lower(),
          "[2] в index.html упоминание видео вне aria-label ролика в #planning")
    check("ЗАМЕНИТЬ" not in raw, "[2] в index.html остался блок «ЗАМЕНИТЬ» — заглушек в редакции 2 нет")
    check(DOSE_UNIT not in raw, f"[G29] в index.html осталось «{DOSE_UNIT}» — цифр дозы в редакции 4 нет")

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
    # Кадры-заставки роликов грузятся сразу, как картинки, — входят в тот же бюджет.
    for video in find_all(body, lambda n: n.tag == "video"):
        poster = ROOT / (video.attrs.get("poster") or "").split("?")[0]
        if poster.is_file():
            total += poster.stat().st_size
        else:
            missing.append(basename(video.attrs.get("poster")))
    if not missing:
        check(total <= IMAGES_BUDGET,
              f"[3] картинки страницы весят {total / 1024:.0f} КБ — больше {IMAGES_BUDGET // 1024} КБ")


# ======================================================================== [G16] превью ссылки

def check_preview(root):
    """Мета-теги превью: каждый ровно один раз и с нужным значением; картинка превью лежит на месте."""
    metas = find_all(root, lambda n: n.tag == "meta")

    def values(attr, key):
        return [(m.attrs.get("content") or "").strip() for m in metas if m.attrs.get(attr) == key]

    for attr, tags in (("property", OG_TAGS), ("name", TWITTER_TAGS)):
        for key, want in tags.items():
            got = values(attr, key)
            check(got == [want], f"[G16] <meta {attr}=\"{key}\">: {got or 'нет'}, нужно ровно одно «{want}»")
    descs = values("name", "description")
    check(len(descs) == 1 and values("property", "og:description") == descs,
          "[G16] og:description должен быть один и совпадать с meta description")
    check((ROOT / "assets" / "img" / OG_IMAGE_NAME).is_file(), f"[G16] нет файла assets/img/{OG_IMAGE_NAME}")


# ======================================================================== [G22] #planning: ролик

def check_planning_video(body, raw):
    """§11 (G22), таск F10: в #planning вместо картинки — ролик «КТ в работе». Один <video> на странице,
    в карточке #planning (элемент с классом, без текста): muted, loop, playsinline, preload="none", poster;
    без autoplay, controls и src — адрес ролика в data-src, его подставляет main.js, когда блок подходит
    к экрану (rootMargin ≈ 300 px); при «уменьшить движение» и saveData ролик не грузится; без JS виден
    poster. width/height — в пропорции файла (3:2), aria-label — подпись для скринридера. Карточка 3:2
    со скруглением 16 px и тёмным фоном под цвет ролика, на телефоне — под текстом на всю ширину.
    exam-ct.jpg остаётся только в шаге «Врач изучит данные»; фото рук xray-hands*.jpg нет."""
    check(PLANNING_RETIRED not in raw, f"[G22] в index.html осталось фото рук {PLANNING_RETIRED}*.jpg")
    exam = [i for i in find_all(body, lambda n: n.tag == "img") if basename(i.attrs.get("src")) == EXAM_CT]
    after = by_id(body, "after")
    check(len(exam) == 1 and after is not None and after in list(exam[0].ancestors()),
          f"[G22] {EXAM_CT} на странице {len(exam)} раз(а) — нужен один, в шаге «Врач изучит данные» (#after)")
    videos = find_all(body, lambda n: n.tag == "video")
    section = by_id(body, "planning")
    if not check(len(videos) == 1 and section is not None and section in list(videos[0].ancestors()),
                 f"[G22] на странице нужен один <video> — в #planning, найдено {len(videos)}"):
        return
    video = videos[0]
    where = f"[G22] <video> (строка {video.line})"
    for flag in VIDEO_FLAGS:
        check(flag in video.attrs, f"{where}: нет атрибута {flag}")
    for attr in VIDEO_BANNED:
        check(attr not in video.attrs, f"{where}: атрибут {attr} — ролик не грузится на старте и без кнопок")
    check(video.attrs.get("preload") == "none", f"{where}: preload=\"{video.attrs.get('preload')}\", нужно \"none\"")
    inner = [n for n in video.iter() if n is not video]
    check(not any("src" in n.attrs for n in inner),
          f"{where}: внутри <source src> — ролик начнёт грузиться на старте; адрес — в data-src")
    check(video.attrs.get("aria-label") == VIDEO_LABEL,
          f"{where}: aria-label «{video.attrs.get('aria-label')}», нужно «{VIDEO_LABEL}»")
    check(video.attrs.get("data-src") == VIDEO_SRC, f"{where}: data-src «{video.attrs.get('data-src')}», нужно {VIDEO_SRC}")
    check(video.attrs.get("poster") == VIDEO_POSTER, f"{where}: poster «{video.attrs.get('poster')}», нужно {VIDEO_POSTER}")
    check((ROOT / VIDEO_SRC).is_file(), f"{where}: нет файла {VIDEO_SRC}")
    poster_size = image_size(ROOT / VIDEO_POSTER) if (ROOT / VIDEO_POSTER).is_file() else None
    check(poster_size is not None, f"{where}: нет файла кадра-заставки {VIDEO_POSTER} (JPEG)")
    dims = [video.attrs.get(d) or "" for d in ("width", "height")]
    if check(all(d.isdigit() and int(d) > 0 for d in dims), f"{where}: нужны width и height — вёрстка не прыгает"):
        w, h = map(int, dims)
        check(abs((w / h) / 1.5 - 1) <= RATIO_TOLERANCE, f"{where}: width/height {w}×{h} — не 3:2")
        if poster_size:
            check(abs((w / h) / (poster_size[0] / poster_size[1]) - 1) <= RATIO_TOLERANCE,
                  f"{where}: width/height {w}×{h} не в пропорции заставки {poster_size[0]}×{poster_size[1]}")
    card = video.parent
    if not check(card is not None and card is not section and card.classes and not squash(card.text()),
                 "[G22] #planning: ролик должен лежать в своей карточке (элемент с классом, без текста)"):
        return

    if not check(STYLE.is_file(), "[G22] нет style.css"):
        return
    css = STYLE.read_text(encoding="utf-8")
    rules = css_rules_media(css)
    tokens = root_tokens(css)
    desktop = ("",)
    phone = ("", TABLET_MEDIA, PHONE_MEDIA)
    radius = resolve(cascade(rules, card.classes, "border-radius", desktop), tokens)
    background = resolve(cascade(rules, card.classes, "background", desktop)
                         or cascade(rules, card.classes, "background-color", desktop), tokens)
    ratio = cascade(rules, card.classes, "aspect-ratio", desktop)
    check(radius == PLANNING_RADIUS, f"[G22] карточка #planning: border-radius {radius}, нужно {PLANNING_RADIUS}")
    shade = luminance(background)
    check(shade is not None and shade <= PLANNING_DARK_MAX,
          f"[G22] карточка #planning: фон {background} — нужен тёмный под цвет ролика (яркость ≤ {PLANNING_DARK_MAX})")
    check(ratio is not None and ratio.replace(" ", "") == PLANNING_RATIO.replace(" ", ""),
          f"[G22] карточка #planning: aspect-ratio {ratio}, нужно {PLANNING_RATIO} (как у ролика 1200×800)")
    for medias in (("", TABLET_MEDIA), phone):
        check(cascade(rules, card.classes, "aspect-ratio", medias) == ratio,
              "[G22] карточка #planning: на узких экранах пропорции не те же, что на десктопе")
    width = cascade(rules, card.classes, "max-width", phone)
    check(width in (None, "none", "100%"),
          f"[G22] карточка #planning на телефоне: max-width {width} — нужна вся ширина под текстом")
    check(cascade(rules, card.classes, "width", phone) in (None, "100%", "auto"),
          "[G22] карточка #planning на телефоне: ширина не на всю колонку")
    template = cascade(rules, ["planning"], "grid-template-columns", phone) or ""
    try:
        cols = len(grid_columns(template, 360, 0)) if template else 0
    except ValueError:
        cols = 0
    check(cols == 1, f"[G22] .planning на телефоне: «{template}» — ролик должен стоять под текстом (одна колонка)")
    for prop, want in (("width", "100%"), ("height", "100%"), ("object-fit", "cover")):
        got = cascade(rules, video.classes, prop, desktop)
        check(got == want, f"[G22] ролик ({' '.join(video.classes) or 'без класса'}): {prop} {got}, нужно {want}")

    # main.js: адрес подставляется при подходе блока, пауза вне экрана, бережно к трафику и движению.
    if not check(SCRIPT.is_file(), "[G22] нет main.js"):
        return
    js = re.sub(r"/\*.*?\*/|(?<![:\w])//[^\n]*", "", SCRIPT.read_text(encoding="utf-8"), flags=re.S)
    check("data-src" in js or "dataset.src" in js, "[G22] main.js не читает data-src ролика — он не загрузится")
    check("saveData" in js, "[G22] main.js: нет проверки navigator.connection.saveData — ролик грузится в режиме экономии")
    check("prefers-reduced-motion" in js, "[G22] main.js: «уменьшить движение» не учитывается")
    check(".play(" in js and ".pause(" in js,
          "[G22] main.js: ролик должен запускаться в зоне видимости и вставать на паузу вне её")
    pixel = [m for m in (margin_bottom(v) for v in root_margins(js)) if m and m[1] == "px"]
    low, high = VIDEO_MARGIN_PX
    check(any(low <= value <= high for value, _ in pixel),
          f"[G22] main.js: нет rootMargin загрузки ролика ≈ 300 px (снизу {low}–{high} px), найдено {pixel}")


def root_margins(js):
    """Значения rootMargin у IntersectionObserver в main.js (строковые литералы)."""
    return re.findall(r"rootMargin\s*:\s*['\"]([^'\"]+)['\"]", js)


def margin_bottom(value):
    """Нижнее поле rootMargin «top right bottom left» (1–4 значения) → (число, «px» или «%»); иначе None."""
    values = value.split()
    bottom = {1: 0, 2: 0, 3: 2, 4: 2}.get(len(values))
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)(px|%)", values[bottom]) if bottom is not None else None
    return (float(m.group(1)), m.group(2)) if m else None


def luminance(color):
    """Относительная яркость (WCAG) цвета #rgb / #rrggbb; иначе None."""
    m = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", (color or "").strip().lower())
    if not m:
        return None
    digits = m.group(1)
    if len(digits) == 3:
        digits = "".join(c * 2 for c in digits)
    channels = [int(digits[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


# ======================================================================== [G29–G31] #safety

def element_children(node):
    return [c for c in node.children if isinstance(c, Node)]


def track_sizes(template, width, gap):
    """Ширины колонок grid-template-columns при ширине сетки width и межколоннике gap: колонки в px
    (и выражения), Nfr и minmax(…, Nfr), repeat(n, …) с числом n. Иначе ValueError."""
    tracks = []
    for part in split_top(template, " "):
        if part.startswith("repeat(") and part.endswith(")"):
            count, spec = split_top(part[7:-1], ",")
            if not count.isdigit():
                raise ValueError(f"repeat({count}, …) — число колонок зависит от ширины")
            tracks += [spec] * int(count)
        else:
            tracks.append(part)
    fixed, frs = [], []
    for spec in tracks:
        high = split_top(spec[7:-1], ",")[1] if spec.startswith("minmax(") and spec.endswith(")") else spec
        m = re.fullmatch(r"(\d+(?:\.\d+)?)fr", high)
        fixed.append(None if m else css_length(high, width))
        frs.append(float(m.group(1)) if m else 0.0)
    free = width - gap * (len(tracks) - 1) - sum(f for f in fixed if f is not None)
    total = sum(frs) or 1.0
    return [f if f is not None else free * fr / total for f, fr in zip(fixed, frs)]


def min_font_px(value):
    """Наименьший кегль: «14px» → 14, «clamp(12px, …, 14px)» → 12, «max(12px, …)» → 12; иначе None."""
    value = (value or "").strip()
    if px(value) is not None:
        return px(value)
    m = re.fullmatch(r"(clamp|max)\((.*)\)", value)
    if not m:
        return None
    args = split_top(m.group(2), ",")
    if m.group(1) == "clamp":
        return px(args[0]) if len(args) == 3 else None
    known = [px(a) for a in args if px(a) is not None]
    return max(known) if known else None


def path_ends(d):
    """Первая и последняя точки пути SVG «M x y … x y» → ((x0, y0), (x1, y1)); иначе None."""
    nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", d or "")]
    if len(nums) < 4 or not (d or "").strip().upper().startswith("M"):
        return None
    return (nums[0], nums[1]), (nums[-2], nums[-1])


def pct(value):
    """«12.5%» → 12.5, иначе None."""
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)%", (value or "").strip())
    return float(m.group(1)) if m else None


def check_safety(body):
    """§12 (G29–G31) с уточнением заказчика (абзацы блока — оба прежних). В #safety два блока: текст
    (H2 и абзацы) и ряд .dose из двух карточек без чисел — картинка в .dose__media и подпись .dose__caption.
    На десктопе — две колонки: текст ≈ 40 %, карточки — остальное до правого края контента, карточка
    ≤ 480 px, по центру колонки по вертикали; на планшете и телефоне — текст сверху (одна колонка).
    На картинке с самолётом — маршрут .route поверх неё (position: absolute, inset 0): inline SVG
    (aria-hidden) с пунктиром 2 px цвета --navy и точки с живыми подписями «Москва» (слева) и «Нью-Йорк»
    (справа) в верхней части картинки (небо), подпись ≥ 12 px; концы линии совпадают с точками.
    Пунктир прокладывается ≈ 1 с при появлении карточки (.is-in); скрытое до этого — только под
    html.has-reveal; при «уменьшить движение» — сразу целиком."""
    safety = by_id(body, "safety")
    if safety is None:
        return
    blocks = by_class(safety, "safety")
    lists = by_class(safety, "dose")
    if not check(len(blocks) == 1 and len(lists) == 1,
                 f"[G31] в #safety нужен один блок .safety и один ряд карточек .dose "
                 f"(найдено {len(blocks)} и {len(lists)})"):
        return
    kids = element_children(blocks[0])
    text_block = kids[0] if kids else None
    check(len(kids) == 2 and kids[1] is lists[0] and text_block is not lists[0]
          and any(n.tag == "h2" for n in text_block.iter())
          and len([n for n in text_block.iter() if n.tag == "p"]) == len(SAFETY_LEADS),
          f"[G31] .safety: нужны ровно два блока — текст (H2 и {len(SAFETY_LEADS)} абзаца) и ряд карточек .dose")

    got = []
    for item in element_children(lists[0]):
        media = by_class(item, "dose__media")
        imgs = find_all(item, lambda n: n.tag == "img")
        caps = by_class(item, "dose__caption")
        check(len(media) == 1 and len(imgs) == 1 and imgs[0].parent is media[0],
              f"[G29] строка {item.line}: картинка карточки — одна, в блоке .dose__media")
        got.append((basename(imgs[0].attrs.get("src")) if imgs else None, squash(caps[0].text()) if caps else None))
    check(got == SAFETY_CARDS, f"[G29] карточки #safety (картинка, подпись) {got}, ожидалось {SAFETY_CARDS}")
    leftovers = sorted({c for n in safety.iter() for c in n.classes
                        if c in ("dose__badge", "dose__num", "dose__unit", "safety__note")})
    check(not leftovers, f"[G29] в #safety остались бейджи с числами или примечание к дозам: {leftovers}")

    # --- G30: маршрут на картинке с самолётом ---
    routes = by_class(safety, ROUTE_CLASS)
    if not check(len(routes) == 1, f"[G30] в #safety нужен один маршрут .{ROUTE_CLASS}, найдено {len(routes)}"):
        return
    route = routes[0]
    media = route.parent
    imgs = [c for c in element_children(media) if c.tag == "img"] if media is not None else []
    check(media is not None and "dose__media" in media.classes and len(imgs) == 1
          and basename(imgs[0].attrs.get("src")) == ROUTE_IMAGE,
          f"[G30] маршрут — поверх картинки {ROUTE_IMAGE}: в её блоке .dose__media рядом с <img>")
    svgs = [n for n in route.iter() if n.tag == "svg"]
    paths = [n for svg in svgs for n in svg.iter() if n.tag == "path" and n.attrs.get("d")]
    if not check(len(svgs) == 1 and len(paths) == 1, "[G30] линия маршрута — один inline <svg> с одним <path>"):
        return
    svg, path = svgs[0], paths[0]
    chain = [svg] + [a for a in svg.ancestors() if a is not route and route in list(a.ancestors())]
    check(any(n.attrs.get("aria-hidden") == "true" for n in chain),
          "[G30] дуга маршрута — украшение: у <svg> (или его обёртки) нужно aria-hidden=\"true\"")
    box = [float(v) for v in (svg.attrs.get("viewbox") or "").replace(",", " ").split()]
    size = image_size(ROOT / "assets" / "img" / ROUTE_IMAGE)
    box_ok = check(len(box) == 4 and size is not None and box[2] > 0 and box[3] > 0
                   and abs((box[2] / box[3]) / (size[0] / size[1]) - 1) <= RATIO_TOLERANCE,
                   f"[G30] viewBox маршрута {box} не в пропорции картинки {size} — дуга съедет при масштабе")
    points = by_class(route, "route__point")
    labels = by_class(route, "route__label")
    check([squash(n.text()) for n in labels] == list(ROUTE_POINTS),
          f"[G30] подписи маршрута {[squash(n.text()) for n in labels]}, нужно {list(ROUTE_POINTS)} (слева направо)")
    check(len(points) == 2 and all(any(lbl in list(p.iter()) for lbl in labels) for p in points),
          "[G30] у маршрута две точки .route__point, в каждой — своя подпись .route__label")
    for label in labels:
        hidden = [n for n in [label, *label.ancestors()] if n.attrs.get("aria-hidden") == "true"]
        check(not hidden, f"[G30] подпись «{squash(label.text())}» — живой текст: без aria-hidden")
    if not STYLE.is_file():
        return
    css = STYLE.read_text(encoding="utf-8")
    rules = css_rules_media(css)
    tokens = root_tokens(css)
    every = ("", TABLET_MEDIA, PHONE_MEDIA)
    check(cascade(rules, ["dose__media"], "position", every) == "relative",
          "[G30] .dose__media: нужно position: relative — маршрут держится за картинку")
    check(cascade(rules, [ROUTE_CLASS], "position", every) == "absolute",
          f"[G30] .{ROUTE_CLASS}: нужно position: absolute — поверх картинки")
    sides = [cascade(rules, [ROUTE_CLASS], s, every) for s in ("top", "right", "bottom", "left")]
    check(cascade(rules, [ROUTE_CLASS], "inset", every) in ("0", "0px") or all(s in ("0", "0px") for s in sides),
          f"[G30] .{ROUTE_CLASS}: inset 0 — маршрут во всю картинку и масштабируется вместе с ней")
    stroke = resolve(cascade(rules, path.classes, "stroke", every), tokens)
    check((stroke or "").lower() == ROUTE_STROKE[0], f"[G30] линия маршрута: stroke {stroke}, нужен --navy")
    width = cascade(rules, path.classes, "stroke-width", every)
    check(width == ROUTE_STROKE[1], f"[G30] линия маршрута: stroke-width {width}, нужно {ROUTE_STROKE[1]}")
    check(cascade(rules, path.classes, "vector-effect", every) == "non-scaling-stroke",
          "[G30] линия маршрута: vector-effect: non-scaling-stroke — пунктир 2 px при любой ширине картинки")
    check(cascade(rules, path.classes, "stroke-dasharray", every) not in (None, "none"),
          "[G30] линия маршрута — пунктир: нужен stroke-dasharray")
    ends = path_ends(path.attrs.get("d"))
    spots = []
    for point in points:
        mods = [c for c in point.classes if c.startswith("route__point--")]
        left = pct(cascade(rules, mods, "left", every)) if mods else None
        top = pct(cascade(rules, mods, "top", every)) if mods else None
        spots.append((left, top))
        check(left is not None and top is not None,
              f"[G30] точка {' '.join(point.classes)}: left и top в % — она должна ехать вместе с картинкой")
    if len(spots) == 2 and all(v is not None for spot in spots for v in spot):
        (fx, fy), (tx, ty) = spots
        check(fx < tx, "[G30] «Москва» — слева, «Нью-Йорк» — справа")
        check(fy <= ROUTE_SKY_PCT and ty <= ROUTE_SKY_PCT,
              f"[G30] точки маршрута — в верхней части картинки (небо, top ≤ {ROUTE_SKY_PCT} %), сейчас {fy} и {ty}")
        if ends and box_ok:
            for (x, y), (left, top), name in zip(ends, spots, ROUTE_POINTS):
                check(abs((x - box[0]) / box[2] * 100 - left) <= 1 and abs((y - box[1]) / box[3] * 100 - top) <= 1,
                      f"[G30] конец линии у «{name}» ({x}, {y}) не совпадает с точкой ({left} %, {top} %)")
    for medias in (("",), ("", TABLET_MEDIA), every):
        size_px = min_font_px(cascade(rules, ["route__label"], "font-size", medias))
        check(size_px is not None and size_px >= ROUTE_LABEL_MIN_PX,
              f"[G30] подписи маршрута {medias[-1] or 'десктоп'}: кегль {size_px}, нужно ≥ {ROUTE_LABEL_MIN_PX} px")
        weight = cascade(rules, ["route__label"], "font-weight", medias) or "400"
        check(weight.isdigit() and int(weight) >= ROUTE_LABEL_WEIGHT,
              f"[G30] подписи маршрута: font-weight {weight}, нужно ≥ {ROUTE_LABEL_WEIGHT}")
    # Прокладка пунктира: скрытое — только под .has-reveal, ≈ 1 с, когда маршрут в экране (main.js);
    # «уменьшить движение» — сразу.
    drawn = []
    for media, sel, d in rules:
        if ".route" not in sel or media.startswith("@keyframes") or media == "@media print" \
                or REDUCED_MOTION in media:
            continue
        hides = d.get("opacity") == "0" or re.search(r"translatex\(-?100%\)", d.get("transform") or "")
        if hides:
            check(all(f".{REVEAL_GATE}" in part for part in sel.split(",")),
                  f"[G30] «{sel}» прячет маршрут без класса .{REVEAL_GATE} — без JS он не будет виден")
        if d.get("transition"):
            drawn += [t for part in split_top(d["transition"], ",")
                      for t in [t for t in (time_s(tok) for tok in split_top(part, " ")) if t is not None][:1]]
    low, high = ROUTE_DRAW_S
    check(any(low <= t <= high for t in drawn),
          f"[G30] пунктир прокладывается при появлении карточки ≈ 1 с ({low}–{high} с) — найдено {drawn}")
    check(any(".route" in sel and d.get("transform") == "none" for media, sel, d in rules if REDUCED_MOTION in media),
          f"[G30] @media ({REDUCED_MOTION}): маршрут сразу целиком (.route… transform: none)")

    # --- G31: раскладка ---
    desk = ("",)
    template = cascade(rules, ["safety"], "grid-template-columns", desk) or ""
    check(cascade(rules, ["safety"], "display", desk) == "grid" and bool(template),
          "[G31] .safety на десктопе: display: grid с двумя колонками (текст и карточки)")
    check(cascade(rules, ["safety"], "align-items", desk) == "center",
          "[G31] .safety на десктопе: align-items: center — карточки по центру колонки по вертикали")
    gap = column_gap(rules, ["safety"], desk)
    dose_gap = column_gap(rules, ["dose"], desk)
    pad = (px(cascade(rules, ["container"], "padding-left", desk)) or 0.0) + \
          (px(cascade(rules, ["container"], "padding-right", desk)) or 0.0)
    low, high = SAFETY_TEXT_SHARE
    for screen in DESKTOP_WIDTHS if template else ():
        width = min(screen, CONTENT_MAX) - pad
        try:
            sizes = track_sizes(template, width, gap)
        except ValueError as err:
            fail(f"[G31] .safety: grid-template-columns «{template}» не разобрать — {err}")
            break
        if not check(len(sizes) == 2, f"[G31] .safety на десктопе: {len(sizes)} колонок, нужно 2"):
            break
        share = sizes[0] / sum(sizes)
        check(low <= share <= high, f"[G31] десктоп {screen} px: колонка текста {share:.0%} ширины, нужно ≈ 40 %")
        card = (sizes[1] - dose_gap) / 2
        check(card <= SAFETY_CARD_MAX + 0.5,
              f"[G31] десктоп {screen} px: карточка {card:.0f} px — не шире {SAFETY_CARD_MAX}")
    for medias in (desk, ("", TABLET_MEDIA), every):
        where = medias[-1] or "десктоп"
        check(cascade(rules, ["dose"], "max-width", medias) in (None, "none"),
              f"[G31] .dose {where}: max-width — справа от карточек останется пусто")
        check(cascade(rules, ["dose"], "width", medias) in (None, "auto", "100%"),
              f"[G31] .dose {where}: ширина не на всю колонку")
        check(cascade(rules, ["dose"], "justify-self", medias) in (None, "auto", "stretch"),
              f"[G31] .dose {where}: justify-self сжимает ряд карточек")
    for medias, where in ((("", TABLET_MEDIA), "планшет"), (every, "телефон")):
        display = cascade(rules, ["safety"], "display", medias)
        narrow = cascade(rules, ["safety"], "grid-template-columns", medias) or ""
        try:
            single = display != "grid" or (bool(narrow) and len(track_sizes(narrow, 700, 0)) == 1)
        except ValueError:
            single = False
        check(single, f"[G31] .safety {where}: текст сверху, карточки под ним — одна колонка")
    # Телефон (ревью F11): карточка не шире 480 px и в столбце, и по 2 в ряд; ряд уже контента — по центру.
    phone_template = cascade(rules, ["dose"], "grid-template-columns", every) or ""
    phone_gap = column_gap(rules, ["dose"], every)
    phone_pad = (px(cascade(rules, ["container"], "padding-left", every)) or 0.0) + \
                (px(cascade(rules, ["container"], "padding-right", every)) or 0.0)
    centered = cascade(rules, ["dose"], "justify-content", every) == "center"
    for screen in SAFETY_PHONE_WIDTHS if phone_template else ():
        width = screen - phone_pad
        try:
            columns = grid_columns(phone_template, width, phone_gap)
        except ValueError as err:
            fail(f"[G31] .dose на телефоне: «{phone_template}» не разобрать — {err}")
            break
        share = (width - phone_gap * (len(columns) - 1)) / len(columns)
        sizes = [share if high is None else min(high, max(low, share)) for low, high in columns]
        check(max(sizes) <= SAFETY_CARD_MAX + 0.5,
              f"[G31] телефон {screen} px: карточка {max(sizes):.0f} px — не шире {SAFETY_CARD_MAX}")
        if sum(sizes) + phone_gap * (len(sizes) - 1) < width - 0.5:
            check(centered, f"[G31] телефон {screen} px: ряд карточек уже контента — нужен justify-content: center")


# ======================================================================== [G20] логотип

class _Source(HTMLParser):
    """Пути (атрибут d) трёх SVG логотипа в logo-intro.html — по viewBox."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.current = {}, None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "svg" and attrs.get("viewbox") in LOGO_PARTS:
            self.current = attrs["viewbox"]
            self.parts[self.current] = []
        elif tag == "path" and self.current and attrs.get("d"):
            self.parts[self.current].append(" ".join(attrs["d"].split()))

    handle_startendtag = handle_starttag

    def handle_endtag(self, tag):
        if tag == "svg":
            self.current = None


def check_logo(root, body, raw):
    """§11 (G20): логотип первого экрана — три SVG из logo-intro.html (знак, надпись, подпись) в одном блоке
    с доступным именем; PNG-логотипа нет; демо-элементов, шрифтов Golos Text / IBM Plex Mono и перехвата
    клавиш нет; ширина ≈ 230 px на десктопе и ≈ 120 px ниже 1200, подпись не мельче 10 px (ниже 1200 —
    скрыта, D05); скрытое до прорисовки — только под html.has-logo-intro (ставит main.js; без JS и при
    «уменьшить движение» его нет)."""
    check("logo-white" not in raw, "[G20] index.html ссылается на PNG-логотип logo-white — нужен SVG из logo-intro.html")
    top = by_id(body, "top")
    if top is None:
        return
    logos = by_class(top, "logo")
    if not check(len(logos) == 1, f"[G20] в первом экране нужен один блок .logo, найдено {len(logos)}"):
        return
    logo = logos[0]
    label = logo.attrs.get("aria-label") or ""
    check(logo.attrs.get("role") == "img" and norm(LOGO_LABEL) in norm(label),
          f"[G20] у .logo нужно role=\"img\" и aria-label с «{LOGO_LABEL}» (сейчас role={logo.attrs.get('role')}, "
          f"aria-label=«{label}»)")
    svgs = [n for n in logo.iter() if n.tag == "svg"]
    boxes = [" ".join((n.attrs.get("viewbox") or "").split()) for n in svgs]
    check(boxes == list(LOGO_PARTS), f"[G20] SVG логотипа (viewBox) {boxes}, нужны {list(LOGO_PARTS)} — "
                                     "знак, надпись и подпись из logo-intro.html")
    for svg in svgs:
        check(svg.attrs.get("aria-hidden") == "true",
              f"[G20] строка {svg.line}: SVG внутри .logo — aria-hidden=\"true\" (имя у блока .logo)")
    mine = {" ".join((n.attrs.get("viewbox") or "").split()):
            [" ".join(p.attrs["d"].split()) for p in n.iter() if p.tag == "path" and p.attrs.get("d")]
            for n in svgs}
    for box, (part, count) in LOGO_PARTS.items():
        check(len(mine.get(box, [])) == count, f"[G20] {part}: путей {len(mine.get(box, []))}, нужно {count}")
    source = ROOT / LOGO_SOURCE
    if source.is_file():
        parser = _Source()
        parser.feed(source.read_text(encoding="utf-8"))
        for box, (part, _) in LOGO_PARTS.items():
            want = parser.parts.get(box)
            if check(want is not None, f"[G20] в {LOGO_SOURCE} не найден SVG {part} (viewBox {box})"):
                check(sorted(mine.get(box, [])) == sorted(want),
                      f"[G20] {part}: геометрия путей не совпадает с {LOGO_SOURCE}")
    for n in body.iter():
        check(not (set(n.classes) & LOGO_DEMO_CLASSES) and n.attrs.get("id") not in LOGO_DEMO_IDS,
              f"[G20] строка {n.line}: демо-элемент заставки ({' '.join(n.classes) or n.attrs.get('id')}) — не переносится")
    texts = [raw] + [path.read_text(encoding="utf-8") for path in (STYLE, SCRIPT) if path.is_file()]
    for font in LOGO_DEMO_FONTS:
        check(not any(font in t for t in texts), f"[G20] шрифт заставки «{font}» — на странице только Inter")
    if not STYLE.is_file():
        return
    css = STYLE.read_text(encoding="utf-8")
    rules = css_rules_media(css)
    for label_, medias in (("десктоп", ("",)), ("телефон", ("", TABLET_MEDIA, PHONE_MEDIA))):
        width = px(cascade(rules, ["logo"], "width", medias))
        want = LOGO_WIDTH[label_]
        check(width is not None and abs(width - want) <= LOGO_TOL,
              f"[G20] .logo {label_}: width {width}, нужно ≈ {want}px (±{LOGO_TOL})")
    # D05: подпись «центр восстановления улыбок» не мельче 10 px. Высота её SVG = ширина × 105 / 1725,9
    # (viewBox); ширина — доля ширины блока .logo. Ниже 1200 логотип 120 px — подпись скрыта.
    mottos = by_class(logo, "logo__motto")
    if check(len(mottos) == 1, "[G20] в логотипе нет подписи .logo__motto"):
        motto = mottos[0]
        box = [float(v) for v in LOGO_MOTTO_BOX.split()]
        check(" ".join((motto.attrs.get("viewbox") or "").split()) == LOGO_MOTTO_BOX,
              f"[G20] .logo__motto: viewBox не {LOGO_MOTTO_BOX}")
        check(cascade(rules, motto.classes, "display", ("",)) != "none", "[G20] на десктопе подпись логотипа скрыта")
        logo_w = px(cascade(rules, ["logo"], "width", ("",)))
        share = cascade(rules, motto.classes, "width", ("",)) or ""
        m = re.fullmatch(r"(\d+(?:\.\d+)?)%", share)
        motto_w = (float(m.group(1)) / 100 * logo_w) if (m and logo_w) else px(share)
        height = motto_w * box[3] / box[2] if motto_w else None
        check(height is not None and height >= LOGO_MOTTO_MIN_PX - 1e-6,
              f"[G20] подпись логотипа на десктопе {height and round(height, 1)} px в высоту — нужно ≥ {LOGO_MOTTO_MIN_PX} px")
        for media in (TABLET_MEDIA, PHONE_MEDIA):
            medias = ("", TABLET_MEDIA) + ((PHONE_MEDIA,) if media == PHONE_MEDIA else ())
            check(cascade(rules, motto.classes, "display", medias) == "none",
                  f"[G20] {media}: подпись логотипа при ширине 120 px мельче {LOGO_MOTTO_MIN_PX} px — нужно display: none")
    for media, sel, decls in rules:
        if REDUCED_MOTION in media or media.startswith("@keyframes"):
            continue
        if ".logo" in sel and any(prop in decls for prop in STROKE_HIDING):  # пунктир маршрута (G30) — не логотип
            check(all(f".{LOGO_GATE}" in part for part in sel.split(",")),
                  f"[G20] «{sel}» прячет линии знака без класса .{LOGO_GATE} — без JS логотип не будет виден")
    gated = [sel for _, sel, _ in rules if f".{LOGO_GATE}" in sel]
    if gated and check(SCRIPT.is_file(), "[G20] нет main.js"):
        js = SCRIPT.read_text(encoding="utf-8")
        check(LOGO_GATE in js and "prefers-reduced-motion" in js,
              f"[G20] main.js не ставит {LOGO_GATE} с учётом «уменьшить движение» — логотип останется скрытым")
        reduced = [(sel, d) for media, sel, d in rules if REDUCED_MOTION in media]
        check(any(f".{LOGO_GATE}" in sel and d.get("opacity") == "1" for sel, d in reduced),
              f"[G20] @media ({REDUCED_MOTION}) не показывает логотип целиком (.{LOGO_GATE} … opacity: 1)")


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


def root_tokens(css):
    """{--токен: значение} из :root style.css (нижний регистр)."""
    tokens = {}
    for sel, decls in css_rules(css):
        if sel == ":root":
            tokens.update({k: v for k, v in decls.items() if k.startswith("--")})
    return tokens


def resolve(value, tokens):
    """«var(--x)» → значение токена; иначе как есть."""
    m = re.fullmatch(r"var\((--[\w-]+)\)", (value or "").strip())
    return tokens.get(m.group(1)) if m else value


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
                want = counts[idx][screen] if isinstance(counts[idx], dict) else counts[idx]
                if not check(count == want, f"[G15] {label} {screen} px, .{block}: {count} в ряд, нужно {want}"):
                    break
                # Колонки с потолком в px допустимы, только если ряд по центру (#safety на телефоне, ревью F11).
                centered = cascade(rules, [block], "justify-content", medias) == "center"
                check(all(high is None for _, high in columns) or centered,
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
            check(all(f".{REVEAL_GATE}" in part or f".{LOGO_GATE}" in part for part in sel.split(",")),
                  f"[G06] «{sel}» прячет контент без класса .{REVEAL_GATE} / .{LOGO_GATE} — без JS он не появится")
        for prop in ("transition", "transition-property"):
            for name in transition_names(d.get(prop) or "", prop):
                check(not LAYOUT_PROPS.match(name), f"[G06] «{sel}» {prop}: {name} — переход сдвигает вёрстку")
    if check(SCRIPT.is_file(), "[G06] нет assets/js/main.js"):
        js = SCRIPT.read_text(encoding="utf-8")
        for needle in ("IntersectionObserver", REVEAL_GATE, "prefers-reduced-motion"):
            check(needle in js, f"[G06] main.js: нет «{needle}» — появление при прокрутке не бережное")


# ======================================================================== [G21] размер H1

def check_hero_title():
    """§11 (G21): H1 — посередине между прежним H1 и H2 на каждой ширине (округлено до целого),
    интерлиньяж — пропорционально прежнему: десктоп 50/55, планшет и телефон 28/35."""
    if not STYLE.is_file():
        return
    rules = css_rules_media(STYLE.read_text(encoding="utf-8"))
    for media, (size, lead) in H1_PREV.items():
        h2_size = H2_SPEC[media][0]
        want_size = round((size + h2_size) / 2)
        want_lead = round(lead * want_size / size)
        medias = ("", media) if media else ("",)
        for prop, want in (("font-size", want_size), ("line-height", want_lead)):
            got = px(css_value(rules, ".hero__title", prop, medias))
            check(got == want, f"[G21] .hero__title {media or 'десктоп'}: {prop} {got}, нужно {want}px")
        if media:  # телефон не перебивает планшет
            phone = px(css_value(rules, ".hero__title", "font-size", ("", media, PHONE_MEDIA)))
            check(phone == want_size, f"[G21] .hero__title на телефоне: font-size {phone}, нужно {want_size}px")


# ======================================================================== [G23, G27] текст без появления, всплывание картинок

def time_s(token):
    """«0.25s» / «250ms» → секунды; иначе None."""
    m = re.fullmatch(r"(-?\d*\.?\d+)(m?s)", token.strip())
    if not m:
        return None
    return float(m.group(1)) / (1000 if m.group(2) == "ms" else 1)


def subject_classes(selector_part):
    """Классы последнего составного селектора: «.has-reveal .reveal.is-in» → {'reveal', 'is-in'}."""
    last = selector_part.strip().split()[-1] if selector_part.strip() else ""
    return set(re.findall(r"\.([\w-]+)", re.sub(r"::?[\w-]+(\([^)]*\))?", "", last)))


def text_outside_pictures(node):
    """Видимый текст узла без подписей маршрута — они часть картинки и появляются вместе с ней (G30)."""
    if isinstance(node, str):
        return node
    if node.tag in HIDDEN_TAGS or "hidden" in node.attrs or ROUTE_CLASS in node.classes:
        return ""
    sep = "" if node.tag in INLINE_TAGS else " "
    return sep + "".join(text_outside_pictures(c) for c in node.children) + sep


def check_text_motion(body):
    """§11 (G23): у текста анимации появления нет совсем — CSS-анимации (animation) и появление из main.js
    касаются только элементов без текста (картинки, карточки, логотип; подписи маршрута — часть картинки);
    въезд первого экрана ≤ 0,6 с. §12 (G27): картинки и карточки #clarify, #safety, #after и карточка
    #planning заметно всплывают — opacity 0 → 1 и translateY ≈ 28 px → 0 за ≈ 0,7 с, в ряду по очереди
    (шаг ≈ 90 мс); срабатывает в зоне видимости: rootMargin снизу от −15 % до 0, порог ≤ 0,5 — не за краем
    экрана; при наведении мышью — подъём 4–6 px."""
    if not STYLE.is_file():
        return

    def with_text(classes):
        return [n for n in body.iter() if classes and classes <= set(n.classes) and squash(text_outside_pictures(n))]

    rules = css_rules_media(STYLE.read_text(encoding="utf-8"))
    hidden_state = shown_state = False
    for media, sel, d in rules:
        if REDUCED_MOTION in media or media == "@media print" or media.startswith("@keyframes"):
            continue
        anim = d.get("animation") or d.get("animation-name")
        if anim and anim != "none":
            for part in sel.split(","):
                hits = with_text(subject_classes(part))
                check(not hits, f"[G23] «{part.strip()}» animation: {anim} — у текста анимации появления нет "
                                f"({', '.join(sorted({' '.join(n.classes) for n in hits}))})")
                if ".hero" in part:
                    times = [t for t in (time_s(tok) for tok in split_top(anim, " ")) if t is not None]
                    check(sum(times[:2]) <= HERO_ENTRANCE_MAX_S + 1e-9,
                          f"[G23] «{part.strip()}»: въезд первого экрана {sum(times[:2]):.2f} с, нужно ≤ {HERO_ENTRANCE_MAX_S} с")
        if f".{REVEAL_GATE}" not in sel:
            continue
        for part in sel.split(","):
            subject = subject_classes(part)
            if "reveal" not in subject:
                continue  # маршрут внутри карточки проверяет check_safety
            transform = d.get("transform") or ""
            where = f"[G27] «{part.strip()}»"
            if "is-in" not in subject:
                hidden_state = True
                low, high = REVEAL_SHIFT_PX
                shift = re.search(r"translatey\((-?\d+(?:\.\d+)?)px\)", transform)
                if check(shift is not None, f"{where}: картинка всплывает снизу — нужен translateY({low}–{high}px)"):
                    check(low <= float(shift.group(1)) <= high,
                          f"{where}: сдвиг при всплывании {shift.group(1)}px, нужно {low}–{high}px")
                check("translatex" not in transform and "scale" not in transform,
                      f"{where}: при всплывании только сдвиг по вертикали")
                check(d.get("opacity") == "0", f"{where}: до появления картинка прозрачна (opacity: 0)")
            elif d.get("transition"):
                shown_state = True
                low, high = REVEAL_S
                for item in split_top(d["transition"], ","):
                    times = [t for t in (time_s(tok) for tok in split_top(item, " ")) if t is not None]
                    check(bool(times) and low <= times[0] <= high,
                          f"{where}: всплывание {times[0] if times else '?'} с, нужно {low}–{high} с")
    check(hidden_state and shown_state,
          f"[G27] в style.css нет пары «.{REVEAL_GATE} .reveal» (скрыто, сдвиг вниз) и «.reveal.is-in» (переход)")

    # Наведение мышью: картинка или её карточка «парит» — подъём 4–6 px.
    lifts = {}
    for media, sel, d in rules:
        shift = re.search(r"translatey\((-?\d+(?:\.\d+)?)px\)", d.get("transform") or "")
        if media != "@media (hover: hover)" or not shift:
            continue
        for part in sel.split(","):
            last = part.strip().split()[-1] if part.strip() else ""
            if last.endswith(":hover"):
                for cls in re.findall(r"\.([\w-]+)", last):
                    lifts[cls] = abs(float(shift.group(1)))
    low, high = HOVER_LIFT_PX
    for sid, cls in REVEAL_TARGETS.items():
        section = by_id(body, sid)
        nodes = by_class(section, cls) if section is not None else []
        check(bool(nodes), f"[G27] в #{sid} нет .{cls} — нечему всплывать")
        for node in nodes:
            got = [lifts[c] for n in [node, *node.ancestors()] for c in n.classes if c in lifts][:1]
            check(bool(got) and low <= got[0] <= high,
                  f"[G27] #{sid} .{cls} (строка {node.line}): при наведении мышью — подъём {low}–{high} px, сейчас {got}")

    if not check(SCRIPT.is_file(), "[G23] нет main.js"):
        return
    js = re.sub(r"/\*.*?\*/|(?<![:\w])//[^\n]*", "", SCRIPT.read_text(encoding="utf-8"), flags=re.S)
    touched = set()
    for literal in re.findall(r"'([^'\n]*)'|\"([^\"\n]*)\"", js):
        text = literal[0] or literal[1]
        touched |= set(re.findall(r"(?<![\w.])\.([a-z][\w-]*)", text))
    for cls in sorted(touched):
        hits = with_text({cls})
        check(not hits, f"[G23] main.js работает с .{cls}, а в нём текст (строка {hits[0].line if hits else ''}) — "
                        "появление при прокрутке только у картинок и карточек")
    for sid, cls in REVEAL_TARGETS.items():
        check(cls in touched, f"[G27] main.js не показывает .{cls} при прокрутке — картинки #{sid} не всплывают")
    step = re.search(r"\bSTEP\s*=\s*(\d+)", js)
    low, high = REVEAL_STEP_MS
    check(bool(step) and low <= int(step.group(1)) <= high,
          f"[G27] main.js: шаг очереди в ряду (STEP) {step and step.group(1)} мс, нужно {low}–{high} мс")
    # Появление — rootMargin в долях экрана; поле загрузки ролика в px (F10) проверяет check_planning_video.
    margins = root_margins(js)
    reveal = [(v, margin_bottom(v)) for v in margins if (margin_bottom(v) or (0, ""))[1] != "px"]
    low, high = REVEAL_MARGIN_PCT
    if check(len(reveal) == 1, f"[G27] main.js: нужен один rootMargin появления (в %), найдено {[v for v, _ in reveal]}"):
        value, bottom = reveal[0]
        check(bool(bottom) and low <= bottom[0] <= high,
              f"[G27] main.js: rootMargin «{value}» — снизу нужно от {low}% до {high}%: картинка всплывает в экране, "
              "а не за его краем")
    # Порог — у наблюдателя всплывания (его параметры — объект с rootMargin в %); у маршрута свой (G30).
    options = [o for o in re.findall(r"\{[^{}]*rootMargin[^{}]*\}", js)
               if (margin_bottom((root_margins(o) or [""])[0]) or (0, ""))[1] == "%"]
    thresholds = [float(v) for o in options for group in re.findall(r"threshold\s*:\s*\[?([\d.,\s]+)\]?", o)
                  for v in re.findall(r"\d*\.?\d+", group)]
    check(len(options) == 1 and all(t <= REVEAL_MAX_THRESHOLD for t in thresholds),
          f"[G27] main.js: threshold всплывания {thresholds} — не позже, чем картинка видна наполовину")


# ======================================================================== README

def check_readme():
    if not check(README.is_file(), "[README] нет README.md"):
        return
    text = README.read_text(encoding="utf-8")
    check("Что заменить" not in text, "[README] осталась таблица «Что заменить» — заглушек в редакции 2 нет")
    for anchor in ("#telegram", "#whatsapp", "#max", "#vopros", "#video", "#uslugi"):
        check(anchor not in text, f"[README] осталась заглушка {anchor}")
    for needle in ("tools/check_site.py", FONT_NAME, "Пикассо", "assets/video/"):  # F10: README — о ролике тоже
        check(needle in text, f"[README] нет «{needle}»")
    for figure in (DOSE_UNIT, "20–200", "50–80", "8 мкЗв"):  # G29: цифр дозы на странице больше нет
        check(figure not in text, f"[README] устаревшее упоминание цифр дозы «{figure}»")


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
