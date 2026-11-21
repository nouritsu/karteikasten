<script lang="ts" module>
  export interface Point {
    a: number | null // the bar's height, or the line's value; null leaves a gap
    b?: number // the lower part of a bar, in a lighter tint (new words)
  }
</script>

<script lang="ts">
  // A chart on the text's grid (D60), SVG stretched to the block's width and `rows` lines
  // high: bars (History) or a line (Score), with optional dashed guides (the score bands).
  // A tap or a drag across it picks a point and `onPick` reads it out below; tapping the
  // picked one again lets go. The press is kept from the page, so a sideways drag reads
  // the chart instead of turning the page; up and down still scroll.
  let {
    points,
    kind = 'bars',
    max,
    rows = 4,
    guides = [],
    picked = $bindable(null),
  }: {
    points: Point[]
    kind?: 'bars' | 'line'
    max: number
    rows?: number
    guides?: number[]
    picked?: number | null
  } = $props()

  let svg = $state<SVGSVGElement>()
  const top = $derived(Math.max(1, max))
  const n = $derived(Math.max(1, points.length))
  const y = (v: number) => 100 - (v / top) * 100
  const GAP = 0.18 // of a bar's slot

  // The line runs through the middle of each slot, broken where a point is missing.
  const runs = $derived.by(() => {
    const out: string[] = []
    let run: string[] = []
    points.forEach((p, i) => {
      if (p.a === null) {
        if (run.length) out.push(run.join(' '))
        run = []
      } else run.push(`${i + 0.5},${y(p.a)}`)
    })
    if (run.length) out.push(run.join(' '))
    return out
  })

  let pressing = false
  let moved = false
  let startedOn: number | null = null

  function at(event: PointerEvent): number {
    const box = svg!.getBoundingClientRect()
    return Math.min(n - 1, Math.max(0, Math.floor(((event.clientX - box.left) / box.width) * n)))
  }

  function down(event: PointerEvent) {
    if (event.button !== 0) return
    event.stopPropagation() // not a page swipe
    pressing = true
    moved = false
    startedOn = picked
    picked = at(event)
  }

  function move(event: PointerEvent) {
    if (!pressing) return
    const i = at(event)
    if (i !== picked) moved = true
    picked = i
  }

  function up() {
    if (pressing && !moved && startedOn === picked) picked = null // a tap on the picked one lets go
    pressing = false
  }
</script>

<svg
  bind:this={svg}
  class="chart"
  style:height="{rows * 1.3}em"
  viewBox="0 0 {n} 100"
  preserveAspectRatio="none"
  role="img"
  onpointerdown={down}
  onpointermove={move}
  onpointerup={up}
  onpointercancel={up}
  onpointerleave={up}
>
  {#each guides as g (g)}<line class="guide" x1="0" x2={n} y1={y(g)} y2={y(g)} vector-effect="non-scaling-stroke" />{/each}
  {#if kind === 'bars'}
    {#each points as p, i (i)}
      {#if p.a}
        <g class:dim={picked !== null && picked !== i}>
          <rect class="a" x={i + GAP / 2} width={1 - GAP} y={y(p.a)} height={100 - y(p.a)} />
          {#if p.b}<rect class="b" x={i + GAP / 2} width={1 - GAP} y={y(p.b)} height={100 - y(p.b)} />{/if}
        </g>
      {/if}
    {/each}
  {:else}
    {#each runs as run (run)}<polyline class="line" points={run} vector-effect="non-scaling-stroke" />{/each}
  {/if}
  {#if picked !== null}<rect class="pick" x={picked} width="1" y="0" height="100" />{/if}
</svg>

<style>
  /* A baseline under the bars and the line, so they stand on something. */
  .chart {
    display: block;
    width: 100%;
    margin: 0.3em 0 0.2em;
    border-bottom: 1px solid var(--border);
    touch-action: pan-y;
    overflow: visible;
  }

  .a {
    fill: var(--accent);
  }

  .b {
    fill: color-mix(in srgb, var(--accent) 45%, var(--bg));
  }

  .dim {
    opacity: 0.4;
  }

  .line {
    fill: none;
    stroke: var(--accent);
    stroke-width: 2px;
    stroke-linejoin: round;
  }

  .guide {
    stroke: var(--border);
    stroke-width: 1px;
    stroke-dasharray: 3 3;
  }

  .pick {
    fill: var(--fg);
    opacity: 0.12;
  }
</style>
