/* Денталь профи — поведение страницы. Без JS страница читается полностью.
   Появление блоков при прокрутке (§9 спеки): заголовки, абзацы, иллюстрации, пункты и шаги
   входят в экран (порог 15 %) из opacity 0 / translateY(24px), один раз. Элементы одного ряда
   или списка — по очереди, шаг 70 мс. Скрытие включает класс html.has-reveal, и ставится он
   только здесь: без JS, без IntersectionObserver и при «уменьшить движение» всё видно сразу. */
(function () {
  'use strict';

  var TARGETS = '.h2, .lead, .gallery__item, .split__img, .split__rule, .howto__item, .steps__item';
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
    // Группа — общий родитель (ряд иллюстраций, список, текст секции); каждая следующая
    // группа этой пачки начинает на шаг позже предыдущей.
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
