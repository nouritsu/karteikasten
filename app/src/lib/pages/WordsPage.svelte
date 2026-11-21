<script lang="ts">
  import { strings } from '../strings'
  import type { Session } from '../session.svelte'
  import Block from '../ui/Block.svelte'
  import { genderClass, headword } from '../ui/format'
  import Icon from '../ui/Icon.svelte'
  import ShuffleText from '../ui/ShuffleText.svelte'
  import { search, statusOf, STATUSES, type WordStatus } from '../words'

  // Words (spec: Words, Suche; D54): one block filling the page. The search field finds
  // words umlaut-tolerantly, three filters step through their values on a tap, and the
  // list scrolls inside the block; a row opens the word's Word pane.
  let { session, onWord }: { session: Session; onWord: (id: string) => void } = $props()
  const t = strings.words

  const SHOWN = 300 // rows drawn at a time; the rest are counted
  const GENDERS = ['der', 'die', 'das', 'plural'] as const

  let query = $state('')
  let status = $state<WordStatus | null>(null)
  let pos = $state<string | null>(null)
  let gender = $state<(typeof GENDERS)[number] | null>(null)

  // Word types by how many words have them, most first.
  const kinds = $derived.by(() => {
    const count = new Map<string, number>()
    for (const word of session.words) count.set(word.pos, (count.get(word.pos) ?? 0) + 1)
    return [...count.entries()].sort((a, b) => b[1] - a[1]).map(([kind]) => kind)
  })

  const n = $derived(session.settings.n ?? session.words.length)
  const found = $derived(
    search(session.words, query).filter(
      (word) =>
        word.rank <= n &&
        (!status || statusOf(session.states.get(word.id)) === status) &&
        (!pos || word.pos === pos) &&
        (!gender || genderClass(word) === gender),
    ),
  )

  /** The next of `values`, then none again ("alle"). */
  function next<T>(values: readonly T[], current: T | null): T | null {
    const i = current === null ? 0 : values.indexOf(current) + 1
    return i < values.length ? values[i] : null
  }
</script>

<Block title={t.title} icon="menu_book" titleRight={String(found.length)} shuffle class="page-block">
  <label class="search">
    <span class="icon" aria-hidden="true"><Icon name="search" /></span>
    <input
      type="search"
      bind:value={query}
      placeholder={t.placeholder}
      aria-label={t.search}
      autocapitalize="off"
      autocomplete="off"
      spellcheck="false"
    />
  </label>
  <div class="filters">
    <span>{t.status}</span>
    <button type="button" class="word" aria-pressed={status !== null} onclick={() => (status = next(STATUSES, status))}
      ><ShuffleText text={status ? t.states[status] : t.all} /></button
    >
    <span>{t.kind}</span>
    <button type="button" class="word" aria-pressed={pos !== null} onclick={() => (pos = next(kinds, pos))}
      ><ShuffleText text={pos ? (strings.pos[pos] ?? pos) : t.all} /></button
    >
    <span>{t.gender}</span>
    <button type="button" class="word" aria-pressed={gender !== null} onclick={() => (gender = next(GENDERS, gender))}
      ><ShuffleText text={gender ? t.genders[gender] : t.all} /></button
    >
  </div>
  <hr class="split" />
  <div class="list scroller">
    {#each found.slice(0, SHOWN) as word (word.id)}
      {@const head = headword(word)}
      {@const st = statusOf(session.states.get(word.id))}
      <button type="button" class="row" onclick={() => onWord(word.id)}>
        <span class="rank muted">#{word.rank}</span>
        <span class="lemma"
          >{#if head.article}<span class="g-{genderClass(word)}">{head.article}</span>{' '}{/if}{head.lemma}</span
        >
        <span class="pos muted">{strings.pos[word.pos] ?? word.pos}</span>
        <span class="state" class:muted={st === 'new' || st === 'paused'}>{t.states[st]}</span>
      </button>
    {:else}
      <p class="muted">{t.none}</p>
    {/each}
    {#if found.length > SHOWN}<p class="muted">{t.more(found.length - SHOWN)}</p>{/if}
  </div>
</Block>

<style>
  .search {
    display: flex;
    align-items: center;
    gap: 0.4ch;
  }

  .search input {
    flex: 1;
    min-width: 0;
  }

  .filters {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0 0.6ch;
    margin-top: 0.3em;
  }

  /* Three filters on one line: brackets tight round the word, as in the mockup. */
  .filters button {
    margin-right: 1ch;
  }

  .filters :global(button.word)::before {
    content: '[';
  }

  .filters :global(button.word)::after {
    content: ']';
  }

  .list {
    padding-top: 0.2em;
  }

  /* A row: rank, the word, its type and its status, in columns. */
  .row {
    display: grid;
    grid-template-columns: 5ch minmax(0, 1fr) auto 8ch;
    column-gap: 1ch;
    width: 100%;
    padding: 0.3em 0;
    background: none;
    border: none;
    border-radius: 0;
    text-align: left;
  }

  .rank {
    text-align: right;
  }

  /* Room between the type and the status, so they read as two columns. */
  .pos {
    margin-right: 1ch;
  }

  .lemma {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .row:active {
    background: var(--button);
    transform: none;
  }
</style>
