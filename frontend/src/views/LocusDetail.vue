<template>
  <div class="locus-detail-page">
    <v-container class="py-8">
      <v-btn 
        variant="text" 
        @click="$router.back()" 
        class="mb-4"
      >
        <v-icon start>mdi-arrow-left</v-icon>
        Back to Search
      </v-btn>
      
      <div v-if="loading" class="d-flex justify-center align-center" style="min-height: 400px;">
        <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
      </div>
      
      <div v-else-if="error">
        <v-alert type="error" variant="tonal">
          {{ error }}
        </v-alert>
      </div>
      
      <div v-else-if="locusData">

        <!-- ── Transcript header card ─────────────────────────────── -->
        <div class="gene-header-card mb-6">
          <div class="gene-header-title">
            <v-icon icon="mdi-dna" size="22" class="mr-2" style="color: #0D7377; opacity: 0.85;"></v-icon>
            <span class="gene-name-text">{{ locusData.transcript.transcript_id }}</span>
          </div>
          <div class="gene-meta-row">
            <div class="gene-meta-item">
              <span class="gene-meta-label">Gene Symbol</span>
              <span class="gene-meta-value font-weight-medium">
                <router-link
                  :to="{ name: 'GeneDetail', params: { geneId: locusData.gene.gene_id } }"
                  class="gene-id-link"
                >{{ locusData.gene.gene_name }}</router-link>
              </span>
            </div>
            <div class="gene-meta-item">
              <span class="gene-meta-label">Gene ID</span>
              <span class="gene-meta-value">
                <router-link
                  :to="{ name: 'GeneDetail', params: { geneId: locusData.gene.gene_id } }"
                  class="gene-id-link"
                >{{ locusData.gene.gene_id }}</router-link>
              </span>
            </div>
            <div class="gene-meta-item">
              <span class="gene-meta-label">Chromosome</span>
              <v-chip size="small" variant="tonal" color="primary">{{ locusData.gene.chromosome }}</v-chip>
            </div>
            <div class="gene-meta-item">
              <span class="gene-meta-label">Strand</span>
              <v-chip size="small" variant="tonal" color="secondary">{{ locusData.gene.strand }}</v-chip>
            </div>
            <div class="gene-meta-item">
              <span class="gene-meta-label">PA Sites</span>
              <span class="gene-meta-value gene-meta-accent">{{ locusData.apa_sites.length }}</span>
            </div>
            <div class="gene-meta-item" v-if="locusData.transcript.transcript_biotype">
              <span class="gene-meta-label">Biotype</span>
              <span class="gene-meta-value">
                <v-chip size="small" variant="tonal" color="teal">{{ locusData.transcript.transcript_biotype }}</v-chip>
              </span>
            </div>
            <div class="gene-meta-item" style="align-items: flex-start;" v-if="locusData.apa_sites[0]?.species">
              <span class="gene-meta-label">Species</span>
              <span class="gene-meta-value">
                {{ locusData.apa_sites[0].species.name }}
                <span style="font-style: italic; opacity: 0.65; font-size: 13.5px;">{{ locusData.apa_sites[0].species.latin_name }}</span>
                <v-chip size="x-small" variant="tonal" color="secondary" class="ml-1">{{ locusData.apa_sites[0].species.assembly }}</v-chip>
              </span>
            </div>
          </div>
        </div>

        <!-- ── Genome Browser ───────────────────────────── -->
        <div class="section-card mb-6" v-if="transcriptStructure">
          <div class="section-title">
            <v-icon size="18" class="mr-2" style="color: #0D7377;">mdi-chart-gantt</v-icon>
            Genome Browser
            <v-chip size="small" variant="tonal" color="primary" class="ml-auto">
              Single Transcript View
            </v-chip>
          </div>
          <div class="panel-box">
            <div class="panel-body">
              <ApaGenomeBrowser
                :transcript-id="locusData.transcript.transcript_id"
                :gene-name="locusData.gene.gene_name"
                :chromosome="locusData.gene.chromosome"
                :strand="locusData.gene.strand"
                :exons="transcriptStructure.exons"
                :cds="transcriptStructure.cds"
                :apa-sites="locusData.apa_sites"
                :all-samples-info="locusData.samples"
              />
            </div>
          </div>
        </div>

        <!-- ── APA Sites Details ─────────────────────────────────────── -->
        <div class="section-card mb-6">
          <div class="section-title">
            <v-icon size="18" class="mr-2" style="color: #0D7377;">mdi-table</v-icon>
            PA Sites Details
            <div class="pas-legend ml-4">
              <span v-for="(meta, key) in PAS_TYPE_META" :key="key"
                class="pas-legend-item"
                :style="{ background: meta.bg, border: '1px solid ' + meta.border, color: meta.text }"
              >
                <span class="pas-chip-dot" :style="{ background: meta.border }"></span>
                {{ meta.label }}
              </span>
            </div>
          </div>
          <div class="panel-box">
            <div class="panel-body pa-0">
              <v-data-table
                :headers="tableHeaders"
                :items="flattenedTableData"
                :items-per-page="-1"
                hide-default-footer
                class="elegant-table"
                item-value="unified_id"
                v-model:expanded="seqOpen"
                :row-props="({ item }) => ({
                  class: seqOpen.includes(item.unified_id) ? 'row-seq-expanded ld-row-clickable' : 'ld-row-clickable',
                  onClick: () => toggleSeqPanel(item.unified_id)
                })"
              >
                <template v-slot:item.unified_id="{ item }">
                  <span class="ld-site-id-tag">{{ item.unified_id }}</span>
                </template>

                <template v-slot:item.mode_site_position="{ item }">
                  <code class="code-plain">{{ item.mode_site_position }}</code>
                </template>

                <template v-slot:item.pas_motif="{ item }">
                  <div v-if="item.pas_motif" class="d-flex align-center ga-1">
                    <span
                      class="pas-chip"
                      :style="{
                        background: pasTypeMeta(item.pas_type).bg,
                        border: '1px solid ' + pasTypeMeta(item.pas_type).border,
                        color: pasTypeMeta(item.pas_type).text,
                      }"
                    >
                      <span class="pas-chip-dot" :style="{ background: pasTypeMeta(item.pas_type).border }"></span>
                      {{ item.pas_motif }}
                    </span>
                    <span class="pas-type-label" :style="{ color: pasTypeMeta(item.pas_type).text }">
                      {{ pasTypeMeta(item.pas_type).label }}
                    </span>
                    <span class="text-caption text-grey" v-if="item.pas_position">
                      {{ item.pas_position }}bp
                    </span>
                  </div>
                  <span v-else class="pas-chip pas-chip--none">
                    <span class="pas-chip-dot" style="background:#BDBDBD"></span>
                    None
                  </span>
                </template>

                <template v-slot:item.sample_count="{ item }">
                  <v-chip size="small" variant="tonal" color="primary">
                    {{ item.sample_count }}
                  </v-chip>
                </template>

                <template v-slot:item.site_abundance="{ item }">
                  <div class="d-flex align-center ga-2">
                    <v-progress-linear
                      :model-value="item.site_abundance * 100"
                      color="primary"
                      height="6"
                      rounded
                      style="width: 80px;"
                    ></v-progress-linear>
                    <span class="text-body-2 font-weight-medium">
                      {{ (item.site_abundance * 100).toFixed(1) }}%
                    </span>
                  </div>
                </template>

                <template v-slot:item.expand="{ item }">
                  <v-icon
                    size="18"
                    class="ld-chevron"
                    :class="{ 'ld-chevron-open': seqOpen.includes(item.unified_id) }"
                  >mdi-chevron-right</v-icon>
                </template>

                <template v-slot:header.site_abundance="{ column }">
                  <div class="ld-header-cell-row">
                    {{ column.title }}
                    <v-menu location="bottom end" :close-on-content-click="true" max-width="320">
                      <template #activator="{ props }">
                        <v-icon
                          v-bind="props"
                          size="13"
                          class="tx-info-icon"
                          @click.stop
                        >mdi-help-circle-outline</v-icon>
                      </template>
                      <v-card class="tx-info-popover" elevation="0" rounded="lg">
                        <v-card-text class="tx-info-popover-text">
                          Arithmetic mean of the relative polyadenylation usage of this PA site on this transcript across all samples in which it was detected.
                        </v-card-text>
                      </v-card>
                    </v-menu>
                  </div>
                </template>

                <template v-slot:header.mode_site_position="{ column }">
                  <div class="ld-header-cell-row">
                    {{ column.title }}
                    <v-menu location="bottom end" :close-on-content-click="true" max-width="355">
                      <template #activator="{ props }">
                        <v-icon
                          v-bind="props"
                          size="13"
                          class="tx-info-icon"
                          @click.stop
                        >mdi-help-circle-outline</v-icon>
                      </template>
                      <v-card class="tx-info-popover" elevation="0" rounded="lg">
                        <v-card-text class="tx-info-popover-text">
                          The modal genomic coordinate of this PA site — the single nucleotide position most frequently observed as the cleavage-and-polyadenylation point across all supporting reads and samples.
                        </v-card-text>
                      </v-card>
                    </v-menu>
                  </div>
                </template>

                <template v-slot:expanded-row="{ item }">
                  <tr class="seq-expanded-row">
                    <td :colspan="tableHeaders.length" class="pa-0">
                      <div class="detail-panel">

                        <div class="detail-panel-inner">

                          <!-- Sample Abundance -->
                          <div v-if="item.sample_details && item.sample_details.length > 0" class="detail-section">
                            <div class="detail-section-label">
                              <v-icon size="12" class="mr-1" style="color:#0D7377;">mdi-chart-bar</v-icon>
                              Sample Abundance
                              <span class="detail-section-sub">{{ item.sample_details.length }} sample{{ item.sample_details.length > 1 ? 's' : '' }}</span>
                            </div>
                            <div class="sample-abundance-list">
                              <div v-for="sd in item.sample_details" :key="sd.sample_name" class="sample-abundance-row">
                                <div class="sample-abundance-label">
                                  <v-chip size="x-small" variant="tonal" color="primary" class="sample-name-chip">{{ sd.sample_name }}</v-chip>
                                  <span class="sample-type-text">{{ sd.sample_type ? sd.sample_type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) : '' }}</span>
                                </div>
                                <div class="sample-abundance-bar">
                                   <v-progress-linear
                                    :model-value="(sd.site_abundance || 0) * 100"
                                    color="primary"
                                    height="6"
                                    rounded
                                    class="sample-bar-track"
                                  ></v-progress-linear>
                                  <span class="sample-pct-text">{{ ((sd.site_abundance || 0) * 100).toFixed(1) }}%</span>
                                </div>
                              </div>
                            </div>
                          </div>

                          <!-- Loading -->
                          <div v-if="seqData[item.unified_id]?.loading" class="detail-section d-flex align-center" style="min-height:60px">
                            <v-progress-circular indeterminate size="20" color="primary" />
                            <span class="ml-3 text-body-2 text-medium-emphasis">Fetching sequence…</span>
                          </div>

                          <!-- Error -->
                          <div v-else-if="seqData[item.unified_id]?.error" class="detail-section">
                            <v-alert type="error" variant="tonal" density="compact">{{ seqData[item.unified_id].error }}</v-alert>
                          </div>

                          <!-- Sequence viewer -->
                          <div v-else-if="seqData[item.unified_id]?.data" class="detail-section">
                            <div class="detail-section-label">
                              <v-icon size="12" class="mr-1" style="color:#0D7377;">mdi-map-marker-path</v-icon>
                              Genomic Sequence Context
                            </div>
                            <div class="seq-meta-row">
                              <span class="seq-meta-chip seq-meta-strand">
                                {{ seqData[item.unified_id].data.strand === '+' ? '(+) positive strand' : '(−) negative strand' }}
                              </span>
                              <span class="seq-meta-chip">
                                {{ seqData[item.unified_id].data.chromosome }}:{{
                                  (seqData[item.unified_id].data.mode_site_position - seqData[item.unified_id].data.flank).toLocaleString()
                                }}–{{
                                  (seqData[item.unified_id].data.mode_site_position + seqData[item.unified_id].data.flank).toLocaleString()
                                }}
                              </span>
                              <span class="seq-meta-chip seq-meta-window">±{{ seqData[item.unified_id].data.flank }} bp window</span>
                              <template v-if="seqData[item.unified_id].data.pas_motif">
                                <span
                                  class="seq-meta-chip seq-meta-pas"
                                  :style="{ background: pasTypeMeta(seqData[item.unified_id].data.pas_type).bg, border: '1px solid ' + pasTypeMeta(seqData[item.unified_id].data.pas_type).border, color: pasTypeMeta(seqData[item.unified_id].data.pas_type).text }"
                                >
                                  {{ seqData[item.unified_id].data.pas_motif }} · {{ pasTypeMeta(seqData[item.unified_id].data.pas_type).label }}
                                  <span v-if="seqData[item.unified_id].data.pas_position"> · {{ seqData[item.unified_id].data.pas_position }}bp</span>
                                </span>
                              </template>
                              <span class="seq-meta-chip seq-meta-pasite">
                                <v-icon size="11" style="color:#D45D79;">mdi-map-marker</v-icon>
                                Representative PA Site
                              </span>
                            </div>
                            <div class="seq-display">
                              <span
                                v-for="(nt, idx) in seqData[item.unified_id].data.sequence.split('')"
                                :key="idx"
                                :class="seqNtClass(nt, idx, seqData[item.unified_id].data)"
                                :style="seqNtStyle(nt, idx, seqData[item.unified_id].data)"
                                :title="idx === seqData[item.unified_id].data.cleavage_index ? 'Cleavage site' : ''"
                              >{{ nt }}</span>
                            </div>
                          </div>

                        </div>
                      </div>
                    </td>
                  </tr>
                </template>

              </v-data-table>
            </div>
          </div>
        </div>

        <!-- ── Abundance Heatmap ─────────────────────────────────────────── -->
        <div class="section-card mb-6" v-if="heatmapData.sites.length > 0">
          <div class="section-title">
            <v-icon size="18" class="mr-2" style="color: #0D7377;">mdi-view-grid-outline</v-icon>
            Per-site Abundance Heatmap
            <div class="heatmap-stats-chip ml-3">
              {{ heatmapData.sites.length }} site{{ heatmapData.sites.length !== 1 ? 's' : '' }}
              <span class="heatmap-stats-sep">×</span>
              {{ heatmapData.samples.length }} sample{{ heatmapData.samples.length !== 1 ? 's' : '' }}
            </div>
            <v-tooltip location="bottom" max-width="320">
              <template #activator="{ props }">
                <v-icon v-bind="props" icon="mdi-information-outline" size="small" class="ml-2" style="color: rgba(0,0,0,0.38);"></v-icon>
              </template>
              Colour intensity shows relative abundance (0–100%) of each PA site in each sample.
              Darker = higher usage. Hatched = site not detected in that sample.
            </v-tooltip>
          </div>
          <div class="panel-box" style="overflow: visible;">
            <div class="panel-body pa-5">
              <div class="heatmap-wrap">
                <div class="heatmap-grid" :style="heatmapGridStyle">

                  <!-- ┌─ Corner ───────────────────────────────────────── -->
                  <div class="heatmap-corner">
                    <span class="heatmap-corner-text">PA&nbsp;Site</span>
                    <v-icon size="10" style="color:rgba(0,0,0,0.28);margin:0 2px;">mdi-arrow-right</v-icon>
                    <span class="heatmap-corner-text">Sample</span>
                  </div>

                  <!-- ┌─ Column headers (samples) ─────────────────────── -->
                  <div
                    v-for="(sample, si) in heatmapData.samples"
                    :key="sample"
                    class="heatmap-col-header"
                    :class="{ 'hm-col-active': hoverSampleName === sample }"
                  >
                    <span
                      class="heatmap-sample-dot"
                      :style="{ background: heatmapSampleColor(si) }"
                    ></span>
                    <span class="heatmap-col-text">{{ sample }}</span>
                  </div>

                  <!-- ┌─ Data rows ────────────────────────────────────── -->
                  <template v-for="(site, si) in heatmapData.sites" :key="site.id">

                    <!-- Row label: numbered badge + full site ID, no position -->
                    <div class="heatmap-row-label" :class="{ 'hm-row-active': hoverSiteId === site.id }">
                      <span class="heatmap-site-badge" :style="heatmapBadgeStyle(si)">{{ si + 1 }}</span>
                      <span class="heatmap-site-id">{{ site.id }}</span>
                    </div>

                    <!-- Cells: plain divs; cross-hair highlight on hover -->
                    <div
                      v-for="sample in heatmapData.samples"
                      :key="sample"
                      class="heatmap-cell"
                      :class="heatmapCellClass(site.id, sample)"
                      :style="heatmapCellStyle(site.id, sample)"
                      @mouseenter="(e) => onCellEnter(e, site, sample)"
                      @mouseleave="onCellLeave"
                    >
                      <div class="heatmap-cell-inner">
                        <span
                          class="heatmap-cell-pct"
                          :style="{ color: heatmapTextColor(site.id, sample) }"
                        >{{ heatmapLabel(site.id, sample) }}</span>
                      </div>
                    </div>

                  </template>
                </div>

                <!-- ── Legend ──────────────────────────────────────────── -->
                <div class="heatmap-legend">
                  <div class="heatmap-legend-left">
                    <div class="heatmap-legend-scale">
                      <span class="heatmap-legend-tick">0%</span>
                      <div class="heatmap-legend-bar"></div>
                      <span class="heatmap-legend-tick">100%</span>
                    </div>
                    <span class="heatmap-legend-caption">Relative Abundance</span>
                  </div>
                  <div class="heatmap-legend-nd">
                    <span class="heatmap-legend-nd-swatch"></span>
                    <span class="heatmap-legend-nd-label">Not detected</span>
                  </div>
                </div>

              </div>
            </div>
          </div>
        </div>

      </div><!-- closes v-else-if="locusData" -->

    </v-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Bar } from 'vue-chartjs'
