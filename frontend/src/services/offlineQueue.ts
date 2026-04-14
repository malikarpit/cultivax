/**
 * Offline queue service using IndexedDB.
 * Queues actions when offline, syncs when online.
 */

interface QueuedAction {
  id: string;
  crop_id: string;
  action_type: string;
  action_effective_date: string;
  local_seq_no: number;
  metadata?: Record<string, any>;
  status: 'pending' | 'syncing' | 'synced' | 'failed';
  error?: string;
  sync_timestamp?: string;
  attempts: number;
}

/**
 * FR-24: Offline message queuing interface.
 */
interface QueuedMessage {
  id: string;
  conversation_id: string;
  content: string;
  message_type: string;
  client_message_id: string;
  status: 'pending' | 'syncing' | 'synced' | 'failed';
  error?: string;
  created_at: string;
  attempts: number;
}

const DB_NAME = 'cultivax-offline';
const STORE_NAME = 'queued-actions';
const MESSAGE_STORE_NAME = 'queued-messages';  // FR-24
const DB_VERSION = 2;  // Bumped for message store

export class OfflineQueueService {
  private db: IDBDatabase | null = null;
  private deviceId: string;
  private sessionId: string;

  constructor() {
    this.deviceId = this.getOrCreateDeviceId();
    this.sessionId = this.generateSessionId();
  }

