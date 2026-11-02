(() => {
  const $ = s => document.querySelector(s), ALL = window.MEM.cards;
  const board = $('#board'), say = $('#say'), SIZES = [8, 12, 16, 24, 36, 42];
  const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
  const esc = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const mobile = () => matchMedia('(max-width:560px)').matches;
  const COLS = { 8: [4, 4], 12: [4, 3], 16: [4, 4], 24: [6, 4], 36: [6, 6], 42: [7, 6] };       // [desktop, mobile] columns
  const COLS_M = { 8: 4, 12: 3, 16: 4, 24: 4, 36: 6, 42: 6 };
  let n = SIZES.includes(store.get('mem_n', 16)) ? store.get('mem_n', 16) : 16;
  let tiles, open, locked, moves, left, t0, timer, found;

  const shuffle = a => { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  const fmt = s => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;


  function layout() {
    const cols = mobile() ? COLS_M[n] : COLS[n][0];
    board.style.setProperty('--cols', cols);
    board.style.setProperty('--maxw', mobile() ? '100%' : Math.min(1000, cols * 150) + 'px');
  }

  function start() {
    clearInterval(timer); timer = null;
    const pairs = shuffle(ALL.slice()).slice(0, n / 2);
    const deck = shuffle(pairs.flatMap(c => [{ c, k: c.id }, { c, k: c.id }]));
    board.innerHTML = ''; open = []; locked = false; moves = 0; left = n / 2; found = []; t0 = null;
    $('#moves').textContent = 0; $('#left').textContent = left; $('#time').textContent = '0:00';
    $('#found').hidden = true; $('#found-row').innerHTML = ''; $('#win').hidden = true;
    say.textContent = 'Pick a tile to begin.';
    document.querySelectorAll('#sizes .chip').forEach(b => b.classList.toggle('on', +b.dataset.n === n));
    layout();
    tiles = deck.map((d, i) => {
      const b = document.createElement('button'); b.type = 'button'; b.className = 'tile'; b.setAttribute('aria-label', `Tile ${i + 1}, face down`);
      b.innerHTML = `<span class="in"><span class="face back" aria-hidden="true">🎨</span><span class="face front"><img src="${d.c.img}" alt="${esc(d.c.t)}" decoding="async"></span></span>`;
      b.onclick = () => flip(b, d);
      board.appendChild(b); d.el = b; d.i = i; return d;
    });
    pairs.forEach(c => { const im = new Image(); im.src = c.img; });   // warm the cache so tiles don't pop in
  }

  function flip(el, d) {
    if (locked || el.classList.contains('up') || el.classList.contains('gone')) return;
    if (!t0) { t0 = Date.now(); timer = setInterval(() => $('#time').textContent = fmt(Math.floor((Date.now() - t0) / 1000)), 500); }
    el.classList.add('up'); el.setAttribute('aria-label', `Tile ${d.i + 1}: ${d.c.t}`);
    open.push(d);
    say.innerHTML = `<i>${esc(d.c.t)}</i> — ${esc(d.c.by)}, ${d.c.y}`;
    if (open.length < 2) return;
    moves++; $('#moves').textContent = moves; locked = true;
    const [a, b] = open;
    if (a.k === b.k) {
      setTimeout(() => {
        [a, b].forEach(x => { x.el.classList.add('gone'); x.el.disabled = true; setTimeout(() => x.el.classList.add('hide'), 460); });
        open = []; locked = false; left--; $('#left').textContent = left;
        found.push(a.c); addFound(a.c);
        say.innerHTML = `✅ A match! <i>${esc(a.c.t)}</i> by ${esc(a.c.by)}`;
        if (!left) win();
      }, 750);
    } else {
      setTimeout(() => { [a, b].forEach(x => { x.el.classList.remove('up'); x.el.setAttribute('aria-label', `Tile ${x.i + 1}, face down`); }); open = []; locked = false; say.textContent = 'Not a match. Try again!'; }, 1100);
    }
  }

  function addFound(c) {
    $('#found').hidden = false;
    const a = document.createElement('a'); a.href = c.url; a.target = '_blank'; a.rel = 'noopener';
    a.innerHTML = `<img src="${c.img}" alt=""><span>${esc(c.t)}</span>`; $('#found-row').appendChild(a);
  }

  function win() {
    clearInterval(timer); const secs = Math.floor((Date.now() - t0) / 1000);
    const bestKey = 'mem_best_' + n, best = store.get(bestKey, null), isBest = !best || moves < best.moves || (moves === best.moves && secs < best.secs);
    if (isBest) store.set(bestKey, { moves, secs });
    $('#win-text').textContent = `You matched all ${n / 2} pairs in ${moves} turns and ${fmt(secs)}.`;
    $('#win-best').textContent = isBest ? '🏆 New best for this board size!' : `Your best for ${n} tiles: ${best.moves} turns (${fmt(best.secs)})`;
    setTimeout(() => { $('#win').hidden = false; $('#again').focus(); }, 500);
    say.textContent = 'Board cleared!';
  }

  $('#sizes').addEventListener('click', e => { const b = e.target.closest('.chip'); if (!b) return; n = +b.dataset.n; store.set('mem_n', n); start(); });
  $('#restart').onclick = start; $('#again').onclick = start; $('#close-win').onclick = () => { $('#win').hidden = true; };
  addEventListener('resize', layout);
  start();
})();
