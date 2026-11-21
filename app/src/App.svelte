<script lang="ts">
  import { onMount, untrack } from 'svelte'
  import { syncBackground } from './lib/background'
  import { applyColors } from './lib/colors'
  import { applyDisplay, buzzFor, reduceQuery, stillFor, systemPrefs, textScale, twelveFor, type SystemPrefs } from './lib/display'
  import type { StudyEvent } from './lib/engine/events'
  import type { Hint } from './lib/engine/score'
  import { strings } from './lib/strings'
  import CardPage from './lib/pages/CardPage.svelte'
  import InfoPage from './lib/pages/InfoPage.svelte'
  import OptionsPage from './lib/pages/OptionsPage.svelte'
  import StatsPage from './lib/pages/StatsPage.svelte'
  import WordsPage from './lib/pages/WordsPage.svelte'
  import FormsPane from './lib/panes/FormsPane.svelte'
  import LicencesPane from './lib/panes/LicencesPane.svelte'
  import WordPane from './lib/panes/WordPane.svelte'
  import { Session, type Answer, type Sink } from './lib/session.svelte'
  import type { Local } from './lib/store/backup'
  import { setCloudBackup } from './lib/native'
  import { storeSink, Store } from './lib/store/db'
  import { loadDeck } from './lib/store/deck'
  import { DEFAULT_SETTINGS, type Settings } from './lib/store/settings'
  import {
    currentTheme,
    revealTheme,
    savedChoice,
    saveTheme,
    setTheme,
    shownTheme,
    systemDark,
    THEME_CHOICES,
    watchSystem,
    type ThemeChoice,
  } from './lib/theme'
  import type { Deck } from './lib/types'
  import { carries, drag, resist, type DragOptions } from './lib/ui/drag'
  import { buzz, setHaptics } from './lib/ui/haptics'
  import { hours } from './lib/ui/hours.svelte'
  import { reducedMotion } from './lib/ui/motion'
  import TabBar from './lib/ui/TabBar.svelte'

  // Karteikasten: five pages side by side, switched by the tabs along the bottom or a
  // swipe (D54). Card is the study screen; Stats, Words, Options and Info are
  // columns of blocks. Forms, a word's Word and Info's Licences open as panes hung below
  // their page, which slides up and off the top, pushed by the pane.
  const PAGES = ['card', 'stats', 'words', 'options', 'info'] as const
  type PageId = (typeof PAGES)[number]
  type PaneId = 'forms' | 'word' | 'licences'

  const SHEET_DELAY_MS = 400 // a charged hint shows its deduction before its pane covers it
  const RECHECK_MS = 5000 // on Feierabend, how often to look for a card that came due
  const PANE_OUT_MS = 240 // the page's slide back down when a pane closes (.page's transition)
  const TURN_MS = 400 // past the slide (--slide), which ends it

  let deck = $state<Deck | null>(null)
  let store = $state<Store | null>(null)
  let session = $state<Session | null>(null)
  let settings = $state<Settings>(DEFAULT_SETTINGS)
  let events = $state.raw<StudyEvent[]>([]) // every event, for Stats
  let loaded = $state(false)
  let failed = $state(false)
  let failure = $state('')
  let rebuild = false // a setting that needs a new session (Behaltensrate) waits for the card to end
  let requeue = false // a new limit picks the waiting card again
  let audio: HTMLAudioElement | null = null
  const t = strings

  // The page in view, and the pane open below it.
  let current = $state<PageId>('card')
  const page = $derived(PAGES.indexOf(current))
  const tabs = $derived(PAGES.map((id) => ({ id, label: t.pages[id] })))
  let pane = $state<PaneId | null>(null) // the open pane
  let shownPane = $state<PaneId | null>(null) // the pane drawn; it stays while the page slides back
  let paneHost = $state<PageId | null>(null) // the page it hangs below
  let paneHeight = $state(0) // how far it pushes its page
  let paneTimer = 0
  let wordId = $state<string | null>(null) // the word the Wort pane shows

  // Theme (D58): what Flavour shows, and the theme on screen, which follows it a beat late.
  let choice = $state<ThemeChoice>(savedChoice())
  let theme = $state(currentTheme())
  let switching = false

  // The picked colours, once the settings have loaded; until then the page wears the
  // last ones (index.html).
  $effect(() => {
    if (loaded) applyColors(settings.colors)
  })

  // Text size, motion, haptics and the clock (D59), from the settings and, where they
  // follow the system, what the phone says (read again whenever the app comes back).
  let system = $state<SystemPrefs | null>(null)
  let reduce = $state(reduceQuery().matches)
  const readSystem = () => void systemPrefs().then((prefs) => (system = prefs))
  $effect(() => {
    if (!loaded || !system) return
    applyDisplay(textScale(settings.textSize, system), stillFor(settings.motion, system, reduce))
    setHaptics(buzzFor(settings.haptics, system))
    hours.twelve = twelveFor(settings.clock, system)
  })

  // The study clock runs only while Card is in view and the app is in front.
  const away = () => document.hidden || current !== 'card'
  $effect(() => {
    void current
    untrack(() => session?.visibility(away(), Date.now()))
  })

  /** The session's events go to the store, and into `events` for Stats. */
  function liveSink(s: Store): Sink {
    const base = storeSink(s)
    return {
      add: async (event, state) => {
        events = [...events, event]
        await base.add(event, state)
      },
      pending: base.pending,
    }
  }

  /** A session over every event in the store; the cache is rewritten from its replay. */
  async function newSession(d: Deck, s: Store): Promise<Session> {
    const [saved, all] = await Promise.all([s.settings(), s.events()])
    settings = saved
    events = all
    const next = new Session({ words: d.words, deckVersion: d.manifest.deck_version, settings: saved, events: all, sink: liveSink(s) })
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
    loaded = true
    // Alarms and the cloud backup switch follow the settings from the first start on.
    await setCloudBackup(settings.cloudBackup)
    background()
  }

  /** Hands Android what it needs with the app closed: the backup and export runs, and the
   *  reminders (D62, D63). */
  function background() {
    if (!store || !session) return
    const [s, now] = [store, session]
    syncBackground(s, now, $state.snapshot(settings) as Settings).catch((error) => console.error(error))
  }

  onMount(() => {
    const unwatch = watchSystem(follow)
    follow()
    readSystem()
    const query = reduceQuery()
    const motion = () => (reduce = query.matches)
    query.addEventListener('change', motion)
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
    const visibility = () => {
      session?.visibility(away(), Date.now())
      if (document.hidden) background()
      else readSystem()
    }
    document.addEventListener('visibilitychange', visibility)
    return () => {
      clearInterval(timer)
      unwatch()
      query.removeEventListener('change', motion)
      document.removeEventListener('visibilitychange', visibility)
    }
  })

  /** Runs something that reads or writes storage; a failure shows as an alert. */
  async function attempt(task: () => Promise<void>) {
    try {
      await task()
    } catch (error) {
      failure = `${t.saveFailed} ${error instanceof Error ? error.message : String(error)}`
      setTimeout(() => (failure = ''), 6000)
    }
  }

  // Settings -------------------------------------------------------------------------

  function setSettings(patch: Partial<Settings>) {
    if (patch.retention !== undefined && patch.retention !== settings.retention) rebuild = true
    if (patch.n !== undefined || patch.newPerDay !== undefined || patch.learnAheadMin !== undefined) requeue = true
    settings = { ...settings, ...patch }
    if (session) session.settings = settings
    attempt(async () => {
      await store?.saveSettings($state.snapshot(settings))
      if (patch.cloudBackup !== undefined) await setCloudBackup(patch.cloudBackup)
      await settle()
    })
    if (patch.reminder || patch.exports) background()
  }

  /** Brings the session up to the settings once no card is in progress: a new
   *  Behaltensrate replays every event, and a new limit picks the waiting card again. */
  async function settle() {
    if (!session || !deck || !store) return
    if (session.phase !== 'ready' && session.phase !== 'done') return
    if (rebuild) {
      rebuild = requeue = false
      session = await newSession(deck, store)
    } else if (requeue) {
      requeue = false
      session.advance()
    }
  }

  // The card -------------------------------------------------------------------------

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
      const open = () => openPane('forms')
      if (charged) setTimeout(open, SHEET_DELAY_MS)
      else open()
    }
    return charged
  }

  function onAnswer(answer: Answer) {
    if (!session) return
    session.respond(answer, Date.now())
    buzz(answer === 'know' ? 'ok' : 'bad')
    if (session.settings.audioAfterAnswer) play()
  }

  function onNext() {
    if (!session) return
    audio?.pause()
    closePane()
    session.next()
    if (rebuild || requeue) attempt(settle)
  }

  // Pages and panes ------------------------------------------------------------------

  // The track slides only while a page is turned (a tab, a swipe, or one springing back).
  let turning = $state(false)
  let turnTimer = 0
  function turn() {
    turning = true
    clearTimeout(turnTimer)
    turnTimer = window.setTimeout(() => (turning = false), TURN_MS)
  }

  // A pane belongs to the page it was opened on; turning the page closes it.
  function go(index: number) {
    turn()
    current = PAGES[Math.min(PAGES.length - 1, Math.max(0, index))]
    clearTimeout(paneTimer)
    pane = shownPane = paneHost = null
  }

  /** Hangs the pane below the current page and pushes the page up to show it. */
  function openPane(id: PaneId) {
    clearTimeout(paneTimer)
    pane = shownPane = id
    paneHost = current
  }

  /** Slides the page back down; the pane goes once it is out of sight. */
  function closePane() {
    if (!pane) return
    pane = null
    clearTimeout(paneTimer)
    paneTimer = window.setTimeout(
      () => {
        if (pane) return // another pane opened meanwhile
        shownPane = paneHost = null
      },
      reducedMotion() ? 0 : PANE_OUT_MS,
    )
  }

  /** A word's pane, under Words; from Stats' Trouble words it turns there first. */
  function openWord(id: string) {
    wordId = id
    if (current !== 'words') go(PAGES.indexOf('words'))
    openPane('word')
  }

  // Pages follow a sideways drag and settle on release: on the next page when it went
  // far or fast enough, else back. Past the first or last page the drag resists. The
  // click a swipe ends in is swallowed (drag.ts), so a swipe across Bereit does not start
  // the card.
  let dragX = $state(0)
  let paging = $state(false)
  let pagesEl = $state<HTMLElement>()
  const pastEnd = (dx: number) => (page === 0 && dx > 0) || (page === PAGES.length - 1 && dx < 0)

  const pageDrag: DragOptions = {
    axis: 'x',
    enabled: () => pane === null,
    onStart: () => (paging = true),
    onMove: (dx) => (dragX = resist(dx, pastEnd(dx))),
    onEnd: (dx, velocity) => {
      paging = false
      turn()
      dragX = 0
      if (!pastEnd(dx) && carries(dx, pagesEl?.clientWidth ?? 1, velocity)) go(page + (dx < 0 ? 1 : -1))
    },
  }

  // An open pane follows a drag down, from the pane or from the page above it, and
  // closes when pulled a third of its height or flicked; upwards it barely gives.
  let pull = $state(0)
  let pulling = $state(false)

  const paneDrag: DragOptions = {
    axis: 'y',
    enabled: () => pane !== null,
    onStart: () => (pulling = true),
    onMove: (dy) => (pull = dy > 0 ? dy : dy / 4),
    onEnd: (dy, velocity) => {
      pulling = false
      pull = 0
      if (dy > 0 && carries(dy, paneHeight, velocity, 0.3)) closePane()
    },
  }

  // Theme ----------------------------------------------------------------------------

  // Flavour steps through Mocha, Latte and System. When that changes the theme shown,
  // the button takes the new one first and the page follows in a circle from it (D37).
  function switchTheme(button: HTMLElement) {
    if (switching) return
    choice = THEME_CHOICES[(THEME_CHOICES.indexOf(choice) + 1) % THEME_CHOICES.length]
    saveTheme(choice)
    const shown = shownTheme(choice, systemDark())
    if (shown === theme) return
    switching = true
    theme = shown
    revealTheme(shown, button).finally(() => {
      switching = false
      follow()
    })
  }

  /** Shows what the choice calls for. System follows the device as it changes, at once. */
  function follow() {
    const shown = shownTheme(choice, systemDark())
    if (switching || shown === theme) return
    theme = shown
    setTheme(shown)
  }

  /** After an import: the session starts over from the merged events and settings. */
  async function onImported(local: Local | null) {
    if (!deck || !store) return
    if (local?.theme === 'latte' || local?.theme === 'mocha' || local?.theme === 'system') {
      choice = local.theme
      saveTheme(choice)
      follow()
    }
    await store.settlePending()
    session = await newSession(deck, store)
    background()
  }
