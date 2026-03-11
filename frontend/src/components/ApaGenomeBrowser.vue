<template>
  <div class="apa-genome-browser">
    <!-- Controls -->
    <div class="browser-controls">
      <v-btn-group density="compact" variant="outlined">
        <v-btn size="small" @click="zoomIn" title="Zoom In">
          <v-icon>mdi-magnify-plus</v-icon>
        </v-btn>
        <v-btn size="small" @click="zoomOut" title="Zoom Out">
          <v-icon>mdi-magnify-minus</v-icon>
        </v-btn>
        <v-btn size="small" @click="resetZoom" title="Reset View">
          <v-icon>mdi-fit-to-screen</v-icon>
        </v-btn>
      </v-btn-group>
      <span class="ml-4 text-caption text-grey">
        <v-icon size="x-small" class="mr-1">mdi-gesture-pinch</v-icon>
        Scroll to zoom • Drag to pan
      </span>
    </div>

    <!-- SVG Browser -->
    <div ref="browserContainer" class="browser-svg-container">
      <svg
        ref="svgElement"
        :width="containerWidth"
        :height="totalHeight"
        class="genome-svg"
      >
        <defs>
          <!-- Arrow markers for strand direction -->
          <marker
            id="strand-arrow-forward"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="5"
            orient="auto"
          >
            <path d="M0,0 L0,10 L10,5 z" fill="#666" />
          </marker>
          <marker
            id="strand-arrow-reverse"
            markerWidth="10"
            markerHeight="10"
            refX="1"
            refY="5"
            orient="auto"
          >
            <path d="M10,0 L10,10 L0,5 z" fill="#666" />
          </marker>
          
          <!-- Clip path for track content area -->
          <clipPath id="track-clip">
            <rect
              :x="margin.left"
              :y="0"
              :width="containerWidth - margin.left - margin.right"
              :height="totalHeight"
            />
          </clipPath>
        </defs>

        <!-- Main zoomable group -->
        <g ref="zoomGroup">
          <!-- Track labels (fixed left column) -->
          <g ref="labelsGroup" class="track-labels">
            <!-- Rendered by D3 -->
          </g>

          <!-- Coordinate ruler -->
          <g ref="rulerGroup" class="ruler-track" clip-path="url(#track-clip)">
            <!-- Rendered by D3 -->
          </g>

          <!-- Transcript structure track -->
          <g ref="transcriptGroup" class="transcript-track" clip-path="url(#track-clip)">
            <!-- Rendered by D3 -->
          </g>

          <!-- Sample tracks -->
          <g
            v-for="(sample, idx) in samples"
            :key="sample"
            :ref="el => { if (el) sampleGroupRefs[idx] = el }"
            class="sample-track"
            clip-path="url(#track-clip)"
          >
            <!-- Rendered by D3 -->
          </g>
        </g>
      </svg>
    </div>

    <!-- Tooltip is rendered via DOM directly to body (see script) -->
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  transcriptId: { type: String, required: true },
  geneName: { type: String, required: true },
  chromosome: { type: String, required: true },
  strand: { type: String, required: true },
  exons: { type: Array, required: true },  // [{ start, end }]
  cds: { type: Array, default: () => [] },
  apaSites: { type: Array, required: true },  // From locus API
  samples: { type: Array, required: true },
  trackHeight: { type: Number, default: 40 }
})

// Measure text width using an offscreen canvas
const measureTextWidth = (text, fontSize = 13, fontWeight = '600') => {
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  ctx.font = `${fontWeight} ${fontSize}px Roboto, sans-serif`
  return ctx.measureText(text).width
}

// Compute dynamic left margin based on all label texts
const dynamicMarginLeft = computed(() => {
  const labels = [
    'Chromosome ' + props.chromosome,
    props.transcriptId,
    ...props.samples
  ]
  const maxW = Math.max(...labels.map(l => measureTextWidth(l)))
  // 16px left padding + maxW + 20px right padding before separator
  return Math.ceil(maxW) + 36
})

// Layout — margin.left is reactive
const margin = reactive({ top: 40, right: 16, bottom: 15, left: 150 })
const rulerHeight = 40
const trackPadding = 10

