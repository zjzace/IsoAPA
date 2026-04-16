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
            <v-icon size="18" class="mr-2" style="color: #0D7377;">mdi-dna</v-icon>
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
                :items-per-page="10"
                class="elegant-table"
                item-value="unified_id"
                v-model:expanded="seqOpen"
                :row-props="({ item }) => seqOpen.includes(item.unified_id) ? { class: 'row-seq-expanded' } : {}"
              >
                <template v-slot:item.unified_id="{ item }">
                  <code class="code-plain">{{ item.unified_id }}</code>
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

                <template v-slot:item.actions="{ item }">
                  <v-btn
                    size="small"
                    :variant="seqOpen.includes(item.unified_id) ? 'flat' : 'tonal'"
                    :color="seqOpen.includes(item.unified_id) ? 'primary' : 'primary'"
                    @click.stop="toggleSeqPanel(item.unified_id)"
                    class="seq-toggle-btn"
                  >
                    <v-icon start size="14">mdi-card-search-outline</v-icon>
                    {{ seqOpen.includes(item.unified_id) ? 'Hide' : 'Detail' }}
                  </v-btn>
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
                                    bg-color="rgba(0,0,0,0.06)"
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
                              <v-icon size="12" class="mr-1" style="color:#0D7377;">mdi-dna</v-icon>
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
            <v-icon size="18" class="mr-2" style="color: #0D7377;">mdi-grid</v-icon>
            Per-site Abundance Heatmap
            <v-tooltip location="bottom" max-width="320">
              <template #activator="{ props }">
                <v-icon v-bind="props" icon="mdi-information-outline" size="small" class="ml-2" style="color: rgba(0,0,0,0.38);"></v-icon>
              </template>
              Colour intensity shows relative abundance (0–100%) of each PA site in each sample.
              Darker = higher usage. Hatched = site not detected in that sample.
            </v-tooltip>
          </div>
          <div class="panel-box">
            <div class="panel-body pa-6">
            <div class="heatmap-wrap">
              <!-- Column headers (samples) -->
              <div class="heatmap-grid" :style="heatmapGridStyle">
                <div class="heatmap-row-label"></div>
                <div
                  v-for="sample in heatmapData.samples"
                  :key="sample"
                  class="heatmap-col-header text-caption font-weight-medium"
                >
                  {{ sample }}
                </div>

                <!-- Data rows -->
                <template v-for="(site, si) in heatmapData.sites" :key="site.id">
                  <!-- Row label -->
                  <div class="heatmap-row-label text-caption text-grey-darken-1">
                    <div class="heatmap-site-pos">chr{{ locusData.gene.chromosome }}:{{ site.position }}</div>
                  </div>
                  <!-- Cells -->
                  <div
                    v-for="sample in heatmapData.samples"
                    :key="sample"
                    class="heatmap-cell"
                    :style="heatmapCellStyle(site.id, sample)"
                  >
                    <v-tooltip location="top">
                      <template #activator="{ props }">
                        <div v-bind="props" class="heatmap-cell-inner">
                          <span
                            class="text-caption font-weight-medium"
                            :style="{ color: heatmapTextColor(site.id, sample) }"
                          >
                            {{ heatmapLabel(site.id, sample) }}
                          </span>
                        </div>
                      </template>
                      <div>
                        <strong>{{ site.id }}</strong><br/>
                        Sample: {{ sample }}<br/>
                        <template v-if="heatmapCount(site.id, sample) > 0">
                          Abundance: {{ heatmapLabel(site.id, sample) }}<br/>
                          Read count: {{ heatmapCount(site.id, sample) }}
                        </template>
                        <template v-else>
                          <em style="opacity:0.7;">Not detected in this sample</em>
                        </template>
                      </div>
                    </v-tooltip>
                  </div>
                </template>
              </div>

              <!-- Legend -->
              <div class="d-flex align-center mt-4 ga-2">
                <span class="text-caption text-grey">0%</span>
                <div class="heatmap-legend-bar"></div>
                <span class="text-caption text-grey">100%</span>
                <span class="text-caption text-grey ml-4" style="display:flex; align-items:center; gap:4px;">
                  <span style="display:inline-block; width:12px; height:12px; border-radius:2px; background: repeating-linear-gradient(45deg, rgba(0,0,0,0.04) 0px, rgba(0,0,0,0.04) 3px, rgba(0,0,0,0.1) 3px, rgba(0,0,0,0.1) 6px); border:1px solid rgba(0,0,0,0.15);"></span>
                  Not detected
                </span>
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
  { title: 'Cluster ID', key: 'unified_id', sortable: true },
  { title: 'Rep. Position', key: 'mode_site_position', sortable: true },
  { title: 'PAS Motif', key: 'pas_motif', sortable: true },
  { title: 'Samples', key: 'sample_count', sortable: true },
  { title: 'Avg Abundance', key: 'site_abundance', sortable: true },
  { title: '', key: 'actions', sortable: false, width: 100 }
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
    gridTemplateColumns: `200px repeat(${n}, minmax(80px, 140px))`,
    gap: '4px'
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
  font-size: 18px;
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
  font-size: 12.5px;
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
  font-size: 13.5px;
  font-family: 'Roboto Mono', 'Courier New', monospace;
}

