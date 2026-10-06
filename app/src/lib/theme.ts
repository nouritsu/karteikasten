// Catppuccin Latte (light) and Mocha (dark), with mauve as the accent. index.html
// sets the first theme before the page paints: the saved choice, else Mocha.
// Thema switches between them and saves the choice.

export type Theme = 'latte' | 'mocha'
export const THEMES: Theme[] = ['latte', 'mocha']

export function currentTheme(): Theme {
  return document.documentElement.dataset.theme === 'latte' ? 'latte' : 'mocha'
}

export function applyTheme(theme: Theme): void {
  const root = document.documentElement
  root.dataset.theme = theme
  // The phone's status bar takes the theme's background.
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', getComputedStyle(root).backgroundColor)
}

export function saveTheme(theme: Theme): void {
  localStorage.setItem('theme', theme)
}
