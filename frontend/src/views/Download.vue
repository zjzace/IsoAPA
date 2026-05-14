<template>
  <div class="download-page">
    <!-- 1. Hero -->
    <section class="hero-section">
      <div class="hero-bg"></div>
      <v-container class="hero-content">
        <h1 class="text-h3 font-weight-bold text-white mb-2">Download ApaAtlas Data</h1>
        <p class="text-h6 text-white mb-6 opacity-90">Bulk export of isoform-level polyadenylation datasets</p>
        
        <div class="d-flex flex-wrap gap-4">
          <v-chip class="mr-2" variant="outlined" color="white" style="background: rgba(255,255,255,0.9);">
            <strong style="color: #0D7377;">235K+ PA Sites</strong>
          </v-chip>
          <v-chip class="mr-2" variant="outlined" color="white" style="background: rgba(255,255,255,0.9);">
            <strong style="color: #0D7377;">3 Datasets</strong>
          </v-chip>
          <v-chip variant="outlined" color="white" style="background: rgba(255,255,255,0.9);">
            <strong style="color: #0D7377;">Multiple Species</strong>
          </v-chip>
        </div>
      </v-container>
    </section>

    <!-- 2. Main content -->
    <v-container class="py-12">
      <!-- A. Dataset Cards -->
      <div class="section-eyebrow mb-2">Choose Dataset</div>
      <div class="dataset-cards-row mb-8">
        <div 
          v-for="item in datasets" 
          :key="item.id"
          class="dataset-card" 
          :class="{ 'dataset-card--selected': selectedDataset?.id === item.id }" 
          @click="selectDataset(item)"
        >
          <div class="dataset-card-icon" :style="{ background: item.gradient }">
            <v-icon :icon="item.icon" size="28" color="white"></v-icon>
          </div>
          <div class="dataset-card-title">{{ item.title }}</div>
          <div class="dataset-card-desc">{{ item.description }}</div>
          <div class="dataset-card-meta">
            <v-chip size="x-small" variant="tonal" color="primary">{{ item.countLabel }}</v-chip>
            <v-chip size="x-small" variant="outlined" class="ml-1" v-for="fmt in item.formats" :key="fmt">{{ fmt.toUpperCase() }}</v-chip>
          </div>
        </div>
      </div>

      <!-- B. Scope + Format -->
      <div class="section-eyebrow mb-2">Filter & Format</div>
      <div class="scope-panel">
        <div class="scope-group">
          <div class="scope-label">
            <v-icon icon="mdi-earth" size="16" class="mr-1"></v-icon>
            Species Scope
          </div>
          <div class="scope-chips-row">
            <button class="scope-chip" :class="{ active: !selectedSpecies }" @click="selectedSpecies = null">
              <v-icon icon="mdi-database" size="14" class="mr-1"></v-icon>
              Whole Dataset
            </button>
            <button
              v-for="sp in speciesList"
              :key="sp.id"
              class="scope-chip"
              :class="{ active: selectedSpecies === sp.name }"
              @click="selectedSpecies = sp.name"
            >
              {{ sp.name }}
              <span class="scope-chip-latin" v-if="sp.latin_name">{{ sp.latin_name }}</span>
            </button>
          </div>
        </div>

        <div class="scope-divider"></div>

        <div class="scope-group">
          <div class="scope-label">
            <v-icon icon="mdi-file-delimited" size="16" class="mr-1"></v-icon>
            Format
          </div>
          <div class="scope-chips-row">
            <template v-if="selectedDataset && selectedDataset.formats.length === 1">
              <button class="scope-chip active" style="cursor:default;">
                {{ selectedDataset.formats[0].toUpperCase() }}
              </button>
            </template>
            <template v-else>
              <button
                v-for="fmt in (selectedDataset ? selectedDataset.formats : ['csv','tsv'])"
                :key="fmt"
                class="scope-chip"
                :class="{ active: selectedFormat === fmt }"
                @click="selectedFormat = fmt"
              >
                {{ fmt.toUpperCase() }}
              </button>
            </template>
          </div>
        </div>
      </div>

      <!-- C. Download Action Panel -->
      <div v-if="selectedDataset" class="download-action-panel">
        <div class="download-action-info">
          <div class="download-action-eyebrow">Ready to Download</div>
          <div class="download-action-title">
            {{ selectedDataset.title }}
            <span v-if="selectedSpecies" class="download-action-species"> · {{ selectedSpecies }}</span>
          </div>
          <div class="download-action-meta">
            <v-chip size="small" variant="tonal" color="primary" class="mr-2">{{ selectedFormat.toUpperCase() }}</v-chip>
            <span class="text-grey text-caption">{{ selectedDataset.countLabel }}</span>
          </div>
        </div>
        <v-btn
          size="x-large"
          class="download-btn"
          :loading="downloading"
          @click="triggerDownload"
        >
          <v-icon start icon="mdi-download"></v-icon>
          Download
        </v-btn>
      </div>

      <!-- D. API Access -->
      <div class="section-eyebrow mb-2">Programmatic Access</div>
      <div class="api-card">
        <div class="api-card-header">
          <div>
            <div class="section-eyebrow mb-1">Programmatic Access</div>
            <h3 class="api-card-title">Download via API</h3>
            <p class="api-card-subtitle">Commands update automatically when you change the dataset or scope above.</p>
          </div>
        </div>

        <div class="lang-tabs">
          <button
            v-for="lang in ['curl','python','r']"
            :key="lang"
            class="lang-tab"
            :class="{ active: apiLang === lang }"
            @click="apiLang = lang"
          >
            {{ langLabel(lang) }}
          </button>
        </div>

        <div class="code-block">
          <pre class="code-text"><code>{{ currentCommand }}</code></pre>
          <button class="copy-btn" @click="copyCommand">
            <v-icon :icon="copied ? 'mdi-check' : 'mdi-content-copy'" size="18"></v-icon>
            {{ copied ? 'Copied!' : 'Copy' }}
          </button>
        </div>
      </div>

      <!-- E. Schema (collapsed) -->
      <div class="schema-section">
        <button class="schema-toggle-btn" @click="schemaOpen = !schemaOpen">
          <v-icon :icon="schemaOpen ? 'mdi-chevron-up' : 'mdi-chevron-down'" size="20" class="mr-2"></v-icon>
          {{ schemaOpen ? 'Hide Data Schema' : 'View Data Schema' }}
        </button>

        <v-expand-transition>
          <div v-if="schemaOpen" class="schema-content mt-6">
            <div class="lang-tabs">
              <button 
                v-for="s in schemas" 
                :key="s.id" 
                class="lang-tab" 
                :class="{ active: schemaTab === s.id }" 
                @click="schemaTab = s.id"
              >
                {{ s.title }}
              </button>
            </div>
            <div class="schema-table-wrapper">
              <v-table density="compact" class="elegant-table">
                <thead>
                  <tr>
                    <th>Field</th><th>Type</th><th>Description</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="f in currentSchema" :key="f.name">
                    <td><code class="field-badge">{{ f.name }}</code></td>
                    <td><span class="type-badge">{{ f.type }}</span></td>
                    <td class="text-grey-darken-1">{{ f.desc }}</td>
                  </tr>
                </tbody>
              </v-table>
            </div>
          </div>
        </v-expand-transition>
      </div>
    </v-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { apiService } from '@/services/api'

