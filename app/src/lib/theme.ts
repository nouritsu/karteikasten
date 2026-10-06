// Catppuccin Latte (light) and Mocha (dark), with mauve as the accent. index.html
// sets the first theme before the page paints: the saved choice, else Mocha.
// Thema switches between them and saves the choice.

export type Theme = 'latte' | 'mocha'
export const THEMES: Theme[] = ['latte', 'mocha']

const LEAD_MS = 150 // the button shows the new theme this long before the page follows
const GROW_MS = 650
const SHRINK_MS = 650

export function currentTheme(): Theme {
  return document.documentElement.dataset.theme === 'latte' ? 'latte' : 'mocha'
}

export function applyTheme(theme: Theme): void {
  document.documentElement.dataset.theme = theme
}

/** The phone's status bar takes the theme's background. */
export function paintStatusBar(): void {
  const background = getComputedStyle(document.documentElement).backgroundColor
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', background)
}

export function saveTheme(theme: Theme): void {
  localStorage.setItem('theme', theme)
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

  origin.dataset.theme = theme
  await new Promise((resolve) => setTimeout(resolve, LEAD_MS))

  const box = origin.getBoundingClientRect()
  const x = box.left + box.width / 2
  const y = box.top + box.height / 2
  const r = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y))
  const grow = theme === 'latte'
  const circles = [`circle(0px at ${x}px ${y}px)`, `circle(${r}px at ${x}px ${y}px)`]

  root.dataset.reveal = grow ? 'grow' : 'shrink'
  try {
    // The old snapshot is taken now, with the button already in the new theme.
    const transition = document.startViewTransition(() => {
      applyTheme(theme)
      delete origin.dataset.theme
    })
    await transition.ready
    // The top of the screen uncovers first when shrinking, last when growing.
    if (!grow) paintStatusBar()
    // fill holds the end circle until the transition is torn down; without it
    // the last frame shows the whole old Latte view again.
    const timing = { fill: 'forwards' } as const
    root.animate(
      { clipPath: grow ? circles : circles.reverse() },
      grow
        ? { ...timing, duration: GROW_MS, easing: 'cubic-bezier(0.4, 0, 0.2, 1)', pseudoElement: '::view-transition-new(root)' }
        : { ...timing, duration: SHRINK_MS, easing: 'cubic-bezier(0.4, 0, 1, 1)', pseudoElement: '::view-transition-old(root)' },
    )
    await transition.finished
  } finally {
    applyTheme(theme)
    delete origin.dataset.theme
    paintStatusBar()
    delete root.dataset.reveal
  }
}