// labelWidth is the usable label area (margin.left minus separator gap)
const labelWidth = computed(() => margin.left - 12)

// Dynamic width: fill container
const containerWidth = ref(1100)

// APA color (single fixed color)
const APA_COLOR = '#D45D79'

// Computed layout
const trackOffsets = computed(() => {
  const offsets = {
    ruler: margin.top,
    transcript: margin.top + rulerHeight + trackPadding,
    samples: []
  }
  
  const transcriptBottom = offsets.transcript + props.trackHeight
  props.samples.forEach((_, idx) => {
    offsets.samples.push(transcriptBottom + trackPadding + (idx * (props.trackHeight + trackPadding)))
  })
  
  return offsets
})

const totalHeight = computed(() => {
  if (trackOffsets.value.samples.length === 0) {
    return trackOffsets.value.transcript + props.trackHeight + margin.bottom + 20
  }
  const lastSampleOffset = trackOffsets.value.samples[trackOffsets.value.samples.length - 1]
  return lastSampleOffset + props.trackHeight + margin.bottom + 20
})

// Domain: genomic coordinates
const genomicExtent = computed(() => {
  const allPositions = [
    ...props.exons.map(e => [e.start, e.end]).flat(),
    ...props.apaSites.map(s => s.site_position)
  ]
  if (allPositions.length === 0) return [0, 1000]
  
  const min = Math.min(...allPositions)
  const max = Math.max(...allPositions)
  const padding = Math.max((max - min) * 0.15, 1000)  // At least 1kb padding
  return [min - padding, max + padding]
})

// D3 scale and zoom
const xScale = ref(null)
const zoomBehavior = ref(null)
const currentTransform = ref(d3.zoomIdentity)

// Refs
const svgElement = ref(null)
const zoomGroup = ref(null)
const labelsGroup = ref(null)
const rulerGroup = ref(null)
const transcriptGroup = ref(null)
const sampleGroupRefs = ref([])
const browserContainer = ref(null)

// Tooltip — single DOM node appended to body, positioned with fixed
let tooltipEl = null

const ensureTooltipEl = () => {
  if (!tooltipEl) {
    tooltipEl = document.createElement('div')
    tooltipEl.className = 'genome-tooltip-global'
    tooltipEl.style.cssText = `
      position: fixed;
      display: none;
      background: rgba(33,37,41,0.95);
      color: #fff;
      padding: 10px 13px;
      border-radius: 6px;
      font-size: 12px;
      font-family: Roboto, sans-serif;
      pointer-events: none;
      z-index: 99999;
      min-width: 190px;
      max-width: 280px;
      box-shadow: 0 4px 16px rgba(0,0,0,0.35);
      backdrop-filter: blur(4px);
    `
    document.body.appendChild(tooltipEl)
  }
  return tooltipEl
}

// Tooltip helpers
const showTooltip = (event, title, items) => {
  const el = ensureTooltipEl()

  // Build inner HTML
  const rows = items.map(i =>
    `<div style="display:flex;justify-content:space-between;gap:14px;margin-top:4px;line-height:1.5">
      <span style="color:#adb5bd;font-weight:500">${i.label}:</span>
      <span style="font-weight:600;text-align:right;color:#f8f9fa">${i.value}</span>
    </div>`
  ).join('')

  el.innerHTML = `
    <div style="font-weight:700;font-size:13px;margin-bottom:6px;padding-bottom:5px;border-bottom:1px solid rgba(255,255,255,0.25)">${title}</div>
    ${rows}
  `
  el.style.display = 'block'

  // In D3 v7, mouse events are native MouseEvent objects passed directly.
  // Use sourceEvent if available (zoom/drag), otherwise use event itself.
  const nativeEvent = event.sourceEvent || event
  const clientX = nativeEvent.clientX
  const clientY = nativeEvent.clientY

  // Position with fixed coords — place right of cursor, flip left/up if near edge
  const OFFSET_X = 14
  const OFFSET_Y = -10
  const W = el.offsetWidth || 220
  const H = el.offsetHeight || 120
  const vw = window.innerWidth
  const vh = window.innerHeight

  let x = clientX + OFFSET_X
  let y = clientY + OFFSET_Y

  if (x + W > vw - 8) x = clientX - W - OFFSET_X
  if (y + H > vh - 8) y = clientY - H - Math.abs(OFFSET_Y)
  if (y < 4) y = 4
  if (x < 4) x = 4

  el.style.left = x + 'px'
  el.style.top  = y + 'px'
}

