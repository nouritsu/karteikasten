<script lang="ts">
  import { onMount, tick } from 'svelte'
  import type { Hint } from './lib/engine/score'
  import { i18n } from './lib/i18n/index.svelte'
  import { Session, type Answer } from './lib/session.svelte'
  import { loadDeck } from './lib/store/deck'
  import { currentTheme, revealTheme, saveTheme, THEMES } from './lib/theme'
  import type { Deck } from './lib/types'
  import Card from './lib/ui/Card.svelte'
  import FormsView from './lib/ui/FormsView.svelte'
  import NavBar, { type Screen } from './lib/ui/NavBar.svelte'
  import Overlay from './lib/ui/Overlay.svelte'
  import { shuffleChanged, snapshot } from './lib/ui/retext'
  import ScoreBar from './lib/ui/ScoreBar.svelte'
  import StatusBar from './lib/ui/StatusBar.svelte'

  type Sheet = 'forms' | 'picture' | Exclude<Screen, 'theme' | 'lang'>
  const AUTOPLAY = true // "audio after answering" becomes a setting in Phase 6
  const SHEET_DELAY_MS = 400 // a charged hint shows its deduction before its sheet covers it

  const session = new Session()
  let deck = $state<Deck | null>(null)
  let failed = $state(false)
  let theme = $state(currentTheme()) // what the Thema button shows; the page follows
  let switching = false
  let sheet = $state<Sheet | null>(null)
  let audio: HTMLAudioElement | null = null
  const t = $derived(i18n.t)

  $effect(() => {
    document.documentElement.lang = i18n.lang
  })

  // Ask for every media file once so the service worker keeps it for offline use.
  function warm(d: Deck) {
    for (const word of d.words) {
      for (const item of [word.audio, word.image]) if (item) fetch(d.base + item.path).catch(() => {})
    }
  }

  onMount(() => {
    loadDeck()
      .then((d) => {
        deck = d
        session.words = d.words
        warm(d)
      })
      .catch(() => (failed = true))
    const tick = setInterval(() => (session.now = Date.now()), 200)
    const visibility = () => session.visibility(document.hidden, Date.now())
    document.addEventListener('visibilitychange', visibility)
    return () => {
      clearInterval(tick)
      document.removeEventListener('visibilitychange', visibility)
    }
  })

  function play() {
    const word = session.word
    if (!deck || !word?.audio) return
    audio?.pause()
    audio = new Audio(deck.base + word.audio.path)
    audio.play().catch(() => {})
  }

  /** Returns whether the hint cost points: only while the clock runs, and only once. */
  function onHint(hint: Hint): boolean {
    const charged = session.use(hint)
    if (hint === 'audio') play()
    if (hint === 'forms' || hint === 'picture') {
      const open = () => (sheet = hint)
      if (charged) setTimeout(open, SHEET_DELAY_MS)
      else open()
    }
    return charged
  }

  function onAnswer(answer: Answer) {
    session.respond(answer, Date.now())
    navigator.vibrate?.(answer === 'know' ? 30 : [30, 70, 30])
    if (AUTOPLAY) play()
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

  function sheetTitle(s: Sheet): string {
    if (s === 'forms') return t.forms.title
    if (s === 'picture') return t.picture.title
    return t.nav[s]
  }
</script>

{#if failed}
  <p class="message">{t.loadFailed}</p>
{:else if !deck}
  <p class="message">{t.loading}</p>
{:else}
  <main class="layout">
    <StatusBar {session} />
    <Card {session} {onHint} />
    <ScoreBar {session} {onAnswer} />
    <NavBar {theme} {onOpen} />
  </main>
{/if}

{#if sheet}
  <Overlay title={sheetTitle(sheet)} onClose={() => (sheet = null)}>
    {#if sheet === 'forms' && session.word}
      <FormsView word={session.word} />
    {:else if sheet === 'picture' && session.word?.image && deck}
      {@const image = session.word.image}
      <figure>
        <img src={deck.base + image.path} alt={session.word.lemma} />
        <figcaption class="muted">
          {image.source}{image.author ? ` · ${image.author}` : ''} · {image.license}
          {#if !image.approved}<br />({t.picture.unapproved}){/if}
        </figcaption>
      </figure>
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
    padding: 1em 0.6em calc(0.6em + env(safe-area-inset-bottom));
    box-sizing: border-box;
  }

  .message {
    padding: 2em 1ch;
  }

  figure {
    margin: 0;
    text-align: center;
  }

  img {
    width: min(60vw, 256px);
    height: auto;
  }
</style>