import { 
  Chart as ChartJS, 
  BarElement, 
  CategoryScale, 
  LinearScale, 
  Tooltip, 
  Legend,
  Title 
} from 'chart.js'
import { apiService } from '@/services/api'
import UTRIsoformDiagram from '@/components/UTRIsoformDiagram.vue'
import ApaGenomeBrowser from '@/components/ApaGenomeBrowser.vue'

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend, Title)

const route = useRoute()

const loading = ref(true)
const error = ref(null)
const locusData = ref(null)
const transcriptStructure = ref(null)
const selectedSiteId = ref(null)
const selectedSample = ref(null)


// ── Sequence context panel ─────────────────────────────────────────────────
// seqOpen: array of site_ids whose sequence panel is expanded (v-model:expanded expects array)
// seqData: Map of unified_id → { loading, data, error }
const seqOpen = ref([])
const seqData = ref({})

const toggleSeqPanel = async (siteId) => {
  const idx = seqOpen.value.indexOf(siteId)
  if (idx !== -1) {
    seqOpen.value = seqOpen.value.filter(id => id !== siteId)
    return
  }
  seqOpen.value = [...seqOpen.value, siteId]

  // Fetch if not already loaded
  if (!seqData.value[siteId]) {
    seqData.value = { ...seqData.value, [siteId]: { loading: true, data: null, error: null } }
    try {
      const transcriptId = locusData.value.transcript.transcript_id
      const result = await apiService.getSiteSequence(transcriptId, siteId)
      seqData.value = { ...seqData.value, [siteId]: { loading: false, data: result, error: null } }
    } catch (e) {
      seqData.value = { ...seqData.value, [siteId]: { loading: false, data: null, error: 'Failed to load sequence' } }
    }
  }
}

