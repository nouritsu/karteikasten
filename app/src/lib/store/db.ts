// IndexedDB (spec: Storage and offline): `events` (append-only), `cards` (the derived
// state, a cache of the replay), `settings` and `meta`. The database lives in the
// app's data: an APK update keeps it, uninstalling deletes it (D43), so export is
// the only backup.

import { deleteDB, openDB, type DBSchema, type IDBPDatabase } from 'idb'
import type { StudyEvent } from '../engine/events'
import type { WordState } from '../engine/scheduler'
import { withDefaults, type Settings } from './settings'

export const DB_NAME = 'karteikasten'

interface Schema extends DBSchema {
  events: { key: string; value: StudyEvent }
  cards: { key: string; value: WordState }
  settings: { key: string; value: Settings }
  meta: { key: string; value: unknown }
}

/** A review answered but not yet closed with Weiter; replayed into an event on the next start. */
const PENDING = 'pending'

export class Store {
  constructor(readonly db: IDBPDatabase<Schema>) {}

  static async open(name = DB_NAME): Promise<Store> {
    const db = await openDB<Schema>(name, 1, {
      upgrade(db) {
        db.createObjectStore('events', { keyPath: 'id' })
        db.createObjectStore('cards')
        db.createObjectStore('settings')
        db.createObjectStore('meta')
      },
    })
    return new Store(db)
  }

  close(): void {
    this.db.close()
  }

  async events(): Promise<StudyEvent[]> {
    return this.db.getAll('events')
  }

  async addEvent(event: StudyEvent): Promise<void> {
    await this.db.put('events', event)
  }

  /** Adds the events whose ids are new; returns how many that was (an import is a union). */
  async mergeEvents(events: readonly StudyEvent[]): Promise<number> {
    const tx = this.db.transaction('events', 'readwrite')
    let added = 0
    for (const event of events) {
      if ((await tx.store.getKey(event.id)) === undefined) {
        await tx.store.add(event)
        added++
      }
    }
    await tx.done
    return added
  }

  async putState(id: string, state: WordState): Promise<void> {
    await this.db.put('cards', state, id)
  }

  /** Replaces the whole cache with a replay. */
  async putStates(states: ReadonlyMap<string, WordState>): Promise<void> {
    const tx = this.db.transaction('cards', 'readwrite')
    await tx.store.clear()
    for (const [id, state] of states) await tx.store.put(state, id)
    await tx.done
  }

  async states(): Promise<Map<string, WordState>> {
    const tx = this.db.transaction('cards')
    const [keys, values] = await Promise.all([tx.store.getAllKeys(), tx.store.getAll()])
    return new Map(keys.map((k, i) => [k, values[i]]))
  }

  async settings(): Promise<Settings> {
    return withDefaults(await this.db.get('settings', 'settings'))
  }

  async saveSettings(settings: Settings): Promise<void> {
    await this.db.put('settings', settings, 'settings')
  }

  async meta<T>(key: string): Promise<T | undefined> {
    return (await this.db.get('meta', key)) as T | undefined
  }

  async setMeta(key: string, value: unknown): Promise<void> {
    if (value === undefined) await this.db.delete('meta', key)
    else await this.db.put('meta', value, key)
  }

  /** This install's id, for exports; made on first use. */
  async deviceId(make: () => string): Promise<string> {
    const known = await this.meta<string>('device_id')
    if (known) return known
    const id = make()
    await this.setMeta('device_id', id)
    return id
  }

  async setPending(event: StudyEvent | null): Promise<void> {
    await this.setMeta(PENDING, event ?? undefined)
  }

  /** A review left open when the app was closed becomes an event, as it stood. */
  async settlePending(): Promise<void> {
    const pending = await this.meta<StudyEvent>(PENDING)
    if (pending) {
      await this.mergeEvents([pending])
      await this.setMeta(PENDING, undefined)
    }
  }
}

/** The session's events go to the store, each with the card state it leads to. */
export function storeSink(store: Store) {
  return {
    add: async (event: StudyEvent, state: WordState) => {
      await store.addEvent(event)
      await store.putState(event.word_id, state)
    },
    pending: (event: StudyEvent | null) => store.setPending(event),
  }
}

export async function wipe(name = DB_NAME): Promise<void> {
  await deleteDB(name)
}
