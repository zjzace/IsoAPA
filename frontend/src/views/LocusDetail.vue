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
              <span class="gene-meta-value font-weight-medium">{{ locusData.gene.gene_name }}</span>
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
              <span class="gene-meta-value">
                <v-chip size="small" variant="tonal" color="primary" class="mr-1">{{ locusData.gene.chromosome }}</v-chip>
                <v-chip size="small" variant="tonal" color="secondary">{{ locusData.gene.strand }}</v-chip>
              </span>
            </div>
            <div class="gene-meta-item">
              <span class="gene-meta-label">APA Sites</span>
              <span class="gene-meta-value gene-meta-accent">{{ locusData.apa_sites.length }}</span>
            </div>
            <div class="gene-meta-item" v-if="locusData.apa_sites[0]?.species">
              <span class="gene-meta-label">Species</span>
              <span class="gene-meta-value">
                {{ locusData.apa_sites[0].species.name }}
                <span style="font-style: italic; opacity: 0.65; font-size: 12px;">{{ locusData.apa_sites[0].species.latin_name }}</span>
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
                :samples="locusData.samples"
              />
            </div>
          </div>
        </div>

        <!-- ── APA Sites Details ─────────────────────────────────────── -->
        <div class="section-card mb-6">
          <div class="section-title">
            <v-icon size="18" class="mr-2" style="color: #0D7377;">mdi-table</v-icon>
            APA Sites Details
          </div>
          <div class="panel-box">
            <div class="panel-body pa-0">
              <v-data-table
                :headers="tableHeaders"
                :items="flattenedTableData"
                :items-per-page="10"
                class="elegant-table"
              >
                <template v-slot:item.site_id="{ item }">
                  <code>{{ item.site_id }}</code>
                </template>
                
                <template v-slot:item.site_position="{ item }">
                  <code>{{ item.site_position }}</code>
                </template>
                
                <template v-slot:item.pas_motif="{ item }">
                  <div v-if="item.pas_motif" class="d-flex align-center ga-1">
                    <code class="pas-motif">{{ item.pas_motif }}</code>
                    <v-chip 
                      size="x-small" 
                      :color="item.pas_type === 'canonical' ? 'success' : 'warning'"
                      variant="flat"
                    >
                      {{ item.pas_type === 'canonical' ? '✓' : '~' }}
                    </v-chip>
                    <span class="text-caption text-grey" v-if="item.pas_position">
                      {{ item.pas_position }}bp
                    </span>
                  </div>
                  <span v-else class="text-grey">—</span>
                </template>
                
                <template v-slot:item.sample_name="{ item }">
                  <v-chip size="small" variant="tonal" color="primary">
                    {{ item.sample_name }}
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
                    variant="tonal"
                    color="primary"
                    @click="selectAPASiteById(item.site_id)"
                  >
                    View
                  </v-btn>
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
              Colour intensity shows relative abundance (0–100%) of each APA site in each sample.
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

        <!-- ── 3′ UTR Length Consequence ────────────────────────────────── -->
        <div class="section-card mb-6" v-if="utrLengthData.length > 0">
          <div class="section-title">
            <v-icon size="18" class="mr-2" style="color: #0D7377;">mdi-arrow-expand-horizontal</v-icon>
            3′ UTR Length Consequence
            <v-tooltip location="bottom" max-width="340">
              <template #activator="{ props }">
                <v-icon v-bind="props" icon="mdi-information-outline" size="small" class="ml-2" style="color: rgba(0,0,0,0.38);"></v-icon>
              </template>
              Each bar shows the distance from the last CDS base to the APA site, representing
              the resulting 3′ UTR length. Shorter isoforms (proximal sites) tend to escape
              miRNA and RBP regulation encoded in the distal 3′ UTR.
            </v-tooltip>
          </div>
          <v-row align="start">
              <!-- Bar chart -->
              <v-col cols="12" md="7">
                <div class="utr-chart">
                  <div
                    v-for="(item, i) in utrLengthData"
                    :key="item.siteId"
                    class="utr-row mb-3"
                  >
                    <div class="d-flex align-center mb-1">
                      <span class="text-caption text-grey-darken-1 utr-row-label">
                        Site {{ i + 1 }}
                        <span class="text-grey ml-1">({{ item.position.toLocaleString() }})</span>
                      </span>
                      <v-chip size="x-small" :color="item.pasType === 'canonical' ? 'success' : 'warning'" variant="flat" class="ml-2">
                        {{ item.pasMotif || '—' }}
                      </v-chip>
                      <v-tooltip location="top" text="Download 3′ UTR sequence (.fa)">
                        <template #activator="{ props }">
                          <v-btn
                            v-bind="props"
                            :href="apiService.getUtrSequenceUrl(locusData.transcript.transcript_id, item.siteId)"
                            download
                            icon
                            size="x-small"
                            variant="text"
                            color="primary"
                            class="ml-1"
                          >
                            <v-icon size="14">mdi-download</v-icon>
                          </v-btn>
                        </template>
                      </v-tooltip>
                    </div>
                    <div class="d-flex align-center ga-2">
                      <div class="utr-bar-track flex-grow-1">
                        <div
                          class="utr-bar"
                          :style="{
                            width: item.pct + '%',
                            background: utrBarColor(i),
                            opacity: item.utrLength === 0 ? 0.2 : 1
                          }"
                        ></div>
                      </div>
                      <span class="text-caption font-weight-medium utr-length-label">
                        {{ item.utrLength > 0 ? item.utrLength.toLocaleString() + ' nt' : 'CDS end' }}
                      </span>
                    </div>
                  </div>
                </div>
                <div class="text-caption text-grey mt-2">
                  * UTR length measured from last annotated CDS base to cleavage site.
                  Requires transcript structure to be loaded.
                </div>
              </v-col>

              <!-- RBP Binding Motif Scanner -->
              <v-col cols="12" md="5">
                <div v-if="rbpLoading" class="d-flex justify-center align-center" style="min-height:180px;">
                  <v-progress-circular indeterminate color="primary" size="32"></v-progress-circular>
                </div>

                <div v-else-if="rbpData.length > 0" class="rbp-panel">
                  <!-- Tab strip: one tab per APA site -->
                  <v-tabs
                    v-model="rbpTab"
                    density="compact"
                    color="primary"
                    class="mb-3"
                    show-arrows
                  >
                    <v-tab
                      v-for="(site, i) in rbpData"
                      :key="site.site_id"
                      :value="i"
                      class="text-caption"
                    >
                      <span
                        class="rbp-site-dot mr-1"
                        :style="{ background: utrBarColor(i) }"
                      ></span>
                      Site {{ i + 1 }}
                    </v-tab>
                  </v-tabs>

                  <v-window v-model="rbpTab">
                    <v-window-item
                      v-for="(site, i) in rbpData"
                      :key="site.site_id"
                      :value="i"
                    >
                      <div v-if="!site.sequence_available" class="text-caption text-grey pa-2">
                        Sequence not available for this site
                      </div>
                      <div v-else>
                        <!-- Category legend pills -->
                        <div class="d-flex flex-wrap ga-1 mb-3">
                          <v-chip
                            v-for="cat in rbpCategories"
                            :key="cat.name"
                            size="x-small"
                            :color="cat.color"
                            variant="tonal"
                          >{{ cat.name }}</v-chip>
                        </div>

                        <!-- One row per RBP -->
                        <div
                          v-for="hit in site.rbp_hits"
                          :key="hit.rbp"
                          class="rbp-row mb-2"
                        >
                          <div class="d-flex align-center mb-1 ga-1">
                            <span
                              class="rbp-color-dot"
                              :style="{ background: hit.color }"
                            ></span>
                            <v-tooltip location="top" max-width="300">
                              <template #activator="{ props }">
                                <span v-bind="props" class="rbp-name text-caption font-weight-medium">
                                  {{ hit.rbp }}
                                </span>
                              </template>
                              <div>
                                <strong>{{ hit.rbp }}</strong><br/>
                                <span class="text-caption">{{ hit.function }}</span>
                              </div>
                            </v-tooltip>
                            <v-spacer></v-spacer>
                            <v-chip
                              size="x-small"
                              :color="hit.count === 0 ? 'default' : hit.color"
                              :variant="hit.count === 0 ? 'tonal' : 'flat'"
                              class="rbp-count-chip"
                            >
                              {{ hit.count === 0 ? 'none' : hit.count + (hit.count === 1 ? ' site' : ' sites') }}
                            </v-chip>
                          </div>

                          <!-- Hit position lollipop track -->
                          <div class="rbp-lollipop-track">
                            <template v-if="hit.count > 0">
                              <div
                                v-for="(pos, pi) in hit.positions"
                                :key="pi"
                                class="rbp-lollipop"
                                :style="{
                                  left: ((pos / site.utr_length) * 100).toFixed(1) + '%',
                                  background: hit.color
                                }"
                              ></div>
                            </template>
                          </div>
                        </div>

                        <!-- Footer: UTR length + density summary -->
                        <div class="d-flex align-center mt-3 ga-2 text-caption text-grey">
                          <v-icon size="12">mdi-ruler</v-icon>
                          {{ site.utr_length.toLocaleString() }} nt UTR
                          <span class="ml-auto">
                            {{ site.rbp_hits.filter(h => h.count > 0).length }} / {{ site.rbp_hits.length }} RBPs detected
                          </span>
                        </div>
                      </div>
                    </v-window-item>
                  </v-window>
                </div>

                <div v-else class="text-caption text-grey text-center pa-4">
                  RBP motif data unavailable
                </div>
              </v-col>
            </v-row>
          </div>
        </div>
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
const rbpData = ref([])
const rbpLoading = ref(false)
const rbpTab = ref(0)

