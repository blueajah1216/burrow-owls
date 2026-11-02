(() => {
  const $ = s => document.querySelector(s), ALL = window.G.cards.filter(c => c.y);
  const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
  const esc = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  let streak, best = store.get('older_best', 0), cur, used, locked;
  const era = y => y < 1500 ? 'Renaissance and earlier' : y < 1700 ? '1500s–1600s' : y < 1800 ? '1700s' : y < 1900 ? '1800s' : '1900s+';
  function start() { streak = 0; used = new Set(); $('#streak').textContent = 0; $('#best').textContent = best; $('#win').hidden = true; next(); }
  function next() {
    locked = false; $('#o-next').hidden = true; $('#o-say').textContent = 'Which one was painted first?';
    let a, b, tries = 0;
    do { a = ALL[Math.floor(Math.random() * ALL.length)]; b = ALL[Math.floor(Math.random() * ALL.length)]; tries++; }
    while ((a === b || Math.abs(a.y - b.y) < (tries < 200 ? 15 : 1) || used.has(a.id) || used.has(b.id)) && tries < 400);
    if (tries >= 400) used.clear();
    used.add(a.id); used.add(b.id); cur = [a, b];
    $('#pair').innerHTML = cur.map((c, k) => `<button type="button" class="o-card" data-k="${k}"><img src="${c.img}" alt="${esc(c.t)}"><span class="o-info"><b>${esc(c.t)}</b><small>${esc(c.by)}</small><em class="o-year" hidden>${c.y}</em></span></button>`).join('');
    document.querySelectorAll('.o-card').forEach(el => el.onclick = () => pick(+el.dataset.k, el));
  }
  function pick(k, el) {
    if (locked) return; locked = true;
    const older = cur[0].y <= cur[1].y ? 0 : 1, ok = k === older;
    document.querySelectorAll('.o-card').forEach((x, j) => { x.querySelector('.o-year').hidden = false; x.disabled = true; x.classList.add(j === older ? 'right' : 'wrong'); });
    if (ok) { streak++; $('#streak').textContent = streak; if (streak > best) { best = streak; store.set('older_best', best); $('#best').textContent = best; } $('#o-say').textContent = `✅ Right! ${cur[older].y} came before ${cur[1 - older].y}.`; const n = $('#o-next'); n.hidden = false; n.focus(); }
    else { $('#o-say').textContent = `❌ Not this time. ${cur[older].y} came before ${cur[1 - older].y}.`; setTimeout(() => { $('#win-text').textContent = `Your streak: ${streak}.`; $('#win-best').textContent = streak && streak >= best ? '⭐ A new best streak!' : `Your best streak: ${best}`; $('#win').hidden = false; $('#again').focus(); }, 1600); }
  }
  $('#o-next').onclick = next; $('#again').onclick = start; start();
})();
