<script lang="ts">
  import { onMount } from 'svelte'
  import { strings } from '../strings'
  import Pane from '../ui/Pane.svelte'

  // Licences (D61): the third-party notices the build bundles (nix/app.nix), as plain text.
  // Shown here, not opened as a page: the WebView would load it in place, with no way back.
  let { onClose }: { onClose: () => void } = $props()

  let text = $state<string | null>(null)
  let missing = $state(false)

  onMount(() => {
    fetch('/THIRD_PARTY_NOTICES.md')
      .then(async (response) => {
        const body = await response.text()
        // A development server answers a missing file with the app's own page.
        if (!response.ok || /^\s*<!doctype html/i.test(body)) throw new Error('missing')
        text = body
      })
      .catch(() => (missing = true))
  })
</script>

<Pane title={strings.info.licences} icon="gavel" {onClose}>
  {#if text !== null}
    <pre class="notices">{text}</pre>
  {:else if missing}
    <p class="muted">{strings.info.noNotices}</p>
  {:else}
    <p class="muted">…</p>
  {/if}
</Pane>

<style>
  /* Wrapped to the pane's width: the pane scrolls up and down only. */
  .notices {
    margin: 0.3em 0;
    font: inherit;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
  }
</style>
