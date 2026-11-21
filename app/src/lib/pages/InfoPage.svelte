<script lang="ts">
  import { strings } from '../strings'
  import type { Deck } from '../types'
  import Block from '../ui/Block.svelte'
  import { genderClass, headword } from '../ui/format'
  import Icon from '../ui/Icon.svelte'
  import ShuffleText from '../ui/ShuffleText.svelte'
  import { search } from '../words'

  // Info (D61): the adjective endings, every source with its licence (and, for a word
  // searched for, its own credits), and About with the versions and the credits; Licences
  // opens the third-party notices as a pane.
  let { deck, visible, onLicences }: { deck: Deck; visible: boolean; onLicences: () => void } = $props()
  const t = strings.info

  // Adjective endings: strong, weak and mixed, by case and gender (spec: Info).
  type Declension = 'strong' | 'weak' | 'mixed'
  const DECLENSIONS: Declension[] = ['weak', 'mixed', 'strong']
  const ENDINGS: Record<Declension, string[][]> = {
    strong: [
      ['-er', '-e', '-es', '-e'],
      ['-en', '-e', '-es', '-e'],
      ['-em', '-er', '-em', '-en'],
      ['-en', '-er', '-en', '-er'],
    ],
    weak: [
      ['-e', '-e', '-e', '-en'],
      ['-en', '-e', '-e', '-en'],
      ['-en', '-en', '-en', '-en'],
      ['-en', '-en', '-en', '-en'],
    ],
    mixed: [
      ['-er', '-e', '-es', '-en'],
      ['-en', '-e', '-es', '-en'],
      ['-en', '-en', '-en', '-en'],
      ['-en', '-en', '-en', '-en'],
    ],
  }
  const CASES = ['nominative', 'accusative', 'dative', 'genitive']
  const COLUMNS = ['m', 'f', 'n', 'pl']
  let declension = $state(0)
  const step = (by: -1 | 1) => (declension = (declension + by + DECLENSIONS.length) % DECLENSIONS.length)

  // Sources, from the deck's attribution.json, fetched the first time the page is shown.
  interface Item {
    kind: 'audio' | 'sentence'
    word: string
    author: string | null
    license: string | null
    source: string
    source_url: string | null
    en_author?: string | null
    en_license?: string | null
  }
  interface Source {
    id: string
    name: string
    license: string
    url: string
  }
  let attribution = $state.raw<{ items: Item[]; sources: Source[] } | null>(null)
  let asked = false
  $effect(() => {
    if (!visible || asked) return
    asked = true
    fetch(`${deck.base}attribution.json`)
      .then((response) => response.json())
      .then((data) => (attribution = data))
      .catch(() => (asked = false))
  })

  let query = $state('')
  const match = $derived(query.trim() ? search(deck.words, query)[0] : undefined)
  const credits = $derived(match && attribution ? attribution.items.filter((item) => item.word === match.id) : [])
</script>

<div class="panes">
  <Block title={t.endings} icon="table_chart">
    <div class="pick">
      <button type="button" class="glyph" aria-label={t.previous} onclick={() => step(-1)}>&lt;</button>
      <span class="name"><ShuffleText text={t.declensions[DECLENSIONS[declension]]} /></span>
      <button type="button" class="glyph" aria-label={t.next} onclick={() => step(1)}>&gt;</button>
    </div>
    <table class="endings">
      <thead>
        <tr><th></th>{#each COLUMNS as c (c)}<th>{strings.forms.columns[c]}</th>{/each}</tr>
      </thead>
      <tbody>
        {#each CASES as c, row (c)}
          <tr>
            <th>{strings.forms.caseNames[c]}</th>
            {#each ENDINGS[DECLENSIONS[declension]][row] as ending, col (col)}<td>{ending}</td>{/each}
          </tr>
        {/each}
      </tbody>
    </table>
  </Block>

  <Block title={t.sources} icon="menu_book">
    <label class="search">
      <span class="icon" aria-hidden="true"><Icon name="search" /></span>
      <input type="search" bind:value={query} placeholder={t.searchCredits} aria-label={t.searchCredits} autocapitalize="off" autocomplete="off" spellcheck="false" />
    </label>
    {#if !attribution}
      <p class="muted">{t.loading}</p>
    {:else}
      {#if match}
        {@const head = headword(match)}
        <p class="word">
          {#if head.article}<span class="g-{genderClass(match)}">{head.article}</span>{' '}{/if}{head.lemma}
          <span class="muted">#{match.rank}</span>
        </p>
        {#each credits as item, i (i)}
          <p class="credit">
            <a class="link" href={item.source_url} target="_blank" rel="noopener noreferrer">{item.kind === 'audio' ? t.audio : t.sentence}</a>
            · <span>{item.author ?? item.source}</span> · <span>{item.license ?? '–'}</span>{#if item.en_author}{' · '}<span
                >{t.translation} {item.en_author}</span
              >{/if}
          </p>
        {:else}
          <p class="muted">{t.noCredits}</p>
        {/each}
        <hr class="split" />
      {/if}
      {#each attribution.sources as source (source.id)}
        <p class="source">
          <a class="link" href={source.url} target="_blank" rel="noopener noreferrer">{source.name}</a>
          <span class="muted licence">{source.license}</span>
        </p>
      {/each}
    {/if}
  </Block>

  <Block title={t.about} icon="info">
    <p>Karteikasten {__APP_VERSION__} · {t.deck} {deck.manifest.deck_version}</p>
    <p><span class="muted">{t.font}</span> Iosevka (SIL OFL 1.1)</p>
    <p><span class="muted">{t.colours}</span> Catppuccin (MIT)</p>
    <p><span class="muted">{t.icons}</span> Material Icons (Apache 2.0)</p>
    <p><span class="muted">{t.licences.toLowerCase()}</span> <button type="button" class="link" onclick={onLicences}>{t.notices}</button></p>
  </Block>
</div>

<style>
  p {
    margin: 0.25em 0;
  }

  .pick {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 0 -0.6ch;
  }

  .name {
    flex: 1;
    text-align: center;
  }

  .endings {
    margin-top: 0.2em;
  }

  .endings td,
  .endings thead th {
    min-width: 6ch;
  }

  .endings tbody th {
    padding-right: 2ch;
  }

  .search {
    display: flex;
    align-items: center;
    gap: 0.4ch;
  }

  .search input {
    flex: 1;
    min-width: 0;
  }

  .word {
    margin-top: 0.6em;
  }

  /* A word's credits break between their parts, not inside a name or a licence. */
  .credit span {
    white-space: nowrap;
  }

  /* A source: its name, and its licence on the line below. */
  .source {
    margin: 0.5em 0;
  }

  .licence {
    display: block;
  }
</style>