// Nucleotide colouring + cleavage/PAS highlighting
const seqNtClass = (nt, idx, data) => {
  if (idx === data.cleavage_index) return 'seq-nt seq-nt--cleavage'
  if (data.pas_motif && data.pas_position !== null && data.pas_position !== undefined) {
    const motifStart = data.cleavage_index + data.pas_position
    const motifEnd   = motifStart + data.pas_motif.length
    if (idx >= motifStart && idx < motifEnd) return 'seq-nt seq-nt--pas'
  }
  return 'seq-nt'
}

// Inline style for PAS motif — uses exact pasTypeMeta colours so it always matches the chip
const seqNtStyle = (nt, idx, data) => {
  if (idx === data.cleavage_index) return {}
  if (data.pas_motif && data.pas_position !== null && data.pas_position !== undefined) {
    const motifStart = data.cleavage_index + data.pas_position
    const motifEnd   = motifStart + data.pas_motif.length
    if (idx >= motifStart && idx < motifEnd) {
      const meta = pasTypeMeta(data.pas_type)
      return { background: meta.bg, color: meta.text }
    }
  }
  return {}
}

const tableHeaders = [
  { title: '', key: 'expand', sortable: false, width: 48 },
  { title: 'Site ID', key: 'unified_id', sortable: true },
  { title: 'Rep. Position', key: 'mode_site_position', sortable: true },
  { title: 'PAS Motif', key: 'pas_motif', sortable: true },
  { title: 'Samples', key: 'sample_count', sortable: true, width: 88 },
  { title: 'Mean Abundance', key: 'site_abundance', sortable: true, width: 150 },
]

const sampleSiteChartOptions = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: function(context) {
          return 'Abundance: ' + (context.raw * 100).toFixed(1) + '%'
        }
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      max: 1,
      title: { display: true, text: 'Abundance' },
      ticks: {
        callback: function(value) {
          return (value * 100).toFixed(0) + '%'
        }
      }
    },
    x: {
      title: { display: true, text: 'PA Site' },
      ticks: {
        maxRotation: 45,
        minRotation: 45
      }
    }
  }
}

const barChartOptions = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: { display: false },
    title: {
      display: true,
      text: 'Site Abundance by Sample',
      font: { size: 14, weight: 'normal' }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      max: 1,
      title: { display: true, text: 'Abundance' },
      ticks: {
        callback: function(value) {
          return (value * 100).toFixed(0) + '%'
        }
      }
    },
    x: {
      title: { display: true, text: 'Sample' }
    }
  }
}

const siteIdOptions = computed(() => {
  if (!locusData.value) return []
  return locusData.value.apa_sites.map(site => ({
    value: site.unified_id,
    label: site.unified_id.substring(0, 20) + (site.unified_id.length > 20 ? '...' : ''),
    position: site.mode_site_position,
    samples: site.sample_details?.length || 0
  }))
})