const speciesList = ref([])
const selectedDataset = ref(null)
const selectedSpecies = ref(null)
const selectedFormat = ref('csv')
const apiLang = ref('curl')
const copied = ref(false)
const schemaOpen = ref(false)
const schemaTab = ref('apa-sites')
const downloading = ref(false)

const datasets = [
  {
    id: 'apa-sites',
    title: 'PA Sites',
    description: 'Polyadenylation sites with genomic positions, read counts, and relative abundances per isoform',
    icon: 'mdi-map-marker-multiple',
    gradient: 'linear-gradient(135deg, #0D7377, #14919B)',
    countLabel: '235K+ records',
    formats: ['csv', 'tsv'],
  },
  {
    id: 'bed',
    title: 'Genome Browser Track',
    description: 'PA sites in BED6 format — ready to load into IGV, UCSC Genome Browser, or JBrowse for visualization',
    icon: 'mdi-dna',
    gradient: 'linear-gradient(135deg, #2E7D32, #388E3C)',
    countLabel: 'BED6 format',
    formats: ['bed'],
  },
  {
    id: 'abundance-matrix',
    title: 'Sample Abundance Matrix',
    description: 'PA site × sample read-count matrix (TSV) for differential APA analysis with DaPars, QAPA, or DEXSeq',
    icon: 'mdi-table-large',
    gradient: 'linear-gradient(135deg, #355C7D, #4A7898)',
    countLabel: 'Sites × Samples',
    formats: ['tsv'],
  },
]

const selectDataset = (item) => {
  selectedDataset.value = item
  selectedFormat.value = item.formats[0]
}

