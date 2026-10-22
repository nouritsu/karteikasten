// Turns a word's key forms into the short lines the card shows. Only data from
// the deck is arranged here; the labels come from the i18n strings.

import type { Strings } from '../i18n/de'
import type { DeckWord } from '../types'

const AUX_3SG: Record<string, string> = { haben: 'hat', sein: 'ist' }

function one(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value
}

export function keyFormLines(word: DeckWord, t: Strings): string[] {
  const k = word.key_forms
  const f = t.forms
  const flags = new Set(word.flags)
  const lines: string[] = []
  switch (word.pos) {
    case 'noun': {
      if (flags.has('plural_only')) lines.push(f.pluralOnly)
      else if (k.plural) lines.push(`${f.plural} die ${one(k.plural)}`)
      if (k.genitive && !flags.has('plural_only')) {
        lines.push(`${f.genitive} ${word.gender === 'f' ? 'der' : 'des'} ${one(k.genitive)}`)
      }
      if (flags.has('weak_noun')) lines.push(f.weakNoun)
      if (flags.has('singular_only')) lines.push(f.singularOnly)
      break
    }
    case 'verb': {
      const present = [k.er && `er ${one(k.er)}`, k.du && `du ${one(k.du)}`].filter(Boolean)
      if (present.length) lines.push(present.join(' · '))
      // Past forms and the verb's kind share a line, so the card keeps room for the sentence.
      const past: string[] = []
      if (k.praeteritum) past.push(`${f.preterite} ${one(k.praeteritum)}`)
      if (k.partizip2) {
        const aux = (Array.isArray(k.auxiliary) ? k.auxiliary : [k.auxiliary]).filter(Boolean)
        past.push(`${f.perfect} ${aux.map((a) => AUX_3SG[a as string] ?? a).join('/')} ${one(k.partizip2)}`.replace('  ', ' '))
      }
      const kinds = [
        flags.has('separable') && f.separable,
        flags.has('reflexive') && f.reflexive,
        flags.has('strong') && f.strong,
        flags.has('weak') && f.weak,
        flags.has('mixed') && f.mixed,
        flags.has('preterite_present') && f.preteritePresent,
      ].filter((kind): kind is string => Boolean(kind))
      if (past.length || kinds.length) lines.push([...past, ...kinds].join(' · '))
      break
    }
    case 'prep':
    case 'postp': {
      const cases = Array.isArray(k.cases) ? k.cases : []
      if (k.case === 'two-way') lines.push(`${f.governs} ${f.twoWay}`)
      else if (cases.length) lines.push(`${f.governs} ${cases.map((c) => f.cases[c] ?? c).join(' / ')}`)
      if (Array.isArray(k.contractions) && k.contractions.length) lines.push(`${f.contractions}: ${k.contractions.join(', ')}`)
      break
    }
    case 'num': {
      if (k.ordinal) lines.push(`${f.ordinal}: ${one(k.ordinal)}`)
      break
    }
    case 'conj': {
      if (k.conjunction === 'subordinating') lines.push(f.subordinating)
      if (k.conjunction === 'coordinating') lines.push(f.coordinating)
      break
    }
  }
  if (k.comparative && k.superlative) lines.push(`${word.lemma} · ${one(k.comparative)} · ${one(k.superlative)}`)
  if (k.attributive) lines.push(`${f.attributive}: ${one(k.attributive)}`)
  if (flags.has('predicative_only')) lines.push(f.predicativeOnly)
  if (flags.has('context_dependent')) lines.push(f.contextDependent)
  return lines
}

/** Colour token for the article: gender, or the plural-only colour. */
export function genderClass(word: DeckWord): string | null {
  if (word.flags.includes('plural_only')) return 'plural'
  return word.gender ? { m: 'der', f: 'die', n: 'das' }[word.gender] : null
}

/** What the card shows as the word: the lemma, with its article for nouns. */
export function headword(word: DeckWord): { article: string; lemma: string } {
  return { article: word.pos === 'noun' && word.article ? word.article : '', lemma: word.lemma }
}
