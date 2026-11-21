<script lang="ts">
  import { dayKey } from '../engine/day'
  import type { StudyEvent } from '../engine/events'
  import { LOCALE, strings } from '../strings'
  import type { Session } from '../session.svelte'
  import { moveIn, SPANS, STAT_PANES, type Span, type StatPane } from '../stats/panes'
  import {
    addDays,
    analyse,
    bars,
    coverageAt,
    currentStreak,
    grades,
    heatmap,
    leeches,
    MATURE_DAYS,
    priorRange,
    rankBands,
    recall,
    records,
    rhythm,
    spanRange,
    streaks,
    summary,
    type Analysis,
    type Summary,
  } from '../stats/stats'
  import type { Settings } from '../store/settings'
  import Block from '../ui/Block.svelte'
  import Chart from '../ui/Chart.svelte'
  import { genderClass, headword } from '../ui/format'
  import { timeOfDay } from '../ui/hours.svelte'
  import Icon from '../ui/Icon.svelte'
  import Meter from '../ui/Meter.svelte'
  import { unfold } from '../ui/motion'
  import ShuffleText from '../ui/ShuffleText.svelte'
  import Stepper from '../ui/Stepper.svelte'

  // Stats (D60): a column of blocks that scrolls. The span in Overview's top edge sets
  // what the blocks below cover, and Overview sets it against the span before; Records
  // and Trouble words cover all time, Days the last twelve weeks. ⇅ Arrange sets ˄ ˅ ✕ into
  // the blocks' top edges, and a Put away block brings back the ones put away.
  let {
    session,
    events,
    settings,
    visible,
    onSettings,
    onWord,
  }: {
    session: Session
    events: StudyEvent[]
    settings: Settings
    visible: boolean
    onSettings: (patch: Partial<Settings>) => void
    onWord: (id: string) => void
  } = $props()

  const t = strings.stats

  // One replay of every event, redone only while the page is in view.
  let analysis = $state.raw<Analysis | null>(null)
  $effect(() => {
    if (visible) analysis = analyse(events, session.words, session.settings.retention)
  })

  const today = $derived(dayKey(session.now))
  const range = $derived(spanRange(settings.statsSpan, settings.statsRange, today, analysis?.days[0]))
  const prior = $derived(priorRange(settings.statsSpan, range))
  const now = $derived(analysis ? summary(analysis, range) : null)
  const before = $derived(analysis && prior ? summary(analysis, prior) : null)
  const n = $derived(session.settings.n ?? session.words.length)

  // Numbers ----------------------------------------------------------------------------
  const fmt = (v: number, digits = 1) => v.toLocaleString(LOCALE, { maximumFractionDigits: digits })
  const pct = (share: number | null) => (share === null ? '–' : `${Math.round(share * 100)}%`)
  const short = (day: string) =>
    new Intl.DateTimeFormat(LOCALE, { day: 'numeric', month: 'short' }).format(new Date(`${day}T12:00:00`))
  const long = (day: string) => new Intl.DateTimeFormat(LOCALE, { dateStyle: 'medium' }).format(new Date(`${day}T12:00:00`))

  /** ▲ or ▼ beside a value that rose or fell against the span before. */
  function trend(key: keyof Summary): 'up' | 'down' | '' {
    if (!now || !before) return ''
    const [a, b] = [now[key], before[key]]
    if (a === null || b === null || Math.abs(a - b) < 1e-9) return ''
    return a > b ? 'up' : 'down'
  }

  // Span and range ---------------------------------------------------------------------
  let picking = $state(false)
  function pickSpan(span: Span) {
    if (span === 'range') {
      picking = true
      onSettings({ statsSpan: 'range', statsRange: settings.statsRange ?? range })
    } else {
      picking = false
      onSettings({ statsSpan: span })
    }
  }
  function stepRange(end: 'from' | 'to', direction: -1 | 1, repeating: boolean) {
    const r = { ...range }
    r[end] = addDays(r[end], direction * (repeating ? 7 : 1))
    if (r.to > today) r.to = today
    if (r.from > r.to) return
    onSettings({ statsSpan: 'range', statsRange: r })
  }

  // Arranging ------------------------------------------------------------------------------
  let arranging = $state(false)
  $effect(() => {
    if (!visible) arranging = picking = false
  })
  const shown = $derived(settings.statsPanes.filter((id) => !settings.hiddenStats.includes(id)))
  const putAway = (id: StatPane) => onSettings({ hiddenStats: [...settings.hiddenStats, id] })
  const bringBack = (id: StatPane) => onSettings({ hiddenStats: settings.hiddenStats.filter((x) => x !== id) })
  function move(id: StatPane, by: -1 | 1) {
    // Moves past the hidden ones, so a step always shows.
    const order = [...settings.statsPanes]
    const visibleOrder = shown
    const neighbour = visibleOrder[visibleOrder.indexOf(id) + by]
    if (!neighbour) return
    let next = order
    while (next.indexOf(id) !== order.indexOf(neighbour)) next = moveIn(next, id, by)
    onSettings({ statsPanes: next })
  }

  // Blocks' data -----------------------------------------------------------------------
  const history = $derived(analysis ? bars(analysis, range) : [])
  const historyMax = $derived(Math.max(1, ...history.map((b) => b.reviews)))
  let historyPick = $state<number | null>(null)
  let scorePick = $state<number | null>(null)
  let hourPick = $state<number | null>(null)
  const when = (b: { from: string; to: string }) => (b.from === b.to ? short(b.from) : `${short(b.from)}–${short(b.to)}`)

  const answerShares = $derived(analysis ? grades(analysis, range) : null)
  const answers = $derived(answerShares ? answerShares.easy + answerShares.good + answerShares.hard + answerShares.again : 0)
  const bandShares = $derived(
    answerShares && answers
      ? (['easy', 'good', 'hard', 'again'] as const).map((key) => ({ key, share: answerShares[key] / answers }))
      : [],
  )

  const recalled = $derived(analysis ? recall(analysis, range) : null)
  const bands = $derived(rankBands(session.words, session.states, n))
  const knownCount = $derived(bands.reduce((sum, b) => sum + b.known, 0))
  const coverageThen = $derived(analysis ? coverageAt(analysis, addDays(range.from, -1)) : 0)
  const grid = $derived(analysis ? heatmap(analysis, today) : [])
  const runs = $derived(analysis ? streaks(analysis, range) : null)
  const streakNow = $derived(analysis ? currentStreak(analysis, today) : 0)
  const rhythmNow = $derived(analysis ? rhythm(analysis, range) : null)
  const rec = $derived(analysis ? records(analysis) : null)
  const troubles = $derived(leeches(session.words, session.states))

  // Days: a square a day, deeper in the accent the more reviews it had.
  const HEAT_STEPS = [10, 25, 50] // reviews a day where a square gets deeper
  const heat = (reviews: number) => (reviews === 0 ? 0 : 1 + HEAT_STEPS.filter((step) => reviews >= step).length)
  const WEEKDAYS = $derived(
    Array.from({ length: 7 }, (_, i) =>
      new Intl.DateTimeFormat(LOCALE, { weekday: 'short' }).format(new Date(2026, 10, 16 + i)).replace('.', '').slice(0, 2),
    ),
  )
