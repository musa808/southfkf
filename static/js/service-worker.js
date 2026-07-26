const CACHE_NAME = "fcms-cache-v1";
const OFFLINE_URL = "/offline/";

// Only genuinely static, safe-to-precache URLs go here.
// Do NOT precache dynamic pages (dashboard, fixtures, etc.) — they change too often
// and could show stale data. Those are handled by the network-first fetch handler below.
const PRECACHE_URLS = [
  OFFLINE_URL,
  "/static/manifest.json",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS))
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;

  // Full page navigations: try network first, fall back to offline page.
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(() => caches.match(OFFLINE_URL))
    );
    return;
  }

  // Static assets (css/js/images/fonts): cache-first, then update cache in background.
  if (["style", "script", "image", "font"].includes(request.destination)) {
    event.respondWith(
      caches.match(request).then((cached) => {
        const fetchPromise = fetch(request)
          .then((response) => {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
            return response;
          })
          .catch(() => cached);
        return cached || fetchPromise;
      })
    );
    return;
  }

  // Everything else: try network, fall back to cache if available.
  event.respondWith(
    fetch(request).catch(() => caches.match(request))
  );
});