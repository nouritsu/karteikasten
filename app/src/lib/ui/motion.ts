// Whether motion is held still, and the unfold of a block in a column of panes.

import { cubicOut } from 'svelte/easing'

/** Whether to hold motion still: data-still on the root, which display.ts sets from the
 *  Motion setting (D59; System follows the phone and the browser) and index.html
 *  before the first paint. */
export const reducedMotion = (): boolean =>
  typeof document !== 'undefined' && document.documentElement.hasAttribute('data-still')

const UNFOLD_MS = 240

/** A block that unfolds below the one that opens it (app.css .panes, .unfold): it grows
 *  from nothing and pushes the blocks below it down, and folds back up when it closes. */
export function unfold(node: HTMLElement) {
  const height = node.offsetHeight
  return {
    duration: reducedMotion() ? 0 : UNFOLD_MS,
    easing: cubicOut,
    css: (t: number) => `height: ${t * height}px; overflow: clip`,
  }
}
