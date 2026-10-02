/* Public static assets only. Authenticated API and private response data are never cached. */
const PACKAGED = self.location.pathname === "/teletena/sw.js";
const ASSETS = PACKAGED ? "/assets/tele_tena/review/" : "/";
const SCOPE = PACKAGED ? "/teletena/" : "/";
const CACHE = "tele-tena-public-v2";
const STATIC = ["/manifest.webmanifest", "/offline.html", "/brand/favicon.svg", "/brand/symbol.svg", "/brand/app-icon.svg", "/brand/app-icon-maskable.svg"].map(path => ASSETS + path.slice(1));
self.addEventListener("install", event => { event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(STATIC))); });
self.addEventListener("activate", event => { event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith("tele-tena-public-") && key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin || url.pathname.startsWith("/api/") || url.pathname.startsWith("/private/") || request.headers.has("authorization")) return;
  if (request.mode === "navigate" && url.pathname.startsWith(SCOPE)) {
    event.respondWith(fetch(request).catch(() => caches.match(ASSETS + "offline.html")));
    return;
  }
  if (url.pathname.startsWith(PACKAGED ? ASSETS + "assets/" : "/assets/") || STATIC.includes(url.pathname)) {
    event.respondWith(caches.match(request).then(hit => hit || fetch(request).then(response => {
      if (response.ok && response.type === "basic") { const copy = response.clone(); caches.open(CACHE).then(cache => cache.put(request, copy)); }
      return response;
    })));
  }
});
self.addEventListener("message", event => { if (event.data === "SKIP_WAITING") self.skipWaiting(); });
