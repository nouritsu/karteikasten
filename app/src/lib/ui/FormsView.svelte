<script lang="ts">
  import { i18n } from '../i18n/index.svelte'
  import type { DeckWord } from '../types'
  import { keyFormLines } from './format'

  let { word }: { word: DeckWord } = $props()
  const t = $derived(i18n.t.forms)

  interface DeclensionCell {
    form: string
    article: string | null
  }
  interface DeclensionRow {
    case: string
    singular: DeclensionCell | null
    plural: DeclensionCell | null
  }
  interface PersonRow {
    person: string
    form: string | null
  }
  // Articles, determiners and pronouns: case x gender/number (m f n pl, or sg pl).
  interface CaseTable {
    columns: string[]
    rows: { case: string; cells: (string | null)[] }[]
  }

  const declension = $derived((word.tables.declension as DeclensionRow[] | undefined) ?? [])
  const conjugation = $derived(
    (
      [
        ['present', t.present],
        ['preterite', t.preteriteTable],
        ['imperative', t.imperative],
        ['subjunctive_ii', t.subjunctiveII],
      ] as const
    )
      .map(([key, label]) => ({ label, rows: (word.tables[key] as PersonRow[] | undefined) ?? [] }))
      .filter((table) => table.rows.some((row) => row.form)),
  )
  const caseTable = $derived(word.tables.cases as CaseTable | undefined)
  const lines = $derived(keyFormLines(word, i18n.t))

  function cell(c: DeclensionCell | null): string {
    return c ? [c.article, c.form].filter(Boolean).join(' ') : '–'
  }
</script>

{#each lines as line (line)}<p>{line}</p>{/each}

{#if declension.length}
  <table>
    <thead><tr><th></th><th>{t.singular}</th><th>{t.pluralColumn}</th></tr></thead>
    <tbody>
      {#each declension as row (row.case)}
        <tr><th>{t.caseNames[row.case] ?? row.case}</th><td>{cell(row.singular)}</td><td>{cell(row.plural)}</td></tr>
      {/each}
    </tbody>
  </table>
{/if}

{#if caseTable}
  <table class="cases">
    <thead><tr><th></th>{#each caseTable.columns as column (column)}<th>{t.columns[column] ?? column}</th>{/each}</tr></thead>
    <tbody>
      {#each caseTable.rows as row (row.case)}
        <tr>
          <th>{t.caseNames[row.case] ?? row.case}</th>
          {#each row.cells as form, i (i)}<td>{form ?? '–'}</td>{/each}
        </tr>
      {/each}
    </tbody>
  </table>
{/if}

{#each conjugation as table (table.label)}
  <table>
    <caption>{table.label}</caption>
    <tbody>
      {#each table.rows as row (row.person)}
        <tr><th>{row.person}</th><td>{row.form ?? '–'}</td></tr>
      {/each}
    </tbody>
  </table>
{/each}

{#if !lines.length && !declension.length && !caseTable && !conjugation.length}<p class="muted">{t.none}</p>{/if}

<style>
  p {
    margin: 0 0 0.2em;
  }

  table {
    border-collapse: collapse;
    margin-top: 0.8em;
  }

  caption {
    text-align: left;
    color: var(--muted);
  }

  th,
  td {
    text-align: left;
    padding: 0.1em 1ch 0.1em 0;
    font-weight: normal;
    vertical-align: top;
  }

  th {
    color: var(--muted);
    min-width: 10ch;
  }

  /* Four form columns have to fit the phone's width. */
  .cases th {
    min-width: 0;
  }
</style>