const sampleOptions = computed(() => {
  if (!locusData.value) return []
  return (locusData.value.samples || []).map(s => s?.name ?? s)
})

const sampleSiteAbundanceData = computed(() => {
  if (!locusData.value || !selectedSample.value) return null
  
  const sites = locusData.value.apa_sites
  if (sites.length === 0) return null
  
  const labels = []
  const data = []
  const colors = ['#0D7377', '#14919B', '#323232', '#E94560', '#FF6B6B', '#4ECDC4', '#5C6BC0', '#AB47BC']
  
  sites.forEach((site, index) => {
    // Shorten unified_id for label
    const shortId = site.unified_id.length > 15 
      ? site.unified_id.substring(0, 15) + '...' 
      : site.unified_id
    labels.push(shortId)
    
    // Find abundance for selected sample
    const sampleDetail = site.sample_details?.find(sd => sd.sample_name === selectedSample.value)
    data.push(sampleDetail?.site_abundance || 0)
  })
  
  if (labels.length === 0) return null
  
  // Dynamic bar width: fixed for few sites, auto for many
  const siteCount = labels.length
  const barPercentage = siteCount <= 3 ? 0.4 : 0.7
  const categoryPercentage = siteCount <= 3 ? 0.5 : 0.8
  
  return {
    labels,
    datasets: [{
      label: 'Abundance',
      data,
      backgroundColor: colors.slice(0, sites.length),
      borderRadius: 6,
      barPercentage,
      categoryPercentage
    }]
  }
})

const flattenedTableData = computed(() => {
  if (!locusData.value) return []
  return locusData.value.apa_sites.map(site => {
    const samples = site.sample_details || []
    const avgAbundance = samples.length > 0
      ? samples.reduce((sum, sd) => sum + (sd.site_abundance || 0), 0) / samples.length
      : site.site_abundance || 0
    return {
      unified_id: site.unified_id,
      mode_site_position: site.mode_site_position,
      pas_motif: site.pas_motif,
      pas_position: site.pas_position,
      pas_type: site.pas_type,
      sample_count: samples.length,
      site_abundance: avgAbundance,
      site_count: site.site_count,
      sample_details: samples,
    }
  })
})

const ucscBrowserLink = computed(() => {
  if (!locusData.value) return ''
  const gene = locusData.value.gene
  const chromosome = gene.chromosome
  const apaSites = locusData.value.apa_sites
  if (apaSites.length === 0) return ''
  
  const positions = apaSites.map(s => s.mode_site_position)
  const minPos = Math.min(...positions) - 5000
  const maxPos = Math.max(...positions) + 5000
  
  const assembly = 'hg38'
  return `https://genome.ucsc.edu/cgi-bin/hgTracks?db=${assembly}&position=chr${chromosome}:${minPos}-${maxPos}`
})

const ensemblBrowserLink = computed(() => {
  if (!locusData.value) return ''
  const gene = locusData.value.gene
  return `https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=${gene.gene_id}`
})

const geneStructureData = computed(() => {
  if (!locusData.value) return null
  
  return {
    gene_name: locusData.value.gene.gene_name,
    transcript_id: locusData.value.transcript.transcript_id,
    exons: []
  }
})

const selectAPASiteById = (siteId) => {
  selectedSiteId.value = siteId
}

const onSiteSelected = (site) => {
  selectedSiteId.value = site?.value || null
}

// ── Heatmap ────────────────────────────────────────────────────────────────

// Build the flat lookup: { [siteId]: { [sampleName]: { abundance, count } } }
const heatmapLookup = computed(() => {
  if (!locusData.value) return {}
  const lookup = {}
  for (const site of locusData.value.apa_sites) {
    lookup[site.unified_id] = {}
    for (const sd of (site.sample_details || [])) {
      lookup[site.unified_id][sd.sample_name] = {
        abundance: sd.site_abundance,
        count: sd.site_count
      }
    }
  }
  return lookup
})

const heatmapData = computed(() => {
  if (!locusData.value) return { sites: [], samples: [] }
  // samples may be [{name, sample_type}] objects or plain strings — normalise to strings
  const allSamples = (locusData.value.samples || []).map(s => s?.name ?? s)
  const sites = locusData.value.apa_sites.map(s => ({
    id: s.unified_id,
    position: s.mode_site_position
  }))
  // Sort sites by position (proximal → distal)
  const strand = locusData.value.gene.strand
  sites.sort((a, b) => strand === '-' ? b.position - a.position : a.position - b.position)
  return { sites, samples: allSamples }
})

const heatmapGridStyle = computed(() => {
  const n = heatmapData.value.samples.length
  // Use fixed-width columns so few-sample layouts don't stretch awkwardly.
  // Each sample column is clamped between 80 px and 140 px.
  return {
    display: 'grid',
    gridTemplateColumns: `max-content repeat(${n}, 72px)`,
    gap: '3px'
  }
})

const HEATMAP_COLOR = [13, 115, 119]   // RGB of primary teal #0D7377

const heatmapCellStyle = (siteId, sample) => {
  const entry = heatmapLookup.value[siteId]?.[sample]
  if (!entry) {
    return {
      background: 'repeating-linear-gradient(45deg, rgba(0,0,0,0.03) 0px, rgba(0,0,0,0.03) 4px, rgba(0,0,0,0.06) 4px, rgba(0,0,0,0.06) 8px)',
      border: '1px solid rgba(0,0,0,0.08)'
    }
  }
  const alpha = Math.max(0.08, entry.abundance)
  const [r, g, b] = HEATMAP_COLOR
  return {
    background: `rgba(${r},${g},${b},${alpha})`,
    border: '1px solid rgba(0,0,0,0.06)'
  }
}

const heatmapTextColor = (siteId, sample) => {
  const entry = heatmapLookup.value[siteId]?.[sample]
  if (!entry) return 'rgba(0,0,0,0.3)'
  return entry.abundance > 0.5 ? '#ffffff' : '#1a1a1a'
}

const heatmapLabel = (siteId, sample) => {
  const entry = heatmapLookup.value[siteId]?.[sample]
  if (!entry) return '—'
  return (entry.abundance * 100).toFixed(0) + '%'
}

const heatmapCount = (siteId, sample) => {
  const entry = heatmapLookup.value[siteId]?.[sample]
  return entry ? entry.count : 0
}

// ── Heatmap visual helpers ──────────────────────────────────────────────────

const HEATMAP_SAMPLE_COLORS = [
  '#0D7377', '#6366F1', '#EC4899', '#F59E0B', '#10B981', '#3B82F6', '#EF4444', '#8B5CF6'
]
const heatmapSampleColor = (idx) => HEATMAP_SAMPLE_COLORS[idx % HEATMAP_SAMPLE_COLORS.length]

const BADGE_GRADIENTS = [
  ['#0D7377', '#14919B'],
  ['#6366F1', '#818CF8'],
  ['#EC4899', '#F472B6'],
  ['#F59E0B', '#FCD34D'],
  ['#10B981', '#34D399'],
  ['#3B82F6', '#60A5FA'],
  ['#EF4444', '#F87171'],
  ['#8B5CF6', '#A78BFA'],
]
const heatmapBadgeStyle = (idx) => {
  const [c1, c2] = BADGE_GRADIENTS[idx % BADGE_GRADIENTS.length]
  return { background: `linear-gradient(135deg, ${c1}, ${c2})` }
}

// Show site ID truncated; full ID visible in tooltip
const formatSiteId = (id) => {
  if (!id) return '—'
  return id.length > 24 ? id.substring(0, 22) + '…' : id
}

