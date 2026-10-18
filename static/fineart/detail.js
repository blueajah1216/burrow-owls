(() => {
  const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
  const fav = document.getElementById('fav'), favs = new Set(store.get('fa_favs', []));
  const paint = () => { const on = favs.has(FA.id); fav.textContent = on ? '♥ Saved' : '♡ Save'; fav.classList.toggle('on', on); };
  fav.onclick = () => { favs.has(FA.id) ? favs.delete(FA.id) : favs.add(FA.id); store.set('fa_favs', [...favs]); paint(); }; paint();
  const lb = document.getElementById('lb'), li = document.getElementById('lb-img');
  const open = () => { li.src = FA.big; lb.hidden = false; document.body.style.overflow = 'hidden'; };
  const close = () => { lb.hidden = true; document.body.style.overflow = ''; };
  document.getElementById('zoom').onclick = open; document.getElementById('zoom2').onclick = open; lb.onclick = close;
  addEventListener('keydown', e => {
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowLeft' && FA.prev && lb.hidden) location.href = FA.prev;
    else if (e.key === 'ArrowRight' && FA.next && lb.hidden) location.href = FA.next;
  });
})();
