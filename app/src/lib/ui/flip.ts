// The card flip (D38): answering and Weiter turn the card over. A scan line carries
// the Card title to the right edge, shuffling it into its mirror image, and the
// back (the author's name) comes in behind it, every character scrambling as the
// line passes. After a hold, the line carries the title back to the left and the
// new front comes in behind it.

import type { Phase } from '../session.svelte'

export const SWEEP_MS = 400 // one pass of the scan line, matching the title's travel
export const SCRAMBLE_MS = 150 // a character settles this long after the line passed it
export const HOLD_MS = 400 // the back side stays this long
// The line follows the title's K: its centre sits this far in from either edge
// (the title's 0.6ch padding plus half a character). Iosevka's ch is half an em.
export const REACH_CH = 1.1

/** Whether the card turns over between these phases: on answering, and on Weiter
 *  to the next card or to Feierabend. */
export function flips(from: Phase, to: Phase): boolean {
  if (from === 'running') return to === 'answered'
  return from === 'answered' && (to === 'ready' || to === 'done')
}

/** The title as seen from the back: Card → etraK. */
export function mirrored(title: string): string {
  return [...title].reverse().join('')
}

/** The back of every card. */
export const NAME_ART = String.raw`
                         _ _
  _ __   ___  _   _ _ __(_) |_ ___ _   _
 | '_ \ / _ \| | | | '__| | __/ __| | | |
 | | | | (_) | |_| | |  | | |_\__ \ |_| |
 |_| |_|\___/ \__,_|_|  |_|\__|___/\__,_|`.slice(1)
