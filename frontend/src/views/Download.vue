<template>
  <div class="download-page">
    <v-container class="py-8">
      <div class="text-center mb-8">
        <h1 class="text-h3 font-weight-bold mb-2">
          <v-icon icon="mdi-download" size="40" color="primary" class="mr-3"></v-icon>
          Download Data
        </h1>
        <p class="text-h6 text-grey">Export ApaAtlas data in your preferred format</p>
      </div>

      <v-row justify="center">
        <v-col cols="12" lg="10">
          <!-- Download Cards -->
          <v-row>
            <v-col cols="12" md="4" v-for="item in downloadOptions" :key="item.id">
              <v-card 
                class="download-card h-100" 
                variant="outlined"
                @click="selectDownload(item)"
                :class="{ 'selected': selectedDownload?.id === item.id }"
                hover
              >
                <v-card-text class="text-center pa-6">
                  <v-avatar :color="item.color" size="72" class="mb-4">
                    <v-icon :icon="item.icon" size="36"></v-icon>
                  </v-avatar>
                  <h3 class="text-h5 font-weight-bold mb-2">{{ item.title }}</h3>
                  <p class="text-body-2 text-grey">{{ item.description }}</p>
                  <div class="mt-4">
                    <v-chip size="small" class="mr-1" v-for="fmt in item.formats" :key="fmt">
                      {{ fmt.toUpperCase() }}
                    </v-chip>
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>

          <!-- Download Options Panel -->
          <v-expand-transition>
            <v-card v-if="selectedDownload" variant="outlined" class="mt-8 pa-6">
              <h3 class="text-h5 font-weight-bold mb-4">
                <v-icon :icon="selectedDownload.icon" class="mr-2"></v-icon>
                Download {{ selectedDownload.title }}
              </h3>

              <v-row>
                <v-col cols="12" md="6">
                  <v-select
                    v-model="filters.species"
                    :items="speciesOptions"
                    label="Filter by Species"
                    variant="outlined"
                    density="compact"
                    clearable
                    hide-details
                    prepend-inner-icon="mdi-earth"
                  ></v-select>
                </v-col>
                <v-col cols="12" md="6" v-if="selectedDownload.id !== 'genes'">
                  <v-select
                    v-model="filters.sample"
                    :items="sampleOptions"
                    label="Filter by Sample"
                    variant="outlined"
                    density="compact"
                    clearable
                    hide-details
                    prepend-inner-icon="mdi-flask"
                  ></v-select>
                </v-col>
                <v-col cols="12" md="6" v-if="selectedDownload.id === 'apa-sites'">
                  <v-text-field
                    v-model="filters.geneName"
                    label="Filter by Gene Name"
                    variant="outlined"
                    density="compact"
                    clearable
                    hide-details
                    prepend-inner-icon="mdi-gene"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-select
                    v-model="filters.format"
                    :items="selectedDownload.formats"
                    label="Export Format"
                    variant="outlined"
                    density="compact"
                    hide-details
                    prepend-inner-icon="mdi-file-delimited"
                  ></v-select>
                </v-col>
              </v-row>

              <div class="d-flex align-center justify-space-between mt-6 pa-4 bg-grey-lighten-4 rounded">
                <div>
                  <div class="text-body-2 text-grey">Estimated records</div>
                  <div class="text-h6 font-weight-bold">{{ estimatedRecords }}</div>
                </div>
                <v-btn 
                  color="primary" 
                  size="large" 
                  @click="downloadData"
                  :loading="downloading"
                >
                  <v-icon start>mdi-download</v-icon>
                  Download
                </v-btn>
              </div>
            </v-card>
          </v-expand-transition>

          <!-- API Documentation -->
          <v-card variant="outlined" class="mt-8 pa-6">
            <h3 class="text-h5 font-weight-bold mb-4">
              <v-icon icon="mdi-code-braces" class="mr-2"></v-icon>
              Programmatic Access (API)
            </h3>
            <p class="text-body-1 mb-4">
              You can also download data programmatically using our REST API:
            </p>
            
            <v-tabs v-model="apiTab" color="primary">
              <v-tab value="curl">cURL</v-tab>
              <v-tab value="python">Python</v-tab>
              <v-tab value="r">R</v-tab>
            </v-tabs>

            <v-tabs-window v-model="apiTab" class="mt-4">
              <v-tabs-window-item value="curl">
                <v-sheet color="grey-darken-4" class="pa-4" style="overflow-x: auto;">
                  <pre class="text-body-2 text-white">{{ apiExamples.curl }}</pre>
                </v-sheet>
              </v-tabs-window-item>
              <v-tabs-window-item value="python">
                <v-sheet color="grey-darken-4" class="pa-4" style="overflow-x: auto;">
                  <pre class="text-body-2 text-white">{{ apiExamples.python }}</pre>
                </v-sheet>
              </v-tabs-window-item>
              <v-tabs-window-item value="r">
                <v-sheet color="grey-darken-4" class="pa-4" style="overflow-x: auto;">
                  <pre class="text-body-2 text-white">{{ apiExamples.r }}</pre>
                </v-sheet>
              </v-tabs-window-item>
            </v-tabs-window>

            <v-btn 
              color="primary" 
              variant="tonal" 
              class="mt-4"
              @click="copyApiCommand"
            >
              <v-icon start>mdi-content-copy</v-icon>
              Copy Command
            </v-btn>
          </v-card>

          <!-- Data Schema -->
          <v-card variant="outlined" class="mt-8 pa-6">
            <h3 class="text-h5 font-weight-bold mb-4">
              <v-icon icon="mdi-table" class="mr-2"></v-icon>
              Data Schema
            </h3>
            
            <v-tabs v-model="schemaTab" color="primary">
              <v-tab value="apa-sites">APA Sites</v-tab>
              <v-tab value="genes">Genes</v-tab>
              <v-tab value="transcripts">Transcripts</v-tab>
            </v-tabs>

            <v-tabs-window v-model="schemaTab" class="mt-4">
              <v-tabs-window-item value="apa-sites">
                <v-table density="compact" class="schema-table">
                  <thead>
                    <tr>
                      <th>Field</th>
                      <th>Type</th>
                      <th>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="field in schemas.apaSites" :key="field.name">
                      <td><code>{{ field.name }}</code></td>
                      <td>{{ field.type }}</td>
                      <td>{{ field.desc }}</td>
                    </tr>
                  </tbody>
                </v-table>
              </v-tabs-window-item>
              <v-tabs-window-item value="genes">
                <v-table density="compact" class="schema-table">
                  <thead>
                    <tr>
                      <th>Field</th>
                      <th>Type</th>
                      <th>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="field in schemas.genes" :key="field.name">
                      <td><code>{{ field.name }}</code></td>
                      <td>{{ field.type }}</td>
                      <td>{{ field.desc }}</td>
                    </tr>
                  </tbody>
                </v-table>
              </v-tabs-window-item>
              <v-tabs-window-item value="transcripts">
                <v-table density="compact" class="schema-table">
                  <thead>
                    <tr>
                      <th>Field</th>
                      <th>Type</th>
                      <th>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="field in schemas.transcripts" :key="field.name">
                      <td><code>{{ field.name }}</code></td>
                      <td>{{ field.type }}</td>
                      <td>{{ field.desc }}</td>
                    </tr>
                  </tbody>
                </v-table>
              </v-tabs-window-item>
            </v-tabs-window>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { apiService } from '@/services/api'

