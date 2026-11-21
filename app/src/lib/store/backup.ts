// Export and import (spec: Export and import). A backup holds every event and the
// settings; importing merges events by id, so importing twice, or a file from
// another device, never duplicates anything. On the phone, export writes
// Documents/Karteikasten/, which a Syncthing folder can sync later (D22).

import { Capacitor } from '@capacitor/core'
import { Directory, Encoding, Filesystem } from '@capacitor/filesystem'
import { dateKey } from '../engine/day'
import type { StudyEvent } from '../engine/events'
import type { Store } from './db'
import { withDefaults, type Settings } from './settings'

export const FORMAT = 'karteikasten-backup'
export const VERSION = 1
export const FOLDER = 'Karteikasten'

/** A UI choice kept in localStorage that travels with the settings: Mocha, Latte or
 *  System. (Backups from before D66 also carry the UI language, which is ignored.) */
export interface Local {
  theme?: string
}

export interface Backup {
  format: typeof FORMAT
  version: typeof VERSION
  exported_at: string
  device_id: string
  settings: Settings & Local
  events: StudyEvent[]
}

export async function makeBackup(store: Store, deviceId: string, local: Local, now = new Date()): Promise<Backup> {
  const events = await store.events()
  return {
    format: FORMAT,
    version: VERSION,
    exported_at: now.toISOString(),
    device_id: deviceId,
    settings: { ...(await store.settings()), ...local },
    events,
  }
}

/** A file a day, or with Keep one file (D62) one file each export replaces. The
 *  scheduled exports use the same names (Exports.java). */
export function backupName(now = new Date(), oneFile = false): string {
  return oneFile ? 'karteikasten.json' : `karteikasten-${dateKey(now)}.json`
}

export class BackupError extends Error {}

/** Parses and checks a backup file; throws BackupError when it is not one. */
export function parseBackup(text: string): Backup {
  let data: unknown
  try {
    data = JSON.parse(text)
  } catch {
    throw new BackupError('not JSON')
  }
  const b = data as Partial<Backup>
  if (b?.format !== FORMAT) throw new BackupError('not a Karteikasten backup')
  if (b.version !== VERSION) throw new BackupError(`backup version ${String(b.version)} is not supported`)
  if (!Array.isArray(b.events) || !b.events.every((e) => typeof e?.id === 'string' && typeof e.word_id === 'string')) {
    throw new BackupError('events are malformed')
  }
  return b as Backup
}

export interface Imported {
  added: number
  total: number
  local: Local | null // the theme to restore, when settings were restored
}

/** Merges the backup's events; with `settings`, its settings replace the current ones. */
export async function importBackup(store: Store, backup: Backup, settings: boolean): Promise<Imported> {
  const added = await store.mergeEvents(backup.events)
  let local: Local | null = null
  if (settings) {
    const { theme, ...rest } = backup.settings as Settings & Local & { lang?: string }
    delete rest.lang
    await store.saveSettings(withDefaults(rest))
    local = { theme }
  }
  return { added, total: backup.events.length, local }
}

/** Saves the file where the user can reach it; returns where it went. */
export async function saveBackupFile(name: string, text: string): Promise<string> {
  if (!Capacitor.isNativePlatform()) {
    // Development in a browser: an ordinary download.
    const url = URL.createObjectURL(new Blob([text], { type: 'application/json' }))
    const link = Object.assign(document.createElement('a'), { href: url, download: name })
    link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
    return name
  }
  const write = () =>
    Filesystem.writeFile({
      path: `${FOLDER}/${name}`,
      data: text,
      directory: Directory.Documents,
      encoding: Encoding.UTF8,
      recursive: true,
    })
  try {
    await write()
  } catch {
    // Android 9 and older ask for storage access first; 11 and newer never need it.
    await Filesystem.requestPermissions()
    await write()
  }
  return `Documents/${FOLDER}/${name}`
}