// ── Heatmap cross-hair hover state ─────────────────────────────────────────
const hoverSiteId = ref(null)
const hoverSampleName = ref(null)

function onCellEnter(_event, site, sample) {
  hoverSiteId.value = site.id
  hoverSampleName.value = sample
}

function onCellLeave() {
  hoverSiteId.value = null
  hoverSampleName.value = null
}

const heatmapCellClass = (siteId, sample) => {
  if (hoverSiteId.value === null) return ''
  const inRow = hoverSiteId.value === siteId
  const inCol = hoverSampleName.value === sample
  if (inRow && inCol) return 'hm-cross-intersection'
  if (inRow || inCol) return 'hm-cross-arm'
  return 'hm-dimmed'
}

const PAS_TYPE_META = {
  canonical  : { label: 'Canonical',   bg: 'rgba(22,163,74,0.12)',   border: '#16A34A', text: '#15803D' },
  variant    : { label: 'Variant',     bg: 'rgba(37,99,235,0.12)',   border: '#2563EB', text: '#1D4ED8' },
  upstream   : { label: 'Upstream',    bg: 'rgba(234,88,12,0.10)',   border: '#EA580C', text: '#C2410C' },
  downstream : { label: 'Downstream',  bg: 'rgba(139,92,246,0.10)',  border: '#8B5CF6', text: '#7C3AED' },
  none       : { label: 'None',        bg: 'rgba(0,0,0,0.05)',       border: '#9CA3AF', text: '#6B7280' },
}
const pasTypeMeta = (type) => PAS_TYPE_META[type] ?? PAS_TYPE_META.none

const abundanceBarChartData = computed(() => {
  if (!locusData.value || !selectedSiteId.value) return null
  
  const site = locusData.value.apa_sites.find(s => s.unified_id === selectedSiteId.value)
  if (!site || !site.sample_details) return null
  
  const labels = site.sample_details.map(sd => sd.sample_name)
  const data = site.sample_details.map(sd => sd.site_abundance)
  
  if (labels.length === 0) return null
  
  // Dynamic bar width: fixed for few samples, auto for many
  const sampleCount = labels.length
  const barPercentage = sampleCount <= 3 ? 0.5 : 0.8
  const categoryPercentage = sampleCount <= 3 ? 0.6 : 0.8
  
  return {
    labels,
    datasets: [{
      label: 'Abundance',
      data,
      backgroundColor: ['#0D7377', '#14919B', '#323232', '#E94560', '#FF6B6B', '#4ECDC4'],
      borderRadius: 6,
      barPercentage,
      categoryPercentage
    }]
  }
})

onMounted(async () => {
  const transcriptId = route.params.transcriptId
  
  loading.value = true
  error.value = null
  
  try {
    // Fetch locus data first — this is required for the page
    const locusResponse = await apiService.getLocusDetail(transcriptId)
    locusData.value = locusResponse

    if (locusData.value.apa_sites && locusData.value.apa_sites.length > 0) {
      selectedSiteId.value = locusData.value.apa_sites[0].unified_id
    }
    if (locusData.value.samples && locusData.value.samples.length > 0) {
      selectedSample.value = locusData.value.samples[0]?.name ?? locusData.value.samples[0]
    }

    // Fetch transcript structure separately — failure is non-fatal
    apiService.getTranscriptStructure(transcriptId)
      .then(structureResponse => {
        transcriptStructure.value = structureResponse
      })
      .catch(structureErr => {
        console.warn('Transcript structure not available:', structureErr)
        // Page still works without structure (genome browser will be hidden)
      })

  } catch (err) {
    console.error('Failed to load locus detail:', err)
    error.value = 'Failed to load locus details. Please try again.'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.locus-detail-page {
  min-height: 100vh;
  background: rgb(var(--v-theme-background));
}

a {
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

code {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
}

/* ── Gene/Transcript header card ─────────────────────────────────── */
.gene-header-card {
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(16px) saturate(160%);
  -webkit-backdrop-filter: blur(16px) saturate(160%);
  border: 1px solid rgba(255, 255, 255, 0.62);
  border-radius: 16px;
  padding: 20px 24px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.07), 0 1px 4px rgba(0, 0, 0, 0.04);
}

.gene-header-title {
  display: flex;
  align-items: center;
  margin-bottom: 14px;
}

.gene-name-text {
  font-size: 1.6rem;
  font-weight: 700;
  color: rgba(0,0,0,0.87);
  letter-spacing: -0.01em;
}

.gene-meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 28px;
}

.gene-meta-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}



.gene-meta-label {
  font-size: 12.5px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(0,0,0,0.42);
}

.gene-meta-value {
  font-size: 15px;
  font-weight: 500;
  color: rgba(0,0,0,0.80);
  display: flex;
  align-items: center;
  gap: 4px;
}

.gene-meta-accent {
  font-size: 15px;
  font-weight: 700;
  color: #0D7377;
}

.gene-id-link {
  font-weight: 600;
  color: #0D7377;
  text-decoration: none;
}

.gene-id-link:hover {
  color: #14919B;
  text-decoration: underline;
}

/* ── Section card ─────────────────────────────────────────────────── */
.section-card {
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(16px) saturate(160%);
  -webkit-backdrop-filter: blur(16px) saturate(160%);
  border: 1px solid rgba(255, 255, 255, 0.58);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06), 0 1px 4px rgba(0, 0, 0, 0.04);
}

.section-title {
  display: flex;
  align-items: center;
  font-size: 1.15rem;
  font-weight: 700;
  color: rgba(0,0,0,0.80);
  margin-bottom: 20px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(0,0,0,0.07);
}

/* ── Panel box ────────────────────────────────────────────────────── */
.panel-box {
  border: 1px solid rgba(13, 115, 119, 0.14);
  border-radius: 12px;
  overflow: hidden;
  background: rgba(250, 252, 252, 0.85);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
  background: rgba(13, 115, 119, 0.06);
  border-bottom: 1px solid rgba(13, 115, 119, 0.12);
  flex-wrap: wrap;
}

.panel-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.panel-icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  flex-shrink: 0;
}

.panel-icon-teal {
  background: #0D7377;
}

.panel-title-text {
  font-size: 1.02rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.82);
  line-height: 1.3;
}

.panel-subtitle-text {
  font-size: 0.86rem;
  color: rgba(0, 0, 0, 0.46);
  margin-top: 2px;
  max-width: 480px;
}

.panel-body {
  padding: 16px;
}

.pas-motif {
  font-weight: 600;
  color: #0D7377;
  letter-spacing: 0.5px;
}

/* ── PAS motif type chips ─────────────────────────────────────────── */
.pas-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 8px 2px 6px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  font-family: 'Roboto Mono', 'Courier New', monospace;
  letter-spacing: 0.3px;
  white-space: nowrap;
  line-height: 1.6;
}

.pas-chip--none {
  background: rgba(0, 0, 0, 0.05);
  border: 1px solid #BDBDBD;
  color: #757575;
  font-family: 'Roboto', sans-serif;
  font-style: italic;
}

.pas-chip-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.pas-type-label {
  font-size: 12.5px;
  font-family: 'Roboto', sans-serif;
  font-weight: 500;
  opacity: 0.85;
}

/* ── PAS legend strip ─────────────────────────────────────────────── */
.pas-legend {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  font-size: 12px;
  font-weight: 400;
}

.pas-legend-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px 2px 6px;
  border-radius: 20px;
  font-size: 12.5px;
  font-family: 'Roboto', sans-serif;
  font-weight: 500;
  white-space: nowrap;
}