const hideTooltip = () => {
  if (tooltipEl) tooltipEl.style.display = 'none'
}

// Initialize scale
const initScale = () => {
  xScale.value = d3.scaleLinear()
    .domain(genomicExtent.value)
    .range([margin.left, containerWidth.value - margin.right])
}

// IGV-style coordinate formatting — unit chosen by visible range, not value magnitude
const formatCoordinate = (value) => {
  const domain = xScale.value ? xScale.value.domain() : genomicExtent.value
  const range = domain[1] - domain[0]

  if (range >= 1_000_000) {
    // Mb — 1 decimal is enough when range spans multiple Mb
    return (value / 1_000_000).toFixed(1) + ' Mb'
  } else if (range >= 10_000) {
    // Kb — show 1 decimal; tighten to 2 decimals when range < 100 Kb for precision
    const dec = range < 100_000 ? 2 : 1
    return (value / 1_000).toFixed(dec) + ' Kb'
  } else if (range >= 1_000) {
    // Kb with 3 decimals (range is a few Kb — need sub-Kb distinction)
    return (value / 1_000).toFixed(3) + ' Kb'
  } else {
    // bp — plain integer with locale separator
    return Math.round(value).toLocaleString() + ' bp'
  }
}

// Render coordinate ruler with smart label placement
const renderRuler = () => {
  const g = d3.select(rulerGroup.value)
  g.selectAll('*').remove()

  g.attr('transform', `translate(0, ${trackOffsets.value.ruler})`)

  // Background
  g.append('rect')
    .attr('x', margin.left)
    .attr('y', 0)
    .attr('width', containerWidth.value - margin.left - margin.right)
    .attr('height', rulerHeight)
    .attr('fill', '#FAFBFC')
    .attr('stroke', 'rgba(0, 0, 0, 0.12)')
    .attr('stroke-width', 1)

  // ── Tick value generation ────────────────────────────────────────────────────
  // Estimate the pixel width of a formatted label (Roboto 12px ~6.5px per char)
  const domain = xScale.value.domain()
  const visibleRange = domain[1] - domain[0]
  const trackWidth = containerWidth.value - margin.left - margin.right

  // Sample label width using a representative value near the centre of the domain
  const sampleLabel = formatCoordinate((domain[0] + domain[1]) / 2)
  const labelPx = sampleLabel.length * 7.5   // ~7.5px per char for Roboto 500 12px
  const minSpacingPx = labelPx + 20           // label width + 20px breathing room

  // How many ticks fit?
  const maxTicks = Math.max(2, Math.floor(trackWidth / minSpacingPx))

  // Pick a "nice" genomic step that is a round number (1/2/5 × 10^n)
  const rawStep = visibleRange / maxTicks
  const magnitude = Math.pow(10, Math.floor(Math.log10(rawStep)))
  const factor = rawStep / magnitude
  const niceStep = factor < 1.5 ? magnitude
    : factor < 3.5 ? 2 * magnitude
    : factor < 7.5 ? 5 * magnitude
    : 10 * magnitude

  // Generate tick values aligned to niceStep multiples
  const start = Math.ceil(domain[0] / niceStep) * niceStep
  const tickValues = []
  for (let v = start; v <= domain[1]; v += niceStep) {
    tickValues.push(v)
  }

  const axis = d3.axisTop(xScale.value)
    .tickValues(tickValues)
    .tickFormat(formatCoordinate)
    .tickSize(8)

  const axisGroup = g.append('g')
    .attr('transform', `translate(0, ${rulerHeight - 5})`)
    .call(axis)

  // Style axis
  axisGroup.selectAll('.domain')
    .attr('stroke', 'rgba(0, 0, 0, 0.2)')
    .attr('stroke-width', 1)

  axisGroup.selectAll('line')
    .attr('stroke', '#999')

  axisGroup.selectAll('text')
    .style('font-family', 'Roboto, sans-serif')
    .style('font-size', '12px')
    .style('font-weight', '500')
    .style('fill', 'rgba(0, 0, 0, 0.6)')
    .attr('dy', '-5px')

  // Chromosome label is rendered in renderLabels() (left margin)
}

