(() => {
  const $ = s => document.querySelector(s), ALL = window.G.cards, SLIDE = window.G.mode === 'slide', KEY = SLIDE ? 'slide' : 'jig';
  const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
  const esc = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const fmt = s => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
  const SIZES = SLIDE ? [3, 4, 5] : [3, 4, 5, 6], pz = $('#pz');
  let n = SIZES.includes(store.get(KEY + '_n', 4)) ? store.get(KEY + '_n', 4) : (SLIDE ? 3 : 4);
  let art, order, sel, moves, t0, timer, done, hole, lastId;

  const pick = () => { let c; do { c = ALL[Math.floor(Math.random() * ALL.length)]; } while (c.id === lastId && ALL.length > 1); lastId = c.id; return c; };
  function stats() { $('#moves').textContent = moves; }
  function clock() { if (!t0) { t0 = Date.now(); timer = setInterval(() => $('#time').textContent = fmt(Math.floor((Date.now() - t0) / 1000)), 500); } }
  function paint() {
    pz.innerHTML = '';
    order.forEach((piece, pos) => {
      const el = document.createElement('div'); el.className = 'pc'; el.dataset.pos = pos; el.draggable = !SLIDE; el.tabIndex = 0;
      if (SLIDE && piece === hole) el.classList.add('hole');
      const cx = piece % n, cy = Math.floor(piece / n);
      el.style.backgroundImage = `url(${art.img})`; el.style.backgroundSize = `${n * 100}% ${n * 100}%`; el.style.backgroundPosition = `${n > 1 ? cx / (n - 1) * 100 : 0}% ${n > 1 ? cy / (n - 1) * 100 : 0}%`;
      if (!SLIDE && piece === pos) el.classList.add('ok');
      if (sel === pos) el.classList.add('sel');
      pz.appendChild(el);
    });
  }
  function start() {
    clearInterval(timer); t0 = null; moves = 0; done = false; sel = null; art = pick(); $('#time').textContent = '0:00'; stats(); $('#win').hidden = true; $('#say').textContent = '';
    document.querySelectorAll('#sizes .chip').forEach(b => b.classList.toggle('on', +b.dataset.n === n));
    pz.style.setProperty('--n', n); pz.style.aspectRatio = `${art.w} / ${art.h}`; $('#peekimg').src = art.img;
    pz.style.maxWidth = Math.min(900, Math.max(280, (innerHeight - 280) * art.w / art.h)) + 'px'; $('#peekimg').style.maxWidth = pz.style.maxWidth;
    order = [...Array(n * n).keys()]; hole = n * n - 1;
    if (SLIDE) { let h = hole, prev = -1; for (let k = 0; k < n * n * 40; k++) { const nb = neigh(h).filter(x => x !== prev); const m = nb[Math.floor(Math.random() * nb.length)]; [order[h], order[m]] = [order[m], order[h]]; prev = h; h = m; } }
    else { do { for (let i = order.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [order[i], order[j]] = [order[j], order[i]]; } } while (order.every((p, i) => p === i)); }
    paint(); $('#say').innerHTML = `<i>A famous painting</i> is hiding here. Can you put it back together?`;
  }
  const neigh = pos => { const r = Math.floor(pos / n), c = pos % n, o = []; if (r) o.push(pos - n); if (r < n - 1) o.push(pos + n); if (c) o.push(pos - 1); if (c < n - 1) o.push(pos + 1); return o; };
  const holePos = () => order.indexOf(hole);
  function slideTo(pos) {
    if (done) return; const h = holePos(); if (!neigh(h).includes(pos)) return;
    clock(); [order[h], order[pos]] = [order[pos], order[h]]; moves++; stats(); paint(); check();
  }
  function swap(a, b) { if (done || a === b) return; clock(); [order[a], order[b]] = [order[b], order[a]]; moves++; sel = null; stats(); paint(); check(); }
  function check() { if (order.every((p, i) => p === i)) win(); }
  function win() {
    done = true; clearInterval(timer); const secs = Math.floor((Date.now() - t0) / 1000);
    pz.classList.add('solved'); paint(); document.querySelectorAll('.pc').forEach(e => e.classList.remove('hole', 'ok'));
    const key = `${KEY}_best_${n}`, best = store.get(key, null), isBest = !best || moves < best.moves; if (isBest) store.set(key, { moves, secs });
    $('#win-text').innerHTML = `<i>${esc(art.t)}</i> by ${esc(art.by)}, ${art.y}.<br>${moves} moves in ${fmt(secs)}.`;
    $('#win-best').textContent = isBest ? '🏆 New best for this size!' : `Your best for this size: ${best.moves} moves`;
    $('#say').innerHTML = `<a href="${art.url}" target="_blank" rel="noopener"><i>${esc(art.t)}</i></a> — ${esc(art.by)}, ${art.y}`;
    setTimeout(() => { $('#win').hidden = false; $('#again').focus(); }, 700);
  }
  pz.addEventListener('click', e => {
    const el = e.target.closest('.pc'); if (!el) return; const pos = +el.dataset.pos;
    if (SLIDE) return slideTo(pos);
    if (done) return; if (sel === null) { sel = pos; paint(); } else if (sel === pos) { sel = null; paint(); } else swap(sel, pos);
  });
  if (!SLIDE) {
    let from = null;
    pz.addEventListener('dragstart', e => { const el = e.target.closest('.pc'); if (!el || done) return e.preventDefault(); from = +el.dataset.pos; e.dataTransfer.effectAllowed = 'move'; e.dataTransfer.setData('text/plain', String(from)); });
    pz.addEventListener('dragover', e => { if (from !== null) e.preventDefault(); });
    pz.addEventListener('drop', e => { e.preventDefault(); const el = e.target.closest('.pc'); if (el && from !== null) swap(from, +el.dataset.pos); from = null; });
  }
  pz.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); e.target.click(); } });
  addEventListener('keydown', e => {
    if (!SLIDE || done) return; const d = { ArrowUp: n, ArrowDown: -n, ArrowLeft: 1, ArrowRight: -1 }[e.key]; if (!d) return;
    e.preventDefault(); const h = holePos(), t = h + d; if (t < 0 || t >= n * n || (Math.abs(d) === 1 && Math.floor(t / n) !== Math.floor(h / n))) return; slideTo(t);
  });
  const peek = on => { $('#peekimg').hidden = !on; pz.style.visibility = on ? 'hidden' : ''; };
  $('#peek').addEventListener('pointerdown', () => peek(true)); ['pointerup', 'pointerleave', 'pointercancel'].forEach(ev => $('#peek').addEventListener(ev, () => peek(false)));
  $('#peek').addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { peek(true); setTimeout(() => peek(false), 1500); } });
  $('#sizes').addEventListener('click', e => { const b = e.target.closest('.chip'); if (!b) return; n = +b.dataset.n; store.set(KEY + '_n', n); start(); });
  $('#restart').onclick = start; $('#again').onclick = start; $('#close-win').onclick = () => { $('#win').hidden = true; };
  start();
})();
