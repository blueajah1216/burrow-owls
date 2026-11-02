// Top-left Menu button: opens/closes the navigation dropdown.
(() => {
  const top = document.querySelector('header.top'), btn = document.getElementById('menu-btn'); if (!top || !btn) return;
  const set = open => { top.classList.toggle('open', open); btn.setAttribute('aria-expanded', open ? 'true' : 'false'); };
  btn.addEventListener('click', () => set(!top.classList.contains('open')));
  document.addEventListener('click', e => { if (top.classList.contains('open') && !top.contains(e.target)) set(false); });
  addEventListener('keydown', e => { if (e.key === 'Escape') { set(false); btn.focus(); } });
})();
