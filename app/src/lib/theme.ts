// Catppuccin Latte (light) and Mocha (dark), with mauve as the accent. index.html
// sets the first theme before the page paints: the saved choice, else Mocha.
// Thema switches between them and saves the choice.

import { Capacitor, SystemBars, SystemBarsStyle } from '@capacitor/core'

export type Theme = 'latte' | 'mocha'
export const THEMES: Theme[] = ['latte', 'mocha']

const LEAD_MS = 150 // the button shows the new theme this long before the page follows
const GROW_MS = 650
const SHRINK_MS = 650
const GROW_EASING = [0.4, 0, 0.2, 1] as const // cubic-bezier() control points
const SHRINK_EASING = [0.4, 0, 1, 1] as const
const STEPS = 100 // keyframes per reveal
const MIN_SCALE = 0.001 // the circle is a pixel or two across; the view stops scaling with it here

export function currentTheme(): Theme {
  return document.documentElement.dataset.theme === 'latte' ? 'latte' : 'mocha'
}

export function applyTheme(theme: Theme): void {
  document.documentElement.dataset.theme = theme
}

/** The phone's status bar follows the theme: in the app the page shows through
 *  it and its icons turn light on Mocha, dark on Latte; in a browser it takes
 *  the theme's background. */
export function paintStatusBar(): void {
  if (Capacitor.isNativePlatform()) {
    const style = currentTheme() === 'mocha' ? SystemBarsStyle.Dark : SystemBarsStyle.Light
    void SystemBars.setStyle({ style })
    return
  }
  const background = getComputedStyle(document.documentElement).backgroundColor
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', background)
}

export function saveTheme(theme: Theme): void {
  localStorage.setItem('theme', theme)
}

/** The reveal's keyframes, sampled along its cubic-bezier easing (offsets from the
 *  curve's x, progress from its y): the circle's scale, and its inverse for the
 *  view inside it, so the view stays put. Both scales are linear between
 *  keyframes, where the view drifts by less than a pixel. */
export function revealFrames(grow: boolean): { circle: Keyframe[]; view: Keyframe[] } {
  const [x1, y1, x2, y2] = grow ? GROW_EASING : SHRINK_EASING
  const bezier = (p1: number, p2: number, u: number) => 3 * (1 - u) ** 2 * u * p1 + 3 * (1 - u) * u ** 2 * p2 + u ** 3
  const circle: Keyframe[] = []
  const view: Keyframe[] = []
  for (let i = 0; i <= STEPS; i++) {
    const u = i / STEPS
    const offset = bezier(x1, x2, u)
    const scale = grow ? bezier(y1, y2, u) : 1 - bezier(y1, y2, u)
    circle.push({ offset, transform: `scale(${scale})` })
    view.push({ offset, transform: `scale(${1 / Math.max(scale, MIN_SCALE)})` })
  }
  return { circle, view }
}

/** Switches to `theme` from the button `origin` (D37): the button takes the new
 *  theme first, then a Latte circle grows from it, or the Latte view shrinks
 *  into it and goes out. Without view transitions, or with reduced motion, the
 *  switch is instant. */
export async function revealTheme(theme: Theme, origin: HTMLElement): Promise<void> {
  const root = document.documentElement
  if (!document.startViewTransition || matchMedia('(prefers-reduced-motion: reduce)').matches) {
    applyTheme(theme)
    paintStatusBar()
    return
  }

  const start = performance.now()
  const page = document.body.getBoundingClientRect()
  const box = origin.getBoundingClientRect()
  const x = box.left + box.width / 2 - page.left
  const y = box.top + box.height / 2 - page.top
  const r = Math.hypot(Math.max(x, page.width - x), Math.max(y, page.height - y))
  const grow = theme === 'latte'
  const geometry = { x, y, r, w: page.width, h: page.height }
  for (const [name, px] of Object.entries(geometry)) root.style.setProperty(`--reveal-${name}`, `${px}px`)

  root.dataset.reveal = grow ? 'grow' : 'shrink'
  origin.dataset.theme = theme
  const animations: Animation[] = []
  try {
    // The old snapshot is taken at the next frame, with the button already in the
    // new theme. It stands in for the page through the lead, while the new theme
    // is applied and painted behind it.
    const transition = document.startViewTransition(() => {
      applyTheme(theme)
      delete origin.dataset.theme
    })
    await transition.ready
    const delay = Math.max(0, LEAD_MS - (performance.now() - start))
    const frames = revealFrames(grow)
    // fill holds the first keyframe through the delay, and the last until the
    // transition is torn down; without it the last frame shows the whole old
    // Latte view again. The animations also keep the transition alive through
    // the delay. They are cancelled afterwards, or they would scale the next
    // switch's snapshots too.
    const timing = { duration: grow ? GROW_MS : SHRINK_MS, delay, fill: 'both' } as const
    animations.push(
      root.animate(frames.circle, { ...timing, pseudoElement: '::view-transition-image-pair(latte)' }),
      root.animate(frames.view, { ...timing, pseudoElement: `::view-transition-${grow ? 'new' : 'old'}(latte)` }),
    )
    // The top of the screen uncovers first when shrinking, last when growing.
    if (!grow) {
      await new Promise((resolve) => setTimeout(resolve, delay))
      paintStatusBar()
    }
    await transition.finished
  } finally {
    for (const animation of animations) animation.cancel()
    applyTheme(theme)
    delete origin.dataset.theme
    paintStatusBar()
    delete root.dataset.reveal
    for (const name of Object.keys(geometry)) root.style.removeProperty(`--reveal-${name}`)
  }
}
