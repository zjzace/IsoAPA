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
          
          <!-- APA arrow markers (colored) -->
          <marker
            v-for="color in apaColors"
            :key="`apa-arrow-${color}`"
            :id="`apa-arrow-${color.replace('#', '')}`"
            markerWidth="8"
            markerHeight="10"
            refX="4"
            refY="5"
            orient="auto-start-reverse"
          >
            <path d="M0,0 L0,10 L8,5 z" :fill="color" />
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

    <!-- Tooltip -->
    <div
      v-if="tooltip.visible"
      ref="tooltipElement"
      class="genome-tooltip"
      :style="{
        left: tooltip.x + 'px',
        top: tooltip.y + 'px'
      }"
    >
      <div class="tooltip-title">{{ tooltip.title }}</div>
      <div v-for="item in tooltip.items" :key="item.label" class="tooltip-item">
        <span class="tooltip-label">{{ item.label }}:</span>
        <span class="tooltip-value">{{ item.value }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
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

// Layout constants
const margin = { top: 40, right: 16, bottom: 15, left: 150 }
const rulerHeight = 40
const trackPadding = 10
const labelWidth = 138

// Dynamic width: fill container
const containerWidth = ref(1100)

// APA color palette
const apaColors = ['#E94560', '#FF6B6B', '#F97316', '#14919B']

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

// Tooltip state
const tooltip = ref({
  visible: false,
  x: 0,
  y: 0,
  title: '',
  items: []
})

// Initialize scale
const initScale = () => {
  xScale.value = d3.scaleLinear()
    .domain(genomicExtent.value)
    .range([margin.left, containerWidth.value - margin.right])
}

// Smart coordinate formatting — adaptive precision based on visible range
const formatCoordinate = (value) => {
  const domain = xScale.value ? xScale.value.domain() : genomicExtent.value
  const range = domain[1] - domain[0]
  
  if (value >= 1000000) {
    // Determine decimal places needed to distinguish ticks
    // range < 10kb → need 4 decimals (127.5917M), < 100kb → 3, < 1M → 2, else 1
    let decimals
    if (range < 10000) decimals = 4
    else if (range < 100000) decimals = 3
    else if (range < 1000000) decimals = 2
    else decimals = 1
    return (value / 1000000).toFixed(decimals) + 'M'
  } else if (value >= 1000) {
    let decimals = range < 1000 ? 2 : 1
    return (value / 1000).toFixed(decimals) + 'K'
  }
  return value.toLocaleString()
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

  // Smart tick calculation based on zoom level
  const domain = xScale.value.domain()
  const range = domain[1] - domain[0]
  
  // Pixel-based tick spacing: ~100px between ticks for consistent readability
  const trackWidth = containerWidth.value - margin.left - margin.right
  const tickCount = Math.max(3, Math.min(8, Math.floor(trackWidth / 100)))

  const axis = d3.axisTop(xScale.value)
    .ticks(tickCount)
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
    .attr('x', labelWidth / 2)
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
    .attr('x', 10)
    .attr('y', trackOffsets.value.transcript + props.trackHeight / 2)
    .attr('dy', '0.35em')
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
      .attr('width', labelWidth - 16)
      .attr('height', 24)
      .attr('fill', idx % 2 === 0 ? 'rgba(13, 115, 119, 0.06)' : 'rgba(13, 115, 119, 0.1)')
      .attr('rx', 4)

    g.append('text')
      .attr('x', labelWidth / 2)
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
      const color = getApaTypeColor(site.apa_type)
      const abundance = sampleData.site_abundance
      const lineHeight = Math.max(2, abundance * maxMarkerHeight)  // Min 2px visible

      // Marker group
      const marker = g.append('g')
        .attr('class', 'apa-marker')
        .attr('transform', `translate(${x}, ${trackY})`)
        .style('cursor', 'pointer')

      // Thin vertical line — height proportional to abundance
      marker.append('line')
        .attr('x1', 0)
        .attr('x2', 0)
        .attr('y1', 0)
        .attr('y2', -lineHeight)
        .attr('stroke', color)
        .attr('stroke-width', 1.5)
        .attr('stroke-linecap', 'round')

      // Interaction
      marker.on('mouseenter', function(event) {
        d3.select(this).select('line')
          .attr('stroke-width', 3)
          .attr('stroke-opacity', 0.8)
        
        showTooltip(event, `APA Site @ ${site.site_position.toLocaleString()}`, [
          { label: 'Sample', value: sample },
          { label: 'Abundance', value: abundance.toFixed(2) },
          { label: 'Count', value: sampleData.site_count.toLocaleString() },
          { label: 'APA Type', value: site.apa_type || 'Unknown' },
          { label: 'PAS Motif', value: site.pas_motif || 'N/A' },
          { label: 'PAS Position', value: site.pas_position ? `${site.pas_position}bp` : 'N/A' },
          { label: 'PAS Type', value: site.pas_type || 'N/A' }
        ])
      })
      .on('mouseleave', function() {
        d3.select(this).select('line')
          .attr('stroke-width', 1.5)
          .attr('stroke-opacity', 1)
        hideTooltip()
      })
    })
  })
}

// Color scheme for APA types
const getApaTypeColor = (apaType) => {
  switch (apaType) {
    case '3UTR-APA': return '#E94560'
    case 'Intronic-APA': return '#FF6B6B'
    case 'Exonic-APA': return '#F97316'
    default: return '#14919B'
  }
}

// Tooltip helpers
const showTooltip = (event, title, items) => {
  const containerRect = browserContainer.value.getBoundingClientRect()
  const x = event.clientX - containerRect.left + 15
  const y = event.clientY - containerRect.top - 10
  
  tooltip.value = {
    visible: true,
    x: Math.min(x, containerWidth.value - 220),  // Prevent overflow
    y: Math.max(y, 10),
    title,
    items
  }
}

const hideTooltip = () => {
  tooltip.value.visible = false
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
})

// Re-render on data changes
watch(() => [props.exons, props.apaSites, props.samples], () => {
  nextTick(() => {
    if (props.exons && props.exons.length > 0) {
      render()
    }
  })
}, { deep: true })
</script>

<style scoped>
.apa-genome-browser {
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
</style>
