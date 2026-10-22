// Until D40 the app registered a Workbox service worker at /sw.js that precached
// the whole build. The APK serves its own files, but a WebView that ran an early
// APK keeps that worker: Capacitor answers 404 for a missing /sw.js, a failed
// update leaves the old worker in place, and it keeps serving the old build.
// The browser checks this file for updates, finds this version, and it clears
// the caches, unregisters itself and reloads the pages it controlled.
self.addEventListener('install', () => self.skipWaiting())

self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      for (const key of await caches.keys()) await caches.delete(key)
      await self.registration.unregister()
      for (const client of await self.clients.matchAll({ type: 'window' })) client.navigate(client.url)
    })(),
  )
})
