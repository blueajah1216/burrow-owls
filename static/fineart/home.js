(() => {
  const $ = s => document.querySelector(s);
  const wall = $('#wall'), status = $('#status'), empty = $('#empty');
  const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
  let D, favs = new Set(store.get('fa_favs', [])), st = { g: '', q: '', era: '', sort: 'fame', nudes: store.get('fa_nudes', false) };
  const STD = [250, 330, 500, 960, 1280, 1920, 3840];
  const W = (p, w) => w < p.w ? p.u.replace('/1280px-', `/${Math.max(...STD.filter(s => s <= w))}px-`) : (/\.(jpe?g|png)(\?|$)/i.test(p.u) && p.w <= 4000 && p.u.includes('/thumb/') ? p.u.replace('thumb.wikimedia.org/wikipedia/commons/thumb/', 'upload.wikimedia.org/wikipedia/commons/').replace(/\/[^/]+$/, '') : p.u);
  const esc = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

  fetch('/fineart/data.json').then(r => r.json()).then(d => {
    D = d;
    d.paintings.forEach(p => { const names = p.a.map(a => d.artists[a]?.n || '').join(' '); p._s = norm(`${p.t} ${names} ${p.y} ${d.genres[p.g].name} ${p.why} ${p.m}`); });
    readUrl(); hero(); rooms(); render();
  });

  function readUrl() {
    const u = new URLSearchParams(location.search);
    st.g = u.get('g') ?? ''; st.q = u.get('q') ?? ''; st.era = u.get('era') ?? ''; st.sort = u.get('sort') ?? 'fame';
    $('#q').value = st.q; $('#era').value = st.era; $('#sort').value = st.sort; $('#nudes').checked = st.nudes;
  }
  function writeUrl() {
    const u = new URLSearchParams();
    for (const k of ['g', 'q', 'era']) if (st[k]) u.set(k, st[k]);
    if (st.sort !== 'fame') u.set('sort', st.sort);
    history.replaceState(null, '', location.pathname + (u.toString() ? '?' + u : '') + location.hash);
  }
  function hero() {
    const pool = D.paintings.slice(0, 300).filter(p => !p.n);
    const p = pool[Math.floor(Date.now() / 864e5) % pool.length];
    $('#potd-img').src = W(p, 960); $('#potd-img').alt = p.t;
    $('#potd-title').textContent = p.t; $('#potd-by').textContent = `${D.artists[p.a[0]].n}, ${p.y}`;
    $('#potd').href = `/fineart/p/${p.id}`;
  }
  function rooms() {
    document.querySelectorAll('.room').forEach(el => {
      const g = +el.dataset.g, list = D.paintings.filter(p => p.g === g && !p.n);
      const cover = list[0]; if (cover) el.querySelector('.room-img').style.backgroundImage = `url(${W(cover, 500)})`;
      el.querySelector('.cnt').textContent = `${list.length} paintings`;
      el.onclick = () => { st.g = String(g); sync(); $('#browse').scrollIntoView(); };
    });
  }
  function match(p) {
    if (p.n && !st.nudes) return false;
    if (st.g === 'fav') { if (!favs.has(p.id)) return false; }
    else if (st.g !== '' && p.g !== +st.g) return false;
    if (st.era) { const [a, b] = st.era.split('-').map(Number); if (p.y < a || p.y > b) return false; }
    if (st.q) { const terms = norm(st.q).split(/\s+/).filter(Boolean); if (!terms.every(t => p._s.includes(t))) return false; }
    return true;
  }
  const sorters = { fame: (a, b) => a.r - b.r, old: (a, b) => a.y - b.y || a.r - b.r, new: (a, b) => b.y - a.y || a.r - b.r, az: (a, b) => a.t.localeCompare(b.t) };
  let shown = [], batch = 0; const STEP = 120;
  function render() {
    shown = D.paintings.filter(match).sort(sorters[st.sort]);
    wall.innerHTML = ''; batch = 0; more();
    const gname = st.g === 'fav' ? 'favorites' : st.g !== '' ? D.genres[+st.g].name.toLowerCase() : 'paintings';
    status.innerHTML = shown.length ? `Showing <b>${shown.length}</b> ${esc(gname)}${st.q ? ` matching “${esc(st.q)}”` : ''}` : '';
    empty.hidden = shown.length > 0;
    if (st.g === 'fav' && !shown.length) empty.innerHTML = 'No favorites yet — tap the ♡ on any painting to save it here.';
    document.querySelectorAll('.chip').forEach(c => c.classList.toggle('on', c.dataset.g === st.g));
    $('#favn').textContent = favs.size ? `(${favs.size})` : '';
  }
  function more() {
    const frag = document.createDocumentFragment();
    shown.slice(batch * STEP, (batch + 1) * STEP).forEach((p, i) => {
      const a = document.createElement('a'); a.className = 'card'; a.style.aspectRatio = `${p.w}/${p.h}`; a.style.animationDelay = `${Math.min(i, 20) * 25}ms`;
      a.href = `/fineart/p/${p.id}` + (st.g !== '' && st.g !== 'fav' ? `?g=${st.g}` : '');
      a.innerHTML = `<img loading="lazy" decoding="async" src="${W(p, 500)}" alt="${esc(p.t)}"><span class="cap"><b>${esc(p.t)}</b><i>${esc(D.artists[p.a[0]].n)} · ${p.y}</i></span><button class="heart${favs.has(p.id) ? ' on' : ''}" aria-label="Save">${favs.has(p.id) ? '♥' : '♡'}</button>`;
      a.querySelector('.heart').onclick = e => { e.preventDefault(); e.stopPropagation(); favs.has(p.id) ? favs.delete(p.id) : favs.add(p.id); store.set('fa_favs', [...favs]); const on = favs.has(p.id); e.currentTarget.classList.toggle('on', on); e.currentTarget.textContent = on ? '♥' : '♡'; $('#favn').textContent = favs.size ? `(${favs.size})` : ''; };
      frag.appendChild(a);
    });
    wall.appendChild(frag); batch++;
    sentinel();
  }
  let io;
  function sentinel() {
    io && io.disconnect();
    if (batch * STEP >= shown.length) return;
    const s = wall.lastElementChild; io = new IntersectionObserver(es => { if (es[0].isIntersecting) more(); }, { rootMargin: '1400px' }); io.observe(s);
  }
  function sync() { writeUrl(); render(); }
  $('#chips').addEventListener('click', e => { const c = e.target.closest('.chip'); if (!c) return; st.g = c.dataset.g; sync(); });
  let t; $('#q').addEventListener('input', e => { clearTimeout(t); t = setTimeout(() => { st.q = e.target.value.trim(); sync(); }, 160); });
  $('#era').onchange = e => { st.era = e.target.value; sync(); };
  $('#sort').onchange = e => { st.sort = e.target.value; sync(); };
  $('#nudes').onchange = e => { st.nudes = e.target.checked; store.set('fa_nudes', st.nudes); sync(); };
})();
