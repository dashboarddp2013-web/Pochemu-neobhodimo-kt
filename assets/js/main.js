/* Денталь профи — поведение страницы (редакция 3, §11 спеки). Без JS страница читается полностью.

   1. Логотип первого экрана (G20) — прорисовка из logo-intro.html: тонкая светлая линия загорается
      на вершине дуги, бежит по ней и по зубам, набирает фирменную толщину, по знаку проходит блик,
      проявляются «Денталь Профи» и подпись. Один раз при загрузке; таймлайн заставки проигрывается
      в SPEED раз быстрее — целиком за ≈ 2,4 с. Заголовок, текст и картинка первого экрана её не ждут.
      Скрытое до прорисовки состояние включает класс html.has-logo-intro. Ставится он только здесь,
      сразу при разборе <head> (скрипт подключён без defer — до первой отрисовки, иначе мелькнул бы
      готовый знак), и только если анимация возможна: есть Web Animations API и «уменьшить движение»
      выключено. После прорисовки класс снимается, анимации отменяются — остаётся статичная разметка,
      она и есть последний кадр. Кнопок и клавиш заставки на странице нет.
   2. Появление при прокрутке (G23): только картинки и карточки без текста — 0,25 с, сдвиг 10 px,
      заранее: за четверть экрана до того, как элемент в него войдёт; соседи в ряду — с шагом 30 мс.
      Текст виден сразу всегда. Скрытие включает класс html.has-reveal — тоже только здесь:
      без JS, без IntersectionObserver и при «уменьшить движение» всё видно сразу.
   3. Ролик «КТ в работе» в #planning (G22, таск F10): в разметке у <video> только кадр-заставка
      (poster, preload="none"), адрес файла — в data-src. Когда блок подходит к экрану ближе ≈ 300 px,
      адрес подставляется и ролик начинает грузиться; играет, пока блок виден, вне экрана — на паузе.
      При «уменьшить движение» и в режиме экономии трафика (navigator.connection.saveData) адрес
      не подставляется вовсе — остаётся заставка. Без JS — тоже заставка. */
