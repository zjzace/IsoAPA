<template>
  <div class="multi-isoform-browser">
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
          <clipPath id="multi-iso-clip">
            <rect
              :x="margin.left"
              :y="0"
              :width="containerWidth - margin.left - margin.right"
              :height="totalHeight"
            />
          </clipPath>
        </defs>

        <!-- Labels group (fixed left) -->
        <g ref="labelsGroup" class="track-labels"></g>

        <!-- Ruler group -->
        <g ref="rulerGroup" class="ruler-track" clip-path="url(#multi-iso-clip)"></g>

        <!-- Per-isoform groups: exon track + apa track -->
        <g
          v-for="(tx, idx) in transcripts"
          :key="tx.transcript_id"
        >
          <g
            :ref="el => { if (el) exonGroupRefs[idx] = el }"
            class="exon-track"
            clip-path="url(#multi-iso-clip)"
          ></g>
          <g
            :ref="el => { if (el) apaGroupRefs[idx] = el }"
            class="apa-track"
            clip-path="url(#multi-iso-clip)"
          ></g>
        </g>
      </svg>
    </div>

    <!-- Statistics strip -->
    <div class="stats-strip mt-4">
      <v-row dense justify="center">
        <v-col cols="auto">
          <div class="stat-card">
            <div class="stat-value">{{ stats.totalSites }}</div>
            <div class="stat-label">Total Sites</div>
          </div>
        </v-col>
        <v-col cols="auto">
          <div class="stat-card stat-shared">
            <div class="stat-value" style="color: #7B5EA7;">{{ stats.sharedSites }}</div>
            <div class="stat-label">Shared</div>
          </div>
        </v-col>
        <v-col cols="auto">
          <div class="stat-card stat-private">
            <div class="stat-value" style="color: #C0715A;">{{ stats.privateSites }}</div>
            <div class="stat-label">Private</div>
          </div>
        </v-col>
        <v-col cols="auto">
          <div class="stat-card">
            <div class="stat-value">{{ stats.isoforms }}</div>
            <div class="stat-label">Isoforms</div>
          </div>
        </v-col>
        <v-col cols="auto">
          <div class="stat-card">
            <div class="stat-value">{{ stats.sharingIndex }}</div>
            <div class="stat-label">Sharing Index</div>
          </div>
        </v-col>
      </v-row>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as d3 from 'd3'

// Tooltip — single DOM node appended to body, positioned with fixed coords
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

const props = defineProps({
  geneData: { type: Object, required: true },
  transcriptStructures: { type: Object, required: true }
})

// ── Measure text width via offscreen canvas ──────────────────────────────────
const measureTextWidth = (text, fontSize = 13, fontWeight = '600') => {
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  ctx.font = `${fontWeight} ${fontSize}px Roboto, sans-serif`
  return ctx.measureText(text).width
}

// ── Dynamic left margin: widest label + padding ───────────────────────────────
const dynamicMarginLeft = computed(() => {
  const labels = [
    'Chromosome ' + (props.geneData?.chromosome ?? ''),
    ...transcripts.value.map(tx => tx.transcript_id),
    'PA Sites'
  ]
  const maxW = Math.max(...labels.map(l => measureTextWidth(l)))
  return Math.ceil(maxW) + 36  // 16px left + 20px right padding before separator
})

// ── Layout — margin.left is reactive ─────────────────────────────────────────
const margin = reactive({ top: 40, right: 16, bottom: 15, left: 150 })
const rulerHeight = 40
const trackPadding = 10
const labelWidth = computed(() => margin.left - 12)
const exonTrackHeight = 40
const apaTrackHeight = 40
const isoformGap = 12

// ── Colors ───────────────────────────────────────────────────────────────────
const SHARED_COLOR = '#7B5EA7'
const PRIVATE_COLOR = '#C0715A'
const CDS_COLOR = '#0D7377'
const UTR_COLOR = '#14919B'
const INTRON_COLOR = '#B0B8C1'

// ── Reactive state ───────────────────────────────────────────────────────────
const containerWidth = ref(1100)
const xScale = ref(null)
const zoomBehavior = ref(null)
const resizeObserver = ref(null)