// Render track labels (fixed left margin)
const renderLabels = () => {
  const g = d3.select(labelsGroup.value)
  g.selectAll('*').remove()

  // Chromosome label (in left margin, aligned with ruler)
  g.append('text')
    .attr('x', labelWidth.value / 2)
    .attr('y', trackOffsets.value.ruler + rulerHeight / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'middle')
    .style('font-family', 'Roboto, sans-serif')
    .style('font-size', '13px')
    .style('font-weight', '600')
    .style('fill', 'rgba(0, 0, 0, 0.87)')
    .text('Chromosome ' + props.chromosome)

  // Transcript label
  g.append('text')
    .attr('x', labelWidth.value / 2)
    .attr('y', trackOffsets.value.transcript + props.trackHeight / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'middle')
    .style('font-family', 'Roboto, sans-serif')
    .style('font-size', '13px')
    .style('font-weight', '600')
    .style('fill', '#0D7377')
    .text(`${props.transcriptId}`)

  // Sample labels
  props.samples.forEach((sample, idx) => {
    g.append('rect')
      .attr('x', 8)
      .attr('y', trackOffsets.value.samples[idx] + props.trackHeight / 2 - 12)
      .attr('width', labelWidth.value - 16)
      .attr('height', 24)
      .attr('fill', idx % 2 === 0 ? 'rgba(13, 115, 119, 0.06)' : 'rgba(13, 115, 119, 0.1)')
      .attr('rx', 4)

    g.append('text')
      .attr('x', labelWidth.value / 2)
      .attr('y', trackOffsets.value.samples[idx] + props.trackHeight / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'middle')
      .style('font-family', 'Roboto, sans-serif')
      .style('font-size', '13px')
      .style('font-weight', '500')
      .style('fill', 'rgba(0, 0, 0, 0.87)')
      .text(sample)
  })

  // Vertical separator line
  g.append('line')
    .attr('x1', margin.left - 5)
    .attr('x2', margin.left - 5)
    .attr('y1', trackOffsets.value.ruler)
    .attr('y2', totalHeight.value - margin.bottom)
    .attr('stroke', 'rgba(0, 0, 0, 0.12)')
    .attr('stroke-width', 1)
}

