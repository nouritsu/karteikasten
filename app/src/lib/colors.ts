// The five colours picked from Catppuccin's accents (D58; catppuccin.com/palette): the
// app's accent and the four gender colours. They are kept as names and resolve to Latte
// or Mocha with the theme (app.css). index.html applies them before the page paints,
// from the copy of the choice in localStorage.

export const ACCENTS = [
  'rosewater',
  'flamingo',
  'pink',
  'mauve',
  'red',
  'maroon',
  'peach',
  'yellow',
  'green',
  'teal',
  'sky',
  'sapphire',
  'blue',
  'lavender',
] as const
export type Accent = (typeof ACCENTS)[number]

/** What can be coloured, each also a CSS variable, --<key>. */
export const COLOR_KEYS = ['accent', 'der', 'die', 'das', 'plural'] as const
export type ColorKey = (typeof COLOR_KEYS)[number]
export type Colors = Record<ColorKey, Accent>

// Plural-only nouns are pink, because mauve is the accent (D30).
export const DEFAULT_COLORS: Colors = { accent: 'mauve', der: 'blue', die: 'red', das: 'green', plural: 'pink' }

const STORAGE_KEY = 'colors'

export const isAccent = (v: unknown): v is Accent => ACCENTS.includes(v as Accent)

/** "mauve" as "Mauve": Catppuccin's names, in English in both languages. */
export const accentName = (accent: Accent): string => accent[0].toUpperCase() + accent.slice(1)

/** Colours read from storage or a backup; each that is not a colour's name falls back to its default. */
export function toColors(v: unknown): Colors {
  const c = (v ?? {}) as Partial<Record<ColorKey, unknown>>
  return Object.fromEntries(COLOR_KEYS.map((key) => [key, isAccent(c[key]) ? c[key] : DEFAULT_COLORS[key]])) as Colors
}

/** The colour `direction` steps from `accent` through the palette, round the ends. */
export function stepAccent(accent: Accent, direction: -1 | 1): Accent {
  return ACCENTS[(ACCENTS.indexOf(accent) + direction + ACCENTS.length) % ACCENTS.length]
}

export const sameColors = (a: Colors, b: Colors): boolean => COLOR_KEYS.every((key) => a[key] === b[key])

/** The rule that points each variable at the colour's name in the palette (--ctp-<name>).
 *  It has the selector of app.css's defaults, so an element with its own theme resolves
 *  the picks in it; being outside their layer, it wins wherever it sits. index.html
 *  builds the same rule. */
export const colorsCss = (colors: Colors): string =>
  `:root,[data-theme]{${COLOR_KEYS.map((key) => `--${key}:var(--ctp-${colors[key]})`).join(';')}}`

/** Applies the colours to the page, and keeps them for the next start's first paint. */
export function applyColors(colors: Colors): void {
  let style = document.getElementById('colors')
  if (!style) {
    style = document.createElement('style')
    style.id = 'colors'
    document.head.append(style)
  }
  const css = colorsCss(colors)
  if (style.textContent !== css) style.textContent = css
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(colors))
  } catch {
    // no storage: the next start paints the defaults until the settings load
  }
}