.elegant-table :deep(code) {
  background: rgba(13, 115, 119, 0.08);
  color: #0D7377;
  padding: 2px 7px;
  border-radius: 4px;
  font-size: 13px;
  font-family: 'Roboto', sans-serif;
}

.elegant-table :deep(code.code-plain) {
  background: none;
  border-radius: 0;
  padding: 0;
  font-family: 'Roboto', sans-serif;
}

.light-card-bg {
  background: rgba(var(--v-theme-surface), 0.5) !important;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.elegant-table {
  background: transparent !important;
  font-family: 'Roboto', sans-serif;
  font-size: 14.5px;
}

.elegant-table :deep(.v-data-table__th) {
  background: rgba(13, 115, 119, 0.04) !important;
  font-size: 12.5px !important;
  font-weight: 600 !important;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  color: rgba(0, 0, 0, 0.60) !important;
  border-bottom: 1px solid rgba(13, 115, 119, 0.10) !important;
  white-space: nowrap;
  font-family: 'Roboto', sans-serif;
}

.elegant-table :deep(.v-data-table__td) {
  padding: 11px 16px;
  background: transparent !important;
  color: rgba(0, 0, 0, 0.82);
  border-bottom: 1px solid rgba(0, 0, 0, 0.055) !important;
  font-family: 'Roboto', sans-serif;
  font-size: 13px;
}

/* When row is expanded: suppress the full-width td borders */
.elegant-table :deep(.row-seq-expanded .v-data-table__td) {
  border-bottom: none !important;
}

.elegant-table :deep(.v-data-table__tr:hover .v-data-table__td) {
  background: rgba(13, 115, 119, 0.04) !important;
}

.elegant-table :deep(.v-data-table-footer) {
  background: transparent !important;
  border-top: 1px solid rgba(13, 115, 119, 0.10) !important;
  font-size: 13.5px;
  color: rgba(0, 0, 0, 0.60);
}

.elegant-table :deep(.v-data-table) {
  background: transparent !important;
}

.elegant-table :deep(table) {
  background: transparent !important;
}

.elegant-table :deep(tbody) {
  background: transparent !important;
}

.elegant-table :deep(thead) {
  background: rgba(13, 115, 119, 0.04) !important;
}

/* ── Heatmap ──────────────────────────────────────────────────────── */
.heatmap-wrap {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.heatmap-grid {
  min-width: 300px;
  max-width: max-content;
  border: 1px solid rgba(13, 115, 119, 0.14);
  box-shadow: 0 2px 14px rgba(13, 115, 119, 0.07);
  border-radius: 8px;
}

/* ── Corner cell ── */
.heatmap-corner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  padding: 10px 12px;
  background: rgba(13, 115, 119, 0.07);
  border-right: 1px solid rgba(13, 115, 119, 0.12);
  border-bottom: 2px solid rgba(13, 115, 119, 0.12);
  min-height: 46px;
}

.heatmap-corner-text {
  font-size: 10.5px;
  font-family: 'Roboto', sans-serif;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.38);
  text-transform: uppercase;
  letter-spacing: 0.6px;
}

/* ── Column headers ── */
.heatmap-col-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  padding: 12px 6px 12px;
  gap: 7px;
  background: rgba(13, 115, 119, 0.04);
  border-bottom: 2px solid rgba(13, 115, 119, 0.12);
  border-right: 1px solid rgba(13, 115, 119, 0.07);
  min-height: 96px;
}

.heatmap-sample-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.85), 0 1px 4px rgba(0, 0, 0, 0.15);
}

.heatmap-col-text {
  font-size: 12px;
  font-family: 'Roboto', sans-serif;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.62);
  letter-spacing: 0.2px;
  writing-mode: vertical-lr;
  text-orientation: mixed;
  transform: rotate(180deg);
  white-space: nowrap;
  max-height: 80px;
}

/* ── Row labels ── */
.heatmap-row-label {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 14px 0 10px;
  background: rgba(13, 115, 119, 0.03);
  border-right: 2px solid rgba(13, 115, 119, 0.12);
  border-bottom: 1px solid rgba(13, 115, 119, 0.07);
  min-height: 44px;
}

.heatmap-site-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  border-radius: 50%;
  color: white;
  font-size: 11px;
  font-weight: 700;
  font-family: 'Roboto', sans-serif;
  flex-shrink: 0;
  box-shadow: 0 1px 5px rgba(0, 0, 0, 0.22);
  letter-spacing: -0.2px;
}

.heatmap-site-id {
  font-size: 12px;
  font-family: 'Roboto', sans-serif;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.80);
  white-space: nowrap;
  cursor: default;
  letter-spacing: -0.2px;
}

/* ── Cells ── */
.heatmap-cell {
  min-height: 44px;
  cursor: default;
  transition: opacity 0.12s ease, box-shadow 0.12s ease;
  position: relative;
  border-right: 1px solid rgba(255, 255, 255, 0.18);
  border-bottom: 1px solid rgba(255, 255, 255, 0.18);
}

/* ── Cross-hair highlight ── */
.heatmap-cell.hm-dimmed {
  opacity: 0.30;
}

.heatmap-cell.hm-cross-arm {
  box-shadow: inset 0 0 0 1.5px rgba(13, 115, 119, 0.45);
  filter: brightness(1.12);
}

.heatmap-cell.hm-cross-intersection {
  box-shadow: inset 0 0 0 2px rgba(13, 115, 119, 0.90);
  filter: brightness(1.22);
  z-index: 1;
}

.hm-row-active {
  background: rgba(13, 115, 119, 0.10) !important;
}

.hm-col-active {
  background: rgba(13, 115, 119, 0.08) !important;
}

.heatmap-cell-inner {
  width: 100%;
  height: 100%;
  min-height: 44px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  padding: 6px 4px;
}

.heatmap-cell-pct {
  font-size: 11.5px;
  font-weight: 700;
  font-family: 'Roboto', sans-serif;
  line-height: 1;
  letter-spacing: -0.3px;
}

/* ── Stats chip in section title ── */
.heatmap-stats-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border-radius: 20px;
  background: rgba(13, 115, 119, 0.08);
  border: 1px solid rgba(13, 115, 119, 0.16);
  font-size: 12px;
  font-weight: 500;
  color: #0D7377;
  font-family: 'Roboto', sans-serif;
}

.heatmap-stats-sep {
  opacity: 0.48;
  font-size: 11px;
}

