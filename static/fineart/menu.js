// Mobile menu: on narrow screens, tapping the logo opens/closes the nav as a dropdown.
(() => {
  const top = document.querySelector('header.top'); if (!top) return;
  const brand = top.querySelector('.brand'), nav = top.querySelector('nav');
  const mq = matchMedia('(max-width:980px)');
  nav.id = nav.id || 'topnav';
  brand.setAttribute('aria-controls', nav.id); brand.setAttribute('aria-expanded', 'false');
  const set = open => { top.classList.toggle('open', open); brand.setAttribute('aria-expanded', open ? 'true' : 'false'); };
  brand.addEventListener('click', e => { if (!mq.matches) return; e.preventDefault(); set(!top.classList.contains('open')); });
  document.addEventListener('click', e => { if (top.classList.contains('open') && !top.contains(e.target)) set(false); });
  addEventListener('keydown', e => { if (e.key === 'Escape') set(false); });
  mq.addEventListener('change', () => set(false));
})();