// Render transcript structure with CLEAR formatting
const renderTranscript = () => {
  const g = d3.select(transcriptGroup.value)
  g.selectAll('*').remove()

  g.attr('transform', `translate(0, ${trackOffsets.value.transcript})`)

  const trackY = props.trackHeight / 2

  // Track background
  g.append('rect')
    .attr('x', margin.left)
    .attr('y', 0)
    .attr('width', containerWidth.value - margin.left - margin.right)
    .attr('height', props.trackHeight)
    .attr('fill', '#FFFFFF')
    .attr('stroke', 'rgba(0, 0, 0, 0.12)')
    .attr('stroke-width', 1)

  // Intron backbone line (thin gray line connecting exons)
  const sortedExons = [...props.exons].sort((a, b) => a.start - b.start)
  if (sortedExons.length > 1) {
    const backboneStart = xScale.value(sortedExons[0].start)
    const backboneEnd = xScale.value(sortedExons[sortedExons.length - 1].end)
    
    g.append('line')
      .attr('class', 'intron-backbone')
      .attr('x1', backboneStart)
      .attr('x2', backboneEnd)
      .attr('y1', trackY)
      .attr('y2', trackY)
      .attr('stroke', '#B0B8C1')
      .attr('stroke-width', 2)

    // Intron direction chevrons (replaces 3' end arrow)
    for (let i = 0; i < sortedExons.length - 1; i++) {
      const intronStartX = xScale.value(sortedExons[i].end)
      const intronEndX = xScale.value(sortedExons[i + 1].start)
      const intronWidth = intronEndX - intronStartX

      // Only add chevrons if intron region is wide enough
      if (intronWidth > 20) {
        const arrowSpacing = 40
        const numArrows = Math.max(1, Math.floor(intronWidth / arrowSpacing))
        const actualSpacing = intronWidth / (numArrows + 1)
        const chevronSize = 4

        for (let j = 1; j <= numArrows; j++) {
          const ax = intronStartX + j * actualSpacing
          const chevronPath = props.strand === '+'
            ? `M${ax - chevronSize},${trackY - chevronSize} L${ax + chevronSize},${trackY} L${ax - chevronSize},${trackY + chevronSize}`
            : `M${ax + chevronSize},${trackY - chevronSize} L${ax - chevronSize},${trackY} L${ax + chevronSize},${trackY + chevronSize}`

          g.append('path')
            .attr('d', chevronPath)
            .attr('fill', 'none')
            .attr('stroke', '#999')
            .attr('stroke-width', 1.5)
            .attr('stroke-linecap', 'round')
            .attr('stroke-linejoin', 'round')
        }
      }
    }
  }

  // Create CDS lookup set for fast checking
  const cdsSet = new Set(props.cds.map(c => `${c.start}-${c.end}`))

  // Render exons with DISTINCT CDS vs UTR styling
  sortedExons.forEach((exon, idx) => {
    const isCDS = cdsSet.has(`${exon.start}-${exon.end}`)
    const exonHeight = isCDS ? 20 : 10  // CDS: tall, UTR: short
    const exonColor = isCDS ? '#0D7377' : '#14919B'
    
    const x = xScale.value(exon.start)
    const width = Math.max(3, xScale.value(exon.end) - x)

    g.append('rect')
      .attr('class', 'exon-box')
      .attr('x', x)
      .attr('y', trackY - exonHeight / 2)
      .attr('width', width)
      .attr('height', exonHeight)
      .attr('fill', exonColor)
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
      .attr('rx', 3)
      .style('cursor', 'pointer')
      .on('mouseenter', function(event) {
        d3.select(this)
          .attr('opacity', 0.8)
          .attr('stroke', '#000')
        
        showTooltip(event, `Exon ${idx + 1}`, [
          { label: 'Position', value: `${exon.start.toLocaleString()} - ${exon.end.toLocaleString()}` },
          { label: 'Type', value: isCDS ? 'Coding Sequence (CDS)' : 'Untranslated Region (UTR)' },
          { label: 'Length', value: `${(exon.end - exon.start).toLocaleString()} bp` }
        ])
      })
      .on('mousemove', function(event) {
        showTooltip(event, `Exon ${idx + 1}`, [
          { label: 'Position', value: `${exon.start.toLocaleString()} - ${exon.end.toLocaleString()}` },
          { label: 'Type', value: isCDS ? 'Coding Sequence (CDS)' : 'Untranslated Region (UTR)' },
          { label: 'Length', value: `${(exon.end - exon.start).toLocaleString()} bp` }
        ])
      })
      .on('mouseleave', function() {
        d3.select(this)
          .attr('opacity', 1)
          .attr('stroke', '#fff')
        hideTooltip()
      })

    // Add exon number label (only if wide enough)
    if (width > 30) {
      g.append('text')
        .attr('x', x + width / 2)
        .attr('y', trackY)
        .attr('dy', '0.35em')
        .attr('text-anchor', 'middle')
        .style('font-size', '10px')
        .style('font-weight', '600')
        .style('fill', '#fff')
        .style('pointer-events', 'none')
        .text(idx + 1)
    }
  })
}