const triggerDownload = async () => {
  if (!downloadUrl.value) return
  downloading.value = true
  try {
    const response = await fetch(downloadUrl.value)
    if (!response.ok) throw new Error(`Server returned ${response.status}`)
    const blob = await response.blob()
    const objectUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = objectUrl
    a.download = downloadFilename.value
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(objectUrl)
  } catch (err) {
    console.error('Download failed:', err)
  } finally {
    downloading.value = false
  }
}

const BASE_URL = '/api/v1'

const downloadUrl = computed(() => {
  if (!selectedDataset.value) return ''
  const params = new URLSearchParams()
  if (selectedSpecies.value) params.set('species', selectedSpecies.value)
  if (selectedDataset.value.formats.length > 1) params.set('format', selectedFormat.value)
  const query = params.toString()
  return `${BASE_URL}/download/${selectedDataset.value.id}${query ? '?' + query : ''}`
})

const downloadFilename = computed(() => {
  if (!selectedDataset.value) return ''
  const sp = selectedSpecies.value ? `_${selectedSpecies.value.toLowerCase().replace(/\s+/g, '_')}` : ''
  return `apaatlas_${selectedDataset.value.id}${sp}.${selectedFormat.value}`
})

const buildQueryString = () => {
  const parts = []
  if (selectedDataset.value?.formats.length > 1) parts.push(`format=${selectedFormat.value}`)
  if (selectedSpecies.value) parts.push(`species=${encodeURIComponent(selectedSpecies.value)}`)
  return parts.length ? '?' + parts.join('&') : ''
}

const curlCommand = computed(() => {
  const dataset = selectedDataset.value?.id || 'apa-sites'
  const qs = buildQueryString()
  const filename = downloadFilename.value || `apaatlas_${dataset}.${selectedFormat.value}`
  return `curl -o "${filename}" \\\n  "http://your-server/api/v1/download/${dataset}${qs}"`
})

const pythonCommand = computed(() => {
  const dataset = selectedDataset.value?.id || 'apa-sites'
  const filename = downloadFilename.value || `apaatlas_${dataset}.${selectedFormat.value}`
  const paramLines = []
  if (selectedDataset.value?.formats.length > 1) paramLines.push(`    "format": "${selectedFormat.value}",`)
  if (selectedSpecies.value) paramLines.push(`    "species": "${selectedSpecies.value}",`)
  const paramBlock = paramLines.length ? `\nparams = {\n${paramLines.join('\n')}\n}\n` : '\nparams = {}\n'
  return `import requests\n\nurl = "http://your-server/api/v1/download/${dataset}"${paramBlock}\nr = requests.get(url, params=params)\nwith open("${filename}", "wb") as f:\n    f.write(r.content)`
})

const rCommand = computed(() => {
  const dataset = selectedDataset.value?.id || 'apa-sites'
  const filename = downloadFilename.value || `apaatlas_${dataset}.${selectedFormat.value}`
  const paramLines = []
  if (selectedDataset.value?.formats.length > 1) paramLines.push(`    format = "${selectedFormat.value}",`)
  if (selectedSpecies.value) paramLines.push(`    species = "${selectedSpecies.value}",`)
  const paramBlock = paramLines.length ? `\nparams <- list(\n${paramLines.join('\n')}\n)\n` : '\nparams <- list()\n'
  return `library(httr)\n\nurl <- "http://your-server/api/v1/download/${dataset}"${paramBlock}\nresponse <- GET(url, query = params)\nwriteBin(content(response, "raw"), "${filename}")`
})

const currentCommand = computed(() => {
  if (apiLang.value === 'curl') return curlCommand.value
  if (apiLang.value === 'python') return pythonCommand.value
  return rCommand.value
})

const langLabel = (lang) => ({ curl: 'cURL', python: 'Python', r: 'R' }[lang])

