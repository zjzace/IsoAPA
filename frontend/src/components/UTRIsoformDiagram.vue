<template>
  <div class="utr-isoform-diagram">
    <svg 
      :width="width" 
      :height="height" 
      :viewBox="`0 0 ${width} ${height}`"
      class="diagram-svg"
    >
      <defs>
        <marker
          id="arrow"
          markerWidth="10"
          markerHeight="10"
          refX="9"
          refY="3"
          orient="auto"
          markerUnits="strokeWidth"
        >
          <path d="M0,0 L0,6 L9,3 z" fill="#0D7377" />
        </marker>
      </defs>
      
      <g :transform="`translate(${padding.left}, ${padding.top})`">
        <text 
          x="0" 
          y="-10" 
          class="diagram-title"
          font-size="14"
          font-weight="600"
          fill="currentColor"
        >
          {{ geneStructure.gene_name }} ({{ geneStructure.transcript_id }})
        </text>
        
        <line 
          :x1="0"
          :y1="centerY"
          :x2="drawWidth"
          :y2="centerY"
          stroke="#999"
          stroke-width="2"
          marker-end="url(#arrow)"
        />
        
        <g v-for="(exon, index) in scaledExons" :key="`exon-${index}`">
          <rect
            :x="exon.x"
            :y="centerY - exonHeight / 2"
            :width="exon.width"
            :height="exonHeight"
            :fill="exon.isCDS ? '#0D7377' : '#14919B'"
            rx="2"
          />
        </g>
        
        <g v-for="(site, index) in scaledApaSites" :key="`site-${index}`">
          <line
            :x1="site.x"
            :y1="centerY - markerHeight"
            :x2="site.x"
            :y2="centerY + markerHeight"
            stroke="#E94560"
            stroke-width="2.5"
          />
          <circle
            :cx="site.x"
            :cy="centerY - markerHeight - 5"
            r="4"
            :fill="getApaSiteColor(site)"
          />
          <text
            :x="site.x"
            :y="centerY + markerHeight + 15"
            text-anchor="middle"
            font-size="10"
            fill="#E94560"
          >
            {{ site.type || 'APA' }}
          </text>
        </g>
        
        <g v-if="scaledApaSites.length >= 2">
          <text
            :x="scaledApaSites[0].x"
            :y="centerY - markerHeight - 20"
            text-anchor="middle"
            font-size="11"
            fill="#666"
          >
            Proximal
          </text>
          <text
            :x="scaledApaSites[scaledApaSites.length - 1].x"
            :y="centerY - markerHeight - 20"
            text-anchor="middle"
            font-size="11"
            fill="#666"
          >
            Distal
          </text>
        </g>
        
        <text 
          :x="0" 
          :y="centerY + 35" 
          font-size="10" 
          fill="#888"
        >
          {{ formatPosition(minPosition) }}
        </text>
        <text 
          :x="drawWidth" 
          :y="centerY + 35" 
          text-anchor="end" 
          font-size="10" 
          fill="#888"
        >
          {{ formatPosition(maxPosition) }}
        </text>
      </g>
    </svg>
    
    <div v-if="legend" class="diagram-legend">
      <div class="legend-item">
        <div class="legend-box" style="background: #0D7377;"></div>
        <span>Coding Exon (CDS)</span>
      </div>
      <div class="legend-item">
        <div class="legend-box" style="background: #14919B;"></div>
        <span>Non-coding Exon (UTR)</span>
      </div>
      <div class="legend-item">
        <div class="legend-marker">|</div>
        <span>APA Cleavage Site</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  geneStructure: {
    type: Object,
    required: true
  },
  apaSites: {
    type: Array,
    default: () => []
  },
  width: {
    type: Number,
    default: 800
  },
  height: {
    type: Number,
    default: 150
  },
  legend: {
    type: Boolean,
    default: true
  }
})

const padding = { top: 30, right: 20, bottom: 50, left: 20 }
const drawWidth = computed(() => props.width - padding.left - padding.right)
const centerY = computed(() => (props.height - padding.top - padding.bottom) / 2)
const exonHeight = 20
const markerHeight = 25

const minPosition = computed(() => {
  const positions = [
    ...props.geneStructure.exons.map(e => e.start),
    ...props.apaSites.map(s => s.site_position)
  ]
  return Math.min(...positions)
})

const maxPosition = computed(() => {
  const positions = [
    ...props.geneStructure.exons.map(e => e.end),
    ...props.apaSites.map(s => s.site_position)
  ]
  return Math.max(...positions)
})

const scale = computed(() => {
  const range = maxPosition.value - minPosition.value
  return drawWidth.value / range
})

const scaledExons = computed(() => {
  return props.geneStructure.exons.map(exon => {
    const x = (exon.start - minPosition.value) * scale.value
    const width = (exon.end - exon.start) * scale.value
    return {
      x,
      width: Math.max(width, 2),
      isCDS: exon.feature === 'CDS'
    }
  })
})

const scaledApaSites = computed(() => {
  return props.apaSites.map(site => {
    const x = (site.site_position - minPosition.value) * scale.value
    return {
      x,
      type: site.apa_type?.replace('-APA', '') || '',
      apa_type: site.apa_type
    }
  })
})

const getApaSiteColor = (site) => {
  switch (site.apa_type) {
    case '3UTR-APA':
      return '#E94560'
    case 'Intronic-APA':
      return '#FF6B6B'
    case 'Exonic-APA':
      return '#F97316'
    default:
      return '#E94560'
  }
}

const formatPosition = (pos) => {
  if (pos >= 1000000) {
    return (pos / 1000000).toFixed(2) + 'M'
  } else if (pos >= 1000) {
    return (pos / 1000).toFixed(1) + 'K'
  }
  return pos.toString()
}
</script>

<style scoped>
.utr-isoform-diagram {
  width: 100%;
  background: rgba(var(--v-theme-surface), 0.3);
  border-radius: 8px;
  padding: 16px;
}

.diagram-svg {
  display: block;
  margin: 0 auto;
}

.diagram-title {
  font-family: 'Roboto', sans-serif;
}

.diagram-legend {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: rgb(var(--v-theme-on-surface));
}

.legend-box {
  width: 16px;
  height: 16px;
  border-radius: 2px;
}

.legend-marker {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #E94560;
  font-size: 18px;
  font-weight: bold;
}
</style>
