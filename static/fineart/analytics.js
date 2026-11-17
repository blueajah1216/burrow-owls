/* Anonymous gallery analytics: no account identifiers, search text or recordings.
 * Engagement measures visible-page time, not proof that someone is attentive.
 */
(() => {
  'use strict';
  const hosts = new Set(['thegreatgallery.art', 'www.thegreatgallery.art']);
  const privatePath = path => /^\/(?:fineart\/)?(?:login|signup|account|logout|lovers)(?:\/|$)/.test(path);
  const enabled = () => {
    if (!hosts.has(location.hostname) || privatePath(location.pathname) || navigator.doNotTrack === '1') return false;
    try { return localStorage.getItem('umami.disabled') !== '1'; }
    catch (_) { return true; } // Storage restrictions must not break the page.
  };

  // Also sanitize referrers: Umami's exclude-search option applies to page URLs.
  window.galleryAnalyticsBeforeSend = (type, payload) => {
    try {
      if (!enabled()) return false;
      const url = new URL(payload.url || location.href, location.origin);
      if (privatePath(url.pathname)) return false;
      const clean = {...payload, url: url.pathname};
      if (clean.referrer) {
        const referrer = new URL(clean.referrer, location.origin);
        clean.referrer = referrer.origin === location.origin
          ? (privatePath(referrer.pathname) ? '/' : referrer.pathname)
          : referrer.origin;
      }
      return clean;
    } catch (_) {
      return false;
    }
  };

  let visibleSince = document.visibilityState === 'visible' ? performance.now() : null;
  let pendingMs = 0;
  const section = location.pathname.startsWith('/photography') ? 'photography'
    : /^\/music(\/|$)/.test(location.pathname) ? 'music'
    : /^\/(games|memory|quiz|older|jigsaw|slide)(\/|$)/.test(location.pathname) ? 'games'
    : 'paintings';

  function flush() {
    const now = performance.now();
    if (visibleSince !== null) pendingMs += now - visibleSince;
    visibleSince = document.visibilityState === 'visible' ? now : null;
    const seconds = Math.floor(pendingMs / 1000);
    try {
      if (!seconds || !enabled() || !window.umami) return;
      // Minute batches limit event volume. Hiding/leaving flushes the remainder.
      // Transport may drop a final event if the browser closes abruptly.
      const result = window.umami.track('engagement', {seconds, section});
      pendingMs -= seconds * 1000;
      if (result && typeof result.catch === 'function') result.catch(() => {});
    } catch (_) {
      // Analytics must never interfere with browsing or playback.
    }
  }
  setInterval(flush, 60000);
  document.addEventListener('visibilitychange', flush);
  window.addEventListener('pagehide', () => {
    flush();
    visibleSince = null;
  });
  window.addEventListener('pageshow', () => {
    visibleSince = document.visibilityState === 'visible' ? performance.now() : null;
  });
})();
