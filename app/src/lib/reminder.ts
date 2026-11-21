// The study reminder (D63): a notification at the time set, on days with cards due that
// have not been studied yet. Android posts it with the app closed (Reminders.java), so the
// app plans the next week's reminders whenever it goes to the background, each with the
// counts it will have if nothing is studied till then; opening the app and studying plans
// them again.

import type { Strings } from './strings'
import type { ReminderItem } from './native'

const DAYS = 7

/** What the planner needs from the session. */
export interface ReminderSource {
  countsAt(at: number): { due: number; fresh: number }
  reviewsOn(at: number): number
  streak: number // days in a row, today included once studied
}

/** The reminders for the next week at `minutes` after midnight, from `now`. */
export function planReminders(source: ReminderSource, minutes: number, now: number, t: Strings['reminder']): ReminderItem[] {
  const today = new Date(now)
  const studiedToday = source.reviewsOn(now) > 0
  const items: ReminderItem[] = []
  for (let i = 0; i < DAYS; i++) {
    const at = new Date(today.getFullYear(), today.getMonth(), today.getDate() + i, Math.floor(minutes / 60), minutes % 60).getTime()
    if (at <= now || (i === 0 && studiedToday)) continue
    const { due, fresh } = source.countsAt(at)
    if (!due && !fresh) continue
    // The streak still alive then: today's, or what today's study carries into tomorrow.
    const streak = i === 0 || (i === 1 && studiedToday) ? source.streak : 0
    const counts = [due ? t.due(due) : '', fresh ? t.fresh(fresh) : '', streak ? t.streak(streak) : ''].filter(Boolean)
    items.push({ at, title: t.title, text: `${counts.join(' · ')}\n${t.notYet}` })
  }
  return items
}
