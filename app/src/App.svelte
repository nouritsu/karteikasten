<script lang="ts">
  import { onMount, tick } from 'svelte'
  import type { Hint } from './lib/engine/score'
  import { i18n, type Lang } from './lib/i18n/index.svelte'
  import { Session, type Answer } from './lib/session.svelte'
  import type { Local } from './lib/store/backup'
  import { storeSink, Store } from './lib/store/db'
  import { loadDeck } from './lib/store/deck'
  import { applyTheme, currentTheme, paintStatusBar, revealTheme, saveTheme, THEMES, type Theme } from './lib/theme'
  import type { Deck } from './lib/types'
  import Card from './lib/ui/Card.svelte'
  import FormsView from './lib/ui/FormsView.svelte'
  import NavBar, { type Screen } from './lib/ui/NavBar.svelte'
  import OptionsView from './lib/ui/OptionsView.svelte'
  import Overlay from './lib/ui/Overlay.svelte'
  import { shuffleChanged, snapshot } from './lib/ui/retext'
  import ScoreBar from './lib/ui/ScoreBar.svelte'
  import StatusBar from './lib/ui/StatusBar.svelte'

  type Sheet = 'forms' | Exclude<Screen, 'theme' | 'lang'>
  const SHEET_DELAY_MS = 400 // a charged hint shows its deduction before its sheet covers it
  const RECHECK_MS = 5000 // on Feierabend, how often to look for a card that came due

  let deck = $state<Deck | null>(null)
  let store = $state<Store | null>(null)
  let session = $state<Session | null>(null)
  let failed = $state(false)
  let theme = $state(currentTheme()) // what the Thema button shows; the page follows
  let switching = false
  let sheet = $state<Sheet | null>(null)
  let audio: HTMLAudioElement | null = null
  const t = $derived(i18n.t)

  $effect(() => {
    document.documentElement.lang = i18n.lang
  })

  /** A session over every event in the store; the cache is rewritten from its replay. */
  async function newSession(d: Deck, s: Store): Promise<Session> {
    const next = new Session({
      words: d.words,
      deckVersion: d.manifest.deck_version,
      settings: await s.settings(),
      events: await s.events(),
      sink: storeSink(s),
    })
    void s.putStates(next.states)
    return next
  }

  async function start() {
    const [d, s] = await Promise.all([loadDeck(), Store.open()])
    await s.settlePending() // an answer left open when the app was closed
    if (!(await s.meta('persist_asked'))) {
      // Ask the WebView not to evict the database under storage pressure.
      await navigator.storage?.persist?.().catch(() => false)
      await s.setMeta('persist_asked', true)
    }
    deck = d
    store = s
    session = await newSession(d, s)
  }

  onMount(() => {
    start().catch((error) => {
      console.error(error)
      failed = true
    })
    let ticks = 0
    const timer = setInterval(() => {
      if (!session) return
      session.now = Date.now()
      if (session.phase === 'done' && ++ticks % (RECHECK_MS / 200) === 0) session.advance()
    }, 200)
    const visibility = () => session?.visibility(document.hidden, Date.now())
    document.addEventListener('visibilitychange', visibility)
    return () => {
      clearInterval(timer)
      document.removeEventListener('visibilitychange', visibility)
    }
  })

  function play() {
    const word = session?.word
    if (!deck || !word?.audio) return
    audio?.pause()
    audio = new Audio(deck.base + word.audio.path)
    audio.play().catch(() => {})
  }

  /** Returns whether the hint cost points: only while the clock runs, and only once. */
  function onHint(hint: Hint): boolean {
    if (!session) return false
    const charged = session.use(hint)
    if (hint === 'audio') play()
    if (hint === 'forms') {
      const open = () => (sheet = hint)
      if (charged) setTimeout(open, SHEET_DELAY_MS)
      else open()
    }
    return charged
  }

  function onAnswer(answer: Answer) {
    if (!session) return
    session.respond(answer, Date.now())
    if (session.settings.haptics) navigator.vibrate?.(answer === 'know' ? 30 : [30, 70, 30])
    if (session.settings.audioAfterAnswer) play()
  }

  function onNext() {
    if (!session) return
    audio?.pause()
    session.next()
  }

  function onOpen(screen: Screen, button: HTMLElement) {
    if (screen === 'theme') switchTheme(button)
    else if (screen === 'lang') switchLanguage()
    else sheet = screen
  }

  // The button takes the new theme first, then the page follows in a circle from it.
  function switchTheme(button: HTMLElement) {
    if (switching) return
    switching = true
    theme = THEMES[(THEMES.indexOf(theme) + 1) % THEMES.length]
    saveTheme(theme)
    revealTheme(theme, button).finally(() => (switching = false))
  }

  // The UI text that changes shuffles into the other language; German content stays.
  async function switchLanguage() {
    const before = snapshot(document.body)
    i18n.lang = i18n.lang === 'de' ? 'en' : 'de'
    await tick()
    shuffleChanged(document.body, before)
  }

  /** After an import: the session starts over from the merged events and settings. */
  async function onImported(local: Local | null) {
    if (!deck || !store) return
    if (local?.lang === 'de' || local?.lang === 'en') i18n.lang = local.lang as Lang
    if (local?.theme === 'latte' || local?.theme === 'mocha') {
      theme = local.theme as Theme
      saveTheme(theme)
      applyTheme(theme)
      paintStatusBar()
    }
    await store.settlePending()
    session = await newSession(deck, store)
  }

  function sheetTitle(s: Sheet): string {
    if (s === 'forms') return t.forms.title
    return t.nav[s]
  }
</script>

{#if failed}
  <p class="message">{t.loadFailed}</p>
{:else if !session}
  <p class="message">{t.loading}</p>
{:else}
  <main class="layout">
    <StatusBar {session} />
    <Card {session} {onHint} />
    <ScoreBar {session} {onAnswer} {onNext} />
    <NavBar {theme} {onOpen} />
  </main>
  {#if session.error}<p class="error" role="alert">{t.saveFailed} {session.error}</p>{/if}
{/if}

{#if sheet}
  <Overlay title={sheetTitle(sheet)} onClose={() => (sheet = null)}>
    {#if sheet === 'forms' && session?.word}
      <FormsView word={session.word} />
    {:else if sheet === 'options' && store}
      <OptionsView {store} {onImported} />
    {:else}
      <p>{t.later}</p>
    {/if}
  </Overlay>
{/if}

<style>
  .layout {
    height: 100%;
    display: grid;
    /* Menü takes the one row it needs and the card the space it frees; status
       and score never shrink below their content. */
    grid-template-rows: minmax(min-content, 20fr) 60fr minmax(min-content, 10fr) auto;
    gap: 1em;
    padding: calc(1em + var(--inset-top)) 0.6em calc(0.6em + var(--inset-bottom));
    box-sizing: border-box;
  }

  .message {
    padding: 2em 1ch;
  }

  .error {
    position: fixed;
    inset: auto 0.6em calc(0.6em + var(--inset-bottom));
    margin: 0;
    padding: 0.4em 1ch;
    background: var(--bg);
    border: 1px solid var(--band-hard);
    color: var(--band-hard);
  }
</style>
