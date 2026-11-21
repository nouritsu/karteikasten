// Text size, Motion, Haptics and Clock (D59). Each can follow the system, which on
// Android is the phone's font size, its "Remove animations", its touch feedback and its
// 24-hour time (SystemPrefsPlugin.java; in a browser, the reduced-motion media query and
// the locale's clock). index.html applies the last text scale and motion before the
// first paint, from the copy kept here.

import { registerPlugin } from '@capacitor/core'

export type TextSize = 'system' | 'small' | 'normal' | 'large'
export const TEXT_SIZES: TextSize[] = ['system', 'small', 'normal', 'large']
export type Switchable = 'system' | 'on' | 'off'
export const SWITCHABLE: Switchable[] = ['system', 'on', 'off']
export type Clock = 'system' | '24h' | '12h'
export const CLOCKS: Clock[] = ['system', '24h', '12h']

const BASE_PX = 16
const SCALES: Record<Exclude<TextSize, 'system'>, number> = { small: 0.875, normal: 1, large: 1.125 }
const STORAGE_KEY = 'display'

/** What Android says; a browser leaves these at their defaults. */
export interface SystemPrefs {
  fontScale: number
  animations: boolean
  haptics: boolean
  clock24: boolean
}

const browser = (): SystemPrefs => ({
  fontScale: 1,
  animations: true,
  haptics: true,
  clock24: !['h11', 'h12'].includes(new Intl.DateTimeFormat(undefined, { hour: 'numeric' }).resolvedOptions().hourCycle ?? ''),
})
const Plugin = registerPlugin<{ get(): Promise<SystemPrefs> }>('SystemPrefs', { web: { get: async () => browser() } })

export async function systemPrefs(): Promise<SystemPrefs> {
  try {
    return await Plugin.get()
  } catch {
    return browser()
  }
}

/** The text's scale for a choice: the phone's font scale for System. */
export const textScale = (size: TextSize, system: SystemPrefs): number => (size === 'system' ? system.fontScale : SCALES[size])

/** Whether motion is held still: Aus, or System when the phone or the browser asks for less. */
export const stillFor = (motion: Switchable, system: SystemPrefs, reduce: boolean): boolean =>
  motion === 'off' || (motion === 'system' && (reduce || !system.animations))

/** Whether to vibrate: An, or System when the phone's touch feedback is on. */
export const buzzFor = (haptics: Switchable, system: SystemPrefs): boolean => haptics === 'on' || (haptics === 'system' && system.haptics)

/** Whether times read on a 12-hour clock: 12 h, or System when the phone keeps one. */
export const twelveFor = (clock: Clock, system: SystemPrefs): boolean => clock === '12h' || (clock === 'system' && !system.clock24)

const REDUCE = '(prefers-reduced-motion: reduce)'
export const reduceQuery = (): MediaQueryList => matchMedia(REDUCE)

/** Sets the text's scale and motion on the page (data-still holds the animations; see
 *  ui/motion.ts), and keeps them for the next start's first paint. */
export function applyDisplay(scale: number, still: boolean): void {
  const root = document.documentElement
  root.style.fontSize = `${BASE_PX * scale}px`
  root.toggleAttribute('data-still', still)
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ scale, still }))
  } catch {
    // no storage: the next start paints at the normal size until the settings load
  }
}