const selectedDownload = ref(null)
const downloading = ref(false)
const apiTab = ref('curl')
const schemaTab = ref('apa-sites')

const filters = ref({
  species: null,
  sample: null,
  geneName: '',
  format: 'csv'
})

const speciesOptions = ref([])
const sampleOptions = ref([])

const downloadOptions = [
  {
    id: 'apa-sites',
    title: 'APA Sites',
    description: 'All polyadenylation sites with positions, abundances, and sample information',
    icon: 'mdi-map-marker',
    color: 'primary',
    formats: ['csv', 'tsv', 'txt']
  },
  {
    id: 'genes',
    title: 'Genes',
    description: 'Gene information including chromosome, strand, and APA site counts',
    icon: 'mdi-gene',
    color: 'secondary',
    formats: ['csv', 'tsv', 'txt']
  },
  {
    id: 'transcripts',
    title: 'Transcripts',
    description: 'Transcript records with APA site counts and associated genes',
    icon: 'mdi-rna',
    color: 'tertiary',
    formats: ['csv', 'tsv', 'txt']
  }
]

const estimatedRecords = computed(() => {
  // This would ideally fetch from API
  return '~10,000+'
})

const selectDownload = (item) => {
  selectedDownload.value = item
  filters.value.format = item.formats[0]
}

