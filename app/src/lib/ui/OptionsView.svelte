<script lang="ts">
  // Optionen, Phase 5 part: export and import (spec: Export and import). The other
  // options come with the screens in Phase 6.
  import { ulid } from '../engine/events'
  import { i18n } from '../i18n/index.svelte'
  import { backupName, importBackup, makeBackup, parseBackup, saveBackupFile, type Local } from '../store/backup'
  import type { Store } from '../store/db'
  import { currentTheme } from '../theme'

  let { store, onImported }: { store: Store; onImported: (local: Local | null) => void } = $props()

  const t = $derived(i18n.t.options)
  let busy = $state(false)
  let message = $state('')
  let lastExport = $state<string | null>(null)
  let picker: HTMLInputElement | undefined = $state()

  $effect(() => {
    store.meta<string>('last_export').then((at) => (lastExport = at ?? null))
  })

  const lastLine = $derived(
    lastExport
      ? t.lastExport(new Intl.DateTimeFormat(i18n.lang, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(lastExport)))
      : t.neverExported,
  )

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
      const deviceId = await store.deviceId(() => ulid())
      const backup = await makeBackup(store, deviceId, { lang: i18n.lang, theme: currentTheme() }, now)
      const where = await saveBackupFile(backupName(now), JSON.stringify(backup))
      await store.setMeta('last_export', now.toISOString())
      lastExport = now.toISOString()
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
      const settings = confirm(t.restoreSettings)
      const result = await importBackup(store, backup, settings)
      onImported(result.local)
      return t.imported(result.added, result.total)
    })
  }
</script>

<section>
  <h3>{t.backup}</h3>
  <p class="muted">{lastLine}</p>
  <div class="row">
    <button type="button" disabled={busy} onclick={exportNow}>{t.export}</button>
    <button type="button" disabled={busy} onclick={() => picker?.click()}>{t.import}</button>
  </div>
  <input bind:this={picker} type="file" accept="application/json,.json" hidden onchange={importFile} />
  {#if message}<p class="message">{message}</p>{/if}
  <p class="muted">{t.rest}</p>
</section>

<style>
  h3 {
    margin: 0 0 0.3em;
    font-size: 1em;
    color: var(--accent);
  }

  p {
    margin: 0.3em 0;
  }

  .row {
    display: flex;
    gap: 1ch;
  }

  .row button {
    flex: 1;
  }

  .message {
    overflow-wrap: anywhere;
  }
</style>
