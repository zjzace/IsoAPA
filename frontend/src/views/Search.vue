<template>
  <div class="search-page">
    <v-container class="py-8">
      <h1 class="text-h4 mb-6">Browse APA Sites</h1>
      
      <v-card class="mb-6" variant="outlined">
        <v-card-text>
          <v-row>
            <v-col cols="12" sm="6" md="3">
              <v-text-field
                v-model="filters.gene_name"
                label="Gene Name"
                prepend-inner-icon="mdi-gene"
                clearable
                @update:model-value="debouncedSearch"
              ></v-text-field>
            </v-col>
            <v-col cols="12" sm="6" md="3">
              <v-text-field
                v-model="filters.transcript_id"
                label="Transcript ID"
                prepend-inner-icon="mdi-rna"
                clearable
                @update:model-value="debouncedSearch"
              ></v-text-field>
            </v-col>
            <v-col cols="12" sm="6" md="3">
              <v-select
                v-model="filters.species"
                label="Species"
                :items="speciesList"
                prepend-inner-icon="mdi-earth"
                clearable
                @update:model-value="debouncedSearch"
              ></v-select>
            </v-col>
            <v-col cols="12" sm="6" md="3">
              <v-select
                v-model="filters.sample"
                label="Sample"
                :items="sampleList"
                prepend-inner-icon="mdi-heart"
                clearable
                @update:model-value="debouncedSearch"
              ></v-select>
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="12" class="d-flex align-center">
              <v-btn 
                color="primary" 
                @click="search"
                :loading="loading"
              >
                <v-icon start>mdi-magnify</v-icon>
                Search
              </v-btn>
              <v-btn 
                variant="text" 
                @click="clearFilters"
                class="ml-2"
              >
                Clear Filters
              </v-btn>
              <v-spacer></v-spacer>
              <v-btn 
                variant="outlined"
                color="primary"
                @click="exportResults"
                :disabled="results.length === 0"
              >
                <v-icon start>mdi-download</v-icon>
                Export CSV
              </v-btn>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
      
      <v-card variant="outlined">
        <v-data-table
          :headers="headers"
          :items="results"
          :loading="loading"
          :items-per-page="pageSize"
          :page="page"
          @update:page="changePage"
          @update:items-per-page="changePageSize"
        >
          <template v-slot:item.gene_name="{ item }">
            <router-link 
              :to="{ name: 'GeneDetail', params: { geneId: item.gene_id } }"
              class="text-primary font-weight-medium"
            >
              {{ item.gene_name }}
            </router-link>
          </template>
          
          <template v-slot:item.transcript_id="{ item }">
            <router-link 
              :to="{ name: 'LocusDetail', params: { transcriptId: item.transcript_id } }"
              class="text-primary font-weight-medium text-decoration-underline"
            >
              {{ item.transcript_id }}
            </router-link>
          </template>
          
          <template v-slot:item.chromosome="{ item }">
            <v-chip size="small" variant="tonal">{{ item.chromosome }}</v-chip>
            <v-chip size="small" variant="tonal" class="ml-1">{{ item.strand }}</v-chip>
          </template>
          
          <template v-slot:item.apa_site_count="{ item }">
            <v-badge 
              :content="item.apa_site_count" 
              color="primary" 
              inline
            ></v-badge>
          </template>
          
          <template v-slot:item.samples="{ item }">
            <v-chip 
              v-for="sample in item.cell_lines.slice(0, 3)" 
              :key="sample"
              size="x-small" 
              class="mr-1"
            >
              {{ sample }}
            </v-chip>
            <span v-if="item.cell_lines.length > 3" class="text-caption">
              +{{ item.cell_lines.length - 3 }} more
            </span>
          </template>
          
          <template v-slot:item.species="{ item }">
            <v-chip 
              size="small" 
              :color="getSpeciesColor(item.species)"
              variant="flat"
            >
              {{ item.species }}
            </v-chip>
          </template>
          
          <template v-slot:item.actions="{ item }">
          </template>
        </v-data-table>
      </v-card>
      
      <v-snackbar v-model="snackbar" :color="snackbarColor">
        {{ snackbarText }}
      </v-snackbar>
    </v-container>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { apiService } from '@/services/api'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const results = ref([])
