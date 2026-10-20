(() => {
  const svg = document.getElementById('svg'), tip = document.getElementById('tip'), box = document.getElementById('map');
  const NS = 'http://www.w3.org/2000/svg', ms = window.FA_MUSEUMS || [];
  // lon/lat bounds per continent: [west, south, east, north]
  const REG = {
    '': [-180, -58, 180, 84], 'North America': [-170, 5, -50, 72], 'South America': [-85, -57, -32, 14],
    'Europe': [-12, 34, 42, 66], 'Asia': [32, -10, 150, 60], 'Africa': [-20, -37, 55, 38], 'Oceania': [110, -48, 180, -8],
  };
  let W, H, K, TOP, vb, anim, cur = '', cont, pins = [];
  const px = (lon, lat) => [(lon + 180) * K, (TOP - lat) * K];
  function setVB(v) { vb = v; svg.setAttribute('viewBox', v.map(n => n.toFixed(1)).join(' ')); scalePins(); }
  function boxFor(r) {
    const [x1, y1] = px(r[0], r[3]), [x2, y2] = px(r[2], r[1]);
    const ar = box.clientWidth / box.clientHeight; let w = x2 - x1, h = y2 - y1;
    if (w / h < ar) { const nw = h * ar; return [x1 - (nw - w) / 2, y1, nw, h]; }
    const nh = w / ar; return [x1, y1 - (nh - h) / 2, w, nh];
  }
  function fly(to) {
    cancelAnimationFrame(anim); const from = vb.slice(), t0 = performance.now(), D = 600;
    const ease = t => t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
    const step = now => { const t = Math.min(1, (now - t0) / D), e = ease(t); setVB(from.map((v, i) => v + (to[i] - v) * e)); if (t < 1) anim = requestAnimationFrame(step); };
    anim = requestAnimationFrame(step);
  }
  function scalePins() {
    const s = vb[2] / box.clientWidth; // svg units per css px
    pins.forEach(p => { p.setAttribute('r', (6 * s).toFixed(2)); p.setAttribute('stroke-width', (1.5 * s).toFixed(2)); });
  }
  function clamp(v) {
    const full = boxFor(REG['']);
    if (v[2] >= full[2]) return full.slice();
    v[0] = Math.max(0, Math.min(W - v[2], v[0])); v[1] = Math.max(0, Math.min(H - v[3], v[1])); return v;
  }
  function zoomAt(f, cx, cy) {
    const w = vb[2] * f, h = vb[3] * f;
    setVB(clamp([vb[0] + (vb[2] - w) * cx, vb[1] + (vb[3] - h) * cy, w, h]));
  }
  function showTip(m, p) {
    const r = box.getBoundingClientRect(), b = p.getBoundingClientRect();
    tip.hidden = false;
    tip.innerHTML = `<b>${m.name}</b><span>${m.city}, ${m.country}</span><a href="/fineart/museum/${m.slug}">Visit museum →</a>`;
    let x = b.left - r.left + b.width / 2, y = b.top - r.top;
    x = Math.max(110, Math.min(r.width - 110, x));
    tip.style.left = x + 'px'; tip.style.top = y + 'px';
  }
  fetch('/static/fineart/world.json').then(r => r.json()).then(w => {
    W = w.w; H = w.h; K = w.k; TOP = w.top;
    const land = document.createElementNS(NS, 'path'); land.setAttribute('d', w.d); land.setAttribute('class', 'land'); svg.appendChild(land);
    ms.forEach(m => {
      const [x, y] = px(m.lon, m.lat), c = document.createElementNS(NS, 'circle');
      c.setAttribute('cx', x.toFixed(1)); c.setAttribute('cy', y.toFixed(1)); c.setAttribute('class', 'pin');
      c.setAttribute('tabindex', 0); c.setAttribute('role', 'link'); c.setAttribute('aria-label', m.name + ', ' + m.city);
      c.addEventListener('click', e => { e.stopPropagation(); showTip(m, c); });
      c.addEventListener('keydown', e => { if (e.key === 'Enter') location.href = '/fineart/museum/' + m.slug; });
      c.addEventListener('mouseenter', () => showTip(m, c));
      c._m = m; svg.appendChild(c); pins.push(c);
    });
    setVB(boxFor(REG['']));
    const q = location.hash.slice(1).replace(/_/g, ' ');
    const b = [...document.querySelectorAll('#conts button')].find(b => b.dataset.c === q); if (b) { b._first = true; b.click(); }
  });
  svg.addEventListener('click', () => { tip.hidden = true; });
  document.querySelectorAll('#conts button').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('#conts button').forEach(x => x.classList.toggle('on', x === b));
    cur = b.dataset.c; tip.hidden = true; if (vb) (b._first ? setVB : fly)(boxFor(REG[cur]));
    document.querySelectorAll('.m-group').forEach(g => { g.hidden = !!cur && g.dataset.c !== cur; });
    history.replaceState(null, '', cur ? '#' + cur.replace(/ /g, '_') : location.pathname);
  }));
  document.getElementById('zin').onclick = () => zoomAt(.6, .5, .5);
  document.getElementById('zout').onclick = () => zoomAt(1 / .6, .5, .5);
  box.addEventListener('wheel', e => {
    e.preventDefault(); const r = box.getBoundingClientRect();
    zoomAt(e.deltaY < 0 ? .8 : 1.25, (e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height);
  }, { passive: false });
  // drag to pan
  let drag = null;
  svg.addEventListener('pointerdown', e => { drag = { x: e.clientX, y: e.clientY, vb: vb.slice(), moved: false }; });
  window.addEventListener('pointermove', e => {
    if (!drag) return; const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    if (Math.abs(dx) + Math.abs(dy) > 4) drag.moved = true; if (!drag.moved) return;
    const s = drag.vb[2] / box.clientWidth; tip.hidden = true;
    setVB(clamp([drag.vb[0] - dx * s, drag.vb[1] - dy * s, drag.vb[2], drag.vb[3]]));
  });
  window.addEventListener('pointerup', () => { drag = null; });
  window.addEventListener('resize', () => { if (vb) setVB(boxFor(REG[cur])); });
  // search filters the list and dims pins
  document.getElementById('msearch').addEventListener('input', e => {
    const q = e.target.value.trim().toLowerCase();
    document.querySelectorAll('.m-card').forEach(c => { c.hidden = !!q && !c.dataset.s.includes(q); });
    document.querySelectorAll('.m-group').forEach(g => { g.hidden = !![...g.querySelectorAll('.m-card')].every(c => c.hidden) || (!!cur && !q && g.dataset.c !== cur); });
    pins.forEach(p => p.classList.toggle('dim', !!q && !`${p._m.name} ${p._m.city} ${p._m.country}`.toLowerCase().includes(q)));
  });
})();
