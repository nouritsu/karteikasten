// A button that repeats while held: one step on a tap (or Enter), then, held past
// HOLD_MS, a step every REPEAT_MS until it is released or becomes disabled. A press
// that turns into a drag (a swipe, a scrub) neither repeats nor steps. `step` is told
// whether it is a repeat, so what changes with each step can hold back its flourish.

import { SLOP_PX } from './drag'

const HOLD_MS = 450
const REPEAT_MS = 90

export function hold(node: HTMLButtonElement, step: (repeating: boolean) => void) {
  let current = step
  let delay = 0
  let repeat = 0
  let repeated = false // the click that ends a hold, or a drag, must not step once more
  let from: { x: number; y: number } | null = null // where the press began, while pressed

  const stop = () => {
    clearTimeout(delay)
    clearInterval(repeat)
  }
  const release = () => {
    stop()
    from = null
  }
  const down = (event: PointerEvent) => {
    if (event.button !== 0 || node.disabled) return
    repeated = false
    from = { x: event.clientX, y: event.clientY }
    delay = window.setTimeout(() => {
      repeated = true
      repeat = window.setInterval(() => (node.disabled ? stop() : current(true)), REPEAT_MS)
      current(true)
    }, HOLD_MS)
  }
  const drift = (event: PointerEvent) => {
    if (!from || Math.hypot(event.clientX - from.x, event.clientY - from.y) < SLOP_PX) return
    stop()
    repeated = true
  }
  const click = () => {
    if (repeated) repeated = false
    else current(false)
  }

  node.addEventListener('pointerdown', down)
  node.addEventListener('pointermove', drift)
  node.addEventListener('click', click)
  for (const type of ['pointerup', 'pointerleave', 'pointercancel']) node.addEventListener(type, release)
  return {
    update(next: (repeating: boolean) => void) {
      current = next
    },
    destroy() {
      stop()
      node.removeEventListener('pointerdown', down)
      node.removeEventListener('pointermove', drift)
      node.removeEventListener('click', click)
      for (const type of ['pointerup', 'pointerleave', 'pointercancel']) node.removeEventListener(type, release)
    },
  }
}
