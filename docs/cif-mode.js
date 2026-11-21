/*
 * Single source of truth for "live backend" vs "static snapshot" mode (audit fix FE-01).
 *
 * Previously five files each decided this with `window.location.port !== '8080'`, so running
 * the real server on any other port (or behind HTTPS on 443) silently switched the UI to
 * canned data, and the login page looped on /api/me until it was rate-limited.
 *
 * Static mode now means exactly one of:
 *   - this file was produced by tools/build_static.py for GitHub Pages (flag below = true),
 *   - the page was opened from disk (file://), or
 *   - the page is hosted on *.github.io (no Python backend can run there).
 * Everything else is live: the page was served by server.py, whatever host or port.
 */
window.__CIF_STATIC_BUILD__ = true; // written by tools/build_static.py
window.CIF_IS_STATIC = function () {
  if (window.__CIF_STATIC_BUILD__ === true) return true;
  if (window.location.protocol === 'file:') return true;
  return window.location.hostname.endsWith('github.io');
};
