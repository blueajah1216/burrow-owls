(() => {
  const $ = s => document.querySelector(s);
  const NS = 'http://www.w3.org/2000/svg';
  const mk = (tag, attrs, parent) => { const el = document.createElementNS(NS, tag); for (const k in attrs) el.setAttribute(k, attrs[k]); parent && parent.appendChild(el); return el; };

  // ---- event page: jump menu + mature toggle
  const jump = $('#jump');
  if (jump) jump.onchange = () => { location.href = jump.value; };
  const mature = $('#mature');
  if (mature) {
    let on = false; try { on = JSON.parse(localStorage.getItem('fa_nudes')) === true; } catch (e) {}
    const apply = () => {
      document.querySelectorAll('.hcard.mature').forEach(c => { c.hidden = !mature.checked; });
      try { localStorage.setItem('fa_nudes', JSON.stringify(mature.checked)); } catch (e) {}
    };
    mature.checked = on; apply(); mature.onchange = apply;
  }

  // ---- timeline: draw the tree (trunk, branches, leaves) behind the nodes
  const tree = $('#tree'), svg = tree && tree.querySelector('svg.trunk');
  if (!svg) return;
  const rnd = (() => { let s = 7; return () => (s = (s * 16807) % 2147483647) / 2147483647; })();

  function draw() {
    svg.innerHTML = '';
    const W = tree.clientWidth, H = tree.scrollHeight, T = tree.getBoundingClientRect();
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`); svg.setAttribute('width', W); svg.setAttribute('height', H);
    const narrow = W < 760, tx = narrow ? 30 : W / 2;
    const wob = y => Math.sin(y / 170) * (narrow ? 5 : 11);
    const defs = mk('defs', {}, svg);
    const g1 = mk('linearGradient', { id: 'bark', x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
    [['0', '#c98b4a'], ['.5', '#9c6a3a'], ['1', '#e9c46a']].forEach(([o, c]) => mk('stop', { offset: o, 'stop-color': c }, g1));
    const start = tree.querySelector('.t-start').getBoundingClientRect(), end = tree.querySelector('.t-end').getBoundingClientRect();
    const y0 = start.top - T.top + start.height / 2, y1 = end.top - T.top + end.height / 2;

    // trunk (smooth path)
    const pts = []; for (let y = y0; y <= y1; y += 60) pts.push([tx + wob(y), y]); pts.push([tx + wob(y1), y1]);
    let d = `M${pts[0][0]},${pts[0][1]}`;
    for (let i = 1; i < pts.length; i++) { const [px, py] = pts[i - 1], [cx, cy] = pts[i], my = (py + cy) / 2; d += ` C${px},${my} ${cx},${my} ${cx},${cy}`; }
    mk('path', { d, fill: 'none', stroke: 'rgba(0,0,0,.25)', 'stroke-width': narrow ? 14 : 22, 'stroke-linecap': 'round', transform: 'translate(3,3)' }, svg);
    mk('path', { d, fill: 'none', stroke: 'url(#bark)', 'stroke-width': narrow ? 12 : 20, 'stroke-linecap': 'round' }, svg);
    mk('path', { d, fill: 'none', stroke: 'rgba(255,240,200,.35)', 'stroke-width': narrow ? 3 : 5, 'stroke-linecap': 'round', transform: 'translate(-3,0)' }, svg);

    // roots at the top
    for (let i = 0; i < 5; i++) {
      const dir = i % 2 ? 1 : -1, len = 70 + i * 22, sx = tx + wob(y0);
      mk('path', { d: `M${sx},${y0 + 6} C${sx + dir * 14},${y0 - 24} ${sx + dir * len * .6},${y0 - 18 - i * 5} ${sx + dir * len},${y0 - 52 - i * 9}`, fill: 'none', stroke: '#9c6a3a', 'stroke-width': 7 - i, 'stroke-linecap': 'round', opacity: .85 }, svg);
    }

    // branches + leaves
    tree.querySelectorAll('.node').forEach(n => {
      const o = n.querySelector('.orb').getBoundingClientRect(), era = getComputedStyle(n.closest('.era')).getPropertyValue('--c').trim() || '#f4c95d';
      const cy = o.top - T.top + o.height / 2, ox = narrow ? o.left - T.left : (n.classList.contains('l') ? o.right - T.left : o.left - T.left);
      const sx = tx + wob(cy), dir = ox > sx ? 1 : -1, sy = cy + 36;
      const bd = `M${sx},${sy} C${sx + dir * 40},${sy + 6} ${ox - dir * 50},${cy + 2} ${ox},${cy}`;
      mk('path', { d: bd, fill: 'none', stroke: '#9c6a3a', 'stroke-width': narrow ? 5 : 7, 'stroke-linecap': 'round' }, svg);
      mk('path', { d: bd, fill: 'none', stroke: 'rgba(255,240,200,.3)', 'stroke-width': 2, 'stroke-linecap': 'round', transform: 'translate(0,-1.5)' }, svg);
      for (let k = 0; k < 3; k++) {
        const t = .25 + k * .25, lx = sx + (ox - sx) * t, ly = sy + (cy - sy) * t, side = k % 2 ? 1 : -1;
        mk('ellipse', { cx: lx, cy: ly + side * 9, rx: 9, ry: 4.5, fill: era, opacity: .75, transform: `rotate(${dir * side * 35 + rnd() * 20} ${lx} ${ly + side * 9})` }, svg);
      }
    });

    // era "boughs": little knots on the trunk
    tree.querySelectorAll('.era-head').forEach(h => {
      const b = h.getBoundingClientRect(), cy = b.top - T.top + b.height / 2;
      mk('circle', { cx: tx + wob(cy), cy, r: narrow ? 11 : 17, fill: getComputedStyle(h.closest('.era')).getPropertyValue('--c').trim(), stroke: '#fff6e2', 'stroke-width': 3 }, svg);
    });

    // crown at the end
    for (let i = 0; i < 7; i++) {
      const dir = i % 2 ? 1 : -1, a = (i + 1) * 14, ex = tx + wob(y1) + dir * (30 + a), ey = y1 + 40 + (i % 3) * 14;
      mk('path', { d: `M${tx + wob(y1)},${y1} Q${tx + wob(y1) + dir * a * .3},${y1 + 26} ${ex},${ey}`, fill: 'none', stroke: '#9c6a3a', 'stroke-width': 4, 'stroke-linecap': 'round' }, svg);
      mk('ellipse', { cx: ex, cy: ey + 4, rx: 10, ry: 5, fill: ['#7ee0a5', '#f4c95d', '#ff8fa3'][i % 3], opacity: .85, transform: `rotate(${dir * 30} ${ex} ${ey})` }, svg);
    }
  }

  let t; const redraw = () => { clearTimeout(t); t = setTimeout(draw, 80); };
  addEventListener('resize', redraw); addEventListener('load', draw);
  tree.querySelectorAll('img').forEach(i => i.addEventListener('load', redraw));
  draw();
})();
