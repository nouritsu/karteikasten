// Clock (D59): whether times of day read on a 12-hour clock. App sets it from the setting
// and, for System, from the phone.

export const hours = $state({ twelve: false })

const pad = (n: number) => String(n).padStart(2, '0')

/** "16:04", or "4:04 PM" on a 12-hour clock. */
export function timeOfDay(date: Date, twelve = hours.twelve): string {
  const h = date.getHours()
  if (!twelve) return `${pad(h)}:${pad(date.getMinutes())}`
  return `${h % 12 || 12}:${pad(date.getMinutes())} ${h < 12 ? 'AM' : 'PM'}`
}

/** Minutes after midnight as a time of day: 1140 is "19:00". */
export const minutesOfDay = (minutes: number, twelve = hours.twelve): string =>
  timeOfDay(new Date(2000, 0, 1, Math.floor(minutes / 60), minutes % 60), twelve)
