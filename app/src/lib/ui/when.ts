// A moment near now, said shortly: "today 22:00", "tomorrow 08:00", "Mon 22:00", "24 Nov 22:00".

import { LOCALE } from '../strings'
import { timeOfDay } from './hours.svelte'

/** Calendar days from `now`'s day to `at`'s. */
function daysApart(at: Date, now: Date): number {
  const day = (d: Date) => Date.UTC(d.getFullYear(), d.getMonth(), d.getDate())
  return Math.round((day(at) - day(now)) / 86_400_000)
}

export function nearClock(at: Date, now: Date): string {
  const apart = daysApart(at, now)
  const time = timeOfDay(at)
  if (apart === 0) return `today ${time}`
  if (apart === 1) return `tomorrow ${time}`
  if (apart > 1 && apart < 7) return `${new Intl.DateTimeFormat(LOCALE, { weekday: 'short' }).format(at)} ${time}`
  return `${new Intl.DateTimeFormat(LOCALE, { day: 'numeric', month: 'short' }).format(at)} ${time}`
}

/** A moment in the past, as a date and a time: "20 Nov 2026, 21:04". */
export const longClock = (at: Date): string => `${new Intl.DateTimeFormat(LOCALE, { dateStyle: 'medium' }).format(at)}, ${timeOfDay(at)}`