const copyCommand = async () => {
  try {
    await navigator.clipboard.writeText(currentCommand.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch (err) {
    console.error('Failed to copy text: ', err)
  }
}

const schemas = [
  { id: 'apa-sites', title: 'PA Sites', fields: [
    { name: 'gene_name', type: 'string', desc: 'Official gene symbol' },
{ name: 'gene_id', type: 'string', desc: 'NCBI Entrez Gene ID' },
      { name: 'transcript_id', type: 'string', desc: 'NCBI RefSeq Transcript ID' },
    { name: 'site_id', type: 'string', desc: 'Unique APA site identifier (shared across samples)' },
    { name: 'representative_position', type: 'integer', desc: 'Consensus genomic coordinate of the PA site, computed as the mode across all supporting samples' },
    { name: 'sample_site_position', type: 'integer', desc: 'Genomic coordinate of the PA cleavage site as detected in this specific sample' },
    { name: 'site_abundance', type: 'float', desc: 'Relative abundance of this PA site within the transcript for this sample (0–1)' },
    { name: 'species', type: 'string', desc: 'Species name' },
    { name: 'sample', type: 'string', desc: 'Sample / cell line name' },
  ]},
  { id: 'bed', title: 'Genome Browser BED', fields: [
    { name: 'chrom', type: 'string', desc: 'Chromosome in UCSC format (e.g. chr1)' },
    { name: 'chromStart', type: 'integer', desc: '0-based start position of the PA site' },
    { name: 'chromEnd', type: 'integer', desc: '1-based end position (half-open interval)' },
    { name: 'name', type: 'string', desc: 'gene_name|transcript_id|site_id' },
    { name: 'score', type: 'string', desc: '.' },
    { name: 'strand', type: 'string', desc: '+ or –' },
  ]},
  { id: 'abundance-matrix', title: 'Abundance Matrix', fields: [
    { name: 'site_id', type: 'string', desc: 'APA site identifier' },
    { name: 'transcript_id', type: 'string', desc: 'NCBI RefSeq Transcript ID' },
    { name: 'gene_name', type: 'string', desc: 'Official gene symbol' },
    { name: 'chromosome', type: 'string', desc: 'Chromosome' },
    { name: 'strand', type: 'string', desc: '+ or –' },
    { name: 'species', type: 'string', desc: 'Species name' },
    { name: '[sample_name]', type: 'integer', desc: 'One column per sample — read count at this PA site' },
  ]},
]

const currentSchema = computed(() => schemas.find(s => s.id === schemaTab.value)?.fields || [])

onMounted(async () => {
  try {
    const species = await apiService.getSpecies()
    // Depending on API response, it might be an array of strings or objects. Handling both:
    if (species && species.length > 0) {
      if (typeof species[0] === 'string') {
        speciesList.value = species.map(s => ({ id: s, name: s }))
      } else {
        speciesList.value = species
      }
    }
  } catch (err) {
    console.error('Failed to load species:', err)
  }
})
</script>

<style scoped>
.download-page {
  min-height: 100vh;
  background-color: #f8fafc;
}

.hero-section {
  position: relative;
  min-height: 300px;
  display: flex;
  align-items: center;
  overflow: hidden;
}
.hero-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #0a4f53 0%, #0D7377 40%, #1a2744 100%);
  background-size: 300% 300%;
  animation: gradientShift 18s ease infinite;
}
.hero-bg::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse 80% 60% at 60% 40%, rgba(20,145,155,0.18) 0%, transparent 70%);
}
@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
.hero-content {
  position: relative;
  z-index: 1;
  padding: 48px 0 56px;
}

.section-eyebrow {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #14919B;
  margin-bottom: 4px;
}

