// The deck as the pipeline's stage 70 writes it (data/dist/deck/<version>/).

export interface Gloss {
  text: string
  tags: string[]
}

export interface Credit {
  source: string
  source_url: string | null
  author: string | null
  license: string | null
  license_url?: string | null
}

export interface Audio extends Credit {
  path: string
  duration_ms: number
  region: string | null // a regional recording, used only when no standard one exists (D24)
}

export interface Sentence {
  id: string
  de: string
  en: string | null
  hl: [number, number]
  source: string
  source_url: string
  author: string | null
  license: string
  native: boolean
  en_author: string | null
  en_license: string | null
}

export type Gender = 'm' | 'f' | 'n'

export interface DeckWord {
  id: string
  rank: number
  lemma: string
  pos: string
  gender: Gender | null
  article: string | null
  token_share: number
  coverage_cum: number
  ipa: string | null
  syllables: string[] | null
  stress_syllable: number | null
  cognate_en: string | null
  flags: string[]
  key_forms: Record<string, string | string[]>
  tables: Record<string, unknown>
  gloss_en: Gloss[]
  gloss_de: Gloss[]
  audio: Audio | null
  sentences: Sentence[]
}

export interface Manifest {
  schema_version: number
  deck_version: string
  n_max: number
  profile: string
  counts: Record<string, number>
}

export interface Deck {
  base: string // URL prefix of the deck version, ends with "/"
  manifest: Manifest
  words: DeckWord[]
}