.elegant-table :deep(code.code-plain) {
  background: none;
  border-radius: 0;
  padding: 0;
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
  font-size: 13px !important;
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
  font-size: 14.5px;
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

/* ── Heatmap ── */
.heatmap-wrap {
  overflow-x: auto;
}

.heatmap-grid {
  min-width: 300px;
  max-width: max-content;  /* don't stretch beyond content when few samples */
}

.heatmap-col-header {
  text-align: center;
  padding: 4px 4px 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  /* Rotate long names 45° for readability */
  writing-mode: vertical-lr;
  text-orientation: mixed;
  transform: rotate(180deg);
  max-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.heatmap-row-label {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding-right: 12px;
  padding-top: 2px;
  padding-bottom: 2px;
}

.heatmap-site-pos {
  font-size: 0.82rem;
  color: rgba(0, 0, 0, 0.6);
  font-family: monospace;
  white-space: nowrap;
}

.heatmap-cell {
  border-radius: 4px;
  min-height: 56px;
  cursor: default;
  transition: transform 0.1s, box-shadow 0.1s;
}

.heatmap-cell:hover {
  transform: scale(1.06);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.18);
  z-index: 1;
  position: relative;
}

.heatmap-cell-inner {
  width: 100%;
  height: 100%;
  min-height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.heatmap-legend-bar {
  width: 160px;
  height: 12px;
  border-radius: 6px;
  background: linear-gradient(to right, rgba(13,115,119,0.08), rgba(13,115,119,1));
  border: 1px solid rgba(0,0,0,0.1);
}

/* ── Detail toggle button ────────────────────────────────────────── */
.seq-toggle-btn { font-size: 13.5px; }

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
  padding: 4px 20px 4px;
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
  font-size: 11.5px;
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
  padding-right: 12px;
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

.sample-name-chip { flex-shrink: 0; }

.sample-type-text {
  font-size: 12.5px;
  color: rgba(0, 0, 0, 0.38);
  font-style: italic;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sample-abundance-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.sample-bar-track { flex: 1; min-width: 0; }

.sample-pct-text {
  font-size: 13px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.55);
  min-width: 44px;
  margin-left: 4px;
  text-align: right;
  font-family: 'Roboto Mono', monospace;
  flex-shrink: 0;
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
  font-size: 12.5px;
  font-weight: 600;
  padding: 5px 10px;
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
  font-size: 14px;
  line-height: 1.6;
  letter-spacing: 0.05em;
  word-break: break-all;
  overflow-wrap: break-word;
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

.v-theme--apaAtlasDarkTheme .heatmap-site-pos {
  color: rgba(255, 255, 255, 0.50);
}

.v-theme--apaAtlasDarkTheme .heatmap-legend-bar {
  background: linear-gradient(to right, rgba(42,168,174,0.08), rgba(42,168,174,1));
  border-color: rgba(255,255,255,0.10);
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
</style>
