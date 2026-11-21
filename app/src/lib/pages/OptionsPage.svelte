<script lang="ts">
  import { untrack } from 'svelte'
  import { backupJson } from '../background'
  import { COLOR_KEYS } from '../colors'
  import { CLOCKS, SWITCHABLE, TEXT_SIZES } from '../display'
  import { DEFAULT_SCORE, type Hint, type ScoreSettings } from '../engine/score'
  import { LOCALE, strings } from '../strings'
  import { askNotifications, lastExport, type ExportResult } from '../native'
  import { backupName, FOLDER, importBackup, parseBackup, saveBackupFile, type Local } from '../store/backup'
  import type { Store } from '../store/db'
  import { describeSchedule, nextRun, parseSchedule, SCHEDULE_EXAMPLES, ScheduleError } from '../store/schedule'
  import type { Settings } from '../store/settings'
  import type { ThemeChoice } from '../theme'
  import Block from '../ui/Block.svelte'
  import { minutesOfDay } from '../ui/hours.svelte'
  import Icon, { type IconName } from '../ui/Icon.svelte'
  import { unfold } from '../ui/motion'
  import ShuffleText from '../ui/ShuffleText.svelte'
  import Stepper from '../ui/Stepper.svelte'
  import { longClock, nearClock } from '../ui/when'
  import ColoursBlock from './ColoursBlock.svelte'

  // Options (D54–D59, D62, D63): a block a category, in one scrolling column. Settings
  // that are on or off show it in their word, muted when off. Colours unfolds below Theme,
  // pushing the rest down, and folds away when the page is left; so does Score's editor.
  let {
    store,
    settings,
    choice,
    nMax,
    visible,
    onSettings,
    onTheme,
    onImported,
  }: {
    store: Store
    settings: Settings
    choice: ThemeChoice
    nMax: number
    visible: boolean
    onSettings: (patch: Partial<Settings>) => void
    onTheme: (button: HTMLElement) => void
    onImported: (local: Local | null) => void
  } = $props()

  const t = strings.options
  let colours = $state(false)
  let editingScore = $state(false)
  $effect(() => {
    if (!visible) colours = editingScore = false
  })

  const THEME_ICONS: Record<ThemeChoice, IconName> = { mocha: 'dark_mode', latte: 'light_mode', system: 'brightness_auto' }

  // A few choices: the word steps to the next.
  function cycle<K extends 'textSize' | 'motion' | 'haptics' | 'clock'>(key: K, choices: readonly Settings[K][]) {
    onSettings({ [key]: choices[(choices.indexOf(settings[key]) + 1) % choices.length] } as Partial<Settings>)
  }

  // Steppers: a value moved by `by` within its limits, rounded so repeats never drift.
  const clamp = (v: number, min: number, max: number) => Math.min(max, Math.max(min, v))
  const stepBy = (value: number, by: number, min: number, max: number) => clamp(Math.round((value + by) / Math.abs(by)) * Math.abs(by), min, max)

  // Study ---------------------------------------------------------------------------
  const n = $derived(settings.n ?? nMax)
  function stepN(direction: -1 | 1) {
    const next = stepBy(n, 100 * direction, 100, nMax)
    onSettings({ n: next >= nMax ? null : next })
  }
  const percent = (share: number) => `${Math.round(share * 100)}%`
  const STUDY_LABEL = 16 // "New words a day" and a space, so Study's values line up
  const RETENTION = { min: 0.8, max: 0.97 }

  // Score (D17, D39) --------------------------------------------------------------------
  const score = $derived(settings.score)
  const seconds = (ms: number) => (ms / 1000).toLocaleString(LOCALE, { maximumFractionDigits: 1 })
  function setScore(patch: Partial<ScoreSettings>) {
    onSettings({ score: { ...score, ...patch } })
  }
  const HINTS: Hint[] = ['audio', 'forms', 'sentence', 'cognate']
  const sameScore = $derived(JSON.stringify(score) === JSON.stringify(DEFAULT_SCORE))

  // Reminder (D63) --------------------------------------------------------------------
  let reminderNote = $state('')
  async function toggleReminder() {
    if (settings.reminder.on) return onSettings({ reminder: { ...settings.reminder, on: false } })
    const allowed = await askNotifications()
    reminderNote = allowed ? '' : t.reminderDenied
    if (allowed) onSettings({ reminder: { ...settings.reminder, on: true } })
  }

  // Backup (D52, D62) -------------------------------------------------------------------
  let busy = $state(false)
  let message = $state('')
  let lastAt = $state<string | null>(null)
  let picker: HTMLInputElement | undefined = $state()
  let auto = $state<ExportResult | null>(null)

  $effect(() => {
    if (!visible) return
    store.meta<string>('last_export').then((at) => (lastAt = at ?? null))
    void lastExport().then((result) => (auto = result))
  })

  async function run(task: () => Promise<string>) {
    busy = true
    try {
      message = await task()
    } catch (error) {
      message = t.failed(error instanceof Error ? error.message : String(error))
    } finally {
      busy = false
    }
  }

  function exportNow() {
    run(async () => {
      const now = new Date()
      const where = await saveBackupFile(backupName(now, settings.exports.oneFile), await backupJson(store, now))
      await store.setMeta('last_export', now.toISOString())
      lastAt = now.toISOString()
      return t.exported(where)
    })
  }

  function importFile(event: Event) {
    const input = event.currentTarget as HTMLInputElement
    const file = input.files?.[0]
    input.value = '' // the same file can be picked again
    if (!file) return
    run(async () => {
      const backup = parseBackup(await file.text())
      const restore = confirm(t.restoreSettings)
      const result = await importBackup(store, backup, restore)
      onImported(result.local)
      return t.imported(result.added, result.total)
    })
  }

  const where = `Documents/${FOLDER}/`

  // Regular exports: the expression is read as it is typed, and saved once it reads.
  const SAVE_MS = 600
  let every = $state(untrack(() => settings.exports.calendar))
  let saveTimer = 0
  let typing = false
  $effect(() => {
    const saved = settings.exports.calendar
    if (!untrack(() => typing)) every = saved
  })

  const reading = $derived.by(() => {
    try {
      const cal = parseSchedule(every)
      const next = nextRun(cal, new Date())
      return {
        ok: true as const,
        text: `${describeSchedule(cal)}.`,
        next: next ? t.nextRun(nearClock(next, new Date())) : t.never,
      }
    } catch (error) {
      const why = error instanceof ScheduleError ? error.message : String(error)
      return { ok: false as const, text: t.scheduleError(why) }
    }
  })

  function typed() {
    clearTimeout(saveTimer)
    typing = true
    const expression = every.trim()
    if (!reading.ok || expression === settings.exports.calendar) return
    saveTimer = window.setTimeout(() => {
      typing = false
      onSettings({ exports: { ...settings.exports, calendar: expression } })
    }, SAVE_MS)
  }

  function example(text: string) {
    every = text
    typed()
  }

  const autoLine = $derived.by(() => {
    if (!auto) return ''
    const at = longClock(new Date(auto.at))
    return auto.error ? t.lastScheduledFailed(at, auto.error) : t.lastScheduled(at, auto.path ?? '')
  })
