<script lang="ts">
  // A share as a bar (Stats' Recall and Coverage): the filled part in the accent over a
  // track in the button colour, a text line high. It fills the width it is given.
  let { share, label }: { share: number; label?: string } = $props()
  const percent = $derived(Math.max(0, Math.min(1, share)) * 100)
</script>

<span class="meter" role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(percent)} aria-label={label}
  ><span class="fill" style:width="{percent}%"></span></span
>

<style>
  .meter {
    display: block;
    height: 0.7em;
    border-radius: 0.2em;
    background: var(--button);
    overflow: hidden;
  }

  .fill {
    display: block;
    height: 100%;
    background: var(--accent);
    border-radius: 0.2em;
  }
</style>
