// static/pwa/sw.js
// Keep this file at the site root scope by serving it from /sw.js (see
// online_learning_system/urls.py) — service workers can only control paths
// within their own scope, and a worker registered from /static/pwa/sw.js
// would default to only covering /static/pwa/*.

const CACHE_VERSION = 'ols-cache-v2';
const OFFLINE_URL = '/offline/';

const PRECACHE_URLS = [
  OFFLINE_URL,
  '/static/css/ols-theme.css',
  '/static/css/dashboard.css',
  '/static/css/reviews.css',
  '/static/css/quizzes.css',
  '/static/css/form.css',
  '/static/pwa/icon-192.png',
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => cache.addAll(PRECACHE_URLS))
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_VERSION).map((key) => caches.delete(key)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const { request } = event;

  // Only handle safe, cacheable GET requests — never intercept POST/PUT/etc,
  // since those are form submissions (login, grading, deletes...) that must
  // always hit the real server.
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  // Full page loads: try the network first (content changes constantly),
  // fall back to a cached copy, and finally to the offline page.
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const clone = response.clone();
          caches.open(CACHE_VERSION).then((cache) => cache.put(request, clone));
          return response;
        })
        .catch(() =>
          caches.match(request).then((cached) => cached || caches.match(OFFLINE_URL))
        )
    );
    return;
  }

  // Static assets: stale-while-revalidate. Answer instantly from cache
  // when we have it (keeps the offline/speed benefit), but always kick
  // off a network fetch in the background and overwrite the cache entry
  // with whatever comes back. A pure cache-first strategy here meant a
  // file could get cached once and then be served forever — the only
  // way to see an edit was to wipe the cache manually (clearing site
  // data/cookies). This way, a normal reload always triggers a
  // background refresh, so at most one load is stale before the cache
  // catches up on its own.
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.open(CACHE_VERSION).then((cache) =>
        cache.match(request).then((cached) => {
          const networkFetch = fetch(request)
            .then((response) => {
              if (response.ok) cache.put(request, response.clone());
              return response;
            })
            .catch(() => null);

          // Cached copy first if we have one — the network fetch above
          // still runs and updates the cache for the next load.
          return cached || networkFetch;
        })
      )
    );
  }
});
