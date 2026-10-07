/* Денталь профи — поведение страницы. Без JS страница читается полностью.
   1. Мобильное меню (ширина < 1200).
   2. Появление блоков при прокрутке (§9 спеки).
   3. Секции 4 и 6: пункт списка ↔ картинка с тем же номером (§9 спеки). */

/* 1. Мобильное меню. Открыть — бургер; закрыть — крестик, Esc, клик по пункту.
   Пока меню открыто, страница не прокручивается, фокус не выходит из меню;
   после закрытия фокус возвращается на бургер. */
(function () {
  'use strict';

  var menu = document.querySelector('[data-menu]');
  var openButton = document.querySelector('[data-menu-open]');
  if (!menu || !openButton) return;

  var closeButton = menu.querySelector('[data-menu-close]');
  var root = document.documentElement;
  var desktop = window.matchMedia('(min-width: 1200px)');

  function isOpen() {
    return !menu.hidden;
  }

  function focusableItems() {
    return Array.prototype.slice.call(menu.querySelectorAll('a[href], button:not([disabled])'));
  }

  function openMenu() {
    if (isOpen()) return;
    menu.hidden = false;
    openButton.setAttribute('aria-expanded', 'true');
    root.classList.add('is-menu-open');
    document.addEventListener('keydown', onKeydown);
    var firstLink = menu.querySelector('.mobile-menu__link');
    (firstLink || closeButton).focus();
  }

  function closeMenu(returnFocus) {
    if (!isOpen()) return;
    menu.hidden = true;
    openButton.setAttribute('aria-expanded', 'false');
    root.classList.remove('is-menu-open');
    document.removeEventListener('keydown', onKeydown);
    if (returnFocus) openButton.focus({ preventScroll: true });
  }

  function onKeydown(event) {
    if (event.key === 'Escape' || event.key === 'Esc') {
      event.preventDefault();
      closeMenu(true);
      return;
    }
    if (event.key !== 'Tab') return;
    // Фокус остаётся внутри меню.
    var items = focusableItems();
    if (!items.length) return;
    var first = items[0];
    var last = items[items.length - 1];
    if (event.shiftKey && (document.activeElement === first || !menu.contains(document.activeElement))) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && (document.activeElement === last || !menu.contains(document.activeElement))) {
      event.preventDefault();
      first.focus();
    }
  }

  openButton.addEventListener('click', openMenu);

  if (closeButton) {
    closeButton.addEventListener('click', function () {
      closeMenu(true);
    });
  }

  // Клик по пункту: меню закрывается, переход по ссылке идёт как обычно.
  menu.addEventListener('click', function (event) {
    var link = event.target.closest('a[href]');
    if (link) closeMenu(true);
  });

  // Окно расширили до десктопа — оверлей больше не нужен.
  function onBreakpoint(event) {
    if (event.matches) closeMenu(false);
  }
  if (desktop.addEventListener) {
    desktop.addEventListener('change', onBreakpoint);
  } else if (desktop.addListener) {
    desktop.addListener(onBreakpoint);
  }
})();

/* 2. Появление при прокрутке: заголовки, абзацы, карточки, ячейки, строки списков, кнопки CTA
   входят в экран (порог 15 %) из opacity 0 / translateY(24px), один раз. Элементы одного ряда,
   сетки или списка — по очереди, шаг 70 мс. Скрытие включает класс html.has-reveal, и ставится
   он только здесь: без JS, без IntersectionObserver и при «уменьшить движение» всё видно сразу. */