</script>

<!-- A pane hangs below the page that opened it; the page slides up by the pane's height to
     show it. Tapping what is left of the page closes it. -->
{#snippet hangingPane(host: PageId)}
  {#if paneHost === host}
    {#if pane}<button
        type="button"
        class="dismiss"
        aria-label={t.close}
        tabindex="-1"
        use:drag={paneDrag}
        onclick={closePane}
      ></button>{/if}
    <div class="hang" bind:offsetHeight={paneHeight} use:drag={paneDrag}>
      <div class="slot">
        {#if shownPane === 'forms' && session?.word}
          <FormsPane word={session.word} onClose={closePane} />
        {:else if shownPane === 'word' && session && wordId}
          <WordPane {session} {events} id={wordId} onClose={closePane} />
        {:else if shownPane === 'licences'}
          <LicencesPane onClose={closePane} />
        {/if}
      </div>
    </div>
  {/if}
{/snippet}

<main class="app">
  <div class="pages" bind:this={pagesEl} use:drag={pageDrag}>
    <div class="track" class:turning class:dragging={paging} style:transform="translateX(calc({-page * 100}% + {dragX}px))">
      {#each PAGES as id (id)}
        <div
          class="page"
          class:pushed={pane !== null && paneHost === id}
          class:pulling={pulling && paneHost === id}
          style:--push="{paneHeight}px"
          style:--pull="{paneHost === id ? pull : 0}px"
          id="page-{id}"
          role="tabpanel"
          aria-labelledby="tab-{id}"
          inert={current !== id}
        >
          <div class="page-main" inert={pane !== null && paneHost === id}>
            {#if failed}
              {#if id === 'card'}<p class="message">{t.loadFailed}</p>{/if}
            {:else if !session || !deck || !store}
              {#if id === 'card'}<p class="message">{t.loading}</p>{/if}
            {:else if id === 'card'}
              <CardPage {session} {onHint} {onAnswer} {onNext} />
            {:else if id === 'stats'}
              <StatsPage
                {session}
                {events}
                {settings}
                visible={current === 'stats'}
                onSettings={setSettings}
                onWord={openWord}
              />
            {:else if id === 'words'}
              <WordsPage {session} onWord={openWord} />
            {:else if id === 'options'}
              <OptionsPage
                {store}
                {settings}
                {choice}
                nMax={deck.manifest.n_max}
                visible={current === 'options'}
                onSettings={setSettings}
                onTheme={switchTheme}
                {onImported}
              />
            {:else if id === 'info'}
              <InfoPage {deck} visible={current === 'info'} onLicences={() => openPane('licences')} />
            {/if}
          </div>
          {@render hangingPane(id)}
        </div>
      {/each}
    </div>
  </div>

  <TabBar {tabs} current={page} label={t.pages.label} onSelect={go} />
</main>

{#if session?.error}<p class="alert" role="alert">{t.saveFailed} {session.error}</p>{/if}
{#if failure}<p class="alert" role="alert">{failure}</p>{/if}

<style>
  /* One column of pages over the tabs; on wide screens a phone-width column. */
  .app {
    height: 100%;
    max-width: var(--column);
    margin-inline: auto;
    display: grid;
    grid-template-rows: minmax(0, 1fr) auto;
    padding: var(--inset-top) 0 var(--inset-bottom);
    box-sizing: border-box;
  }

  /* The pages sit side by side; the track slides to the current one. Vertical
     scrolling stays with the page, horizontal drags come here as swipes. Clipped, not
     hidden: focus moving into a pane must not scroll the track out of line. */
  .pages {
    min-width: 0;
    min-height: 0;
    overflow: clip;
    touch-action: pan-y;
  }

  .track {
    display: flex;
    height: 100%;
  }

  .track.turning {
    transition: transform var(--slide);
  }

  /* Under the finger, the track and a pulled page follow it without easing. */
  .track.dragging,
  .page.pulling {
    transition: none;
  }

  :global(:root[data-still]) .track {
    transition: none;
  }

  /* Room above each block for the titles in its top edge, and below it for the
     buttons in its bottom edge, inside the page so the slide does not clip them. */
  .page {
    flex: 0 0 100%;
    min-width: 0;
    height: 100%;
    box-sizing: border-box;
    padding: 1em 0.6em 1.3em;
    position: relative;
    /* Back down when a pane closes: easing in, like falling back. */
    transition: transform 0.24s cubic-bezier(0.32, 0, 0.67, 0);
  }

  /* A pane hangs below the page (Pane.svelte); opening it pushes the page up by the
     pane's height, the top of the page flowing off the screen. */
  .page.pushed {
    transform: translateY(calc(-1 * var(--push) + var(--pull, 0px)));
    transition: transform 0.32s cubic-bezier(0.33, 1, 0.68, 1);
  }

  .page-main {
    height: 100%;
  }

  /* Just below the page, as tall as its pane, at most the page's height. Vertical
     drags here pull the pane, not scroll (a pane whose content scrolls lets it). */
  .hang {
    touch-action: none;
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    max-height: 100%;
    display: flex;
    flex-direction: column;
  }

  .slot {
    min-height: 0;
    display: flex;
    flex-direction: column;
    background: var(--bg);
  }

  /* What is left of the page above an open pane: a tap there closes the pane, and a
     drag down pulls it. */
  .dismiss {
    touch-action: none;
    position: absolute;
    inset: 0;
    padding: 0;
    background: none;
    border: none;
    border-radius: 0;
  }

  :global(:root[data-still]) .page,
  :global(:root[data-still]) .page.pushed {
    transition: none;
  }

  .message {
    padding: 2em 1ch;
  }
</style>