/* ── Legend ── */
.heatmap-legend {
  margin-top: 18px;
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.heatmap-legend-left {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.heatmap-legend-scale {
  display: flex;
  align-items: center;
  gap: 8px;
}

.heatmap-legend-tick {
  font-size: 11.5px;
  font-family: 'Roboto', sans-serif;
  color: rgba(0, 0, 0, 0.48);
  min-width: 26px;
}

.heatmap-legend-tick:last-child {
  text-align: right;
}

.heatmap-legend-bar {
  width: 180px;
  height: 11px;
  border-radius: 6px;
  background: linear-gradient(
    to right,
    rgba(13, 115, 119, 0.06),
    rgba(13, 115, 119, 0.28),
    rgba(13, 115, 119, 0.62),
    rgba(13, 115, 119, 1.0)
  );
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.heatmap-legend-caption {
  font-size: 10.5px;
  font-family: 'Roboto', sans-serif;
  color: rgba(0, 0, 0, 0.38);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.7px;
  padding-left: 2px;
}

.heatmap-legend-nd {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 5px 12px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.09);
  background: rgba(0, 0, 0, 0.015);
}

.heatmap-legend-nd-swatch {
  display: inline-block;
  width: 16px;
  height: 16px;
  border-radius: 4px;
  background: repeating-linear-gradient(
    45deg,
    rgba(0, 0, 0, 0.04) 0px,
    rgba(0, 0, 0, 0.04) 3px,
    rgba(0, 0, 0, 0.10) 3px,
    rgba(0, 0, 0, 0.10) 6px
  );
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.heatmap-legend-nd-label {
  font-size: 12px;
  font-family: 'Roboto', sans-serif;
  color: rgba(0, 0, 0, 0.48);
}

/* ── Site ID tag (outer table) ───────────────────────────────────── */
.ld-site-id-tag {
  display: inline-block;
  font-family: 'Roboto', sans-serif;
  font-weight: 500;
  color: #0D7377;
  background: rgba(13, 115, 119, 0.10);
  border: 1px solid rgba(13, 115, 119, 0.22);
  border-radius: 10px;
  padding: 2px 9px;
  white-space: nowrap;
  cursor: default;
}

/* ── Row expand chevron ──────────────────────────────────────────── */
.ld-row-clickable {
  cursor: pointer;
}

.ld-chevron {
  color: rgba(13, 115, 119, 0.45);
  transition: color 0.15s ease, transform 0.2s ease;
  display: block;
}

.ld-row-clickable:hover .ld-chevron {
  color: #0D7377;
}

.ld-chevron-open {
  transform: rotate(90deg);
  color: #0D7377;
}

/* ── Expanded row container ──────────────────────────────────────── */
.seq-expanded-row td {
  background: transparent !important;
  padding: 0 !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.055) !important;
  vertical-align: top;
}

.detail-panel {
  width: 100%;
  box-sizing: border-box;
  background: rgba(13, 115, 119, 0.03);
  border-top: 1px solid rgba(13, 115, 119, 0.12);
}

.detail-panel-inner {
  box-sizing: border-box;
  width: 100%;
  padding: 12px 24px 16px 66px;
  display: flex;
  flex-direction: column;
}

.detail-section {
  box-sizing: border-box;
  width: 100%;
  padding: 14px 0 14px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.055);
}

.detail-section:last-child {
  border-bottom: none;
}

.detail-section-label {
  display: flex;
  align-items: center;
  font-size: 12.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: #0D7377;
  margin-bottom: 8px;
  gap: 2px;
}

.detail-section-sub {
  font-weight: 400;
  text-transform: none;
  letter-spacing: 0;
  color: rgba(0, 0, 0, 0.35);
  font-style: italic;
  margin-left: 4px;
}

/* ── Sample abundance ────────────────────────────────────────────── */
.sample-abundance-list {
  display: flex;
  flex-direction: column;
  gap: 9px;
  max-height: 200px;
  overflow-y: auto;
  padding-right: 6px;
}

.sample-abundance-row {
  display: grid;
  grid-template-columns: minmax(120px, 220px) 1fr;
  align-items: center;
  gap: 12px;
  min-height: 24px;
}

.sample-abundance-label {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.sample-name-chip {
  flex-shrink: 0;
  font-size: 12px !important;
  font-family: 'Roboto', sans-serif !important;
}

.sample-type-text {
  font-size: 11px;
  font-family: 'Roboto', sans-serif;
  color: rgba(0, 0, 0, 0.38);
  font-style: italic;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sample-abundance-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-width: 0;
}

.sample-bar-track { flex: 1; min-width: 0; }

.sample-pct-text {
  font-size: 12px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.55);
  width: 44px;
  flex-shrink: 0;
  font-family: 'Roboto', sans-serif;
}

/* ── Sequence viewer ─────────────────────────────────────────────── */
.seq-meta-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  padding-bottom: 8px;
}

.seq-meta-chip {
  display: inline-flex;
  align-items: center;
  line-height: 1;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 9px;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.06);
  color: rgba(0, 0, 0, 0.65);
  border: 1px solid rgba(0, 0, 0, 0.10);
}

.seq-meta-strand {
  background: rgba(13, 115, 119, 0.10);
  color: #0D7377;
  border-color: rgba(13, 115, 119, 0.25);
}

.seq-meta-window {
  background: rgba(0, 0, 0, 0.04);
}

.seq-meta-pasite {
  background: rgba(212, 93, 121, 0.08);
  border-color: rgba(212, 93, 121, 0.25);
  color: rgba(0, 0, 0, 0.55);
  gap: 4px;
}

.seq-display {
  box-sizing: border-box;
  width: 100%;
  font-family: 'Roboto Mono', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  letter-spacing: 0.05em;
  white-space: nowrap;
  overflow-x: auto;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  padding: 8px 0 2px;
}

.seq-nt {
  display: inline;
  color: rgba(0, 0, 0, 0.82);
}

.seq-nt--pas {
  border-radius: 2px;
  font-weight: 700;
}

.seq-nt--cleavage {
  background: #D45D79;
  color: #fff;
  border-radius: 3px;
  padding: 0 1px;
  font-weight: 700;
}

/* ── Dark mode ─────────────────────────────────────────────────── */
.v-theme--apaAtlasDarkTheme .gene-header-card {
  background: rgba(24, 28, 37, 0.82);
  border: 1px solid rgba(255, 255, 255, 0.07);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.35), 0 1px 4px rgba(0, 0, 0, 0.25);
}

.v-theme--apaAtlasDarkTheme .section-card {
  background: rgba(24, 28, 37, 0.80);
  border: 1px solid rgba(255, 255, 255, 0.07);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.30), 0 1px 4px rgba(0, 0, 0, 0.20);
}

.v-theme--apaAtlasDarkTheme .section-title {
  color: rgba(255, 255, 255, 0.85);
  border-bottom-color: rgba(255, 255, 255, 0.07);
}

.v-theme--apaAtlasDarkTheme .panel-box {
  background: rgba(20, 24, 33, 0.85);
  border-color: rgba(42, 168, 174, 0.15);
}

.v-theme--apaAtlasDarkTheme .panel-header {
  background: rgba(42, 168, 174, 0.07);
  border-bottom-color: rgba(42, 168, 174, 0.12);
}

.v-theme--apaAtlasDarkTheme .panel-title-text {
  color: rgba(255, 255, 255, 0.87);
}

.v-theme--apaAtlasDarkTheme .panel-subtitle-text {
  color: rgba(255, 255, 255, 0.45);
}

.v-theme--apaAtlasDarkTheme .gene-name-text {
  color: rgba(255, 255, 255, 0.90);
}

.v-theme--apaAtlasDarkTheme .gene-meta-label {
  color: rgba(255, 255, 255, 0.38);
}

.v-theme--apaAtlasDarkTheme .gene-meta-value {
  color: rgba(255, 255, 255, 0.75);
}

.v-theme--apaAtlasDarkTheme .gene-meta-accent {
  color: #2AA8AE;
}

.v-theme--apaAtlasDarkTheme .gene-id-link {
  color: #2AA8AE;
}

.v-theme--apaAtlasDarkTheme .elegant-table :deep(.v-data-table__th) {
  background: rgba(42, 168, 174, 0.07) !important;
  color: rgba(255, 255, 255, 0.50) !important;
  border-bottom-color: rgba(42, 168, 174, 0.12) !important;
}

.v-theme--apaAtlasDarkTheme .elegant-table :deep(.v-data-table__td) {
  color: rgba(255, 255, 255, 0.78) !important;
  border-bottom-color: rgba(255, 255, 255, 0.05) !important;
}

