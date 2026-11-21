// What the Android side needs to act with the app closed (D62, D63): the latest backup and
// the export run times, and the next week's reminders. App calls this when it goes to the
// background and when a setting they depend on changes.

import { ulid } from './engine/events'
import { strings } from './strings'
import { native, planExports, planReminders, stage } from './native'
import { planReminders as reminderPlan } from './reminder'
import type { Session } from './session.svelte'
import { makeBackup } from './store/backup'
import type { Store } from './store/db'
import { parseSchedule, upcomingRuns } from './store/schedule'
import type { Settings } from './store/settings'
import { savedChoice } from './theme'

const PLAN_RUNS = 400 // export run times handed over at a time; the next background plans on

/** The export run times from `now`: none when regular exports are off or the expression does not read. */
export function exportRuns(settings: Settings, now: Date): number[] {
  if (!settings.exports.scheduled) return []
  try {
    return upcomingRuns(parseSchedule(settings.exports.calendar), now, PLAN_RUNS)
  } catch {
    return []
  }
}

/** The backup as the app exports it, for a file or for the export alarm. */
export async function backupJson(store: Store, now = new Date()): Promise<string> {
  const deviceId = await store.deviceId(() => ulid())
  return JSON.stringify(await makeBackup(store, deviceId, { theme: savedChoice() }, now))
}

export async function syncBackground(store: Store, session: Session, settings: Settings): Promise<void> {
  if (!native()) return // a browser has no alarms to hand anything to
  const now = Date.now()
  const runs = exportRuns(settings, new Date(now))
  if (runs.length) await stage(await backupJson(store))
  await planExports(runs, settings.exports.oneFile)
  const items = settings.reminder.on ? reminderPlan(session, settings.reminder.at, now, strings.reminder) : []
  await planReminders(items)
}