// Template refs
const browserContainer = ref(null)
const svgElement = ref(null)
const labelsGroup = ref(null)
const rulerGroup = ref(null)
const exonGroupRefs = ref([])
const apaGroupRefs = ref([])

// ── Computed data ─────────────────────────────────────────────────────────────
const transcripts = computed(() => props.geneData?.transcripts ?? [])

const siteTranscriptCount = computed(() => {
  const map = new Map()
  for (const tx of transcripts.value) {
    for (const site of tx.apa_sites ?? []) {
      map.set(site.site_id, (map.get(site.site_id) ?? 0) + 1)
    }
  }
  return map
})

const isShared = (siteId) => (siteTranscriptCount.value.get(siteId) ?? 0) >= 2

const genomicExtent = computed(() => {
  const positions = []
  for (const tx of transcripts.value) {
    const struct = props.transcriptStructures[tx.transcript_id]
    if (struct?.exons) {
      for (const e of struct.exons) { positions.push(e.start, e.end) }
    }
    for (const site of tx.apa_sites ?? []) {
      positions.push(site.site_position)
    }
  }
  if (positions.length === 0) return [0, 1000]
  const min = Math.min(...positions)
  const max = Math.max(...positions)
  const pad = Math.max((max - min) * 0.15, 1000)
  return [min - pad, max + pad]
})

// Track Y offsets
const trackOffsets = computed(() => {
  const offsets = { ruler: margin.top, isoforms: [] }
  let y = margin.top + rulerHeight + trackPadding
  for (let i = 0; i < transcripts.value.length; i++) {
    offsets.isoforms.push({ exon: y, apa: y + exonTrackHeight + trackPadding })
    y += exonTrackHeight + trackPadding + apaTrackHeight + isoformGap
  }
  return offsets
})

const totalHeight = computed(() => {
  if (trackOffsets.value.isoforms.length === 0) {
    return margin.top + rulerHeight + margin.bottom + 20
  }
  const last = trackOffsets.value.isoforms[trackOffsets.value.isoforms.length - 1]
  return last.apa + apaTrackHeight + margin.bottom + 20
})

// ── Statistics ────────────────────────────────────────────────────────────────
const stats = computed(() => {
  const allSiteIds = new Set()
  for (const tx of transcripts.value) {
    for (const site of tx.apa_sites ?? []) allSiteIds.add(site.site_id)
  }
  const totalSites = allSiteIds.size
  const sharedSites = [...allSiteIds].filter(id => isShared(id)).length
  const privateSites = totalSites - sharedSites
  const isoforms = transcripts.value.length
  const sharingIndex = totalSites > 0 ? (sharedSites / totalSites * 100).toFixed(1) + '%' : '0%'
  return { totalSites, sharedSites, privateSites, isoforms, sharingIndex }
})

// ── Helpers ───────────────────────────────────────────────────────────────────
// IGV-style coordinate formatting — unit chosen by visible range, not value magnitude
const formatCoordinate = (value) => {
  if (!xScale.value) return String(value)
  const domain = xScale.value.domain()
  const range = domain[1] - domain[0]

  if (range >= 1_000_000) {
    return (value / 1_000_000).toFixed(1) + ' Mb'
  } else if (range >= 10_000) {
    const dec = range < 100_000 ? 2 : 1
    return (value / 1_000).toFixed(dec) + ' Kb'
  } else if (range >= 1_000) {
    return (value / 1_000).toFixed(3) + ' Kb'
  } else {
    return Math.round(value).toLocaleString() + ' bp'
  }
}

