import type { Deck, DeckWord, Manifest } from '../types'

async function json<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`)
  return (await response.json()) as T
}

/** /deck/latest.json names the current version; its files never change once published. */
export async function loadDeck(root = '/deck/'): Promise<Deck> {
  const latest = await json<{ version: string }>(`${root}latest.json`)
  const base = `${root}${latest.version}/`
  const [manifest, words] = await Promise.all([json<Manifest>(`${base}manifest.json`), json<DeckWord[]>(`${base}words.json`)])
  return { base, manifest, words }
}