const downloadData = async () => {
  downloading.value = true
  try {
    let url = `/api/v1/download/${selectedDownload.value.id}`
    const params = new URLSearchParams()
    
    if (filters.value.species) params.append('species', filters.value.species)
    if (filters.value.sample) params.append('sample', filters.value.sample)
    if (filters.value.geneName) params.append('gene_name', filters.value.geneName)
    params.append('format', filters.value.format)
    
    const response = await fetch(`${url}?${params.toString()}`)
    const blob = await response.blob()
    const filename = `${selectedDownload.value.id}.${filters.value.format}`
    
    const link = document.createElement('a')
    link.href = window.URL.createObjectURL(blob)
    link.download = filename
    link.click()
  } catch (err) {
    console.error('Download failed:', err)
  } finally {
    downloading.value = false
  }
}

const apiExamples = {
  curl: `# Download APA Sites
curl -o apa_sites.csv "http://localhost:8000/api/v1/download/apa-sites?format=csv"

# Download Genes
curl -o genes.csv "http://localhost:8000/api/v1/download/genes?format=csv"

# With filters
curl -o hep_apa_sites.csv "http://localhost:8000/api/v1/download/apa-sites?species=Human&format=csv"`,
  
  python: `import requests

# Download APA Sites
url = "http://localhost:8000/api/v1/download/apa-sites"
params = {"format": "csv", "species": "Human"}
response = requests.get(url, params=params)

with open("apa_sites.csv", "wb") as f:
    f.write(response.content)`,
  
  r: `# Download using httr
library(httr)

url <- "http://localhost:8000/api/v1/download/apa-sites"
params <- list(format = "csv", species = "Human")

response <- GET(url, query = params)
writeBin(content(response, "raw"), "apa_sites.csv")`
}

const schemas = {
  apaSites: [
    { name: 'gene_name', type: 'string', desc: 'Official gene symbol' },
    { name: 'gene_id', type: 'string', desc: 'Ensembl Gene ID' },
    { name: 'transcript_id', type: 'string', desc: 'Ensembl Transcript ID' },
    { name: 'site_id', type: 'string', desc: 'APA site identifier' },
    { name: 'site_position', type: 'integer', desc: 'Genomic position of APA site' },
    { name: 'site_count', type: 'integer', desc: 'Number of reads at site' },
    { name: 'site_abundance', type: 'float', desc: 'Relative abundance (0-1)' },
    { name: 'species', type: 'string', desc: 'Species name' },
    { name: 'sample', type: 'string', desc: 'Sample/cell line name' }
  ],
  genes: [
    { name: 'gene_name', type: 'string', desc: 'Official gene symbol' },
    { name: 'gene_id', type: 'string', desc: 'Ensembl Gene ID' },
    { name: 'chromosome', type: 'string', desc: 'Chromosome number' },
    { name: 'strand', type: 'string', desc: '+ or -' },
    { name: 'species', type: 'string', desc: 'Species name' },
    { name: 'transcript_count', type: 'integer', desc: 'Number of transcripts' },
    { name: 'apa_site_count', type: 'integer', desc: 'Total APA sites' }
  ],
  transcripts: [
    { name: 'gene_name', type: 'string', desc: 'Official gene symbol' },
    { name: 'gene_id', type: 'string', desc: 'Ensembl Gene ID' },
    { name: 'transcript_id', type: 'string', desc: 'Ensembl Transcript ID' },
    { name: 'chromosome', type: 'string', desc: 'Chromosome number' },
    { name: 'strand', type: 'string', desc: '+ or -' },
    { name: 'species', type: 'string', desc: 'Species name' },
    { name: 'apa_site_count', type: 'integer', desc: 'Number of APA sites' }
  ]
}

const copyApiCommand = () => {
  const command = apiExamples[apiTab.value]
  navigator.clipboard.writeText(command)
}

onMounted(async () => {
  try {
    const species = await apiService.getSpecies()
    speciesOptions.value = species.map(s => s.name)
    
    const samples = await apiService.getSamples()
    sampleOptions.value = samples.map(s => s.name)
  } catch (err) {
    console.error('Failed to load options:', err)
  }
})

import { onMounted } from 'vue'
</script>

<style scoped>
.download-page {
  min-height: 100vh;
  background: rgb(var(--v-theme-background));
}

.download-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent !important;
}

.download-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.download-card.selected {
  border-color: rgb(var(--v-theme-primary)) !important;
  background: rgba(var(--v-theme-primary), 0.04);
}

code {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.85em;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}

.schema-table {
  background: transparent !important;
}

.schema-table th {
  background: rgba(var(--v-theme-surface-variant), 0.3) !important;
}
</style>