// Render APA sites for each sample (CLEAR non-overlapping markers)
const renderSampleTracks = () => {
  props.samples.forEach((sample, idx) => {
    const g = d3.select(sampleGroupRefs.value[idx])
    g.selectAll('*').remove()

    g.attr('transform', `translate(0, ${trackOffsets.value.samples[idx]})`)

    const trackY = props.trackHeight * 0.8

    // Track background with zebra striping
    g.append('rect')
      .attr('x', margin.left)
      .attr('y', 0)
      .attr('width', containerWidth.value - margin.left - margin.right)
      .attr('height', props.trackHeight)
      .attr('fill', idx % 2 === 0 ? '#FFFFFF' : '#FAFBFC')
      .attr('stroke', 'rgba(0, 0, 0, 0.12)')
      .attr('stroke-width', 1)

    // Baseline
    g.append('line')
      .attr('class', 'baseline')
      .attr('x1', margin.left)
      .attr('x2', containerWidth.value - margin.right)
      .attr('y1', trackY)
      .attr('y2', trackY)
      .attr('stroke', 'rgba(0, 0, 0, 0.08)')
      .attr('stroke-width', 1)

    // APA sites for this sample
    const maxMarkerHeight = props.trackHeight * 0.75 - 2  // Max height from baseline upward
    
    props.apaSites.forEach((site, siteIdx) => {
      const sampleData = site.sample_details?.find(sd => sd.sample_name === sample)
      if (!sampleData || sampleData.site_abundance === 0) return

      const x = xScale.value(site.site_position)
      const color = '#D45D79'
      const abundance = sampleData.site_abundance
      const lineHeight = Math.max(2, abundance * maxMarkerHeight)  // Min 2px visible

      // Marker group
      const marker = g.append('g')
        .attr('class', 'apa-marker')
        .attr('transform', `translate(${x}, ${trackY})`)
        .style('cursor', 'pointer')

      // Lollipop stem — height proportional to abundance
      marker.append('line')
        .attr('x1', 0)
        .attr('x2', 0)
        .attr('y1', 0)
        .attr('y2', -lineHeight)
        .attr('stroke', color)
        .attr('stroke-width', 1.5)
        .attr('stroke-linecap', 'round')

      // Lollipop circle head
      marker.append('circle')
        .attr('cx', 0)
        .attr('cy', -lineHeight)
        .attr('r', 4)
        .attr('fill', color)
        .attr('stroke', '#fff')
        .attr('stroke-width', 1)

      // Interaction
      marker.on('mouseenter', function(event) {
        d3.select(this).select('line').attr('stroke-width', 3).attr('stroke-opacity', 0.8)
        d3.select(this).select('circle').attr('r', 6)
        
        showTooltip(event, `PA Site @ ${site.site_position.toLocaleString()}`, [
          { label: 'Sample', value: sample },
          { label: 'Abundance', value: abundance.toFixed(2) },
          { label: 'Count', value: sampleData.site_count.toLocaleString() },
          { label: 'PAS Motif', value: site.pas_motif || 'N/A' },
          { label: 'PAS Position', value: site.pas_position ? `${site.pas_position}bp` : 'N/A' },
          { label: 'PAS Type', value: site.pas_type || 'N/A' }
        ])
      })
      .on('mousemove', function(event) {
        showTooltip(event, `PA Site @ ${site.site_position.toLocaleString()}`, [
          { label: 'Sample', value: sample },
          { label: 'Abundance', value: abundance.toFixed(2) },
          { label: 'Count', value: sampleData.site_count.toLocaleString() },
          { label: 'PAS Motif', value: site.pas_motif || 'N/A' },
          { label: 'PAS Position', value: site.pas_position ? `${site.pas_position}bp` : 'N/A' },
          { label: 'PAS Type', value: site.pas_type || 'N/A' }
        ])
      })
      .on('mouseleave', function() {
        d3.select(this).select('line').attr('stroke-width', 1.5).attr('stroke-opacity', 1)
        d3.select(this).select('circle').attr('r', 4)
        hideTooltip()
      })
    })
  })
}

