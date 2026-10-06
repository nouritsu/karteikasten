import { de, type Strings } from './de'
import { en } from './en'

export type Lang = 'de' | 'en'

// The translate button in the Menü switches the whole UI between German (the
// default) and English, and with it the meaning on the card: English glosses and
// sentence translations, or German definitions. The choice is saved.
function saved(): Lang {
  try {
    return localStorage.getItem('lang') === 'en' ? 'en' : 'de'
  } catch {
    return 'de' // no storage (tests)
  }
}

let lang = $state<Lang>(saved())

export const i18n = {
  get t(): Strings {
    return lang === 'de' ? de : en
  },
  get lang(): Lang {
    return lang
  },
  set lang(value: Lang) {
    lang = value
    localStorage.setItem('lang', value)
  },
}
