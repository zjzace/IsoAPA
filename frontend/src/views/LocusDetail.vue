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
        
        <v-card variant="outlined" class="mb-6">
          <v-card-title class="d-flex align-center">
            <v-icon icon="mdi-table" class="mr-2"></v-icon>
            APA Sites Details
          </v-card-title>
          <v-card-text>
            <v-data-table
              :headers="tableHeaders"
              :items="locusData.apa_sites"
              :items-per-page="10"
              :search="tableSearch"
            >
              <template v-slot:top>
                <v-text-field
                  v-model="tableSearch"
                  label="Filter APA Sites"
                  prepend-inner-icon="mdi-filter"
                  class="mb-4"
                  style="max-width: 300px;"
                ></v-text-field>
              </template>
              
              <template v-slot:item.site_id="{ item }">
                <code>{{ item.site_id }}</code>
              </template>
              
              <template v-slot:item.site_position="{ item }">
                <code>{{ item.site_position }}</code>
              </template>
              
              <template v-slot:item.samples="{ item }">
                <v-chip 
                  v-for="sd in item.sample_details" 
                  :key="sd.sample_name"
                  size="x-small" 
                  class="mr-1 mb-1"
                  variant="tonal"
                >
                  {{ sd.sample_name }}: {{ (sd.site_abundance * 100).toFixed(1) }}%
                </v-chip>
              </template>
              
              <template v-slot:item.actions="{ item }">
                <v-btn 
                  size="small" 
                  variant="tonal"
                  color="primary"
                  @click="selectAPASite(item)"
                >
                  View
                </v-btn>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
        
        <v-card variant="outlined">
          <v-card-title class="d-flex align-center">
            <v-icon icon="mdi-chart-bar" class="mr-2"></v-icon>
            APA Site Analysis
          </v-card-title>
          <v-card-text>
            <v-row align="center" class="mb-4">
              <v-col cols="12" sm="6" md="4">
                <v-select
                  v-model="selectedSiteId"
                  :items="siteIdOptions"
                  label="Select APA Site"
                  item-title="label"
                  item-value="value"
                  density="compact"
                  variant="outlined"
                  return-object
                  @update:model-value="onSiteSelected"
                >
                  <template v-slot:item="{ props, item }">
                    <v-list-item v-bind="props">
                      <v-list-item-subtitle>
                        Position: {{ item.raw.position }} | Samples: {{ item.raw.samples }}
                      </v-list-item-subtitle>
                    </v-list-item>
                  </template>
                </v-select>
              </v-col>
            </v-row>
            
            <v-row v-if="selectedSiteId">
              <v-col cols="12" md="6">
                <div class="text-subtitle-2 mb-2">Sample Distribution</div>
                <Bar 
                  v-if="sampleBarChartData" 
                  :data="sampleBarChartData" 
                  :options="chartOptions"
                ></Bar>
                <div v-else class="text-center py-8 text-grey">No data available</div>
              </v-col>
              <v-col cols="12" md="6">
                <div class="text-subtitle-2 mb-2">Abundance by Sample</div>
                <Bar 
                  v-if="abundanceBarChartData" 
                  :data="abundanceBarChartData" 
                  :options="barChartOptions"
                ></Bar>
                <div v-else class="text-center py-8 text-grey">No data available</div>
              </v-col>
            </v-row>
            
            <div v-else class="text-center py-8 text-grey">
              Select an APA site from the dropdown above to view analysis
            </div>
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

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend, Title)

const route = useRoute()

const loading = ref(true)
const error = ref(null)
const locusData = ref(null)
const tableSearch = ref('')
const selectedSiteId = ref(null)

const tableHeaders = [
  { title: 'Site ID', key: 'site_id', sortable: true },
  { title: 'Position', key: 'site_position', sortable: true },
  { title: 'Samples', key: 'samples', sortable: false },
  { title: '', key: 'actions', sortable: false, width: 100 }
]

const chartOptions = {
  responsive: true,
  maintainAspectRatio: true,
  indexAxis: 'y',
  plugins: {
    legend: { display: false }
  }
}

const barChartOptions = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: { display: false }
  },
  scales: {
    y: {
      beginAtZero: true,
      max: 1
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

const selectAPASite = (item) => {
  selectedSiteId.value = item.site_id
}

const onSiteSelected = (site) => {
  selectedSiteId.value = site?.value || null
}

const sampleBarChartData = computed(() => {
  if (!locusData.value || !selectedSiteId.value) return null
  
  const site = locusData.value.apa_sites.find(s => s.site_id === selectedSiteId.value)
  if (!site || !site.sample_details) return null
  
  const labels = site.sample_details.map(sd => sd.sample_name)
  const data = site.sample_details.map(sd => sd.site_count)
  
  if (labels.length === 0) return null
  
  return {
    labels,
    datasets: [{
      label: 'Read Count',
      data,
      backgroundColor: ['#0D7377', '#14919B', '#323232', '#E94560', '#FF6B6B', '#4ECDC4']
    }]
  }
})

const abundanceBarChartData = computed(() => {
  if (!locusData.value || !selectedSiteId.value) return null
  
  const site = locusData.value.apa_sites.find(s => s.site_id === selectedSiteId.value)
  if (!site || !site.sample_details) return null
  
  const labels = site.sample_details.map(sd => sd.sample_name)
  const data = site.sample_details.map(sd => sd.site_abundance)
  
  if (labels.length === 0) return null
  
  return {
    labels,
    datasets: [{
      label: 'Abundance',
      data,
      backgroundColor: ['#0D7377', '#14919B', '#323232', '#E94560', '#FF6B6B', '#4ECDC4']
    }]
  }
})

onMounted(async () => {
  const transcriptId = route.params.transcriptId
  
  try {
    loading.value = true
    locusData.value = await apiService.getLocusDetail(transcriptId)
    
    if (locusData.value.apa_sites.length > 0) {
      selectedSiteId.value = locusData.value.apa_sites[0].site_id
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
</style>
