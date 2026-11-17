/* Progressive enhancement: the GET form and every reading page work without JS. */
(() => {
  const form = document.getElementById('history-filter');
  if (!form) return;
  const search = document.getElementById('history-search');
  const era = document.getElementById('era-filter');
  const sections = [...document.querySelectorAll('[data-era]')];
  const result = document.getElementById('result-count');
  const normalize = value => value.toLowerCase().normalize('NFKD').replace(/\p{M}/gu, '');
  const view = form.elements.view.value;
  function filter(updateURL = true) {
    const tokens = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
    let total = 0;
    for (const section of sections) {
      let count = 0;
      for (const item of section.querySelectorAll('[data-item]')) {
        item.hidden = (era.value !== 'all' && era.value !== section.dataset.era) ||
          !tokens.every(token => item.dataset.search.includes(token));
        if (!item.hidden) count++;
      }
      section.hidden = count === 0;
      section.querySelector('[data-era-count]').textContent = count;
      total += count;
    }
    result.textContent = `${total} ${view === 'composers' ? 'composers' : 'works'} on the timeline`;
    document.getElementById('empty-state').hidden = total !== 0;
    const url = new URL(location.href);
    if (search.value.trim()) url.searchParams.set('q', search.value.trim());
    else url.searchParams.delete('q');
    if (era.value !== 'all') url.searchParams.set('era', era.value);
    else url.searchParams.delete('era');
    if (updateURL) history.replaceState(null, '', url);
    // Switching views keeps the user's current search and era.
    for (const link of document.querySelectorAll('.view-tabs a')) {
      const target = new URL(link.href);
      for (const key of ['q', 'era']) {
        if (url.searchParams.has(key)) target.searchParams.set(key, url.searchParams.get(key));
        else target.searchParams.delete(key);
      }
      link.href = target.href;
    }
  }
  search.addEventListener('input', () => filter());
  era.addEventListener('change', () => filter());
  form.addEventListener('submit', event => {event.preventDefault(); filter();});
  document.getElementById('clear-filters').addEventListener('click', event => {
    event.preventDefault(); search.value = ''; era.value = 'all'; filter(); search.focus();
  });
  window.addEventListener('popstate', () => {
    const params = new URL(location.href).searchParams;
    search.value = params.get('q') || '';
    era.value = sections.some(s => s.dataset.era === params.get('era')) ? params.get('era') : 'all';
    filter(false);
  });
  document.body.classList.add('history-enhanced');
  filter(false);
})();
