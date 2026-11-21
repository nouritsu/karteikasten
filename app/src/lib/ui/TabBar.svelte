<script lang="ts" module>
  export interface Tab<T extends string = string> {
    id: T
    label: string
  }
</script>

<script lang="ts" generics="T extends string">
  // The pages' names along the bottom (D54), ratatui Tabs style: words between bars, the
  // current one in the accent with a line under it. The line slides to the next page with
  // the pages themselves.
  let {
    tabs,
    current,
    label,
    onSelect,
  }: { tabs: Tab<T>[]; current: number; label: string; onSelect: (index: number) => void } = $props()

  let buttons = $state<HTMLButtonElement[]>([])
  let line = $state({ left: 0, width: 0 })

  $effect(() => {
    const button = buttons[current]
    tabs.map((tab) => tab.label) // measure again when the language changes the words
    if (!button) return
    const measure = () => {
      // The line spans the word only, not the button's padding. Measured on screen
      // against the row: the pressed button's 1px press (a transform) would otherwise
      // make it the word's offset parent, and the line would jump to the far left.
      const word = (button.firstElementChild as HTMLElement).getBoundingClientRect()
      const row = button.parentElement!.getBoundingClientRect()
      line = { left: word.left - row.left, width: word.width }
    }
    measure()
    const observer = new ResizeObserver(measure)
    observer.observe(button.parentElement!)
    observer.observe(button.firstElementChild!)
    return () => observer.disconnect()
  })

  function keydown(event: KeyboardEvent) {
    const step = event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0
    if (!step) return
    event.preventDefault()
    const next = (current + step + tabs.length) % tabs.length
    onSelect(next)
    buttons[next]?.focus()
  }
</script>

<nav class="tabs" aria-label={label}>
  <div class="row" role="tablist" tabindex="-1" onkeydown={keydown}>
    {#each tabs as tab, i (tab.id)}
      {#if i}<span class="bar" aria-hidden="true">│</span>{/if}
      <button
        type="button"
        role="tab"
        id="tab-{tab.id}"
        aria-controls="page-{tab.id}"
        aria-selected={i === current}
        tabindex={i === current ? 0 : -1}
        class:current={i === current}
        bind:this={buttons[i]}
        onclick={() => onSelect(i)}><span>{tab.label}</span></button
      >
    {/each}
    <span class="line" style:transform="translateX({line.left}px)" style:width="{line.width}px" aria-hidden="true"></span>
  </div>
</nav>

<style>
  .tabs {
    padding: 0 0.6ch;
  }

  .row {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  button {
    flex: 1 1 auto;
    padding: 0.7em 0 0.8em;
    background: none;
    border: none;
    border-radius: 0;
    color: var(--muted);
    white-space: nowrap;
    transition: color 0.3s ease;
  }

  button.current {
    color: var(--accent);
  }

  .bar {
    color: var(--border);
    flex: none;
  }

  /* Under the current word; moves with the pages (App's .track). */
  .line {
    position: absolute;
    left: 0;
    bottom: 0.35em;
    height: 2px;
    border-radius: 1px;
    background: var(--accent);
    transition:
      transform var(--slide),
      width var(--slide);
  }

  :global(:root[data-still]) .line {
    transition: none;
  }
</style>
