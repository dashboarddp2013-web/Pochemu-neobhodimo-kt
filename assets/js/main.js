/* Денталь профи — мобильное меню (ширина < 1200).
   Открыть — бургер; закрыть — крестик, Esc, клик по пункту.
   Пока меню открыто, страница не прокручивается, фокус не выходит из меню;
   после закрытия фокус возвращается на бургер. Без JS страница читается полностью. */
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