const page = ref(1)
const pageSize = ref(20)
const totalResults = ref(0)

const filters = reactive({
  gene_name: '',
  transcript_id: '',
  species: '',
  sample: ''
})

const speciesList = ref(['Human', 'Mouse', 'Rat', 'Zebrafish'])
const sampleList = ref(['A549', 'HepG2', 'K562'])

const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

let searchTimeout = null

const headers = [
  { title: 'Gene Name', key: 'gene_name', sortable: true },
  { title: 'Transcript ID', key: 'transcript_id', sortable: true },
  { title: 'Chromosome', key: 'chromosome', sortable: false },
  { title: 'PA Sites', key: 'apa_site_count', sortable: true },
  { title: 'Samples', key: 'samples', sortable: false },
  { title: 'Species', key: 'species', sortable: true },
]

const speciesColors = {
  'Human': '#E94560',
  'Mouse': '#0D7377',
  'Rat': '#14919B',
  'Zebrafish': '#323232'
}

const getSpeciesColor = (species) => {
  return speciesColors[species] || 'primary'
}

const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    search()
  }, 500)
}

const search = async () => {
  loading.value = true
  results.value = []
  try {
    console.log('Searching with filters:', filters)
    const params = {
      page: page.value,
      limit: pageSize.value
    }
    
    if (filters.gene_name) params.gene_name = filters.gene_name
    if (filters.transcript_id) params.transcript_id = filters.transcript_id
    if (filters.species) params.species = filters.species
    if (filters.sample) params.sample = filters.sample
    
    console.log('API params:', params)
    const data = await apiService.search(params)
    console.log('Search results:', data)
    results.value = data
  } catch (error) {
    console.error('Search failed:', error)
    snackbarText.value = 'Search failed. Please try again.'
    snackbarColor.value = 'error'
    snackbar.value = true
  } finally {
    loading.value = false
  }
}

const clearFilters = () => {
  filters.gene_name = ''
  filters.transcript_id = ''
  filters.species = ''
  filters.sample = ''
  page.value = 1
  search()
}

const changePage = (newPage) => {
  page.value = newPage
  search()
}

const changePageSize = (newSize) => {
  pageSize.value = newSize
  page.value = 1
  search()
}

const viewDetail = (item) => {
  router.push({
    path: `/locus/${item.transcript_id}`,
    query: { species: item.species }
  })
}

const exportResults = () => {
  const headers = ['Gene Name', 'Transcript ID', 'Gene ID', 'Chromosome', 'Strand', 'APA Site Count', 'Species', 'Tissues']
  const rows = results.value.map(item => [
    item.gene_name,
    item.transcript_id,
    item.gene_id,
    item.chromosome,
    item.strand,
    item.apa_site_count,
    item.species,
    item.cell_lines.join('; ')
  ])
  
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
  ].join('\n')
  
  const blob = new Blob([csvContent], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `apa_sites_export_${Date.now()}.csv`
  a.click()
  window.URL.revokeObjectURL(url)
  
  snackbarText.value = 'Export completed successfully!'
  snackbarColor.value = 'success'
  snackbar.value = true
}

onMounted(async () => {
  try {
    const [speciesData, samplesData] = await Promise.all([
      apiService.getSpecies(),
      apiService.getSamples()
    ])
    
    if (speciesData && speciesData.length > 0) {
      speciesList.value = speciesData.map(s => s.name)
    }
    if (samplesData && samplesData.length > 0) {
      sampleList.value = [...new Set(samplesData.map(s => s.name))]
    }
  } catch (error) {
    console.error('Failed to load filters:', error)
  }
  
  if (route.query) {
    if (route.query.gene_name) filters.gene_name = route.query.gene_name
    if (route.query.transcript_id) filters.transcript_id = route.query.transcript_id
    if (route.query.sample) filters.sample = route.query.sample
    if (route.query.species) filters.species = route.query.species
  }
  
  search()
})

