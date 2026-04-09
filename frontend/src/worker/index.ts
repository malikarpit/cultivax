/// <reference lib="webworker" />

// Custom worker logic for background sync
const sw = self as unknown as ServiceWorkerGlobalScope;

sw.addEventListener('sync', (event: any) => {
  if (event.tag === 'cultivax-sync') {
    event.waitUntil(syncOfflineActions());
  }
});

async function syncOfflineActions() {
  console.log('[ServiceWorker] Background sync triggered: cultivax-sync');

  try {
    // Open IndexedDB
    const db = await new Promise<IDBDatabase>((resolve, reject) => {
      const request = indexedDB.open('cultivax-offline', 1);
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result as IDBDatabase);
    });

    const clients = await sw.clients.matchAll();
    if (clients && clients.length > 0) {
      clients.forEach(client => {
        client.postMessage({ type: 'SYNC_OFFLINE_ACTIONS' });
      });
      return;
    }

    console.log('[ServiceWorker] No open clients to perform sync, deferring to app launch.');

  } catch (err) {
    console.error('[ServiceWorker] Sync failed:', err);
    throw err; // Throwing ensures the browser might retry later
  }
}

// Ensure the custom worker doesn't break basic SW lifecycle
sw.addEventListener('install', () => {
  sw.skipWaiting();
});

sw.addEventListener('activate', () => {
  sw.clients.claim();
});

export {}; // Ensure this is treated as a module