const showTooltip = (event, title, items) => {
  const el = ensureTooltipEl()

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

  // Use sourceEvent if available (zoom/drag wrapper), otherwise use event directly
  const nativeEvent = event.sourceEvent || event
  const clientX = nativeEvent.clientX
  const clientY = nativeEvent.clientY

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

// ── Render: ruler ─────────────────────────────────────────────────────────────
const renderRuler = () => {
  const g = d3.select(rulerGroup.value)
  g.selectAll('*').remove()
  g.attr('transform', `translate(0, ${trackOffsets.value.ruler})`)

  g.append('rect')
    .attr('x', margin.left).attr('y', 0)
    .attr('width', containerWidth.value - margin.left - margin.right)
    .attr('height', rulerHeight)
    .attr('fill', '#FAFBFC')
    .attr('stroke', 'rgba(0,0,0,0.12)').attr('stroke-width', 1)

  const domain = xScale.value.domain()
  const visibleRange = domain[1] - domain[0]
  const trackWidth = containerWidth.value - margin.left - margin.right

  const sampleLabel = formatCoordinate((domain[0] + domain[1]) / 2)
  const labelPx = sampleLabel.length * 7.5
  const minSpacingPx = labelPx + 20

  const maxTicks = Math.max(2, Math.floor(trackWidth / minSpacingPx))

  const rawStep = visibleRange / maxTicks
  const magnitude = Math.pow(10, Math.floor(Math.log10(rawStep)))
  const factor = rawStep / magnitude
  const niceStep = factor < 1.5 ? magnitude
    : factor < 3.5 ? 2 * magnitude
    : factor < 7.5 ? 5 * magnitude
    : 10 * magnitude

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

  axisGroup.selectAll('.domain').attr('stroke', 'rgba(0,0,0,0.2)').attr('stroke-width', 1)
  axisGroup.selectAll('line').attr('stroke', '#999')
  axisGroup.selectAll('text')
    .style('font-family', 'Roboto, sans-serif')
    .style('font-size', '12px')
    .style('font-weight', '500')
    .style('fill', 'rgba(0,0,0,0.6)')
    .attr('dy', '-5px')
}

// ── Render: labels ────────────────────────────────────────────────────────────
const renderLabels = () => {
  const g = d3.select(labelsGroup.value)
  g.selectAll('*').remove()

  // Chromosome label
  g.append('text')
    .attr('x', labelWidth.value / 2)
    .attr('y', trackOffsets.value.ruler + rulerHeight / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'middle')
    .style('font-family', 'Roboto, sans-serif')
    .style('font-size', '13px')
    .style('font-weight', '600')
    .style('fill', 'rgba(0,0,0,0.87)')
    .text('Chromosome ' + (props.geneData?.chromosome ?? ''))

  // Per-isoform labels
  transcripts.value.forEach((tx, i) => {
    const offsets = trackOffsets.value.isoforms[i]

    // Exon track label — full transcript ID, centered in left column
    g.append('text')
      .attr('x', labelWidth.value / 2)
      .attr('y', offsets.exon + exonTrackHeight / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'middle')
      .style('font-family', 'Roboto, sans-serif')
      .style('font-size', '12px')
      .style('font-weight', '600')
      .style('fill', CDS_COLOR)
      .text(tx.transcript_id)

    // APA track label — centered in left column
    g.append('text')
      .attr('x', labelWidth.value / 2)
      .attr('y', offsets.apa + apaTrackHeight / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'middle')
      .style('font-family', 'Roboto, sans-serif')
      .style('font-size', '11px')
      .style('font-weight', '500')
      .style('fill', 'rgba(0,0,0,0.54)')
      .text('PA Sites')
  })

  // Vertical separator
  g.append('line')
    .attr('x1', margin.left - 5).attr('x2', margin.left - 5)
    .attr('y1', trackOffsets.value.ruler)
    .attr('y2', totalHeight.value - margin.bottom)
    .attr('stroke', 'rgba(0,0,0,0.12)').attr('stroke-width', 1)
}

// ── Render: single exon track ─────────────────────────────────────────────────
const renderExonTrack = (txIndex) => {
  const tx = transcripts.value[txIndex]
  const g = d3.select(exonGroupRefs.value[txIndex])
  if (!g || !g.node()) return
  g.selectAll('*').remove()

  const offsets = trackOffsets.value.isoforms[txIndex]
  g.attr('transform', `translate(0, ${offsets.exon})`)

  const trackY = exonTrackHeight / 2
  const struct = props.transcriptStructures[tx.transcript_id]

  // Track background
  g.append('rect')
    .attr('x', margin.left).attr('y', 0)
    .attr('width', containerWidth.value - margin.left - margin.right)
    .attr('height', exonTrackHeight)
    .attr('fill', txIndex % 2 === 0 ? '#FFFFFF' : '#FAFBFC')
    .attr('stroke', 'rgba(0,0,0,0.12)').attr('stroke-width', 1)

  if (!struct?.exons?.length) return

  const sortedExons = [...struct.exons].sort((a, b) => a.start - b.start)
  const cdsSet = new Set((struct.cds ?? []).map(c => `${c.start}-${c.end}`))
  const strand = props.geneData?.strand ?? '+'

  // Intron backbone
  if (sortedExons.length > 1) {
    const bx1 = xScale.value(sortedExons[0].start)
    const bx2 = xScale.value(sortedExons[sortedExons.length - 1].end)
    g.append('line')
      .attr('x1', bx1).attr('x2', bx2)
      .attr('y1', trackY).attr('y2', trackY)
      .attr('stroke', INTRON_COLOR).attr('stroke-width', 2)

    // Chevrons
    for (let i = 0; i < sortedExons.length - 1; i++) {
      const ix1 = xScale.value(sortedExons[i].end)
      const ix2 = xScale.value(sortedExons[i + 1].start)
      const iw = ix2 - ix1
      if (iw > 20) {
        const num = Math.max(1, Math.floor(iw / 40))
        const sp = iw / (num + 1)
        const cs = 4
        for (let j = 1; j <= num; j++) {
          const ax = ix1 + j * sp
          const path = strand === '+'
            ? `M${ax - cs},${trackY - cs} L${ax + cs},${trackY} L${ax - cs},${trackY + cs}`
            : `M${ax + cs},${trackY - cs} L${ax - cs},${trackY} L${ax + cs},${trackY + cs}`
          g.append('path').attr('d', path)
            .attr('fill', 'none').attr('stroke', '#999')
            .attr('stroke-width', 1.5).attr('stroke-linecap', 'round').attr('stroke-linejoin', 'round')
        }
      }
    }
  }

  // Exons
  sortedExons.forEach((exon, idx) => {
    const isCDS = cdsSet.has(`${exon.start}-${exon.end}`)
    const exonH = isCDS ? 20 : 10
    const exonColor = isCDS ? CDS_COLOR : UTR_COLOR
    const x = xScale.value(exon.start)
    const w = Math.max(3, xScale.value(exon.end) - x)

    g.append('rect')
      .attr('class', 'exon-box')
      .attr('x', x).attr('y', trackY - exonH / 2)
      .attr('width', w).attr('height', exonH)
      .attr('fill', exonColor)
      .attr('stroke', '#fff').attr('stroke-width', 1.5).attr('rx', 3)
      .style('cursor', 'pointer')
      .on('mouseenter', function(event) {
        d3.select(this).attr('opacity', 0.8).attr('stroke', '#000')
        showTooltip(event, `Exon ${idx + 1}`, [
          { label: 'Transcript', value: tx.transcript_id },
          { label: 'Position', value: `${exon.start.toLocaleString()} – ${exon.end.toLocaleString()}` },
          { label: 'Type', value: isCDS ? 'CDS' : 'UTR' },
          { label: 'Length', value: `${(exon.end - exon.start).toLocaleString()} bp` }
        ])
      })
      .on('mousemove', function(event) {
        showTooltip(event, `Exon ${idx + 1}`, [
          { label: 'Transcript', value: tx.transcript_id },
          { label: 'Position', value: `${exon.start.toLocaleString()} – ${exon.end.toLocaleString()}` },
          { label: 'Type', value: isCDS ? 'CDS' : 'UTR' },
          { label: 'Length', value: `${(exon.end - exon.start).toLocaleString()} bp` }
        ])
      })
      .on('mouseleave', function() {
        d3.select(this).attr('opacity', 1).attr('stroke', '#fff')
        hideTooltip()
      })

    if (w > 30) {
      g.append('text')
        .attr('x', x + w / 2).attr('y', trackY).attr('dy', '0.35em')
        .attr('text-anchor', 'middle')
        .style('font-size', '10px').style('font-weight', '600')
        .style('fill', '#fff').style('pointer-events', 'none')
        .text(idx + 1)
    }
  })
}

// ── Render: single APA track ──────────────────────────────────────────────────
const renderApaTrack = (txIndex) => {
  const tx = transcripts.value[txIndex]
  const g = d3.select(apaGroupRefs.value[txIndex])
  if (!g || !g.node()) return
  g.selectAll('*').remove()

  const offsets = trackOffsets.value.isoforms[txIndex]
  g.attr('transform', `translate(0, ${offsets.apa})`)

  const baseline = apaTrackHeight * 0.8
  const maxLollipopH = apaTrackHeight * 0.75 - 2

  // Track background
  g.append('rect')
    .attr('x', margin.left).attr('y', 0)
    .attr('width', containerWidth.value - margin.left - margin.right)
    .attr('height', apaTrackHeight)
    .attr('fill', txIndex % 2 === 0 ? '#FAFBFC' : '#FFFFFF')
    .attr('stroke', 'rgba(0,0,0,0.12)').attr('stroke-width', 1)

  // Baseline
  g.append('line')
    .attr('x1', margin.left).attr('x2', containerWidth.value - margin.right)
    .attr('y1', baseline).attr('y2', baseline)
    .attr('stroke', 'rgba(0,0,0,0.08)').attr('stroke-width', 1)

  for (const site of tx.apa_sites ?? []) {
    const x = xScale.value(site.site_position)
    const sampleDetails = site.sample_details ?? []
    const meanAbundance = sampleDetails.length > 0
      ? sampleDetails.reduce((s, d) => s + d.site_abundance, 0) / sampleDetails.length
      : 1
    const lineH = Math.max(4, meanAbundance * maxLollipopH)
    const color = isShared(site.site_id) ? SHARED_COLOR : PRIVATE_COLOR
    const classification = isShared(site.site_id) ? 'Shared' : 'Private'

    const marker = g.append('g')
      .attr('class', 'apa-marker')
      .attr('transform', `translate(${x}, ${baseline})`)
      .style('cursor', 'pointer')

    // Stem
    marker.append('line')
      .attr('x1', 0).attr('x2', 0)
      .attr('y1', 0).attr('y2', -lineH)
      .attr('stroke', color).attr('stroke-width', 1.5).attr('stroke-linecap', 'round')

    // Circle head
    marker.append('circle')
      .attr('cx', 0).attr('cy', -lineH)
      .attr('r', 4).attr('fill', color)

    // Interaction area (wider hit target)
    marker.append('rect')
      .attr('x', -8).attr('y', -lineH - 4)
      .attr('width', 16).attr('height', lineH + 8)
      .attr('fill', 'transparent')
      .on('mouseenter', function(event) {
        d3.select(marker.node()).select('line').attr('stroke-width', 3)
        d3.select(marker.node()).select('circle').attr('r', 6)
        const tooltipItems = [
          { label: 'Site ID', value: site.site_id },
          { label: 'Position', value: site.site_position.toLocaleString() },
          { label: 'Classification', value: classification },
          { label: 'Mean Abundance', value: meanAbundance.toFixed(3) }
        ]
        sampleDetails.forEach(sd => {
          tooltipItems.push({ label: sd.sample_name, value: (sd.site_abundance * 100).toFixed(1) + '%' })
        })
        showTooltip(event, `PA Site @ ${site.site_position.toLocaleString()}`, tooltipItems)
      })
      .on('mousemove', function(event) {
        const tooltipItems = [
          { label: 'Site ID', value: site.site_id },
          { label: 'Position', value: site.site_position.toLocaleString() },
          { label: 'Classification', value: classification },
          { label: 'Mean Abundance', value: meanAbundance.toFixed(3) }
        ]
        sampleDetails.forEach(sd => {
          tooltipItems.push({ label: sd.sample_name, value: (sd.site_abundance * 100).toFixed(1) + '%' })
        })
        showTooltip(event, `PA Site @ ${site.site_position.toLocaleString()}`, tooltipItems)
      })
      .on('mouseleave', function() {
        d3.select(marker.node()).select('line').attr('stroke-width', 1.5)
        d3.select(marker.node()).select('circle').attr('r', 4)
        hideTooltip()
      })
  }
}

// ── Full render ───────────────────────────────────────────────────────────────
const render = () => {
  if (!svgElement.value) return
  initScale()
  renderLabels()
  renderRuler()
  transcripts.value.forEach((_, i) => {
    renderExonTrack(i)
    renderApaTrack(i)
  })
}

const renderTracks = () => {
  renderRuler()
  transcripts.value.forEach((_, i) => {
    renderExonTrack(i)
    renderApaTrack(i)
  })
}

// ── Scale init ────────────────────────────────────────────────────────────────
const initScale = () => {
  xScale.value = d3.scaleLinear()
    .domain(genomicExtent.value)
    .range([margin.left, containerWidth.value - margin.right])
}

// ── Zoom ──────────────────────────────────────────────────────────────────────
const setupZoom = () => {
  const baseScale = xScale.value.copy()

  zoomBehavior.value = d3.zoom()
    .scaleExtent([1, 100])
    .translateExtent([
      [margin.left, 0],
      [containerWidth.value - margin.right, totalHeight.value]
    ])
    .on('zoom', (event) => {
      xScale.value = event.transform.rescaleX(baseScale)
      renderTracks()
    })

  d3.select(svgElement.value).call(zoomBehavior.value)
}

const zoomIn = () => {
  d3.select(svgElement.value).transition().duration(300).call(zoomBehavior.value.scaleBy, 1.5)
}

const zoomOut = () => {
  d3.select(svgElement.value).transition().duration(300).call(zoomBehavior.value.scaleBy, 0.67)
}

const resetZoom = () => {
  d3.select(svgElement.value).transition().duration(500).call(zoomBehavior.value.transform, d3.zoomIdentity)
}

// ── Width measurement ─────────────────────────────────────────────────────────
const measureWidth = () => {
  if (browserContainer.value) {
    containerWidth.value = Math.floor(browserContainer.value.getBoundingClientRect().width - 24)
  }
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────
onMounted(() => {
  nextTick(() => {
    measureWidth()
    if (transcripts.value.length > 0) {
      render()
      setupZoom()
    }
    resizeObserver.value = new ResizeObserver(() => {
      measureWidth()
      if (transcripts.value.length > 0) render()
    })
    if (browserContainer.value) resizeObserver.value.observe(browserContainer.value)
  })
})

onBeforeUnmount(() => {
  resizeObserver.value?.disconnect()
  if (tooltipEl) {
    tooltipEl.remove()
    tooltipEl = null
  }
})

watch(
  () => [props.geneData, props.transcriptStructures],
  () => { nextTick(() => { if (transcripts.value.length > 0) render() }) },
  { deep: true }
)

// Sync margin.left whenever dynamic label width changes, then re-render
watch(dynamicMarginLeft, (newLeft) => {
  margin.left = newLeft
  nextTick(() => { if (transcripts.value.length > 0) render() })
}, { immediate: true })
</script>

<style scoped>
.multi-isoform-browser {
  width: 100%;
  background: transparent;
  border-radius: 8px;
  padding: 0;
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

/* Tooltip */
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

.tooltip-label { color: #adb5bd; font-weight: 500; }
.tooltip-value { font-weight: 600; text-align: right; color: #f8f9fa; }

/* Statistics strip */
.stats-strip {
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  padding-top: 16px;
}

.stat-card {
  text-align: center;
  padding: 8px 20px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.08);
  min-width: 90px;
}

.stat-shared { background: rgba(123, 94, 167, 0.05); border-color: rgba(123, 94, 167, 0.2); }
.stat-private { background: rgba(192, 113, 90, 0.05); border-color: rgba(192, 113, 90, 0.2); }

.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.87);
  line-height: 1.2;
}

.stat-label {
  font-size: 11px;
  color: rgba(0, 0, 0, 0.54);
  margin-top: 2px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

:deep(.exon-box) {
  transition: opacity 0.15s ease, stroke 0.15s ease;
}

:deep(.apa-marker line) {
  transition: stroke-width 0.15s ease;
}
</style>