(function () {
  'use strict';

  var TARGETS = '.h2, .lead, .card, .facts__item, .facts__cell, .compare__title, .compare__item, ' +
    '.best__line, .best__img, .cta__text, .cta__buttons .btn';
  var STEP = 70;       // мс между соседями
  var MAX_STEPS = 8;   // дальше задержка не растёт
  var DURATION = 600;  // мс — как переход .reveal.is-in в style.css

  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce || !('IntersectionObserver' in window)) return;

  var targets = Array.prototype.slice.call(document.querySelectorAll(TARGETS));
  if (!targets.length) return;

  var order = new Map();
  targets.forEach(function (el, index) {
    order.set(el, index);
    el.classList.add('reveal');
  });
  document.documentElement.classList.add('has-reveal');

  function show(el, delay) {
    el.style.setProperty('--reveal-delay', delay + 'ms');
    el.classList.add('is-in');
    // После появления элемент возвращается к обычным стилям — наведение без задержки.
    window.setTimeout(function () {
      el.classList.remove('reveal', 'is-in');
      el.style.removeProperty('--reveal-delay');
      if (!el.getAttribute('style')) el.removeAttribute('style');
    }, delay + DURATION + 50);
  }

  var observer = new IntersectionObserver(function (entries) {
    var batch = entries
      .filter(function (entry) { return entry.isIntersecting; })
      .map(function (entry) { return entry.target; })
      .sort(function (a, b) { return order.get(a) - order.get(b); });
    // Группа — общий родитель (ряд карточек, сетка, список); каждая следующая группа
    // этой пачки начинает на шаг позже предыдущей.
    var groups = [];
    var counts = new Map();
    batch.forEach(function (el) {
      var group = el.parentNode;
      if (!counts.has(group)) {
        counts.set(group, 0);
        groups.push(group);
      }
      var step = Math.min(groups.indexOf(group) + counts.get(group), MAX_STEPS);
      counts.set(group, counts.get(group) + 1);
      observer.unobserve(el);
      show(el, step * STEP);
    });
  }, { threshold: 0.15 });

  targets.forEach(function (el) {
    observer.observe(el);
  });
})();

/* 3. Секции 4 и 6 ([data-facts]): пункт списка — кнопка с aria-controls на картинку своего номера.
   Наведение мыши или фокус с клавиатуры на пункт и наведение на картинку подсвечивают пару
   (класс is-lit у пункта и картинки). Нажатие делает пару активной до следующего нажатия
   (aria-pressed, класс is-active); повторное нажатие снимает. Если сетка стоит под списком
   (телефон), нажатие мышью или пальцем плавно прокручивает к картинке. */
(function () {
  'use strict';

  var blocks = document.querySelectorAll('[data-facts]');
  if (!blocks.length) return;
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)');

  // Фокус мышью не подсвечивает — иначе снятая нажатием пара осталась бы подсвеченной.
  function keyboardFocus(el) {
    try {
      return el.matches(':focus-visible');
    } catch (error) {
      return true;
    }
  }

  Array.prototype.forEach.call(blocks, function (block) {
    var list = block.querySelector('.facts__list');
    var grid = block.querySelector('.facts__grid');
    var pairs = [];
    Array.prototype.forEach.call(block.querySelectorAll('button[aria-controls]'), function (button) {
      var cell = document.getElementById(button.getAttribute('aria-controls'));
      var item = button.closest('.facts__item');
      if (cell && item) pairs.push({ button: button, item: item, cell: cell, hover: false, focus: false });
    });

    function paint(pair) {
      var lit = pair.hover || pair.focus;
      pair.item.classList.toggle('is-lit', lit);
      pair.cell.classList.toggle('is-lit', lit);
    }

    function setActive(active) {
      pairs.forEach(function (pair) {
        var on = pair === active;
        pair.button.setAttribute('aria-pressed', on ? 'true' : 'false');
        pair.item.classList.toggle('is-active', on);
        pair.cell.classList.toggle('is-active', on);
      });
    }

    function gridBelowList() {
      return grid.getBoundingClientRect().top >= list.getBoundingClientRect().bottom - 1;
    }

    function scrollToCell(cell) {
      var rect = cell.getBoundingClientRect();
      var viewport = window.innerHeight || document.documentElement.clientHeight;
      if (rect.top >= 0 && rect.bottom <= viewport) return;
      cell.scrollIntoView({ behavior: reduce && reduce.matches ? 'auto' : 'smooth', block: 'center' });
    }

    function hover(pair, on) {
      return function (event) {
        if (event.pointerType === 'touch') return;  // тап — нажатие, а не наведение
        pair.hover = on;
        paint(pair);
      };
    }

    pairs.forEach(function (pair) {
      pair.item.addEventListener('pointerenter', hover(pair, true));
      pair.item.addEventListener('pointerleave', hover(pair, false));
      pair.cell.addEventListener('pointerenter', hover(pair, true));
      pair.cell.addEventListener('pointerleave', hover(pair, false));

      pair.button.addEventListener('focus', function () {
        pair.focus = keyboardFocus(pair.button);
        paint(pair);
      });
      pair.button.addEventListener('blur', function () {
        pair.focus = false;
        paint(pair);
      });

      pair.button.addEventListener('click', function (event) {
        var pressed = pair.button.getAttribute('aria-pressed') === 'true';
        setActive(pressed ? null : pair);
        // detail > 0 — мышь или палец; с клавиатуры фокус не уводим из вида.
        if (!pressed && event.detail > 0 && list && grid && gridBelowList()) scrollToCell(pair.cell);
      });
    });
  });
})();
