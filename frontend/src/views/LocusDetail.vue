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
        <v-card class="mb-6" variant="outlined">
          <v-card-title class="d-flex align-center">
            <v-icon icon="mdi-gene" class="mr-2" color="primary"></v-icon>
            {{ locusData.gene.gene_name }}
          </v-card-title>
          <v-card-text>
            <v-row align="center">
              <v-col cols="12" sm="6" md="3">
                <div class="text-caption text-grey">Gene ID</div>
                <router-link 
                  :to="{ name: 'GeneDetail', params: { geneId: locusData.gene.gene_id } }"
                  class="text-primary font-weight-medium"
                >
                  {{ locusData.gene.gene_id }}
                </router-link>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <div class="text-caption text-grey">Transcript ID</div>
                <div class="text-body-1 font-weight-medium">{{ locusData.transcript.transcript_id }}</div>
              </v-col>
              <v-col cols="12" sm="6" md="2">
                <div class="text-caption text-grey">Chromosome</div>
                <div class="text-body-1">
                  <v-chip size="small">{{ locusData.gene.chromosome }}</v-chip>
                  <v-chip size="small" class="ml-1">{{ locusData.gene.strand }}</v-chip>
                </div>
              </v-col>
              <v-col cols="12" sm="6" md="2">
                <div class="text-caption text-grey">APA Sites</div>
                <div class="text-body-1 font-weight-bold text-primary">
                  {{ locusData.apa_sites.length }}
                </div>
              </v-col>
              <v-col cols="12" sm="6" md="2">
                <div class="text-caption text-grey">Samples</div>
                <div class="text-body-1">
                  <v-chip 
                    v-for="sample in locusData.samples" 
                    :key="sample"
                    size="x-small" 
                    class="mr-1"
                    variant="tonal"
                  >
                    {{ sample }}
                  </v-chip>
                </div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
        
        <v-card variant="outlined" class="mb-6" v-if="transcriptStructure">
          <v-card-title class="d-flex align-center">
            <v-icon icon="mdi-dna" class="mr-2"></v-icon>
            Interactive Genome Browser
            <v-spacer></v-spacer>
            <v-chip size="small" variant="tonal" color="primary">
              Single Transcript View
            </v-chip>
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text>
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
            
            <!-- External browser links -->
            <div class="mt-4 d-flex flex-wrap ga-2">
              <v-btn
                :href="ucscBrowserLink"
                target="_blank"
                size="small"
                variant="outlined"
                prepend-icon="mdi-open-in-new"
              >
                Compare in UCSC
              </v-btn>
              <v-btn
                :href="ensemblBrowserLink"
                target="_blank"
                size="small"
                variant="outlined"
                prepend-icon="mdi-open-in-new"
              >
                View in Ensembl
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
        
        <v-card variant="outlined" class="mb-6">
          <v-card-title class="d-flex align-center">
            <v-icon icon="mdi-table" class="mr-2"></v-icon>
            APA Sites Details
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text class="pa-4">
            <v-card variant="flat" class="rounded-lg overflow-hidden light-card-bg">
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
                
                <template v-slot:item.apa_type="{ item }">
                  <v-chip 
                    v-if="item.apa_type"
                    size="small" 
                    :color="getApaTypeColor(item.apa_type)"
                    variant="tonal"
                  >
                    {{ item.apa_type }}
                  </v-chip>
                  <span v-else class="text-grey">—</span>
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
            </v-card>
          </v-card-text>
        </v-card>
        
        <v-card variant="outlined">
          <v-card-title class="d-flex align-center">
            <v-icon icon="mdi-chart-bar" class="mr-2"></v-icon>
            APA Site Analysis
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text>
            <v-row>
              <!-- Left Panel: Abundance by APA Site (for selected sample) -->
              <v-col cols="12" md="6">
                <v-card variant="flat" class="pa-4 light-card-bg rounded-lg">
                  <div class="d-flex align-center justify-space-between mb-4">
                    <div class="text-subtitle-1 font-weight-medium">APA Loci Distribution</div>
                    <v-select
                      v-model="selectedSample"
                      :items="sampleOptions"
                      label="Select Sample"
                      density="compact"
                      variant="outlined"
                      hide-details
                      style="min-width: 140px; max-width: 180px;"
                    ></v-select>
                  </div>
                  <Bar 
                    v-if="sampleSiteAbundanceData" 
                    :data="sampleSiteAbundanceData" 
                    :options="sampleSiteChartOptions"
                  ></Bar>
                  <div v-else class="text-center py-8 text-grey">No data available</div>
                </v-card>
              </v-col>
              
              <!-- Right Panel: Abundance by Sample (for selected site) -->
              <v-col cols="12" md="6">
                <v-card variant="flat" class="pa-4 light-card-bg rounded-lg">
                  <div class="d-flex align-center justify-space-between mb-4">
                    <div class="text-subtitle-1 font-weight-medium">Abundance by Sample</div>
                    <v-select
                      v-model="selectedSiteId"
                      :items="siteIdOptions"
                      label="Select APA Site"
                      item-title="label"
                      item-value="value"
                      density="compact"
                      variant="outlined"
                      hide-details
                      return-object
                      style="min-width: 180px; max-width: 240px;"
                      @update:model-value="onSiteSelected"
                    ></v-select>
                  </div>
                  <Bar 
                    v-if="abundanceBarChartData" 
                    :data="abundanceBarChartData" 
                    :options="barChartOptions"
                  ></Bar>
                  <div v-else class="text-center py-8 text-grey">No data available</div>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
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

const tableHeaders = [
  { title: 'Site ID', key: 'site_id', sortable: true },
  { title: 'Position', key: 'site_position', sortable: true },
  { title: 'APA Type', key: 'apa_type', sortable: true },
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
          apa_type: site.apa_type,
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
        apa_type: site.apa_type,
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

const getApaTypeColor = (apaType) => {
  switch (apaType) {
    case '3UTR-APA':
      return 'success'
    case 'Intronic-APA':
      return 'warning'
    case 'Exonic-APA':
      return 'error'
    default:
      return 'default'
  }
}

const selectAPASiteById = (siteId) => {
  selectedSiteId.value = siteId
}

const onSiteSelected = (site) => {
  selectedSiteId.value = site?.value || null
}

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
    // Fetch locus data and transcript structure in parallel
    const [locusResponse, structureResponse] = await Promise.all([
      apiService.getLocusDetail(transcriptId),
      apiService.getTranscriptStructure(transcriptId)
    ])
    
    locusData.value = locusResponse
    transcriptStructure.value = structureResponse
    
    if (locusData.value.apa_sites && locusData.value.apa_sites.length > 0) {
      selectedSiteId.value = locusData.value.apa_sites[0].site_id
    }
    if (locusData.value.samples && locusData.value.samples.length > 0) {
      selectedSample.value = locusData.value.samples[0]
    }
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
</style>