</script>

<!-- A setting that is on or off: its name, and the word to press. -->
{#snippet toggle(name: string, on: boolean, flip: () => void, first = false)}
  <div class="row" class:first>
    <span>{name}</span>
    <button type="button" class="word" aria-pressed={on} onclick={flip}><ShuffleText text={on ? t.on : t.off} /></button>
  </div>
{/snippet}

<!-- A setting of a few choices: its name, and the word to press for the next one. -->
{#snippet choose(name: string, shown: string, next: () => void, first = false)}
  <div class="row" class:first>
    <span>{name}</span>
    <button type="button" class="word" aria-label="{name}: {shown}" onclick={next}><ShuffleText text={shown} /></button>
  </div>
{/snippet}

{#snippet scoreEdge()}
  {#if editingScore}
    <button type="button" class="edge" disabled={sameScore} onclick={() => setScore(DEFAULT_SCORE)}
      ><span class="icon" aria-hidden="true"><Icon name="restart_alt" /></span>{t.defaults}</button
    >
    <button type="button" class="edge primary" onclick={() => (editingScore = false)}
      ><span class="icon" aria-hidden="true"><Icon name="check" /></span>{t.done}</button
    >
  {:else}
    <span></span>
    <button type="button" class="edge" onclick={() => (editingScore = true)}
      ><span class="icon" aria-hidden="true"><Icon name="edit" /></span>{t.edit}</button
    >
  {/if}
{/snippet}

<div class="panes">
  <Block title={t.theme} icon="contrast">
    <div class="row first">
      <span>{t.variant}</span>
      <button type="button" class="word" aria-label="{t.variant}: {t.variants[choice]}" onclick={(e) => onTheme(e.currentTarget)}>
        <span class="mark" aria-hidden="true"><Icon name={THEME_ICONS[choice]} /></span><ShuffleText text={t.variants[choice]} />
      </button>
    </div>
    <!-- The whole row opens the block; the button inside is what a keyboard or screen reader finds. -->
    <div class="row" role="presentation" onclick={() => (colours = !colours)}>
      <span>{t.colors}</span>
      <button type="button" class="word" aria-label={t.colors} aria-expanded={colours}>
        {#each COLOR_KEYS as key (key)}<span style:color="var(--{key})" aria-hidden="true">■</span>{/each}
      </button>
    </div>
  </Block>

  {#if colours}
    <div class="unfold" transition:unfold>
      <ColoursBlock colors={settings.colors} onChange={(colors) => onSettings({ colors })} onClose={() => (colours = false)} />
    </div>
  {/if}

  <Block title={t.display} icon="text_fields">
    {@render choose(t.textSize, t.sizes[settings.textSize], () => cycle('textSize', TEXT_SIZES), true)}
    {@render choose(t.motion, t.switchable[settings.motion], () => cycle('motion', SWITCHABLE))}
    {@render choose(t.haptics, t.switchable[settings.haptics], () => cycle('haptics', SWITCHABLE))}
    {@render choose(t.clock, t.clocks[settings.clock], () => cycle('clock', CLOCKS))}
    <p class="muted">{t.displayHelp}</p>
  </Block>

  <Block title={t.study} icon="school">
    <Stepper
      label={t.newPerDay}
      labelWidth={STUDY_LABEL}
      width={3}
      value={String(settings.newPerDay)}
      onStep={(d) => onSettings({ newPerDay: stepBy(settings.newPerDay, d, 0, 50) })}
      atStart={settings.newPerDay <= 0}
      atEnd={settings.newPerDay >= 50}
    />
    <Stepper label={t.vocabulary} labelWidth={STUDY_LABEL} width={9} value={t.top(n)} onStep={stepN} atStart={n <= 100} atEnd={n >= nMax} />
    <Stepper
      label={t.retention}
      labelWidth={STUDY_LABEL}
      width={4}
      value={percent(settings.retention)}
      onStep={(d) => onSettings({ retention: clamp(Math.round((settings.retention + d / 100) * 100) / 100, RETENTION.min, RETENTION.max) })}
      atStart={settings.retention <= RETENTION.min}
      atEnd={settings.retention >= RETENTION.max}
    />
    <Stepper
      label={t.learnAhead}
      labelWidth={STUDY_LABEL}
      width={7}
      value={t.minutes(settings.learnAheadMin)}
      onStep={(d) => onSettings({ learnAheadMin: stepBy(settings.learnAheadMin, 5 * d, 0, 60) })}
      atStart={settings.learnAheadMin <= 0}
      atEnd={settings.learnAheadMin >= 60}
    />
    {@render toggle(t.audioAfter, settings.audioAfterAnswer, () => onSettings({ audioAfterAnswer: !settings.audioAfterAnswer }))}
    <p class="muted">{t.learnAheadHelp}</p>
  </Block>

  <Block title={t.score} icon="speed" actions={scoreEdge}>
    {#if editingScore}
      {@const f = t.scoreFields}
      <Stepper label={f.start} labelWidth={10} width={4} value={String(score.start)}
        onStep={(d) => setScore({ start: stepBy(score.start, 5 * d, 50, 100) })} atStart={score.start <= 50} atEnd={score.start >= 100} />
      <Stepper label={f.grace} labelWidth={10} width={6} value={t.seconds(seconds(score.graceMs))}
        onStep={(d) => setScore({ graceMs: stepBy(score.graceMs, 500 * d, 0, 5000) })} atStart={score.graceMs <= 0} atEnd={score.graceMs >= 5000} />
      <Stepper label={f.step} labelWidth={10} width={4} value="−{score.step}"
        onStep={(d) => setScore({ step: stepBy(score.step, d, 1, 20) })} atStart={score.step <= 1} atEnd={score.step >= 20} />
      <Stepper label={f.interval} labelWidth={10} width={6} value={t.seconds(seconds(score.intervalMs))}
        onStep={(d) => setScore({ intervalMs: stepBy(score.intervalMs, 500 * d, 500, 5000) })} atStart={score.intervalMs <= 500} atEnd={score.intervalMs >= 5000} />
      {#each HINTS as hint (hint)}
        <Stepper label={strings.hints[hint]} labelWidth={10} width={4} value="−{score.penalties[hint]}"
          onStep={(d) => setScore({ penalties: { ...score.penalties, [hint]: stepBy(score.penalties[hint], 5 * d, 0, 50) } })}
          atStart={score.penalties[hint] <= 0} atEnd={score.penalties[hint] >= 50} />
      {/each}
      <Stepper label={f.easy} labelWidth={10} width={4} value={String(score.bands.easy)}
        onStep={(d) => setScore({ bands: { ...score.bands, easy: stepBy(score.bands.easy, 5 * d, score.bands.good + 5, 100) } })}
        atStart={score.bands.easy <= score.bands.good + 5} atEnd={score.bands.easy >= 100} />
      <Stepper label={f.good} labelWidth={10} width={4} value={String(score.bands.good)}
        onStep={(d) => setScore({ bands: { ...score.bands, good: stepBy(score.bands.good, 5 * d, 5, score.bands.easy - 5) } })}
        atStart={score.bands.good <= 5} atEnd={score.bands.good >= score.bands.easy - 5} />
    {:else}
      <p>{t.scoreRate(score.start, seconds(score.graceMs), score.step, seconds(score.intervalMs))}</p>
      <!-- A hint's name and its cost stay together when the line breaks. -->
      <p class="parts">
        {#each HINTS as hint, i (hint)}{#if i}{' · '}{/if}<span>{strings.hints[hint]} −{score.penalties[hint]}</span>{/each}
      </p>
      <p>{t.scoreBands(score.bands.easy, score.bands.good)}</p>
    {/if}
  </Block>

  <Block title={t.reminder} icon="notifications">
    {@render toggle(t.reminder, settings.reminder.on, toggleReminder, true)}
    <Stepper
      label={t.reminderAt}
      labelWidth={4}
      width={8}
      value={minutesOfDay(settings.reminder.at)}
      onStep={(d) => onSettings({ reminder: { ...settings.reminder, at: stepBy(settings.reminder.at, 15 * d, 0, 24 * 60 - 15) } })}
      atStart={settings.reminder.at <= 0}
      atEnd={settings.reminder.at >= 24 * 60 - 15}
    />
    <p class="muted">{t.reminderHelp}</p>
    {#if reminderNote}<p class="problem" role="status">{reminderNote}</p>{/if}
  </Block>

  <Block title={t.backup} icon="backup">
    <p class="muted">{lastAt ? t.lastExport(longClock(new Date(lastAt))) : t.neverExported}</p>
    <div class="pair">
      <button type="button" class="word lead" disabled={busy} onclick={exportNow}
        ><span class="icon" aria-hidden="true"><Icon name="download" /></span>{t.export}</button
      >
      <button type="button" class="word" disabled={busy} onclick={() => picker?.click()}
        ><span class="icon" aria-hidden="true"><Icon name="upload" /></span>{t.import}</button
      >
    </div>
    <input bind:this={picker} type="file" accept="application/json,.json" hidden onchange={importFile} />
    {#if message}<p class="message" role="status">{message}</p>{/if}
    <p class="muted">{t.importHelp}</p>

    <hr class="split" />
    {@render toggle(t.oneFile, settings.exports.oneFile, () => onSettings({ exports: { ...settings.exports, oneFile: !settings.exports.oneFile } }))}
    <p class="muted path">{settings.exports.oneFile ? t.oneFileHelp(`${where}${backupName(new Date(), true)}`) : t.dailyFileHelp(where)}</p>
    {@render toggle(t.scheduled, settings.exports.scheduled, () => onSettings({ exports: { ...settings.exports, scheduled: !settings.exports.scheduled } }))}
    <label class="when">
      <span>{t.every}</span>
      <input
        type="text"
        bind:value={every}
        oninput={typed}
        onblur={() => (typing = false)}
        autocapitalize="off"
        autocomplete="off"
        spellcheck="false"
        aria-describedby="when-reads"
      />
    </label>
    <p id="when-reads" class:problem={!reading.ok} role="status">
      {reading.text}{#if reading.ok && settings.exports.scheduled}{' '}<span class="muted">{reading.next}</span>{/if}
    </p>
    <div class="examples">
      {#each SCHEDULE_EXAMPLES as text (text)}<button type="button" class="link" onclick={() => example(text)}>{text}</button>{/each}
    </div>
    {#if autoLine}<p class="muted message">{autoLine}</p>{/if}
  </Block>

  <Block title={t.privacy} icon="lock">
    {@render toggle(t.cloudBackup, settings.cloudBackup, () => onSettings({ cloudBackup: !settings.cloudBackup }), true)}
    <p class="muted">{t.cloudHelp}</p>
  </Block>
</div>

<style>
  .row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 0.4em;
  }

  .row.first {
    margin-top: 0;
  }

  p {
    margin: 0.3em 0;
  }

  hr.split {
    margin-top: 0.8em;
  }

  /* A Material icon at the start of a word button. */
  .mark {
    margin-right: 0.6ch;
  }

  .pair {
    display: flex;
    gap: 3ch;
  }

  .message,
  .path {
    overflow-wrap: anywhere;
  }

  .parts span {
    white-space: nowrap;
  }

  .when {
    display: flex;
    align-items: center;
    gap: 1ch;
    margin-top: 0.4em;
  }

  .when input {
    flex: 1;
    min-width: 0;
  }

  /* Example schedules to tap, spaced out, with room round each for a finger. */
  .examples {
    display: flex;
    flex-wrap: wrap;
    gap: 0 2ch;
  }

  .examples button {
    padding: 0.35em 0;
  }

  .problem {
    color: var(--bad);
  }
</style>