  /**
   * Initialize IndexedDB.
   */
  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Create object store
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          const store = db.createObjectStore(STORE_NAME, { keyPath: 'id' });
          store.createIndex('status', 'status', { unique: false });
          store.createIndex('crop_id', 'crop_id', { unique: false });
          store.createIndex('local_seq_no', 'local_seq_no', { unique: false });
        }

        // FR-24: Create message queue store
        if (!db.objectStoreNames.contains(MESSAGE_STORE_NAME)) {
          const msgStore = db.createObjectStore(MESSAGE_STORE_NAME, { keyPath: 'id' });
          msgStore.createIndex('status', 'status', { unique: false });
          msgStore.createIndex('conversation_id', 'conversation_id', { unique: false });
          msgStore.createIndex('client_message_id', 'client_message_id', { unique: true });
        }
      };
    });
  }

  /**
   * Queue an action for offline submission.
   */
  async queueAction(
    crop_id: string,
    action_type: string,
    action_effective_date: string,
    metadata?: Record<string, any>
  ): Promise<string> {
    if (!this.db) throw new Error('Database not initialized');

    // Get next sequence number
    const maxSeq = await this.getMaxSequenceNumber(crop_id);
    const local_seq_no = maxSeq + 1;

    const action: QueuedAction = {
      id: `action_${Date.now()}_${Math.random()}`,
      crop_id,
      action_type,
      action_effective_date,
      local_seq_no,
      metadata,
      status: 'pending',
      attempts: 0
    };

    return new Promise((resolve, reject) => {
      const tx = this.db!.transaction([STORE_NAME], 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      const request = store.add(action);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.registerBackgroundSync().catch(e => console.debug('Sync register skipped:', e));
        
        // Optimistic UI update using SWR mutate
        import('swr').then(({ mutate }) => {
          const actionsUrl = `/api/v1/crops/${crop_id}/actions`;
          mutate(actionsUrl, (currentData: any) => {
            const optimisticAction = {
              id: action.id, // temporary id
              action_type: action.action_type,
              action_date: action.action_effective_date, // assuming backend uses action_date
              description: `[Offline] ${action.action_type}`,
              status: 'pending_sync',
              created_at: new Date().toISOString()
            };
            return currentData ? [optimisticAction, ...currentData] : [optimisticAction];
          }, { revalidate: false }).catch(console.error);
        });

        resolve(action.id);
      };
    });
  }

  /**
   * Get pending actions for a crop.
   */
  async getPendingActions(crop_id: string): Promise<QueuedAction[]> {
    if (!this.db) throw new Error('Database not initialized');

    return new Promise((resolve, reject) => {
      const tx = this.db!.transaction([STORE_NAME], 'readonly');
      const store = tx.objectStore(STORE_NAME);
      const index = store.index('crop_id');
      const request = crop_id === '*' ? store.getAll() : index.getAll(crop_id);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        const actions = request.result.filter(a => a.status === 'pending' || a.status === 'failed'); // retry failed ones too
        resolve(actions.sort((a, b) => a.local_seq_no - b.local_seq_no));
      };
    });
  }

  /**
   * Get all queued actions (any status).
   */
  async getAllQueuedActions(): Promise<QueuedAction[]> {
    if (!this.db) throw new Error('Database not initialized');

    return new Promise((resolve, reject) => {
      const tx = this.db!.transaction([STORE_NAME], 'readonly');
      const store = tx.objectStore(STORE_NAME);
      const request = store.getAll();

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
    });
  }

  /**
   * Sync queued actions to server.
   */
  async syncActions(): Promise<{
    synced: number;
    failed: number;
    errors: Record<string, string>;
  }> {
    const actions = await this.getPendingActions('*'); // Get all pending

    if (actions.length === 0) {
      return { synced: 0, failed: 0, errors: {} };
    }

    // Group by crop_id to make multiple requests
    const byCrop = new Map<string, QueuedAction[]>();
    for (const action of actions) {
      if (!byCrop.has(action.crop_id)) {
        byCrop.set(action.crop_id, []);
      }
      byCrop.get(action.crop_id)!.push(action);
    }

    let synced = 0;
    let failed = 0;
    const errors: Record<string, string> = {};
    const { apiPost } = await import('@/lib/api'); // Dynamic import to avoid circular dependency issues if any

    for (const [cropId, cropActions] of Array.from(byCrop.entries())) {
      try {
        // Mark as syncing
        for (const action of cropActions) {
          await this.updateActionStatus(action.id, 'syncing');
        }

        // Call sync API using the shared api client
        const result = await apiPost<any>('/api/v1/offline-sync', {
          device_id: this.deviceId,
          session_id: this.sessionId,
          actions: cropActions.map((a: QueuedAction) => ({
            crop_instance_id: a.crop_id,
            action_type: a.action_type,
            action_effective_date: a.action_effective_date,
            local_seq_no: a.local_seq_no,
            metadata: a.metadata || {}
          }))
        });

        // Mark synced actions
        if (result.synced_actions) {
          for (const syncedAction of result.synced_actions) {
            const queuedAction = cropActions.find(
              (a: QueuedAction) => a.local_seq_no === syncedAction.local_seq_no
            );
            if (queuedAction) {
              await this.updateActionStatus(queuedAction.id, 'synced', {
                sync_timestamp: result.sync_timestamp
              });
              synced++;
            }
          }
        }

        // Mark failed actions
        if (result.failed_actions) {
          for (const failedAction of result.failed_actions) {
            const queuedAction = cropActions[failedAction.action_index];
            if (queuedAction) {
              await this.updateActionStatus(queuedAction.id, 'failed', {
                error: failedAction.error,
                attempts: queuedAction.attempts + 1
              });
              failed++;
              errors[queuedAction.id] = failedAction.error;
            }
          }
        }

        // Handle duplicates (from idempotency)
        if (result.warnings && result.warnings.some((w: string) => w.includes('Duplicate'))) {
          // In real app, match the exact duplicate action from warnings.
          // For now we'll fetch success locally to prevent resync
          // the backend returns the successfully synced count anyway.
        }

      } catch (error) {
        failed += cropActions.length;
        for (const action of cropActions) {
          errors[action.id] = (error as Error).message;
          await this.updateActionStatus(action.id, 'failed', {
            error: (error as Error).message,
            attempts: action.attempts + 1
          });
        }
      }
    }

    return { synced, failed, errors };
  }

  /**
   * Update action status.
   */
  private async updateActionStatus(
    actionId: string,
    status: QueuedAction['status'],
    updates?: Partial<QueuedAction>
  ): Promise<void> {
    if (!this.db) throw new Error('Database not initialized');

    return new Promise((resolve, reject) => {
      const tx = this.db!.transaction([STORE_NAME], 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      const getRequest = store.get(actionId);

      getRequest.onsuccess = () => {
        const action = getRequest.result;
        if (action) {
          action.status = status;
          Object.assign(action, updates);
          const updateRequest = store.put(action);
          updateRequest.onerror = () => reject(updateRequest.error);
          updateRequest.onsuccess = () => resolve();
        }
      };

      getRequest.onerror = () => reject(getRequest.error);
    });
  }

  /**
   * Register for Background Sync API if supported.
   * This tells the Service Worker to wake up and sync when internet is restored.
   */
  private async registerBackgroundSync(): Promise<void> {
    if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.ready;
        if ('sync' in registration) {
          // @ts-ignore - SyncManager types often missing in standard TS dom lib
          await registration.sync.register('cultivax-sync');
        }
      } catch (error) {
        console.warn('Background sync registration failed:', error);
      }
    }
  }

  /**
   * Get max local_seq_no for a crop.
   */
  private async getMaxSequenceNumber(crop_id: string): Promise<number> {
    const actions = await this.getPendingActions(crop_id);
    return actions.length > 0 ? Math.max(...actions.map(a => a.local_seq_no)) : 0;
  }

  /**
   * Get or create device ID (persists in localStorage).
   */
  private getOrCreateDeviceId(): string {
    if (typeof window === 'undefined') return 'server-side';
    const key = 'cultivax_device_id';
    let id = localStorage.getItem(key);
    if (!id) {
      id = `device_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem(key, id);
    }
    return id;
  }

  /**
   * Generate session ID (unique per app launch).
   */
  private generateSessionId(): string {
    if (typeof window === 'undefined') return 'server-side';
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Clear all synced actions from queue.
   */
  async clearSyncedActions(): Promise<void> {
    if (!this.db) throw new Error('Database not initialized');

    return new Promise((resolve, reject) => {
      const tx = this.db!.transaction([STORE_NAME], 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      const index = store.index('status');
      const request = index.openCursor(IDBKeyRange.only('synced'));

      request.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest).result;
        if (cursor) {
          cursor.delete();
          cursor.continue();
        } else {
          resolve();
        }
      };

      request.onerror = () => reject(request.error);
    });
  }
  /**
   * FR-24: Queue a message for offline sync.
   */
  async queueMessage(
    conversationId: string,
    content: string,
    messageType: string = 'text'
  ): Promise<string> {
    if (!this.db) throw new Error('Database not initialized');

    const clientMsgId = `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;

    const msg: QueuedMessage = {
      id: clientMsgId,
      conversation_id: conversationId,
      content,
      message_type: messageType,
      client_message_id: clientMsgId,
      status: 'pending',
      created_at: new Date().toISOString(),
      attempts: 0,
    };

    return new Promise((resolve, reject) => {
      const tx = this.db!.transaction([MESSAGE_STORE_NAME], 'readwrite');
      const store = tx.objectStore(MESSAGE_STORE_NAME);
      const request = store.add(msg);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.registerBackgroundSync().catch(e => console.debug('Msg sync register skipped:', e));
        resolve(clientMsgId);
      };
    });
  }

  /**
   * FR-24: Get all pending messages for a conversation.
   */
  async getPendingMessages(conversationId?: string): Promise<QueuedMessage[]> {
    if (!this.db) throw new Error('Database not initialized');

    return new Promise((resolve, reject) => {
      const tx = this.db!.transaction([MESSAGE_STORE_NAME], 'readonly');
      const store = tx.objectStore(MESSAGE_STORE_NAME);
      const index = store.index('status');
      const request = index.getAll(IDBKeyRange.only('pending'));

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        let results = request.result as QueuedMessage[];
        if (conversationId) {
          results = results.filter(m => m.conversation_id === conversationId);
        }
        resolve(results);
      };
    });
  }

  /**
   * FR-24: Sync pending messages when back online.
   */
  async syncMessages(token: string): Promise<{ synced: number; failed: number }> {
    const pending = await this.getPendingMessages();
    let synced = 0;
    let failed = 0;

    for (const msg of pending) {
      try {
        const res = await fetch(
          `/api/v1/messages/conversations/${msg.conversation_id}/messages`,
          {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              content: msg.content,
              message_type: msg.message_type,
              client_message_id: msg.client_message_id,
            }),
          }
        );

        if (res.ok || res.status === 200 || res.status === 201) {
          await this.updateMessageStatus(msg.id, 'synced');
          synced++;
        } else {
          await this.updateMessageStatus(msg.id, 'failed', `HTTP ${res.status}`);
          failed++;
        }
      } catch (err: any) {
        await this.updateMessageStatus(msg.id, 'failed', err.message);
        failed++;
      }
    }

    return { synced, failed };
  }

  /**
   * FR-24: Update queued message status.
   */
  private async updateMessageStatus(
    id: string,
    status: QueuedMessage['status'],
    error?: string
  ): Promise<void> {
    if (!this.db) return;

    return new Promise((resolve, reject) => {
      const tx = this.db!.transaction([MESSAGE_STORE_NAME], 'readwrite');
      const store = tx.objectStore(MESSAGE_STORE_NAME);
      const request = store.get(id);

      request.onsuccess = () => {
        const msg = request.result;
        if (msg) {
          msg.status = status;
          msg.attempts = (msg.attempts || 0) + 1;
          if (error) msg.error = error;
          store.put(msg);
        }
        resolve();
      };
      request.onerror = () => reject(request.error);
    });
  }
}

// Export singleton
export const offlineQueue = new OfflineQueueService();