(function () {
  'use strict';

  var root = document.documentElement;
  var reduce = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  /* ================= 1. Логотип ================= */

  var LOGO_GATE = 'has-logo-intro';
  var logoIntro = !reduce && typeof root.animate === 'function' && typeof Promise === 'function';
  if (logoIntro) root.classList.add(LOGO_GATE);

  /* Таймлайн заставки logo-intro.html, секунды от старта (без приглушения фона и «приземления»). */
  var T = {
    cam: 5.4,                    // медленное «отъезжание» 1.05 → 1
    pen0: 0.5, pen: 2.45,        // тонкая линия прочерчивает знак
    swell0: 2.75, swell: 1.3,    // линия набирает толщину
    sheen0: 3.6, sheen: 1.4,     // блик по знаку
    word: 3.2, wordStep: 0.06, wordDur: 1.4,
    tag: 3.95, tagDur: 1.7       // подпись — последней: 3,95 + 1,7 = 5,65 с
  };
  var SPEED = 2.35;              // 5,65 с / 2,35 ≈ 2,4 с — не дольше ~2,5 с (§11)
  var H = 70;                    // длина светящегося кончика, ед. viewBox
  var FRAMES = 110;              // кадров на ход линии

  /* Аналог CSS cubic-bezier() для расчёта движения линии по кадрам. */
  function bezier(x1, y1, x2, y2) {
    function cx(t) { return ((1 - 3 * x2 + 3 * x1) * t + (3 * x2 - 6 * x1)) * t * t + 3 * x1 * t; }
    function cy(t) { return ((1 - 3 * y2 + 3 * y1) * t + (3 * y2 - 6 * y1)) * t * t + 3 * y1 * t; }
    function dx(t) { return 3 * (1 - 3 * x2 + 3 * x1) * t * t + 2 * (3 * x2 - 6 * x1) * t + 3 * x1; }
    return function (x) {
      if (x <= 0) return 0;
      if (x >= 1) return 1;
      var t = x;
      var i;
      var d;
      for (i = 0; i < 8; i++) {
        d = dx(t);
        if (Math.abs(d) < 1e-6) break;
        t -= (cx(t) - x) / d;
      }
      if (!(t >= 0 && t <= 1) || Math.abs(cx(t) - x) > 1e-4) {
        var lo = 0;
        var hi = 1;
        t = x;
        for (i = 0; i < 40; i++) {
          if (cx(t) < x) lo = t; else hi = t;
          t = (lo + hi) / 2;
        }
      }
      return cy(t);
    };
  }
  // мягкий разгон и долгое плавное торможение у кончиков корней
  var penEase = bezier(0.45, 0.05, 0.2, 1);

  function ms(seconds) {
    return Math.round(seconds * 1000 / SPEED);
  }

  function clamp(v) {
    return v < 0 ? 0 : v > 1 ? 1 : v;
  }

  function startLogo() {
    var logo = document.querySelector('.logo');
    var anims = [];
    var sparks = [];
    var done = false;

    // Всё доиграно (или что-то пошло не так): статичная разметка — и есть последний кадр.
    function finish() {
      if (done) return;
      done = true;
      root.classList.remove(LOGO_GATE);
      anims.forEach(function (a) {
        try { a.cancel(); } catch (e) { /* уже отменена */ }
      });
      sparks.forEach(function (el) {
        el.style.removeProperty('stroke-dasharray');
        if (!el.getAttribute('style')) el.removeAttribute('style');
      });
    }

    function play(el, keyframes, options) {
      if (!el) return;
      options.fill = 'both';
      anims.push(el.animate(keyframes, options));
    }

    if (!logo) {
      finish();
      return;
    }

    try {
      // Шесть отрезков: дуга от вершины влево и вправо, затем каждый зуб — двумя половинами
      // от стыка с дугой до кончика корня.
      var ids = ['AL', 'AR', 'BR', 'BL', 'SR', 'SL'];
      var line = {};
      var head = {};
      var len = {};
      ids.forEach(function (k) {
        line[k] = document.getElementById('dp' + k);
        head[k] = document.getElementById('dp' + k + 'h');
        len[k] = line[k].getTotalLength();
        sparks.push(head[k]);
      });

      // --- сцена: композиция чуть-чуть «отъезжает», как камера ---
      play(logo, [{ transform: 'scale(1.05)' }, { transform: 'scale(1)' }],
        { delay: 0, duration: ms(T.cam), easing: 'cubic-bezier(.25,.55,.25,1)' });

      // --- тонкая линия: все четыре ветки замыкаются в один момент; доли общего хода, когда дуга
      // доходит до зубов, подобраны так, чтобы скорость линий была близкой ---
      var uJ = len.AL / (len.AL + (len.BR + len.BL) / 2);
      var uK = len.AR / (len.AR + (len.SR + len.SL) / 2);
      var progress = {
        AL: function (u) { return u / uJ; },
        AR: function (u) { return u / uK; },
        BR: function (u) { return (u - uJ) / (1 - uJ); },
        BL: function (u) { return (u - uJ) / (1 - uJ); },
        SR: function (u) { return (u - uK) / (1 - uK); },
        SL: function (u) { return (u - uK) / (1 - uK); }
      };
      var offset = function (p) { return p <= 0 ? 1001 : 1000 * (1 - p); };   // при p=0 линии нет совсем
      var headOffset = function (p, h) { return h + 1 - 1000 * p; };          // кончик: [1000p-h-1, 1000p-1]

      ids.forEach(function (k) {
        var h = H / len[k] * 1000;
        var arc = k.charAt(0) === 'A';
        head[k].style.strokeDasharray = h.toFixed(2) + ' 9000';
        var lineFrames = [];
        var headFrames = [];
        for (var i = 0; i <= FRAMES; i++) {
          var x = i / FRAMES;
          var p = progress[k](penEase(x));
          lineFrames.push({ offset: x, strokeDashoffset: offset(clamp(p)) });
          // кончик дуги уходит за её конец и гаснет там, где начинаются ветки зуба
          headFrames.push({ offset: x, strokeDashoffset: headOffset(arc ? Math.max(p, 0) : clamp(p), h) });
        }
        play(line[k], lineFrames, { delay: ms(T.pen0), duration: ms(T.pen), easing: 'linear' });
        play(head[k], headFrames, { delay: ms(T.pen0), duration: ms(T.pen), easing: 'linear' });

        // --- линия набирает толщину; клип держит точный контур логотипа ---
        play(line[k], [
          { strokeWidth: '5.5px', easing: 'cubic-bezier(.62,0,.3,1)' },
          { strokeWidth: '31px', offset: 0.88 },
          { strokeWidth: '36px' }
        ], { delay: ms(T.swell0), duration: ms(T.swell), easing: 'linear' });
      });

      // светящиеся кончики: мягко загораются и гаснут, когда ветки сошлись
      var headDur = T.pen + 0.55;
      play(logo.querySelector('.logo__sparks'), [
        { strokeOpacity: 0 },
        { strokeOpacity: 1, offset: 0.3 / headDur },
        { strokeOpacity: 1, offset: (T.pen - 0.12) / headDur },
        { strokeOpacity: 0 }
      ], { delay: ms(T.pen0), duration: ms(headDur), easing: 'linear' });

      // --- блик по знаку, как свет по эмали ---
      play(logo.querySelector('.logo__sweep'), [{ transform: 'translateX(-780px)' }, { transform: 'translateX(780px)' }],
        { delay: ms(T.sheen0), duration: ms(T.sheen), easing: 'cubic-bezier(.45,.05,.3,1)' });

      // --- «ДЕНТАЛЬ ПРОФИ»: буквы по очереди проявляются, чуть всплывая и сходясь к центру ---
      var word = logo.querySelector('.logo__word');
      var wordCenter = parseFloat(word.getAttribute('data-cx')) || 1005;
      Array.prototype.forEach.call(word.querySelectorAll('.logo__letter'), function (el, k) {
        var c = parseFloat(el.getAttribute('data-cx'));
        var delay = ms(T.word + k * T.wordStep);
        play(el, [
          { transform: 'translate(' + ((c - wordCenter) * 0.045).toFixed(1) + 'px, 34px)' },
          { transform: 'translate(0px, 0px)' }
        ], { delay: delay, duration: ms(T.wordDur), easing: 'cubic-bezier(.2,.6,.25,1)' });
        play(el, [{ opacity: 0 }, { opacity: 1 }],
          { delay: delay, duration: ms(T.wordDur * 0.8), easing: 'cubic-bezier(.4,0,.3,1)' });
      });

      // --- подпись: буквы медленно сходятся к центру — трекинг сжимается ---
      var motto = logo.querySelector('.logo__motto');
      var mottoCenter = parseFloat(motto.getAttribute('data-cx')) || 1004;
      Array.prototype.forEach.call(motto.querySelectorAll('.logo__glyph'), function (el) {
        var c = parseFloat(el.getAttribute('data-cx'));
        play(el, [
          { transform: 'translateX(' + ((c - mottoCenter) * 0.12).toFixed(1) + 'px)' },
          { transform: 'translateX(0px)' }
        ], { delay: ms(T.tag), duration: ms(T.tagDur), easing: 'cubic-bezier(.2,.65,.25,1)' });
        play(el, [{ opacity: 0 }, { opacity: 1 }],
          { delay: ms(T.tag), duration: ms(T.tagDur * 0.75), easing: 'cubic-bezier(.4,0,.3,1)' });
      });

      Promise.all(anims.map(function (a) { return a.finished; })).then(finish, finish);
      // страховка: что бы ни случилось с анимациями, через секунду после конца логотип виден целиком
      window.setTimeout(finish, ms(T.tag + T.tagDur) + 1000);
    } catch (e) {
      finish();
    }
  }

  /* ================= 2. Появление картинок при прокрутке ================= */

  var TARGETS = '.gallery__img, .planning__card, .dose__img, .steps__img, .split__img';
  var STEP = 30;        // мс между соседями
  var MAX_STEPS = 3;    // дальше задержка не растёт: с задержкой — не дольше 0,34 с
  var DURATION = 250;   // мс — как переход .reveal.is-in в style.css

  function startReveal() {
    if (reduce || !('IntersectionObserver' in window)) return;
    var targets = Array.prototype.slice.call(document.querySelectorAll(TARGETS));
    if (!targets.length) return;

    var order = new Map();
    targets.forEach(function (el, index) {
      order.set(el, index);
      el.classList.add('reveal');
    });
    root.classList.add('has-reveal');

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
      // Картинки, вошедшие в зону вместе (ряд иллюстраций, шаги), — по очереди, в порядке страницы.
      batch.forEach(function (el, index) {
        observer.unobserve(el);
        show(el, Math.min(index, MAX_STEPS) * STEP);
      });
    }, { rootMargin: '0px 0px 25% 0px', threshold: 0 });

    targets.forEach(function (el) {
      observer.observe(el);
    });
  }

  /* ================= 3. Ролик в #planning ================= */

  function saveData() {
    var connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    return !!(connection && connection.saveData);
  }

  function startVideo() {
    var video = document.querySelector('.planning__video');
    if (!video) return;
    var src = video.getAttribute('data-src');
    // Ролик — украшение: без него остаётся заставка, а трафик и движение пациента важнее.
    if (!src || reduce || saveData() || !('IntersectionObserver' in window)) return;

    var loaded = false;
    var visible = false;
    video.muted = true;   // свойство, а не только атрибут: без звука браузер разрешает автозапуск

    function update() {
      if (!loaded) return;
      if (visible) {
        var playing = video.play();
        // Автозапуск может быть запрещён (например, режим энергосбережения iOS) — тогда видна заставка.
        if (playing && typeof playing.catch === 'function') playing.catch(function () { return null; });
      } else {
        video.pause();
      }
    }

    // Загрузка — заранее, когда блок ближе ≈ 300 px к экрану; один раз.
    var loader = new IntersectionObserver(function (entries) {
      if (!entries.some(function (entry) { return entry.isIntersecting; })) return;
      loader.disconnect();
      loaded = true;
      video.preload = 'auto';
      video.src = src;
      video.load();
      update();
    }, { rootMargin: '300px 0px 300px 0px' });

    // Воспроизведение — пока хоть часть ролика на экране.
    var player = new IntersectionObserver(function (entries) {
      visible = entries[entries.length - 1].isIntersecting;
      update();
    });

    loader.observe(video);
    player.observe(video);
  }

  /* ================= Запуск ================= */

  function ready(fn) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn);
    else fn();
  }

  ready(function () {
    if (logoIntro) startLogo();
    startReveal();
    startVideo();
  });
})();