</script>

<!-- The span, in Overview's top edge: the current one in the accent, the others muted. -->
{#snippet spans()}
  <span class="spans">
    {#each SPANS as span (span)}
      <button
        type="button"
        class="span"
        class:current={settings.statsSpan === span}
        aria-pressed={settings.statsSpan === span}
        aria-label={t.spanNames[span]}
        onclick={() => pickSpan(span)}>{#if span === 'range'}<Icon name="event" />{:else}{t.spans[span]}{/if}</button
      >
    {/each}
  </span>
{/snippet}

{#snippet arrange()}
  <button type="button" class="edge" onclick={() => (arranging = !arranging)}
    ><span class="icon" aria-hidden="true"><Icon name="swap_vert" /></span>{t.arrange}</button
  >
{/snippet}

<!-- While arranging, every block below Overview carries its moves in its top edge. -->
{#snippet moves(id: StatPane)}
  <span class="moves">
    <button type="button" class="glyph" aria-label="{t.panes[id]} {t.up}" disabled={shown[0] === id} onclick={() => move(id, -1)}
      ><Icon name="keyboard_arrow_up" /></button
    >
    <button type="button" class="glyph" aria-label="{t.panes[id]} {t.down}" disabled={shown.at(-1) === id} onclick={() => move(id, 1)}
      ><Icon name="keyboard_arrow_down" /></button
    >
    <button type="button" class="glyph quit" aria-label="{t.panes[id]} {t.remove}" onclick={() => putAway(id)}><Icon name="close" /></button>
  </span>
{/snippet}

{#snippet arrangeEdge()}
  <button
    type="button"
    class="edge"
    disabled={settings.hiddenStats.length === 0 && settings.statsPanes.join() === STAT_PANES.join()}
    onclick={() => onSettings({ statsPanes: [...STAT_PANES], hiddenStats: [] })}
    ><span class="icon" aria-hidden="true"><Icon name="restart_alt" /></span>{t.defaults}</button
  >
  <button type="button" class="edge primary" onclick={() => (arranging = false)}
    ><span class="icon" aria-hidden="true"><Icon name="check" /></span>{t.done}</button
  >
{/snippet}

{#snippet closeRange()}
  <button type="button" class="edge quit" onclick={() => (picking = false)}
    ><span class="icon" aria-hidden="true"><Icon name="close" /></span>{strings.close}</button
  >
{/snippet}

{#snippet arrow(key: keyof Summary)}{#if trend(key) === 'up'}<span class="up">{' ▲'}</span>{:else if trend(key) === 'down'}<span
      class="down">{' ▼'}</span
    >{/if}{/snippet}

{#snippet pane(id: StatPane)}
  {#snippet mv()}{@render moves(id)}{/snippet}
  {#if id === 'history'}
    <Block title={t.panes.history} icon="bar_chart" headingRight={arranging ? mv : undefined}
      titleRight={arranging ? '' : t.perDayTitle(fmt(now?.perDay ?? 0))}>
      {#if now?.reviews}
        <span class="muted axis">{historyMax}</span>
        <Chart points={history.map((b) => ({ a: b.reviews, b: b.fresh }))} max={historyMax} bind:picked={historyPick} />
        <p class="muted axis ends"><span>{short(range.from)}</span><span>{short(range.to)}</span></p>
        <p class="read">
          {#if historyPick !== null && history[historyPick]}{t.readBar(when(history[historyPick]), history[historyPick].reviews, history[historyPick].fresh)}{:else}<span class="legend"
              ><span><span class="swatch fill-a"></span>{t.legendReviews}</span><span><span class="swatch fill-b"></span>{t.legendNew}</span></span
            >{/if}
        </p>
      {:else}<p class="muted">{t.empty}</p>{/if}
    </Block>
  {:else if id === 'score'}
    <Block title={t.panes.score} icon="speed" headingRight={arranging ? mv : undefined}
      titleRight={arranging || now?.average == null ? '' : t.averageTitle(Math.round(now.average))}>
      {#if now?.reviews}
        <Chart
          kind="line"
          points={history.map((b) => ({ a: b.average }))}
          max={100}
          guides={[session.settings.score.bands.good, session.settings.score.bands.easy]}
          bind:picked={scorePick}
        />
        <p class="read">
          {#if scorePick !== null && history[scorePick]}{t.readScore(when(history[scorePick]), history[scorePick].average)}{:else}<span
              class="muted">{t.touch}</span
            >{/if}
        </p>
        <div class="bandbar" aria-hidden="true">
          {#each bandShares as band (band.key)}{#if band.share}<span class="band-{band.key}" style:flex-grow={band.share}></span>{/if}{/each}
        </div>
        <div class="legend">
          {#each bandShares as band (band.key)}
            <span><span class="swatch band-{band.key}"></span>{t.bands[band.key]} <span class="value">{pct(band.share)}</span></span>
          {/each}
        </div>
      {:else}<p class="muted">{t.empty}</p>{/if}
    </Block>
  {:else if id === 'retention'}
    <Block title={t.panes.retention} icon="psychology" headingRight={arranging ? mv : undefined}
      titleRight={arranging ? '' : pct(now?.retention ?? null)}>
      {#if recalled && recalled.young.total + recalled.mature.total}
        {@const all = { known: recalled.young.known + recalled.mature.known, total: recalled.young.total + recalled.mature.total }}
        <p>{t.recallLine(all.known, all.total, Math.round(session.settings.retention * 100))}</p>
        <div class="bars">
          {#each [['young', recalled.young], ['mature', recalled.mature]] as const as [key, group] (key)}
            {@const share = group.total ? group.known / group.total : 0}
            <span>{key === 'young' ? t.young : t.mature}</span>
            <Meter {share} label={key === 'young' ? t.young : t.mature} />
            <span class="num">{group.total ? pct(share) : '–'}</span>
          {/each}
        </div>
        <p class="muted">{t.youngHelp(MATURE_DAYS)}</p>
      {:else}<p class="muted">{t.empty}</p>{/if}
    </Block>
  {:else if id === 'coverage'}
    <Block title={t.panes.coverage} icon="pie_chart" headingRight={arranging ? mv : undefined}
      titleRight={arranging ? '' : pct(session.coverage)}>
      <div class="bars">
        {#each bands as band (band.from)}
          <span class="num">{band.from}–{band.to}</span>
          <Meter share={band.total ? band.known / band.total : 0} label="{band.from}–{band.to}" />
          <span class="num">{band.known}</span>
        {/each}
      </div>
      {@const change = Math.round((session.coverage - coverageThen) * 100)}
      <p>{t.known(knownCount, n)}{#if settings.statsSpan !== 'all'}{' · '}{t.since(`${change >= 0 ? '+' : ''}${change}%`, short(range.from))}{/if}</p>
    </Block>
  {:else if id === 'days'}
    <Block title={t.panes.days} icon="calendar_month" headingRight={arranging ? mv : undefined}
      titleRight={arranging ? '' : t.streak(streakNow)}>
      <div class="heat" style:--weeks={grid.length} aria-hidden="true">
        {#each Array(7) as _, d (d)}
          <span class="day muted">{d % 2 === 0 ? WEEKDAYS[d] : ''}</span>
          {#each grid as week, w (w)}
            {@const cell = week[d]}
            <span class="cell level-{cell.future ? 'none' : heat(cell.reviews)}" class:today={cell.day === today}></span>
          {/each}
        {/each}
      </div>
      <div class="legend heat-legend">
        <span><span class="cell level-1"></span>1+</span>
        {#each HEAT_STEPS as step, i (step)}<span><span class="cell level-{i + 2}"></span>{step}+</span>{/each}
        <span class="muted">{t.heatLegend}</span>
      </div>
      {#if runs}<p>{t.bestStreak(runs.best)} · {t.perWeek(fmt(runs.perWeek))}</p>{/if}
    </Block>
  {:else if id === 'rhythm'}
    <Block title={t.panes.rhythm} icon="schedule" headingRight={arranging ? mv : undefined}>
      {#if rhythmNow && rhythmNow.peak !== null}
        <Chart points={rhythmNow.hours.map((a) => ({ a }))} max={Math.max(...rhythmNow.hours)} rows={3} bind:picked={hourPick} />
        <p class="muted axis ends"><span>00</span><span>06</span><span>12</span><span>18</span><span>24</span></p>
        <p class="read">
          {#if hourPick !== null}{t.readHour(timeOfDay(new Date(2000, 0, 1, hourPick)), rhythmNow.hours[hourPick])}{:else}{t.peak(
              timeOfDay(new Date(2000, 0, 1, rhythmNow.peak)),
            )}{/if}
        </p>
        <p>{t.minutes(fmt(rhythmNow.minutesPerDay ?? 0), fmt(rhythmNow.sittingsPerDay ?? 0))}</p>
      {:else}<p class="muted">{t.empty}</p>{/if}
    </Block>
  {:else if id === 'records'}
    <Block title={t.panes.records} icon="emoji_events" headingRight={arranging ? mv : undefined}
      titleRight={arranging ? '' : t.allTime}>
      {#if rec && rec.total}
        <table class="records">
          <tbody>
            {#if rec.streak}<tr><th>{t.recStreak}</th><td>{t.days(rec.streak.days)}</td><td>{short(rec.streak.from)}–{short(rec.streak.to)}</td></tr>{/if}
            {#if rec.mostReviews}<tr><th>{t.recMost}</th><td>{rec.mostReviews.reviews}</td><td>{short(rec.mostReviews.day)}</td></tr>{/if}
            {#if rec.bestAverage}<tr><th>{t.recAverage}</th><td>{Math.round(rec.bestAverage.average)}</td><td>{short(rec.bestAverage.day)}</td></tr>{/if}
            <tr><th>{t.recTotal}</th><td colspan="2">{t.total(rec.total, rec.studiedDays)}</td></tr>
          </tbody>
        </table>
      {:else}<p class="muted">{t.empty}</p>{/if}
    </Block>
  {:else if id === 'leeches'}
    <Block title={t.panes.leeches} icon="warning" headingRight={arranging ? mv : undefined}
      titleRight={arranging ? '' : String(troubles.length)}>
      {#each troubles as { word, lapses } (word.id)}
        {@const head = headword(word)}
        <button type="button" class="trouble" onclick={() => onWord(word.id)}>
          <span><span class="muted">#{word.rank}</span> {#if head.article}<span class="g-{genderClass(word)}">{head.article}</span>{' '}{/if}{head.lemma}</span>
          <span class="muted">{t.forgotten(lapses)}</span>
        </button>
      {:else}
        <p class="muted">{t.noLeeches}</p>
      {/each}
    </Block>
  {/if}
{/snippet}

<div class="panes">
  <Block title={t.overview} icon="insights" headingRight={spans} actions={arrange}>
    {#if now && now.reviews}
      {@const l = t.labels}
      <div class="overview">
        <span><span class="value"><ShuffleText text={String(now.reviews)} /></span> {l.reviews(now.reviews)}{@render arrow('reviews')}</span>
        <span><span class="value"><ShuffleText text={fmt(now.perDay)} /></span> {l.perDay}{@render arrow('perDay')}</span>
        <span><span class="value"><ShuffleText text={String(now.newWords)} /></span> {l.newWords(now.newWords)}{@render arrow('newWords')}</span>
        <span>{l.average} <span class="value"><ShuffleText text={now.average === null ? '–' : String(Math.round(now.average))} /></span>{@render arrow('average')}</span>
        <span>{l.retention} <span class="value"><ShuffleText text={pct(now.retention)} /></span>{@render arrow('retention')}</span>
      </div>
      {#if before}
        <!-- Breaks only between its parts, never inside one. -->
        <p class="muted before">
          <span>{t.before(t.beforeNames[settings.statsSpan] ?? t.beforeNames.range)}</span>
          {#each t.beforeValues(before.reviews, before.average === null ? '–' : String(Math.round(before.average)), pct(before.retention)) as part, i (i)}{#if i}{' · '}{/if}<span
              >{part}</span
            >{/each}
        </p>
      {/if}
    {:else}
      <p class="muted">{t.empty}</p>
    {/if}
  </Block>

  {#if picking}
    <div class="unfold" transition:unfold>
      <Block title={t.range} icon="event" headingRight={closeRange}>
        <Stepper label={t.from} labelWidth={4} width={14} value={long(range.from)} onStep={(d, r) => stepRange('from', d, r)} />
        <Stepper label={t.to} labelWidth={4} width={14} value={long(range.to)} onStep={(d, r) => stepRange('to', d, r)} atEnd={range.to >= today} />
      </Block>
    </div>
  {/if}

  {#if arranging}
    <div class="unfold" transition:unfold>
      <Block title={t.putAway} icon="layers" actions={arrangeEdge}>
        <div class="away">
          {#each settings.hiddenStats as id (id)}
            <button type="button" class="word" onclick={() => bringBack(id)}
              ><span class="icon" aria-hidden="true"><Icon name="add" /></span>{t.panes[id]}</button
            >
          {:else}
            <span class="muted">–</span>
          {/each}
        </div>
      </Block>
    </div>
  {/if}

  {#each shown as id (id)}
    {@render pane(id)}
  {/each}
</div>

<style>
  p {
    margin: 0.25em 0;
  }

  /* The span's words on the border line, a space apart, each with a finger's room. */
  .spans {
    display: inline-flex;
    gap: 0.4ch;
    margin: -0.6em 0;
  }

  .span {
    padding: 0.6em 0.4ch;
    background: var(--bg);
    border: none;
    border-radius: 0;
    color: var(--muted);
  }

  .span.current {
    color: var(--accent);
    font-weight: 700;
  }

  .moves {
    display: inline-flex;
    margin: -0.6em -0.6ch;
    background: var(--bg);
  }

  .moves .glyph {
    min-width: 2em;
    padding: 0.5em 0.3ch;
  }

  .up {
    color: var(--ok);
  }

  .down {
    color: var(--bad);
  }

  .accent {
    color: var(--accent);
  }

  .axis {
    font-size: 0.85em;
  }

  .ends {
    display: flex;
    justify-content: space-between;
    margin: 0;
  }

  .read {
    min-height: 1.3em;
  }

  /* Overview: each value with its label and its change, two to a line. */
  .overview {
    display: grid;
    grid-template-columns: repeat(2, max-content);
    gap: 0.3em 3ch;
    margin-bottom: 0.2em;
  }

  .before {
    margin-top: 0.5em;
  }

  .before span {
    white-space: nowrap;
  }

  /* A legend: each colour's square beside its name, never split across lines. */
  .legend {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25em 2.5ch;
  }

  .legend > span {
    white-space: nowrap;
  }

  .swatch {
    display: inline-block;
    width: 0.75em;
    height: 0.75em;
    margin-right: 0.8ch;
    border-radius: 0.15em;
    vertical-align: -0.05em;
    background: currentColor;
  }

  .fill-a {
    background: var(--accent);
  }

  .fill-b {
    background: color-mix(in srgb, var(--accent) 45%, var(--bg));
  }

  .band-easy {
    color: var(--band-easy);
    background: var(--band-easy);
  }

  .band-good {
    color: var(--band-good);
    background: var(--band-good);
  }

  .band-hard {
    color: var(--band-hard);
    background: var(--band-hard);
  }

  .band-again {
    color: var(--muted);
    background: var(--muted);
  }

  .legend .band-easy,
  .legend .band-good,
  .legend .band-hard,
  .legend .band-again {
    color: inherit;
  }

  /* The answers' shares as one bar across the block, a hairline between them. */
  .bandbar {
    display: flex;
    gap: 2px;
    height: 0.7em;
    margin: 0.5em 0 0.6em;
    border-radius: 0.2em;
    overflow: hidden;
  }

  .bandbar > span {
    flex-basis: 0;
  }

  /* Rows of a label, a meter and a number (Recall, Coverage). */
  .bars {
    display: grid;
    grid-template-columns: max-content minmax(0, 1fr) max-content;
    align-items: center;
    gap: 0.45em 1.5ch;
    margin: 0.4em 0 0.5em;
  }

  .num {
    text-align: right;
    font-variant-numeric: tabular-nums;
  }

  /* Days: twelve weeks of squares, Monday at the top, today's week last. */
  .heat {
    display: grid;
    grid-template-columns: 3ch repeat(var(--weeks), minmax(0, 1fr));
    gap: 3px;
    margin: 0.2em 0 0.5em;
  }

  .day {
    font-size: 0.85em;
    line-height: 1;
    align-self: center;
  }

  .cell {
    display: inline-block;
    aspect-ratio: 1;
    border-radius: 0.15em;
    background: var(--button);
  }

  .heat-legend .cell {
    width: 0.75em;
    margin-right: 0.8ch;
    vertical-align: -0.05em;
  }

  .level-none {
    background: none;
  }

  .level-1 {
    background: color-mix(in srgb, var(--accent) 30%, var(--button));
  }

  .level-2 {
    background: color-mix(in srgb, var(--accent) 55%, var(--button));
  }

  .level-3 {
    background: color-mix(in srgb, var(--accent) 80%, var(--button));
  }

  .level-4 {
    background: var(--accent);
  }

  .today {
    outline: 1px solid var(--fg);
    outline-offset: 1px;
  }

  .records {
    margin-top: 0;
  }

  .trouble {
    display: flex;
    justify-content: space-between;
    gap: 1ch;
    width: 100%;
    padding: 0.25em 0;
    background: none;
    border: none;
    border-radius: 0;
    text-align: left;
  }

  .away {
    display: flex;
    flex-wrap: wrap;
    gap: 0 2ch;
  }
</style>
