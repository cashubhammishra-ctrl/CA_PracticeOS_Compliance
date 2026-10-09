// Service worker for CA PracticeOS Compliance - enables PWA installability
// and offline app-shell loading. Deliberately does NOT cache or intercept
// API calls (AI backend, Tally connector/relay) or third-party CDN scripts -
// only same-origin GET requests for the app shell are cached, so live data
// always comes fresh from the network.
//
// Strategy: the page itself is NETWORK-FIRST (so users always get the latest
// version when online, with a short timeout so a flaky connection falls back
// to the saved copy). Icons/manifest are cache-first with background refresh.
const CACHE_NAME = 'ca-practiceos-v3';
const APP_PAGE = './CA_PracticeOS_Compliance.html';
const NAV_TIMEOUT_MS = 5000;
const APP_SHELL = [
  APP_PAGE,
  './manifest.json',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-512.png',
  './icons/apple-touch-icon.png',
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)).catch(() => {})
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

function cleanKey(url) {
  return new Request(url.origin + url.pathname);
}

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== self.location.origin) {
    return; // let API calls, CDN scripts, cross-origin requests pass through untouched
  }

  if (req.mode === 'navigate') {
    // Store/lookup under the clean URL so ?query variants (e.g. approval links) share one entry.
    const key = cleanKey(url);
    event.respondWith(
      new Promise((resolve) => {
        let settled = false;
        const fallback = () =>
          caches.match(key).then((c) => c || caches.match(APP_PAGE)).then((c) => c || Response.error());
        const timer = setTimeout(() => {
          if (!settled) fallback().then((r) => { if (!settled) { settled = true; resolve(r); } });
        }, NAV_TIMEOUT_MS);
        fetch(req)
          .then((response) => {
            if (response && response.status === 200) {
              const copy = response.clone();
              caches.open(CACHE_NAME).then((cache) => cache.put(key, copy));
            }
            if (!settled) { settled = true; clearTimeout(timer); resolve(response); }
          })
          .catch(() => {
            clearTimeout(timer);
            if (!settled) fallback().then((r) => { if (!settled) { settled = true; resolve(r); } });
          });
      })
    );
    return;
  }

  event.respondWith(
    caches.match(req).then((cached) => {
      const network = fetch(req)
        .then((response) => {
          if (response && response.status === 200) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
          }
          return response;
        })
        .catch(() => cached || Response.error());
      return cached || network;
    })
  );
});
