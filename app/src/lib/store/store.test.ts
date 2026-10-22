import 'fake-indexeddb/auto'
import { describe, expect, it } from 'vitest'
import { replay, scheduler } from '../engine/scheduler'
import { Session } from '../session.svelte'
import { deckWords } from '../testing'
import { BackupError, backupName, importBackup, makeBackup, parseBackup } from './backup'
import { storeSink, Store, wipe } from './db'
import { DEFAULT_SETTINGS } from './settings'

const T0 = new Date('2026-10-10T10:00:00').getTime()
let dbCount = 0

/** A store with a few days of study written through the real session. */
async function studied(name: string) {
  const store = await Store.open(name)
  const settings = { ...DEFAULT_SETTINGS, newPerDay: 4, haptics: false }
  await store.saveSettings(settings)
  for (let day = 0; day < 3; day++) {
    const start = T0 + day * 86_400_000
    const s = new Session({ words: deckWords(8), deckVersion: 'v1', settings, events: await store.events(), sink: storeSink(store), now: start })
    for (let i = 0; i < 12 && s.phase !== 'done'; i++) {
      const at = start + i * 20_000
      s.start()
      s.revealed(at)
      s.respond(i % 4 === 0 ? 'dont_know' : 'know', at + 3000 + i * 500)
      s.next(at + 9000)
    }
    await new Promise((resolve) => setTimeout(resolve, 0)) // let the writes land
  }
  return store
}

describe('store', () => {
  it('keeps a cache that equals a full replay', async () => {
    const store = await studied(`cache-${dbCount++}`)
    const events = await store.events()
    expect(events.length).toBeGreaterThan(10)
    expect(await store.states()).toEqual(replay(events, scheduler()))
    store.close()
  })

  it('restores the identical state after export, wipe and import', async () => {
    const name = `roundtrip-${dbCount++}`
    const store = await studied(name)
    const before = { events: await store.events(), settings: await store.settings() }
    const file = JSON.stringify(await makeBackup(store, 'device-1', { lang: 'en', theme: 'latte' }, new Date(T0)))
    store.close()
    await wipe(name)

    const empty = await Store.open(name)
    expect(await empty.events()).toEqual([])
    const result = await importBackup(empty, parseBackup(file), true)
    expect(result).toMatchObject({ added: before.events.length, total: before.events.length, local: { lang: 'en', theme: 'latte' } })
    const after = { events: await empty.events(), settings: await empty.settings() }
    expect(after).toEqual(before)
    const f = scheduler()
    expect(replay(after.events, f)).toEqual(replay(before.events, f))

    // a union: importing again adds nothing
    expect((await importBackup(empty, parseBackup(file), false)).added).toBe(0)
    expect((await empty.events()).length).toBe(before.events.length)
    empty.close()
  })

  it('turns an answer left open into an event on the next start', async () => {
    const store = await Store.open(`pending-${dbCount++}`)
    const s = new Session({
      words: deckWords(2), deckVersion: 'v1', settings: DEFAULT_SETTINGS, sink: storeSink(store), now: T0,
      events: [{ id: '00', type: 'intro', word_id: 'a#noun#1', ts: '2026-10-09T10:00:00.000Z', deck_version: 'v1', app_version: '0' }],
    })
    await store.mergeEvents([{ id: '00', type: 'intro', word_id: 'a#noun#1', ts: '2026-10-09T10:00:00.000Z', deck_version: 'v1', app_version: '0' }])
    s.start()
    s.revealed(T0)
    s.respond('know', T0 + 2000)
    s.undo()
    await new Promise((resolve) => setTimeout(resolve, 0))
    // the app is closed here, before Weiter
    await store.settlePending()
    const events = await store.events()
    expect(events.map((e) => e.type)).toEqual(['intro', 'review'])
    expect(events[1].review).toMatchObject({ undo: true, score: 0 })
    await store.settlePending() // nothing left to settle
    expect((await store.events()).length).toBe(2)
    store.close()
  })

  it('refuses files that are not backups', () => {
    expect(() => parseBackup('{')).toThrow(BackupError)
    expect(() => parseBackup('{"format": "other"}')).toThrow(/not a Karteikasten backup/)
    expect(() => parseBackup('{"format": "karteikasten-backup", "version": 2, "events": []}')).toThrow(/version 2/)
    expect(() => parseBackup('{"format": "karteikasten-backup", "version": 1, "events": [{}]}')).toThrow(/malformed/)
    expect(backupName(new Date('2026-10-22T23:30:00'))).toBe('karteikasten-2026-10-22.json')
  })
})