// Zoom behavior
const setupZoom = () => {
  const baseScale = xScale.value.copy()  // Store original scale

  zoomBehavior.value = d3.zoom()
    .scaleExtent([1, 100])  // Allow up to 100x zoom
    .translateExtent([
      [margin.left, 0],
      [containerWidth.value - margin.right, totalHeight.value]
    ])
    .on('zoom', (event) => {
      currentTransform.value = event.transform
      
      // Rescale the x-axis
      xScale.value = event.transform.rescaleX(baseScale)
      
      // Re-render everything with new scale
      renderRuler()
      renderTranscript()
      renderSampleTracks()
    })

  d3.select(svgElement.value).call(zoomBehavior.value)
}

// Zoom controls
const zoomIn = () => {
  d3.select(svgElement.value)
    .transition()
    .duration(300)
    .call(zoomBehavior.value.scaleBy, 1.5)
}

const zoomOut = () => {
  d3.select(svgElement.value)
    .transition()
    .duration(300)
    .call(zoomBehavior.value.scaleBy, 0.67)
}

const resetZoom = () => {
  d3.select(svgElement.value)
    .transition()
    .duration(500)
    .call(zoomBehavior.value.transform, d3.zoomIdentity)
}

// Main render function
const render = () => {
  initScale()
  renderLabels()
  renderRuler()
  renderTranscript()
  renderSampleTracks()
}

// Measure container width
const resizeObserver = ref(null)

const measureWidth = () => {
  if (browserContainer.value) {
    const rect = browserContainer.value.getBoundingClientRect()
    // Account for container padding (12px each side)
    containerWidth.value = Math.floor(rect.width - 24)
  }
}

// Initialize on mount
onMounted(() => {
  nextTick(() => {
    measureWidth()
    if (props.exons && props.exons.length > 0) {
      render()
      setupZoom()
    }
    // Watch for container resize
    resizeObserver.value = new ResizeObserver(() => {
      measureWidth()
      if (props.exons && props.exons.length > 0) {
        render()
      }
    })
    if (browserContainer.value) {
      resizeObserver.value.observe(browserContainer.value)
    }
  })
})

onBeforeUnmount(() => {
  if (resizeObserver.value) {
    resizeObserver.value.disconnect()
  }
  if (tooltipEl) {
    tooltipEl.remove()
    tooltipEl = null
  }
})

// Re-render on data changes
watch(() => [props.exons, props.apaSites, props.samples], () => {
  nextTick(() => {
    if (props.exons && props.exons.length > 0) {
      render()
    }
  })
}, { deep: true })

// Sync margin.left whenever dynamic label width changes, then re-render
watch(dynamicMarginLeft, (newLeft) => {
  margin.left = newLeft
  nextTick(() => {
    if (props.exons && props.exons.length > 0) {
      render()
    }
  })
}, { immediate: true })
</script>

<style scoped>
.apa-genome-browser {
  width: 100%;
  background: transparent;
  border-radius: 8px;
  padding: 0;
  position: relative;
}

.browser-controls {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.browser-svg-container {
  position: relative;
  width: 100%;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.5);
  padding: 12px;
}

.genome-svg {
  display: block;
  cursor: grab;
}

.genome-svg:active {
  cursor: grabbing;
}

/* Tooltip styling */
.genome-tooltip {
  position: absolute;
  background: rgba(33, 37, 41, 0.95);
  color: white;
  padding: 12px 14px;
  border-radius: 6px;
  font-size: 12px;
  pointer-events: none;
  z-index: 1000;
  min-width: 200px;
  max-width: 300px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(4px);
}

.tooltip-title {
  font-weight: 700;
  font-size: 13px;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.3);
  color: #fff;
}

.tooltip-item {
  display: flex;
  justify-content: space-between;
  margin-top: 5px;
  gap: 16px;
  line-height: 1.5;
}

.tooltip-label {
  color: #adb5bd;
  font-weight: 500;
}

.tooltip-value {
  font-weight: 600;
  text-align: right;
  color: #f8f9fa;
}

/* SVG element styling via classes */
:deep(.exon-box) {
  transition: opacity 0.15s ease, stroke 0.15s ease;
}

:deep(.apa-marker line) {
  transition: stroke-width 0.15s ease;
}

:deep(.apa-marker circle) {
  transition: r 0.15s ease;
}
</style>
