(() => {
  const $ = s => document.querySelector(s), ALL = window.G.cards, ROUNDS = 10;
  const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
  const esc = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const shuffle = a => { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  let mode = store.get('quiz_mode', 'by') === 't' ? 't' : 'by', deck, i, score, locked;
  const short = s => s.replace(/\s*\(.*?\)\s*$/, '');
  function start() {
    deck = shuffle(ALL.slice()).slice(0, ROUNDS); i = 0; score = 0; $('#score').textContent = 0; $('#win').hidden = true;
    document.querySelectorAll('#modes .chip').forEach(b => b.classList.toggle('on', b.dataset.m === mode)); ask();
  }
  function options(c) {
    const seen = new Set([c[mode]]), out = [c];
    for (const d of shuffle(ALL.slice())) {
      const v = d[mode]; if (seen.has(v) || (mode === 't' && short(v).toLowerCase() === short(c.t).toLowerCase())) continue;
      if (mode === 'by' && d.by === c.by) continue; seen.add(v); out.push(d); if (out.length === 4) break;
    }
    return shuffle(out);
  }
  function ask() {
    locked = false; const c = deck[i]; $('#qn').textContent = i + 1; $('#q-img').src = c.img; $('#q-say').innerHTML = ''; $('#q-next').hidden = true;
    $('#q-ask').textContent = mode === 'by' ? 'Who painted this?' : 'What is this painting called?';
    const box = $('#q-opts'); box.innerHTML = '';
    options(c).forEach(o => { const b = document.createElement('button'); b.type = 'button'; b.className = 'q-opt'; b.textContent = mode === 'by' ? o.by : short(o.t); b.onclick = () => pick(b, o === c || o[mode] === c[mode]); b.dataset.right = o === c ? '1' : ''; box.appendChild(b); });
  }
  function pick(b, ok) {
    if (locked) return; locked = true; const c = deck[i];
    document.querySelectorAll('.q-opt').forEach(x => { x.disabled = true; if (x.dataset.right) x.classList.add('right'); });
    if (ok) { score++; $('#score').textContent = score; } else b.classList.add('wrong');
    $('#q-say').innerHTML = `${ok ? '✅ Yes!' : '❌ Not quite.'} <a href="${c.url}" target="_blank" rel="noopener"><i>${esc(c.t)}</i></a> by ${esc(c.by)}, ${c.y}.`;
    const nx = $('#q-next'); nx.hidden = false; nx.textContent = i + 1 === ROUNDS ? 'See my score' : 'Next →'; nx.focus();
  }
  $('#q-next').onclick = () => { if (++i < ROUNDS) ask(); else end(); };
  function end() {
    const key = 'quiz_best_' + mode, best = store.get(key, 0), isBest = score > best; if (isBest) store.set(key, score);
    $('#win-h').textContent = score >= 9 ? '🏆 Art expert!' : score >= 6 ? '🎉 Nice work!' : '🖌️ Good try!';
    $('#win-text').textContent = `You got ${score} out of ${ROUNDS}.`;
    $('#win-best').textContent = isBest ? '⭐ New best score!' : `Your best: ${best} out of ${ROUNDS}`; $('#win').hidden = false; $('#again').focus();
  }
  $('#modes').addEventListener('click', e => { const b = e.target.closest('.chip'); if (!b) return; mode = b.dataset.m; store.set('quiz_mode', mode); start(); });
  $('#again').onclick = start; start();
})();
