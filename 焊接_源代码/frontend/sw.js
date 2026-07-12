// Welding Lab Service Worker
const CACHE = 'welding-lab-v1';

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE).then((cache) => {
      return cache.addAll([
        '/',
        '/static/css/style.css',
        '/static/js/app.js',
        '/static/manifest.json'
      ]);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)));
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  // For API calls, go network-first
  if (e.request.url.includes('/api/')) {
    e.respondWith(
      fetch(e.request).catch(() => caches.match(e.request))
    );
    return;
  }
  // For static assets, cache-first
  e.respondWith(
    caches.match(e.request).then((cached) => {
      const fetched = fetch(e.request).then((response) => {
        const clone = response.clone();
        caches.open(CACHE).then((cache) => cache.put(e.request, clone));
        return response;
      });
      return cached || fetched;
    })
  );
});