const rbpCategories = [
  { name: 'Stability',        color: 'error'   },
  { name: 'Decay',            color: 'warning' },
  { name: 'Translation',      color: 'purple'  },
  { name: 'Polyadenylation',  color: 'blue'    },
  { name: 'miRNA',            color: 'teal'    },
]

const tableHeaders = [
  { title: 'Site ID', key: 'site_id', sortable: true },
  { title: 'Position', key: 'site_position', sortable: true },
  { title: 'PAS Motif', key: 'pas_motif', sortable: true },
  { title: 'Sample', key: 'sample_name', sortable: true },
  { title: 'Relative Abundance', key: 'site_abundance', sortable: true },
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
      title: { display: true, text: 'APA Site' },
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
    value: site.site_id,
    label: site.site_id.substring(0, 20) + (site.site_id.length > 20 ? '...' : ''),
    position: site.site_position,
    samples: site.sample_details?.length || 0
  }))
})

const sampleOptions = computed(() => {
  if (!locusData.value) return []
  return locusData.value.samples || []
})

const sampleSiteAbundanceData = computed(() => {
  if (!locusData.value || !selectedSample.value) return null
  
  const sites = locusData.value.apa_sites
  if (sites.length === 0) return null
  
  const labels = []
  const data = []
  const colors = ['#0D7377', '#14919B', '#323232', '#E94560', '#FF6B6B', '#4ECDC4', '#5C6BC0', '#AB47BC']
  
  sites.forEach((site, index) => {
    // Shorten site_id for label
    const shortId = site.site_id.length > 15 
      ? site.site_id.substring(0, 15) + '...' 
      : site.site_id
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
  
  const flattened = []
  locusData.value.apa_sites.forEach(site => {
    if (site.sample_details && site.sample_details.length > 0) {
      site.sample_details.forEach(sd => {
        flattened.push({
          site_id: site.site_id,
          site_position: site.site_position,
          pas_motif: site.pas_motif,
          pas_position: site.pas_position,
          pas_type: site.pas_type,
          pas_confidence: site.pas_confidence,
          sample_name: sd.sample_name,
          site_abundance: sd.site_abundance,
          site_count: sd.site_count
        })
      })
    } else {
      flattened.push({
        site_id: site.site_id,
        site_position: site.site_position,
        pas_motif: site.pas_motif,
        pas_position: site.pas_position,
        pas_type: site.pas_type,
        pas_confidence: site.pas_confidence,
        sample_name: '-',
        site_abundance: 0,
        site_count: 0
      })
    }
  })
  return flattened
})

const ucscBrowserLink = computed(() => {
  if (!locusData.value) return ''
  const gene = locusData.value.gene
  const chromosome = gene.chromosome
  const apaSites = locusData.value.apa_sites
  if (apaSites.length === 0) return ''
  
  const positions = apaSites.map(s => s.site_position)
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
    lookup[site.site_id] = {}
    for (const sd of (site.sample_details || [])) {
      lookup[site.site_id][sd.sample_name] = {
        abundance: sd.site_abundance,
        count: sd.site_count
      }
    }
  }
  return lookup
})

const heatmapData = computed(() => {
  if (!locusData.value) return { sites: [], samples: [] }
  const allSamples = locusData.value.samples || []
  const sites = locusData.value.apa_sites.map(s => ({
    id: s.site_id,
    position: s.site_position
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

// ── 3′ UTR Length ──────────────────────────────────────────────────────────

const utrLengthData = computed(() => {
  if (!locusData.value) return []
  const strand = locusData.value.gene.strand

  // Derive CDS end from transcript structure if available, else fall back
  // to inferring from site positions (the most-distal detected site ~ CDS end)
  let cdsEndPos = null
  if (transcriptStructure.value?.cds?.length) {
    const cdsPositions = transcriptStructure.value.cds.flatMap(c => [c.start, c.end])
    cdsEndPos = strand === '-' ? Math.min(...cdsPositions) : Math.max(...cdsPositions)
  }

  const sites = locusData.value.apa_sites.map(s => ({
    siteId: s.site_id,
    position: s.site_position,
    pasMotif: s.pas_motif,
    pasType: s.pas_type
  }))

  // Sort proximal → distal (relative to transcript direction)
  sites.sort((a, b) => strand === '-' ? b.position - a.position : a.position - b.position)

  // If no CDS info, use the most-proximal site as the reference baseline
  if (cdsEndPos === null && sites.length > 0) {
    cdsEndPos = sites[0].position
  }

  const result = sites.map(s => {
    const utrLength = cdsEndPos !== null
      ? Math.abs(s.position - cdsEndPos)
      : 0
    return { ...s, utrLength }
  })

  const maxLen = Math.max(...result.map(r => r.utrLength), 1)
  return result.map(r => ({ ...r, pct: (r.utrLength / maxLen) * 100 }))
})

const UTR_BAR_COLORS = ['#0D7377', '#14919B', '#2196F3', '#7B1FA2', '#E53935', '#FB8C00', '#43A047', '#00ACC1']
const utrBarColor = (i) => UTR_BAR_COLORS[i % UTR_BAR_COLORS.length]

const abundanceBarChartData = computed(() => {
  if (!locusData.value || !selectedSiteId.value) return null
  
  const site = locusData.value.apa_sites.find(s => s.site_id === selectedSiteId.value)
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
      selectedSiteId.value = locusData.value.apa_sites[0].site_id
    }
    if (locusData.value.samples && locusData.value.samples.length > 0) {
      selectedSample.value = locusData.value.samples[0]
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

    // Fetch RBP motif hits — non-fatal
    rbpLoading.value = true
    apiService.getRbpMotifs(transcriptId)
      .then(data => {
        // Sort to match utrLengthData order (proximal → distal)
        const strand = locusData.value?.gene?.strand
        rbpData.value = [...data].sort((a, b) =>
          strand === '-'
            ? b.site_position - a.site_position
            : a.site_position - b.site_position
        )
      })
      .catch(err => {
        console.warn('RBP motif data not available:', err)
      })
      .finally(() => {
        rbpLoading.value = false
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
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.10);
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

.gene-header-title {
  display: flex;
  align-items: center;
  margin-bottom: 14px;
}

.gene-name-text {
  font-size: 1.45rem;
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
  gap: 2px;
}

.gene-meta-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(0,0,0,0.42);
}

.gene-meta-value {
  font-size: 14px;
  font-weight: 500;
  color: rgba(0,0,0,0.80);
  display: flex;
  align-items: center;
  gap: 4px;
}

.gene-meta-accent {
  font-size: 16px;
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
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.10);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

.section-title {
  display: flex;
  align-items: center;
  font-size: 1.05rem;
  font-weight: 700;
  color: rgba(0,0,0,0.80);
  margin-bottom: 20px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(0,0,0,0.07);
}

/* ── Panel box ────────────────────────────────────────────────────── */
.panel-box {
  border: 1px solid rgba(13, 115, 119, 0.15);
  border-radius: 10px;
  overflow: hidden;
  background: #fafcfc;
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
  font-size: 0.92rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.82);
  line-height: 1.3;
}

.panel-subtitle-text {
  font-size: 0.75rem;
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

.light-card-bg {
  background: rgba(var(--v-theme-surface), 0.5) !important;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.elegant-table {
  background: transparent !important;
}

.elegant-table :deep(.v-data-table__th) {
  background: transparent !important;
  font-weight: 600;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.12);
}

.elegant-table :deep(.v-data-table__td) {
  padding: 12px 16px;
  background: transparent !important;
}

.elegant-table :deep(.v-data-table__tr:hover) {
  background: rgba(var(--v-theme-primary), 0.08) !important;
}

.elegant-table :deep(.v-data-table-footer) {
  background: transparent !important;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.12);
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
  background: transparent !important;
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
  font-size: 0.72rem;
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

/* ── 3′ UTR bars ── */
.utr-chart {
  width: 100%;
}

.utr-row-label {
  min-width: 160px;
  display: inline-block;
}

.utr-bar-track {
  height: 18px;
  background: rgba(0,0,0,0.06);
  border-radius: 4px;
  overflow: hidden;
}

.utr-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.utr-length-label {
  min-width: 72px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

/* ── RBP Binding Motif Scanner ── */
.rbp-panel { width: 100%; }

.rbp-site-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; display: inline-block;
}

.rbp-color-dot {
  width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0;
}

.rbp-name {
  cursor: default;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 160px;
}

.rbp-count-chip {
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

/* Lollipop position track */
.rbp-lollipop-track {
  position: relative;
  height: 10px;
  background: rgba(0,0,0,0.05);
  border-radius: 5px;
  overflow: hidden;
}

.rbp-lollipop {
  position: absolute;
  top: 1px;
  width: 3px;
  height: 8px;
  border-radius: 2px;
  transform: translateX(-50%);
  opacity: 0.85;
}
</style>
