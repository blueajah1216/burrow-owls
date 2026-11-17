/* Shared account favorites. Browser-only picks remain useful before sign-up. */
(() => {
  'use strict';
  const node = document.getElementById('gallery-config');
  if (!node) return;
  const config = JSON.parse(node.textContent);
  const keys = {painting:'fa_favs', photo:'ph_favs', music:'mu_favs'};
  const kinds = Object.keys(keys);
  const ownerKey = 'gg_favorites_owner';
  const pendingKey = 'gg_pending_import';
  const read = (key, fallback) => {try {return JSON.parse(localStorage.getItem(key)) ?? fallback;} catch (_) {return fallback;}};
  const write = (key, value) => {try {localStorage.setItem(key, JSON.stringify(value));} catch (_) {}};
  const remove = key => {try {localStorage.removeItem(key);} catch (_) {}};
  const empty = () => Object.fromEntries(kinds.map(k => [k, []]));
  const clean = ids => Object.fromEntries(kinds.map(k => [k, [...new Set(
    (Array.isArray(ids?.[k]) ? ids[k] : []).filter(id => typeof id === 'string' && id.length <= 120))]]));
  const local = () => clean(Object.fromEntries(kinds.map(k => [k, read(keys[k], [])])));
  const count = ids => kinds.reduce((n,k) => n + ids[k].length, 0);
  let ids = empty(), toastTimer, queue = Promise.resolve();
  const userId = config.userId === null ? null : String(config.userId);
  const canonicalNext = () => location.pathname + location.search + location.hash;
  const authURL = endpoint => {
    const url = new URL(config[endpoint], location.origin);
    url.searchParams.set('next', canonicalNext());
    return url.href;
  };

  function notify(message, action, href, retry) {
    let toast = document.getElementById('gallery-toast');
    if (!toast) {
      toast = document.createElement('div'); toast.id = 'gallery-toast';
      toast.setAttribute('role','status'); toast.setAttribute('aria-live','polite'); document.body.append(toast);
    }
    toast.replaceChildren();
    const text = document.createElement('span'); text.textContent = message; toast.append(text);
    if (href) {const link = document.createElement('a'); link.textContent = action; link.href = href; toast.append(link);}
    if (retry) {const button = document.createElement('button'); button.type='button'; button.textContent='Try again'; button.onclick=retry; toast.append(button);}
    toast.hidden = false; clearTimeout(toastTimer);
    if (!retry) toastTimer = setTimeout(() => {if (!toast.contains(document.activeElement)) toast.hidden=true;}, 9000);
  }

  async function request(body) {
    const response = await fetch(config.api, {
      method:body ? 'POST' : 'GET', credentials:'same-origin', cache:'no-store',
      headers:body ? {'Content-Type':'application/json','X-CSRF-Token':config.csrf} : {},
      ...(body ? {body:JSON.stringify(body)} : {}),
    });
    if (!response.ok) {
      const error = new Error(response.status === 401 ? 'Please log in again to keep saving.' : 'Your change could not be saved. Please try again.');
      error.status = response.status; throw error;
    }
    return response.json();
  }

  function adopt(next, reason='sync') {
    const previous = JSON.stringify(ids);
    ids = clean(next);
    for (const kind of kinds) write(keys[kind], ids[kind]);
    write(ownerKey, userId || 'guest');
    paint();
    for (const kind of ['painting','photo']) dispatchEvent(new Event(kind === 'painting' ? 'fa-favs' : 'ph-favs'));
    dispatchEvent(new CustomEvent('gallery-changed',{detail:{ids, reason}}));
    if (previous !== JSON.stringify(ids) && document.querySelector('[data-personal-gallery]') && ['mutation','import'].includes(reason)) {
      location.reload();
    }
  }

  function paint() {
    for (const button of document.querySelectorAll('[data-gallery-kind][data-gallery-id]')) {
      const on = (ids[button.dataset.galleryKind] || []).includes(button.dataset.galleryId);
      button.classList.toggle('is-saved', on); button.classList.toggle('on', on);
      button.setAttribute('aria-pressed', String(on));
      const label = button.classList.contains('heart') ? (on ? '♥' : '♡') :
        (on ? button.dataset.removeLabel || '♥ In your gallery' : '♡ Add to my gallery');
      if (button.textContent !== label) button.textContent = label;
      if (button.classList.contains('heart')) button.setAttribute('aria-label', on ? 'Remove from my gallery' : 'Add to my gallery');
      const action = button.form?.querySelector('[name="action"]');
      if (action) action.value = on ? 'remove' : 'add';
    }
    for (const badge of document.querySelectorAll('[data-gallery-total]')) {
      if (badge.textContent !== String(count(ids))) badge.textContent = count(ids);
    }
    const pending = read(pendingKey, null);
    for (const panel of document.querySelectorAll('[data-gallery-import]')) {
      panel.hidden = !pending || pending.userId !== userId || !count(clean(pending.ids));
      if (!panel.hidden) {
        const badge = panel.querySelector('[data-import-count]'), total = String(count(clean(pending.ids)));
        if (badge.textContent !== total) badge.textContent = total;
      }
    }
  }

  function errorNotice(error, retry) {
    notify(error.message || 'Your change could not be saved.', error.status === 401 ? 'Log in' : null,
      error.status === 401 ? authURL('login') : null, error.status === 401 ? null : retry);
  }

  async function importPending() {
    const pending = read(pendingKey, null);
    if (!userId || pending?.userId !== userId) return;
    const response = await request({add:clean(pending.ids)});
    remove(pendingKey); adopt(response.ids, 'import'); paint();
  }

  async function initialize() {
    const owner = read(ownerKey, null);
    const browserIds = local();
    if (!userId) {
      // A signed-out or expired session must not expose another account's cache.
      if (owner && owner !== 'guest') {for (const key of Object.values(keys)) remove(key); remove(ownerKey); remove(pendingKey);}
      ids = owner && owner !== 'guest' ? empty() : browserIds;
      paint(); return;
    }
    if (owner !== userId && owner && owner !== 'guest') remove(pendingKey);
    if ((!owner || owner === 'guest') && count(browserIds)) {
      write(pendingKey, {userId, ids:browserIds});
    }
    adopt(config.ids);
    if (owner === 'guest' && count(browserIds)) {
      try {await importPending();} catch (error) {errorNotice(error, () => importPending().catch(e => errorNotice(e)));}
    } else if (!owner && count(browserIds) && !document.querySelector('[data-gallery-import]')) {
      notify('Bring your browser favorites into your account.', 'Open my gallery', config.gallery);
    }
  }
  const ready = initialize();

  async function change(kind, id, desired) {
    if (!kinds.includes(kind)) return;
    const on = desired === undefined ? !ids[kind].includes(id) : desired;
    if (userId) {
      const response = await request({[on ? 'add' : 'remove']:{[kind]:[id]}});
      if (response.ids[kind].includes(id) !== on) throw new Error('This item could not be saved. Please refresh and try again.');
      adopt(response.ids, 'mutation');
      notify(on ? 'Added to your gallery.' : 'Removed from your gallery.', 'View my gallery', config.gallery);
    } else {
      const next = clean(ids);
      next[kind] = on ? [...new Set([...next[kind],id])] : next[kind].filter(value => value !== id);
      adopt(next, 'mutation');
      notify(on ? 'Saved on this device. Keep it in your own gallery.' : 'Removed from this device.',
        on ? 'Create your gallery' : null, on ? authURL('signup') : null);
    }
    return on;
  }

  function enqueue(kind, id, desired) {
    const job = queue.then(() => ready).then(() => change(kind,id,desired));
    queue = job.catch(() => {});
    return job;
  }
  window.Gallery = {ready, has:(kind,id) => (ids[kind]||[]).includes(id),
    toggle:(kind,id) => enqueue(kind,id), set:(kind,id,on) => enqueue(kind,id,on), paint};
  // Compatibility for existing painting pages cached during a deployment.
  window.faSync = (id,on) => enqueue('painting',id,on).catch(error => errorNotice(error));

  document.addEventListener('click', async event => {
    const button = event.target.closest('[data-gallery-kind][data-gallery-id]');
    if (!button) return;
    event.preventDefault(); event.stopPropagation();
    const kind = button.dataset.galleryKind, id = button.dataset.galleryId;
    button.disabled = true; button.setAttribute('aria-busy','true');
    try {await enqueue(kind,id);} catch (error) {errorNotice(error, () => enqueue(kind,id).catch(e => errorNotice(e)));}
    finally {button.disabled=false; button.removeAttribute('aria-busy');}
  });
  document.addEventListener('click', async event => {
    const button = event.target.closest('[data-import-favorites]');
    if (!button) return;
    button.disabled=true;
    try {await importPending();} catch (error) {errorNotice(error);}
    finally {button.disabled=false;}
  });
  document.addEventListener('submit', event => {
    if (event.target.matches('[data-gallery-signout]')) {
      for (const key of [...Object.values(keys),ownerKey,pendingKey]) remove(key);
    }
    if (event.target.matches('[data-gallery-delete]')) {
      if (!confirm('Delete your account and all saved paintings, photographs, and music? This cannot be undone.')) {event.preventDefault(); return;}
      for (const key of [...Object.values(keys),ownerKey,pendingKey]) remove(key);
    }
  });
  let repaint;
  new MutationObserver(() => {cancelAnimationFrame(repaint); repaint=requestAnimationFrame(paint);})
    .observe(document.body,{childList:true,subtree:true});
  addEventListener('pageshow', event => {
    if (userId && event.persisted) request().then(data => adopt(data.ids)).catch(error => errorNotice(error));
  });
})();