watch(() => route.query, (newQuery) => {
  if (newQuery.gene_name) filters.gene_name = newQuery.gene_name
  if (newQuery.transcript_id) filters.transcript_id = newQuery.transcript_id
  if (newQuery.sample) filters.sample = newQuery.sample
  if (newQuery.species) filters.species = newQuery.species
  search()
})

watch(() => route.query, (newQuery) => {
  if (newQuery.gene_name) filters.gene_name = newQuery.gene_name
  if (newQuery.transcript_id) filters.transcript_id = newQuery.transcript_id
  if (newQuery.cell_line) filters.cell_line = newQuery.cell_line
  if (newQuery.species) filters.species = newQuery.species
  search()
})
</script>

<style scoped>
.search-page {
  min-height: 100vh;
  background: rgb(var(--v-theme-background));
}

/* ── Page title ─────────────────────────────────────────────── */
.search-page :deep(h1.text-h4) {
  font-weight: 700;
  letter-spacing: -0.02em;
  color: rgba(0, 0, 0, 0.82);
}

/* ── Filter card — glassmorphism ────────────────────────────── */
.search-page :deep(.v-card) {
  background: rgba(255, 255, 255, 0.72) !important;
  backdrop-filter: blur(16px) saturate(160%) !important;
  -webkit-backdrop-filter: blur(16px) saturate(160%) !important;
  border: 1px solid rgba(255, 255, 255, 0.60) !important;
  border-radius: 16px !important;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06), 0 1px 4px rgba(0, 0, 0, 0.04) !important;
}

/* ── Data table — keep glass bg, refine header ───────────────── */
.search-page :deep(.v-data-table) {
  background: transparent !important;
}

.search-page :deep(.v-data-table__th) {
  background: rgba(13, 115, 119, 0.05) !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  color: rgba(0, 0, 0, 0.55) !important;
  border-bottom: 1px solid rgba(13, 115, 119, 0.10) !important;
  white-space: nowrap;
}

.search-page :deep(.v-data-table__td) {
  padding: 11px 16px !important;
  background: transparent !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05) !important;
  font-size: 14.5px;
}

.search-page :deep(.v-data-table__tr:hover .v-data-table__td) {
  background: rgba(13, 115, 119, 0.03) !important;
}

.search-page :deep(.v-data-table-footer) {
  border-top: 1px solid rgba(13, 115, 119, 0.08) !important;
  font-size: 13.5px;
  color: rgba(0, 0, 0, 0.55);
}

/* ── Chips in table ─────────────────────────────────────────── */
.search-page :deep(.v-chip) {
  font-size: 13px;
  font-weight: 500;
}

/* ── Outlined input fields ──────────────────────────────────── */
.search-page :deep(.v-field__outline) {
  --v-field-border-opacity: 0.18;
}

/* ── Search/Export buttons ──────────────────────────────────── */
.search-page :deep(.v-btn) {
  letter-spacing: 0.02em;
}

/* ── Dark mode ──────────────────────────────────────────────── */
.v-theme--apaAtlasDarkTheme .search-page :deep(.v-card) {
  background: rgba(24, 28, 37, 0.80) !important;
  border: 1px solid rgba(255, 255, 255, 0.07) !important;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.30), 0 1px 4px rgba(0, 0, 0, 0.20) !important;
}

.v-theme--apaAtlasDarkTheme .search-page :deep(h1.text-h4) {
  color: rgba(255, 255, 255, 0.90);
}

.v-theme--apaAtlasDarkTheme .search-page :deep(.v-data-table__th) {
  background: rgba(13, 115, 119, 0.08) !important;
  color: rgba(255, 255, 255, 0.50) !important;
  border-bottom-color: rgba(13, 115, 119, 0.15) !important;
}

.v-theme--apaAtlasDarkTheme .search-page :deep(.v-data-table__td) {
  border-bottom-color: rgba(255, 255, 255, 0.05) !important;
}

.v-theme--apaAtlasDarkTheme .search-page :deep(.v-data-table__tr:hover .v-data-table__td) {
  background: rgba(42, 168, 174, 0.06) !important;
}
</style>
