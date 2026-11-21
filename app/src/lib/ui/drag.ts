// Drags and swipes. A drag commits to an axis once it has moved past a small slop, so
// a vertical scroll never turns a page and a sideways swipe never scrolls; the `drag`
// action then follows it along that axis and reports where and how fast it ended.

export type Axis = 'x' | 'y'

export const SLOP_PX = 10 // a press that moves less than this is still a tap

/** The axis a drag has committed to, or null while it is within the slop. */
export function lockAxis(dx: number, dy: number, slop = SLOP_PX): Axis | null {
  if (Math.hypot(dx, dy) < slop) return null
  return Math.abs(dx) > Math.abs(dy) ? 'x' : 'y'
}

/** Past an end, a drag moves a third as far: the edge gives, but resists. */
export const resist = (offset: number, pastEnd: boolean): number => (pastEnd ? offset / 3 : offset)

/** Whether a drag carries through: far enough (a `share` of `size`), or flicked fast
 *  enough (px per ms) in the direction it went. */
export function carries(offset: number, size: number, velocity: number, share = 0.25, speed = 0.4): boolean {
  if (!offset) return false
  return Math.abs(offset) > size * share || (Math.abs(velocity) > speed && Math.sign(velocity) === Math.sign(offset))
}

/** Whole steps a drag has passed, `stepPx` apart, towards zero. */
export const stepsAt = (offset: number, stepPx: number): number => Math.trunc(offset / stepPx)

export interface DragOptions {
  axis: Axis
  /** Whether a drag may start now. */
  enabled?: () => boolean
  /** Keeps the press from outer drags (a list item's swipe inside a swiping page). */
  claim?: boolean
  onStart?: () => void
  /** The offset along the axis, in px, as it moves. */
  onMove: (offset: number) => void
  /** Where it ended and how fast it was going (px per ms); a cancelled drag ends at 0. */
  onEnd: (offset: number, velocity: number) => void
}

/** Follows a drag along one axis. The click a drag would end in is swallowed, so a
 *  swipe across a button does not press it. */
export function drag(node: HTMLElement, options: DragOptions) {
  let opts = options
  let start: { x: number; y: number; id: number } | null = null
  let axis: Axis | null = null
  let offset = 0
  let velocity = 0
  let sample = { at: 0, offset: 0 }
  let dragged = false

  const down = (event: PointerEvent) => {
    dragged = false
    if (event.button !== 0 || (opts.enabled && !opts.enabled())) return
    if (opts.claim) event.stopPropagation()
    start = { x: event.clientX, y: event.clientY, id: event.pointerId }
    axis = null
    offset = velocity = 0
  }

  const move = (event: PointerEvent) => {
    if (!start || event.pointerId !== start.id) return
    const [dx, dy] = [event.clientX - start.x, event.clientY - start.y]
    if (!axis) {
      axis = lockAxis(dx, dy)
      if (!axis) return
      if (axis !== opts.axis) return void (start = null) // the other axis: not ours
      try {
        node.setPointerCapture(event.pointerId)
      } catch {
        // a synthetic or finished pointer: follow it without capture
      }
      sample = { at: event.timeStamp, offset: 0 }
      opts.onStart?.()
    }
    offset = opts.axis === 'x' ? dx : dy
    const elapsed = event.timeStamp - sample.at
    if (elapsed > 0) {
      // Smoothed over the last few moves, so one jittery sample does not decide a fling.
      velocity = 0.6 * ((offset - sample.offset) / elapsed) + 0.4 * velocity
      sample = { at: event.timeStamp, offset }
    }
    opts.onMove(offset)
  }

  const up = (event: PointerEvent) => {
    if (!start || event.pointerId !== start.id) return
    start = null
    if (axis !== opts.axis) return
    // Only the click this drag ends in, if any: it comes right after pointerup. A
    // touch swipe ends in none, and a later click (a key, a screen reader) must go through.
    dragged = true
    setTimeout(() => (dragged = false))
    opts.onEnd(offset, velocity)
  }

  const cancel = (event: PointerEvent) => {
    if (!start || event.pointerId !== start.id) return
    start = null
    if (axis === opts.axis) opts.onEnd(0, 0)
  }

  const click = (event: MouseEvent) => {
    if (!dragged) return
    dragged = false
    event.stopPropagation()
    event.preventDefault()
  }

  node.addEventListener('pointerdown', down)
  node.addEventListener('pointermove', move)
  node.addEventListener('pointerup', up)
  node.addEventListener('pointercancel', cancel)
  node.addEventListener('click', click, true)
  return {
    update(next: DragOptions) {
      opts = next
    },
    destroy() {
      node.removeEventListener('pointerdown', down)
      node.removeEventListener('pointermove', move)
      node.removeEventListener('pointerup', up)
      node.removeEventListener('pointercancel', cancel)
      node.removeEventListener('click', click, true)
    },
  }
}
