(() => {
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
