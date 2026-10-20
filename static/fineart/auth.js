// Favorites sync for signed-in visitors. Logged-out visitors keep using localStorage only.
(() => {
  const KEY = 'fa_favs';
  const read = () => { try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch (e) { return []; } };
  const write = ids => { try { localStorage.setItem(KEY, JSON.stringify(ids)); } catch (e) {} };
  const post = body => fetch('/fineart/api/favorites', {
    method: 'POST', credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': window.FA_CSRF || '' },
    body: JSON.stringify(body),
  }).then(r => r.ok ? r.json() : Promise.reject(r.status));

  // Called by the page scripts whenever a heart is toggled.
  window.faSync = (id, on) => {
    if (!window.FA_USER) return;
    post(on ? { add: [id] } : { remove: [id] }).catch(() => {});
  };

  if (!window.FA_USER) return;
  // On every page load: merge this device's favorites into the account (union), then
  // adopt the account's list locally and tell the page to repaint.
  const local = read();
  post({ add: local }).then(({ ids }) => {
    const same = ids.length === local.length && ids.every(i => local.includes(i));
    if (!same) { write(ids); dispatchEvent(new Event('fa-favs')); }
  }).catch(() => {});
})();
