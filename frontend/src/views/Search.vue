<template>
  <div class="search-page">
    <v-container class="py-10">
      <div class="section-eyebrow mb-2">Search & Filter</div>
      <h1 class="section-heading mb-6">Browse APA Sites</h1>

      <!-- Glassmorphism Search Frame -->
      <div class="search-frame mb-8">
        <!-- Top bar -->
        <div class="search-frame-topbar">
          <div class="d-flex align-center" style="gap:10px;">
            <div class="topbar-icon">
              <v-icon icon="mdi-filter-variant" size="17" color="white"></v-icon>
            </div>
            <span class="topbar-label">Filter by</span>
          </div>
          <button class="reset-btn" @click="clearFilters">
            <v-icon icon="mdi-refresh" size="14" class="mr-1"></v-icon>
            Reset
          </button>
        </div>

        <!-- Filter inputs -->
        <div class="filter-grid">
          <div class="filter-card">
            <div class="filter-inner-label" :class="{ 'label-hidden': !!filters.gene_name }">
              <span class="filter-col-icon" style="background: linear-gradient(135deg,#0D7377,#14919B)">
                <v-icon icon="mdi-dna" size="13" color="white"></v-icon>
              </span>
              <span>Gene Name</span>
            </div>
            <v-text-field
              v-model="filters.gene_name"
              clearable
              variant="plain"
              density="compact"
              hide-details
              class="filter-field"
              @update:model-value="debouncedSearch"
            ></v-text-field>
          </div>

          <div class="filter-card">
            <div class="filter-inner-label" :class="{ 'label-hidden': !!filters.transcript_id }">
              <span class="filter-col-icon" style="background: linear-gradient(135deg,#5C6BC0,#7986CB)">
                <v-icon icon="mdi-rna" size="13" color="white"></v-icon>
              </span>
              <span>Transcript ID</span>
            </div>
            <v-text-field
              v-model="filters.transcript_id"
              clearable
              variant="plain"
              density="compact"
              hide-details
              class="filter-field"
              @update:model-value="debouncedSearch"
            ></v-text-field>
          </div>

          <div class="filter-card filter-card--select">
            <div class="filter-inner-label" :class="{ 'label-hidden': !!filters.species }">
              <span class="filter-col-icon" style="background: linear-gradient(135deg,#2E7D32,#43A047)">
                <v-icon icon="mdi-earth" size="13" color="white"></v-icon>
              </span>
              <span>Species</span>
            </div>
            <v-select
              v-model="filters.species"
              :items="speciesList"
              clearable
              variant="plain"
              density="compact"
              hide-details
              class="filter-field"
              :menu-props="{ class: 'search-select-menu' }"
              @update:model-value="debouncedSearch"
            ></v-select>
          </div>

          <div class="filter-card filter-card--select">
            <div class="filter-inner-label" :class="{ 'label-hidden': !!filters.sample }">
              <span class="filter-col-icon" style="background: linear-gradient(135deg,#C75B00,#EF6C00)">
                <v-icon icon="mdi-flask-outline" size="13" color="white"></v-icon>
              </span>
              <span>Sample</span>
            </div>
            <v-select
              v-model="filters.sample"
              :items="sampleList"
              clearable
              variant="plain"
              density="compact"
              hide-details
              class="filter-field"
              :menu-props="{ class: 'search-select-menu' }"
              @update:model-value="debouncedSearch"
            ></v-select>
          </div>
        </div>

        <!-- Actions row -->
        <div class="search-frame-actions">
          <button class="search-btn" @click="search" :disabled="loading">
            <v-progress-circular v-if="loading" size="16" width="2" indeterminate class="mr-2" color="white"></v-progress-circular>
            <v-icon v-else icon="mdi-magnify" size="18" class="mr-2"></v-icon>
            Search
          </button>
          <v-spacer></v-spacer>
          <button
            class="export-btn"
            @click="exportResults"
            :disabled="results.length === 0"
          >
            <v-icon icon="mdi-download" size="16" class="mr-2"></v-icon>
            Export CSV
          </button>
        </div>
      </div>
      
      <div class="results-card">
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
      </div>
      
      <v-snackbar v-model="snackbar" :color="snackbarColor">
        {{ snackbarText }}
      </v-snackbar>
    </v-container>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
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
</script>

<style scoped>
.search-page {
  min-height: 100vh;
  background: rgb(var(--v-theme-background));
}

/* ── Eyebrow + Heading ──────────────────────────────────────── */
.section-eyebrow {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #14919B;
  background: rgba(20, 145, 155, 0.08);
  border-radius: 20px;
  padding: 3px 12px;
}
.section-heading {
  font-size: 1.75rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: rgba(0, 0, 0, 0.82);
}

/* ── Search Frame ───────────────────────────────────────────── */
.search-frame {
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.65);
  border-radius: 20px;
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.06), 0 1px 4px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.search-frame-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 24px;
  background: linear-gradient(90deg, rgba(13, 115, 119, 0.07) 0%, rgba(20, 145, 155, 0.02) 100%);
  border-bottom: 1px solid rgba(13, 115, 119, 0.10);
}

