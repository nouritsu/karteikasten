<script lang="ts">
  import { LOCALE, strings } from '../strings'
  import type { Session } from '../session.svelte'
  import Block from './Block.svelte'
  import { genderClass } from './format'
  import { timeOfDay } from './hours.svelte'

  let { session }: { session: Session } = $props()
  const t = strings.status
  // Bereit: every field shows dashes at its normal width.
  const dashed = $derived(session.phase === 'ready')
  const word = $derived(session.word)

  function dash(text: string): string {
    return text.replace(/[^#[\]%·:]/g, '-')
  }
  function show(text: string): string {
    return dashed ? dash(text) : text
  }

  const today = $derived(String(session.today).padStart(2, ' '))
  const total = $derived(String(session.total).padStart(3, ' '))
  // Feierabend has no word: its fields stay dashed.
  const rank = $derived(word ? `#${String(word.rank).padStart(3, ' ')}` : '#---')
  const pos = $derived(word ? (strings.pos[word.pos] ?? word.pos) : '-----')
  const article = $derived(word?.pos === 'noun' ? (word.article ?? '') : '')
  const counts = $derived(session.counts)
  const due = $derived(String(counts.due).padStart(2, ' '))
  const fresh = $derived(String(counts.fresh).padStart(2, ' '))
  const streak = $derived(String(session.streak).padStart(2, ' '))
  const coverage = $derived(Math.round(session.coverage * 100))
  const bar = $derived('#'.repeat(Math.round(coverage / (100 / 12))).padEnd(12, '.'))
  const elapsed = $derived(Math.max(0, Math.floor((session.now - session.startedAt) / 1000)))
  const clock = $derived(`${String(Math.floor(elapsed / 60)).padStart(2, '0')}:${String(elapsed % 60).padStart(2, '0')}`)
  const average = $derived(session.average === null ? '--' : String(session.average).padStart(2, ' '))
  // The title's right side: weekday and time of day, never dashed.
  const weekdays = $derived(new Intl.DateTimeFormat(LOCALE, { weekday: 'long' }))
  const now = $derived(new Date(session.now))
  const daytime = $derived(`${weekdays.format(now)} ${timeOfDay(now)}`)
</script>

<Block title={t.title} titleRight={daytime} class="status">
  <p>
    {t.rank} {show(rank)} · {show(pos.padEnd(5, ' '))}
    {#if article}· <span class={dashed ? '' : `g-${genderClass(word!)}`}>{show(article)}</span>{/if}
  </p>
  <p>{t.today} {show(today)} · {t.total} {show(total)}</p>
  <p>{t.due} {show(due)} · {t.new} {show(fresh)} · {t.streak} {show(streak)}</p>
  <!-- The bar's # fill dashes too: show() keeps # only for Rang. -->
  <p>{t.coverage} [{dashed ? '-'.repeat(bar.length) : bar}] {show(String(coverage).padStart(2, ' '))}%</p>
  <p>{t.session} {show(clock)} · {t.average} {show(average)} {t.points}</p>
</Block>

<style>
  :global(.status) {
    justify-content: space-evenly;
  }

  /* No ligatures, so a dashed field shows every dash, where Iosevka would join three
     into a line. */
  p {
    margin: 0;
    white-space: pre;
    font-variant-ligatures: none;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.35;
  }
</style>
