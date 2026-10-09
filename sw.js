// Service worker for CA PracticeOS Compliance - enables PWA installability
// and offline app-shell loading. Deliberately does NOT cache or intercept
// API calls (AI backend, Tally connector/relay) or third-party CDN scripts -
// only same-origin GET requests for the app shell are cached, so live data
// always comes fresh from the network.
const CACHE_NAME = 'ca-practiceos-v2';
const APP_PAGE = './CA_PracticeOS_Compliance.html';
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

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== self.location.origin) {
    return; // let API calls, CDN scripts, cross-origin requests pass through untouched
  }
  event.respondWith(
    caches.match(req, { ignoreSearch: true }).then((cached) => {
      const network = fetch(req)
        .then((response) => {
          if (response && response.status === 200) {
            const copy = response.clone();
            // Store under the clean URL so ?query variants (e.g. approval links) don't pile up as copies.
            const key = req.mode === 'navigate' ? new Request(url.origin + url.pathname) : req;
            caches.open(CACHE_NAME).then((cache) => cache.put(key, copy));
          }
          return response;
        })
        .catch(() => {
          if (cached) return cached;
          // Offline and not cached (e.g. opening the site root): fall back to the app itself.
          if (req.mode === 'navigate') return caches.match(APP_PAGE);
          return Response.error();
        });
      return cached || network;
    })
  );
});
