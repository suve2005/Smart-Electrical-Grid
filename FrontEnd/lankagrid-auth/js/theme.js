/* ==========================================================================
   theme.js – dark / light mode
   - The inline snippet in <head> sets data-theme before first paint.
   - This file wires the toggle button(s), persists the choice, follows the
     OS setting until the user picks a theme manually, and syncs aria-pressed.
   ========================================================================== */
(function () {
  'use strict';

  var KEY = 'lg-theme';
  var root = document.documentElement;
  var media = window.matchMedia('(prefers-color-scheme: dark)');
  var timer;

  function readStored() {
    try {
      var v = localStorage.getItem(KEY);
      return v === 'light' || v === 'dark' ? v : null;
    } catch (e) {
      return null; // storage blocked (private mode etc.)
    }
  }

  function store(theme) {
    try { localStorage.setItem(KEY, theme); } catch (e) { /* ignore */ }
  }

  function current() {
    return root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  }

  function apply(theme, animate) {
    if (animate) {
      // Enables the 200ms colour transition only during a manual switch
      root.classList.add('theme-transition');
      clearTimeout(timer);
      timer = setTimeout(function () { root.classList.remove('theme-transition'); }, 300);
    }
    root.setAttribute('data-theme', theme);
    document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
      btn.setAttribute('aria-pressed', String(theme === 'dark'));
    });
  }

  // Initial sync (stored choice > OS preference)
  apply(readStored() || (media.matches ? 'dark' : 'light'), false);

  document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var next = current() === 'dark' ? 'light' : 'dark';
      store(next);
      apply(next, true);
    });
  });

  // Follow OS changes only while the user has not chosen manually
  var onOsChange = function (e) {
    if (!readStored()) apply(e.matches ? 'dark' : 'light', true);
  };
  if (media.addEventListener) media.addEventListener('change', onOsChange);
  else if (media.addListener) media.addListener(onOsChange);
})();