.topbar-icon {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: linear-gradient(135deg, #0D7377, #14919B);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.topbar-label {
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(0, 0, 0, 0.50);
}

.reset-btn {
  display: flex;
  align-items: center;
  font-size: 0.80rem;
  font-weight: 500;
  color: #0D7377;
  background: none;
  border: none;
  cursor: pointer;
  padding: 5px 12px;
  border-radius: 8px;
  transition: background 0.15s;
}
.reset-btn:hover {
  background: rgba(13, 115, 119, 0.08);
}

/* ── Filter Grid ─────────────────────────────────────────────── */
.filter-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  padding: 20px 24px 8px;
}
@media (max-width: 960px) {
  .filter-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .filter-grid { grid-template-columns: 1fr; }
}

.filter-card {
  position: relative;
  background: rgba(255, 255, 255, 0.68);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.82);
  border-radius: 12px;
  padding: 0;
  height: 50px;
  display: flex;
  align-items: center;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  transition: border-color 0.2s, box-shadow 0.2s, border-bottom-left-radius 0.1s, border-bottom-right-radius 0.1s;
}
.filter-card:focus-within {
  border-color: rgba(20, 145, 155, 0.45);
  box-shadow: 0 2px 18px rgba(13, 115, 119, 0.13);
}
.filter-card--select:focus-within {
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
  border-bottom-color: transparent;
}

/* Label floats over the input area; fades on hover, focus, or when value is filled */
.filter-inner-label {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: rgba(0, 0, 0, 0.48);
  white-space: nowrap;
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.filter-inner-label.label-hidden,
.filter-card:hover .filter-inner-label,
.filter-card:focus-within .filter-inner-label {
  opacity: 0;
  transform: translateY(-50%) translateX(-4px);
}

.filter-col-icon {
  width: 20px;
  height: 20px;
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* v-field spans full card width (no card padding) → dropdown width = card width */
.filter-field {
  flex: 1;
  min-width: 0;
  align-self: stretch;
}
.filter-field :deep(.v-field__input) {
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  padding-left: 0 !important;
  font-size: 0.91rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.80);
  min-height: unset !important;
}
.filter-field :deep(.v-field) {
  padding: 0 12px !important;
  align-items: center;
  height: 100%;
}
.filter-field :deep(.v-input__control) {
  min-height: unset !important;
  height: 100%;
}
.filter-field :deep(.v-field__clearable) {
  padding-top: 0 !important;
  padding-right: 0 !important;
}
.filter-field :deep(.v-select__selection-text) {
  font-size: 0.91rem;
  font-weight: 500;
}

/* ── Actions row ────────────────────────────────────────────── */
.search-frame-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px 20px;
  border-top: 1px solid rgba(13, 115, 119, 0.08);
}

.search-btn {
  display: inline-flex;
  align-items: center;
  height: 42px;
  padding: 0 24px;
  border-radius: 10px;
  border: none;
  background: linear-gradient(135deg, #0D7377, #14919B);
  color: white;
  font-size: 0.9rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  cursor: pointer;
  box-shadow: 0 2px 12px rgba(13, 115, 119, 0.30);
  transition: box-shadow 0.2s, opacity 0.15s;
}
.search-btn:hover:not(:disabled) {
  box-shadow: 0 4px 20px rgba(13, 115, 119, 0.42);
}
.search-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.export-btn {
  display: inline-flex;
  align-items: center;
  height: 42px;
  padding: 0 20px;
  border-radius: 10px;
  border: 1.5px solid rgba(13, 115, 119, 0.40);
  background: transparent;
  color: #0D7377;
  font-size: 0.875rem;
  font-weight: 500;
  letter-spacing: 0.02em;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.export-btn:hover:not(:disabled) {
  background: rgba(13, 115, 119, 0.06);
  border-color: #0D7377;
}
.export-btn:disabled {
  opacity: 0.40;
  cursor: not-allowed;
}

/* ── Results Card — glassmorphism ───────────────────────────── */
.results-card {
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(24px) saturate(200%);
  -webkit-backdrop-filter: blur(24px) saturate(200%);
  border: 1px solid rgba(255, 255, 255, 0.70);
  border-radius: 20px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.07), 0 2px 8px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

/* ── Data table ─────────────────────────────────────────────── */
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
</style>

<!-- Global: Vuetify overlays are teleported outside the component root;
     scoped styles cannot reach them — this block is intentionally unscoped. -->
<style>
.search-select-menu {
  margin-top: -1px;
}
.search-select-menu .v-overlay__content {
  min-width: unset !important;
  max-width: unset !important;
}
.search-select-menu .v-list {
  background: rgba(255, 255, 255, 0.90) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  border: 1px solid rgba(255, 255, 255, 0.82) !important;
  border-top: none !important;
  border-top-left-radius: 0 !important;
  border-top-right-radius: 0 !important;
  border-bottom-left-radius: 12px !important;
  border-bottom-right-radius: 12px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.10), 0 2px 8px rgba(0, 0, 0, 0.06) !important;
  padding: 6px !important;
}
.search-select-menu .v-list-item {
  border-radius: 8px !important;
  min-height: 36px !important;
  margin: 1px 0 !important;
  padding: 0 12px !important;
  transition: background 0.15s !important;
}
.search-select-menu .v-list-item:hover {
  background: rgba(13, 115, 119, 0.08) !important;
}
.search-select-menu .v-list-item--active {
  background: rgba(13, 115, 119, 0.12) !important;
}
.search-select-menu .v-list-item-title {
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  color: rgba(0, 0, 0, 0.75) !important;
  letter-spacing: 0.01em !important;
}
.search-select-menu .v-list-item--active .v-list-item-title {
  color: #0D7377 !important;
  font-weight: 600 !important;
}
</style>
