// Service worker for offline support (basic PWA).
//
// Strategy:
//   - Navigations & static assets: cache-first with background refresh, so a
//     previously loaded app shell works offline.
//   - Public API GETs (decks, cards, SVGs): network-first, falling back to cache
//     so previously viewed content is available offline.
//   - Authenticated API requests (Authorization header) and non-GET requests:
//     network-only, never cached (user-specific / mutating).

const CACHE = "medchem-v1";

self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)));
      await self.clients.claim();
    })(),
  );
});

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) {
    // Refresh in the background.
    fetch(request)
      .then((resp) => resp.ok && caches.open(CACHE).then((c) => c.put(request, resp.clone())))
      .catch(() => {});
    return cached;
  }
  const resp = await fetch(request);
  if (resp.ok) (await caches.open(CACHE)).put(request, resp.clone());
  return resp;
}

async function networkFirst(request) {
  try {
    const resp = await fetch(request);
    if (resp.ok) (await caches.open(CACHE)).put(request, resp.clone());
    return resp;
  } catch (err) {
    const cached = await caches.match(request);
    if (cached) return cached;
    throw err;
  }
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  // Never cache user-specific API responses.
  if (url.pathname.startsWith("/api/") && request.headers.get("authorization")) return;

  if (url.pathname.startsWith("/api/")) {
    event.respondWith(networkFirst(request));
    return;
  }
  // App shell / static assets.
  event.respondWith(cacheFirst(request));
});