.dataset-cards-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}
@media (max-width: 767px) {
  .dataset-cards-row { grid-template-columns: 1fr; }
}
.dataset-card {
  background: rgba(255, 255, 255, 0.80);
  backdrop-filter: blur(16px) saturate(150%);
  -webkit-backdrop-filter: blur(16px) saturate(150%);
  border: 1px solid rgba(255, 255, 255, 0.55);
  border-radius: 20px;
  padding: 28px 24px;
  cursor: pointer;
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  position: relative;
  overflow: hidden;
}
.dataset-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 32px rgba(13,115,119,0.12);
}
.dataset-card--selected {
  border: 2px solid #14919B !important;
  box-shadow: 0 0 0 4px rgba(20,145,155,0.12), 0 12px 32px rgba(13,115,119,0.16) !important;
  background: rgba(240, 253, 250, 0.90) !important;
}
.dataset-card-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.dataset-card-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 8px;
}
.dataset-card-desc {
  font-size: 0.82rem;
  color: #64748b;
  line-height: 1.5;
  margin-bottom: 16px;
}
.dataset-card-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.scope-panel {
  background: rgba(255,255,255,0.80);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.55);
  border-radius: 18px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  padding: 20px 28px;
  display: flex;
  align-items: flex-start;
  gap: 32px;
  flex-wrap: wrap;
  margin-bottom: 32px;
}
.scope-group { display: flex; flex-direction: column; gap: 10px; }
.scope-label {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #94a3b8;
  display: flex;
  align-items: center;
}
.scope-chips-row { display: flex; flex-wrap: wrap; gap: 8px; }
.scope-chip {
  display: inline-flex;
  align-items: center;
  padding: 7px 16px;
  border-radius: 9999px;
  font-size: 0.85rem;
  font-weight: 500;
  border: 1px solid #e2e8f0;
  background: white;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s ease;
  gap: 4px;
}
.scope-chip:hover {
  border-color: #14919B;
  color: #0D7377;
}
.scope-chip.active {
  background: linear-gradient(135deg, #0D7377, #14919B);
  border-color: #14919B;
  color: white;
  box-shadow: 0 3px 10px rgba(13,115,119,0.25);
}
.scope-chip-latin {
  font-style: italic;
  font-size: 0.75rem;
  opacity: 0.75;
  margin-left: 2px;
}
.scope-chip.active .scope-chip-latin { opacity: 0.85; }
.scope-divider {
  width: 1px;
  background: #e2e8f0;
  align-self: stretch;
  min-height: 40px;
}
@media (max-width: 600px) { .scope-divider { display: none; } }

.download-action-panel {
  background: rgba(240, 253, 250, 0.95);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 2px solid rgba(20,145,155,0.25);
  border-radius: 18px;
  padding: 28px 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 32px;
  box-shadow: 0 8px 32px rgba(13,115,119,0.10);
  flex-wrap: wrap;
}
.download-action-eyebrow {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #14919B;
  margin-bottom: 6px;
}
.download-action-title {
  font-size: 1.4rem;
  font-weight: 800;
  color: #1e293b;
  margin-bottom: 10px;
}
.download-action-species {
  color: #14919B;
}
.download-btn {
  background: linear-gradient(135deg, #0D7377, #14919B) !important;
  color: white !important;
  font-weight: 700 !important;
  letter-spacing: 0.05em !important;
  border-radius: 14px !important;
  padding: 0 32px !important;
  box-shadow: 0 6px 20px rgba(13,115,119,0.30) !important;
  transition: transform 0.2s ease, box-shadow 0.2s ease !important;
  flex-shrink: 0;
}
.download-btn:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 10px 28px rgba(13,115,119,0.40) !important;
}

.api-card {
  background: rgba(255,255,255,0.80);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.55);
  border-radius: 20px;
  padding: 32px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  margin-bottom: 32px;
}
.api-card-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 4px;
}
.api-card-subtitle {
  font-size: 0.85rem;
  color: #64748b;
  margin-bottom: 0;
}
.api-card-header {
  margin-bottom: 24px;
}
.lang-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 0;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 0;
}
.lang-tab {
  padding: 10px 20px;
  font-size: 0.88rem;
  font-weight: 600;
  color: #94a3b8;
  background: none;
  border: none;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 0.2s, border-color 0.2s;
}
.lang-tab:hover { color: #0D7377; }
.lang-tab.active {
  color: #0D7377;
  border-bottom-color: #14919B;
}
.code-block {
  position: relative;
  background: #0f172a;
  border-radius: 0 0 12px 12px;
  padding: 24px;
  border: 1px solid #1e293b;
  border-top: none;
}
.code-text {
  color: #e2e8f0;
  font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
  font-size: 0.85rem;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}
.copy-btn {
  position: absolute;
  top: 14px;
  right: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 8px;
  color: #94a3b8;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.copy-btn:hover {
  background: rgba(20,145,155,0.25);
  color: #14919B;
  border-color: #14919B;
}

.schema-section {
  background: rgba(255,255,255,0.80);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.55);
  border-radius: 20px;
  padding: 24px 32px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}
.schema-toggle-btn {
  display: flex;
  align-items: center;
  background: none;
  border: none;
  font-size: 0.95rem;
  font-weight: 600;
  color: #0D7377;
  cursor: pointer;
  padding: 0;
}
.schema-toggle-btn:hover { text-decoration: underline; }
.schema-table-wrapper {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  margin-top: 0;
}
.field-badge {
  background: #f0fdfa;
  color: #0D7377;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.82rem;
  border: 1px solid rgba(13,115,119,0.2);
  font-family: var(--aa-font-mono);
}
.type-badge {
  font-size: 0.78rem;
  font-weight: 600;
  color: #355C7D;
  background: #eef2ff;
  padding: 2px 8px;
  border-radius: 4px;
}
.elegant-table { background: transparent !important; }
.elegant-table :deep(th) {
  background: #f8fafc !important;
  font-size: 0.8rem !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.06em !important;
  color: #64748b !important;
}
.elegant-table :deep(td) { border-bottom: 1px solid #f1f5f9 !important; }
.elegant-table :deep(tr:hover td) { background: #f0fdfa !important; }
</style>