.v-theme--apaAtlasDarkTheme .elegant-table :deep(.v-data-table__tr:hover .v-data-table__td) {
  background: rgba(42, 168, 174, 0.05) !important;
}

.v-theme--apaAtlasDarkTheme .elegant-table :deep(.v-data-table-footer) {
  color: rgba(255, 255, 255, 0.45) !important;
  border-top-color: rgba(42, 168, 174, 0.12) !important;
}

.v-theme--apaAtlasDarkTheme .elegant-table :deep(code) {
  background: rgba(42, 168, 174, 0.10);
  color: #2AA8AE;
}

.v-theme--apaAtlasDarkTheme code {
  background: rgba(255, 255, 255, 0.07);
  color: rgba(255, 255, 255, 0.75);
}

.v-theme--apaAtlasDarkTheme .heatmap-grid {
  border-color: rgba(42, 168, 174, 0.18);
  box-shadow: 0 2px 14px rgba(0, 0, 0, 0.32);
}

.v-theme--apaAtlasDarkTheme .heatmap-corner {
  background: rgba(42, 168, 174, 0.08);
  border-color: rgba(42, 168, 174, 0.15);
}

.v-theme--apaAtlasDarkTheme .heatmap-corner-text {
  color: rgba(255, 255, 255, 0.32);
}

.v-theme--apaAtlasDarkTheme .heatmap-col-header {
  background: rgba(42, 168, 174, 0.05);
  border-color: rgba(42, 168, 174, 0.15);
}

.v-theme--apaAtlasDarkTheme .heatmap-col-text {
  color: rgba(255, 255, 255, 0.60);
}

.v-theme--apaAtlasDarkTheme .heatmap-sample-dot {
  box-shadow: 0 0 0 2px rgba(20, 20, 30, 0.85), 0 1px 4px rgba(0, 0, 0, 0.3);
}

.v-theme--apaAtlasDarkTheme .heatmap-row-label {
  background: rgba(42, 168, 174, 0.04);
  border-color: rgba(42, 168, 174, 0.15);
}

.v-theme--apaAtlasDarkTheme .heatmap-site-id {
  color: rgba(255, 255, 255, 0.82);
}

.v-theme--apaAtlasDarkTheme .heatmap-stats-chip {
  background: rgba(42, 168, 174, 0.12);
  border-color: rgba(42, 168, 174, 0.22);
  color: #2AA8AE;
}

.v-theme--apaAtlasDarkTheme .heatmap-legend-bar {
  background: linear-gradient(
    to right,
    rgba(42, 168, 174, 0.06),
    rgba(42, 168, 174, 0.28),
    rgba(42, 168, 174, 0.65),
    rgba(42, 168, 174, 1.0)
  );
  border-color: rgba(255, 255, 255, 0.08);
}

.v-theme--apaAtlasDarkTheme .heatmap-legend-tick {
  color: rgba(255, 255, 255, 0.42);
}

.v-theme--apaAtlasDarkTheme .heatmap-legend-caption {
  color: rgba(255, 255, 255, 0.30);
}

.v-theme--apaAtlasDarkTheme .heatmap-legend-nd {
  border-color: rgba(255, 255, 255, 0.10);
  background: rgba(255, 255, 255, 0.03);
}

.v-theme--apaAtlasDarkTheme .heatmap-legend-nd-swatch {
  background: repeating-linear-gradient(
    45deg,
    rgba(255, 255, 255, 0.04) 0px,
    rgba(255, 255, 255, 0.04) 3px,
    rgba(255, 255, 255, 0.10) 3px,
    rgba(255, 255, 255, 0.10) 6px
  );
  border-color: rgba(255, 255, 255, 0.14);
}

.v-theme--apaAtlasDarkTheme .heatmap-legend-nd-label {
  color: rgba(255, 255, 255, 0.42);
}

.v-theme--apaAtlasDarkTheme .seq-meta-chip {
  background: rgba(255, 255, 255, 0.07);
  color: rgba(255, 255, 255, 0.60);
  border-color: rgba(255, 255, 255, 0.10);
}

.v-theme--apaAtlasDarkTheme .seq-meta-strand {
  background: rgba(42, 168, 174, 0.12);
  color: #2AA8AE;
  border-color: rgba(42, 168, 174, 0.28);
}

.v-theme--apaAtlasDarkTheme .seq-display {
  color: rgba(255, 255, 255, 0.82);
  border-top-color: rgba(255, 255, 255, 0.07);
}

.v-theme--apaAtlasDarkTheme .seq-nt {
  color: rgba(255, 255, 255, 0.82);
}

.v-theme--apaAtlasDarkTheme .detail-panel {
  background: rgba(42, 168, 174, 0.04);
  border-top-color: rgba(42, 168, 174, 0.15);
}

.v-theme--apaAtlasDarkTheme .detail-section {
  border-bottom-color: rgba(255, 255, 255, 0.06);
}

.v-theme--apaAtlasDarkTheme .detail-section-label {
  color: #2AA8AE;
}

.v-theme--apaAtlasDarkTheme .detail-section-sub {
  color: rgba(255, 255, 255, 0.28);
}

.v-theme--apaAtlasDarkTheme .sample-type-text {
  color: rgba(255, 255, 255, 0.30);
}

.v-theme--apaAtlasDarkTheme .sample-pct-text {
  color: rgba(255, 255, 255, 0.55);
}

.v-theme--apaAtlasDarkTheme .ld-chevron {
  color: rgba(42, 168, 174, 0.5);
}

.v-theme--apaAtlasDarkTheme .ld-row-clickable:hover .ld-chevron {
  color: #2AA8AE;
}

.v-theme--apaAtlasDarkTheme .ld-chevron-open {
  color: #2AA8AE;
}

.v-theme--apaAtlasDarkTheme .ld-site-id-tag {
  background: rgba(42, 168, 174, 0.10);
  color: #2AA8AE;
  border-color: rgba(42, 168, 174, 0.22);
}

/* ── Mean Abundance header with popover ─────────────────────────── */
.ld-header-cell-row {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
}

.tx-info-icon {
  color: rgba(13, 115, 119, 0.55);
  cursor: pointer;
  flex-shrink: 0;
  transition: color 0.15s ease;
  vertical-align: middle;
}

.tx-info-icon:hover {
  color: #0D7377;
}

.tx-info-popover {
  width: 100%;
  background: rgba(255, 255, 255, 0.60) !important;
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid rgba(13, 115, 119, 0.20) !important;
  box-shadow: 0 8px 32px rgba(13, 115, 119, 0.10), 0 2px 8px rgba(0, 0, 0, 0.08) !important;
}

.tx-info-popover-text {
  font-family: 'Roboto', sans-serif;
  font-size: 13px;
  line-height: 1.65;
  color: rgba(0, 0, 0, 0.78);
  padding: 14px 16px !important;
  text-align: justify;
}

/* Dark theme */
.v-theme--apaAtlasDarkTheme .tx-info-icon {
  color: rgba(42, 168, 174, 0.6);
}

.v-theme--apaAtlasDarkTheme .tx-info-icon:hover {
  color: #2AA8AE;
}

.v-theme--apaAtlasDarkTheme .tx-info-popover {
  background: rgba(16, 22, 32, 0.52) !important;
  backdrop-filter: blur(20px) saturate(160%);
  -webkit-backdrop-filter: blur(20px) saturate(160%);
  border-color: rgba(42, 168, 174, 0.28) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.40), 0 2px 8px rgba(42, 168, 174, 0.08) !important;
}

.v-theme--apaAtlasDarkTheme .tx-info-popover-text {
  color: rgba(255, 255, 255, 0.82);
}
</style>
