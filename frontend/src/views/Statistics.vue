<template>
  <div class="statistics-page">
    <v-container class="py-12">
      <!-- Loading / Error States -->
      <div v-if="loading" class="d-flex justify-center align-center" style="min-height: 400px;">
        <v-progress-circular indeterminate color="#14919B" size="64"></v-progress-circular>
      </div>

      <div v-else-if="error">
        <v-alert type="error" variant="tonal" class="mb-8">
          {{ error }}
        </v-alert>
      </div>

      <div v-else>
        <!-- SECTION 1: Minimal Header + 3 Derived Insight Callouts -->
        <div class="mb-10">
          <div class="section-eyebrow mb-2">Database Overview</div>
          <h1 class="text-h3 font-weight-bold mb-8 text-primary">Isoform Regulatory Landscape</h1>
          
          <div class="insight-banners-row">
            <div class="insight-banner">
              <span class="insight-number">{{ isoformCount }}</span>
              <span class="insight-text">isoforms profiled across <strong>{{ speciesCount }} species</strong></span>
            </div>
            <div class="insight-banner highlight">
              <span class="insight-number">{{ avgPAPerIsoform }}×</span>
              <span class="insight-text">avg PA sites per isoform — a metric impossible at gene-level resolution</span>
            </div>
            <div class="insight-banner">
              <span class="insight-number">{{ pctWithMultiPA }}%</span>
              <span class="insight-text">of isoforms carry 2 or more distinct PA sites</span>
            </div>
          </div>
        </div>

        <!-- SECTION 2: Data Hierarchy Flow -->
        <div class="mb-12">
          <div class="section-eyebrow">Database Depth</div>
          <h2 class="section-title">Resolution from Gene to Cleavage Site</h2>
          <div class="flow-container mt-6">
            <div class="flow-node">
              <div class="flow-node-number">{{ detailedStats.total_genes?.toLocaleString() || '—' }}</div>
              <div class="flow-node-label">Genes</div>
              <div class="flow-node-icon mt-2"><v-icon icon="mdi-dna" color="#14919B"></v-icon></div>
            </div>

            <div class="flow-arrow">
              <div class="flow-arrow-label">avg {{ avgIsoformsPerGene }}×</div>
              <div class="flow-arrow-line">──────────▶</div>
              <div class="flow-arrow-sublabel">isoforms per gene</div>
            </div>

            <div class="flow-node">
              <div class="flow-node-number">{{ detailedStats.total_transcripts?.toLocaleString() || '—' }}</div>
              <div class="flow-node-label">Isoforms</div>
              <div class="flow-node-icon mt-2"><v-icon icon="mdi-file-tree" color="#14919B"></v-icon></div>
            </div>

            <div class="flow-arrow">
              <div class="flow-arrow-label">avg {{ avgSitesPerIsoform }}×</div>
              <div class="flow-arrow-line">──────────▶</div>
              <div class="flow-arrow-sublabel">sites per isoform</div>
            </div>

            <div class="flow-node">
              <div class="flow-node-number">{{ detailedStats.total_apa_sites?.toLocaleString() || '—' }}</div>
              <div class="flow-node-label">PA Sites</div>
              <div class="flow-node-icon mt-2"><v-icon icon="mdi-map-marker" color="#14919B"></v-icon></div>
            </div>
          </div>
        </div>

        <!-- SECTION 3: Isoform PA Site Multiplicity Distribution -->
        <v-card variant="outlined" class="data-section">
          <div class="section-header">
            <div class="section-eyebrow">Regulatory Complexity</div>
            <h2 class="section-title">PA Site Multiplicity per Isoform</h2>
            <p class="section-subtitle">How many PA sites does each transcript isoform carry? This distribution reveals the regulatory diversity hidden within the transcriptome.</p>
          </div>
          
          <div class="chart-shell chart-shell--large">
            <Bar v-if="multiplicityChartData" :data="multiplicityChartData" :options="multiplicityChartOptions" />
          </div>

          <div class="d-flex flex-wrap gap-4 mt-6">
            <div class="multiplicity-annotation">
              <div class="d-flex align-center mb-1">
                <v-icon icon="mdi-numeric-1-box" color="#94a3b8" class="mr-2"></v-icon>
                <span class="text-grey-darken-1 font-weight-medium">Isoforms with 1 site</span>
              </div>
              <div class="multiplicity-annotation-number">{{ pctSingleSite }}%</div>
              <div class="text-caption text-grey mt-1">Single-site isoforms have fixed 3' end regulation</div>
            </div>
            
            <div class="multiplicity-annotation" style="border-color: #14919B; background: #f0fdfa;">
              <div class="d-flex align-center mb-1">
                <v-icon icon="mdi-numeric-2-box-multiple" color="#14919B" class="mr-2"></v-icon>
                <span class="text-teal-darken-3 font-weight-medium">Isoforms with 2+ sites</span>
              </div>
              <div class="multiplicity-annotation-number" style="color: #0D7377;">{{ pctWithMultiPA }}%</div>
              <div class="text-caption text-teal-darken-2 mt-1">These isoforms can produce short OR long 3' UTR forms</div>
            </div>

            <div class="multiplicity-annotation">
              <div class="d-flex align-center mb-1">
                <v-icon icon="mdi-sigma" color="#0a5c5f" class="mr-2"></v-icon>
                <span class="text-grey-darken-1 font-weight-medium">Most complex (5+ sites)</span>
              </div>
              <div class="multiplicity-annotation-number" style="color: #0a5c5f;">{{ multiplicityBuckets?.buckets['5+']?.toLocaleString() || 0 }}</div>
              <div class="text-caption text-grey mt-1">Maximum regulatory flexibility</div>
            </div>
          </div>
        </v-card>

        <!-- SECTION 4: Species Data Richness Panel -->
        <v-card variant="outlined" class="data-section">
          <div class="section-header">
            <div class="section-eyebrow">Taxonomic Scope</div>
            <h2 class="section-title">Species Richness</h2>
            <p class="section-subtitle">Relative abundance of profiled cleavage events across mapped species.</p>
          </div>
          
          <div class="species-richness-container mt-4">
            <div v-for="sp in speciesRichnessData" :key="sp.name" class="species-richness-row">
              <div class="species-name-col">
                <div class="species-common">{{ sp.name }}</div>
                <div class="species-latin">{{ sp.latin_name }}</div>
              </div>
              <div class="species-bar-col">
                <div class="species-bar-track">
                  <div class="species-bar-fill" :style="{ width: sp.pct + '%', background: sp.color }"></div>
                </div>
                <div class="species-bar-count">{{ sp.apaCount?.toLocaleString() || '—' }}</div>
              </div>
              <div class="species-assembly-col">
                <v-chip size="x-small" variant="outlined">{{ sp.assembly }}</v-chip>
              </div>
            </div>
            <div v-if="!speciesRichnessData?.length" class="text-center text-grey py-4">No species data available</div>
          </div>
        </v-card>

        <!-- SECTION 5: Two-Column Chart Row -->
        <v-row class="mb-8">
          <v-col cols="12" md="6">
            <v-card variant="outlined" class="data-section h-100 mb-0">
              <div class="section-eyebrow">Genomic Bias</div>
              <h2 class="text-h6 font-weight-bold mb-6 text-primary">Strand Distribution</h2>
              <div class="chart-shell">
                <Doughnut v-if="strandChartData" :data="strandChartData" :options="doughnutOptions" />
                <div v-else class="d-flex h-100 justify-center align-center text-grey">No strand data</div>
              </div>
            </v-card>
          </v-col>
          <v-col cols="12" md="6">
            <v-card variant="outlined" class="data-section h-100 mb-0">
              <div class="section-eyebrow">Genomic Topology</div>
              <h2 class="text-h6 font-weight-bold mb-6 text-primary">Chromosome Distribution</h2>
              <div class="chart-shell">
                <Bar v-if="chromosomeChartData" :data="chromosomeChartData" :options="chromosomeBarOptions" />
                <div v-else class="d-flex h-100 justify-center align-center text-grey">No chromosome data</div>
              </div>
            </v-card>
          </v-col>
        </v-row>

        <!-- SECTION 6: Top Genes Leaderboard -->
        <v-card variant="outlined" class="data-section">
          <div class="section-header">
            <div class="section-eyebrow">Database Highlights</div>
            <h2 class="section-title">Most Highly Regulated Genes</h2>
            <p class="section-subtitle">Genes producing transcripts with the highest number of distinct polyadenylation events.</p>
          </div>
          
          <div class="leaderboard-container mt-6">
            <div v-for="(gene, i) in detailedStats.top_genes_by_apa" :key="gene.gene_id" class="leaderboard-row">
              <div class="rank-badge" :class="rankClass(i)">{{ i + 1 }}</div>
              <router-link :to="{ name: 'GeneDetail', params: { geneId: gene.gene_db_id } }" class="gene-name-link">
                {{ gene.gene_name }}
              </router-link>
              <code class="gene-id-badge">{{ gene.gene_id }}</code>
              <div class="leaderboard-bar-track">
                <div class="leaderboard-bar-fill" :style="{ width: ((gene.apa_count / maxGeneApaCount) * 100) + '%' }"></div>
              </div>
              <v-chip size="small" color="#14919B" variant="tonal" class="font-weight-bold">{{ gene.apa_count.toLocaleString() }}</v-chip>
            </div>
            <div v-if="!detailedStats.top_genes_by_apa?.length" class="text-center text-grey py-4">No top genes available</div>
          </div>
        </v-card>
      </div>
    </v-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Bar, Doughnut } from 'vue-chartjs'
import { 
  Chart as ChartJS, 
  BarElement, 
  CategoryScale, 
  LinearScale, 
  Tooltip, 
  Legend,
  Title,
  ArcElement
} from 'chart.js'
import { apiService } from '@/services/api'

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend, Title, ArcElement)

const loading = ref(true)
const error = ref(null)

const detailedStats = ref({})
const basicStats = ref({})
const speciesList = ref([])

onMounted(async () => {
  try {
    loading.value = true
    const [detailed, basic, species] = await Promise.all([
      apiService.getDetailedStats(),
      apiService.getStats(),
      apiService.getSpecies()
    ])
    detailedStats.value = detailed || {}
    basicStats.value = basic || {}
    speciesList.value = species || []
  } catch (err) {
    console.error('Failed to load stats:', err)
    error.value = 'Failed to load statistics. Please try again.'
  } finally {
    loading.value = false
  }
})

// SECTION 1 COMPUTED
const isoformCount = computed(() => detailedStats.value.total_transcripts?.toLocaleString() || '—')
const speciesCount = computed(() => detailedStats.value.total_species || '—')
const avgPAPerIsoform = computed(() => detailedStats.value.avg_apa_per_transcript || '—')

const pctWithMultiPA = computed(() => {
  const items = basicStats.value.apa_sites_per_transcript || []
  if (!items.length) return null
  const multi = items.filter(x => x.count >= 2).length
  return ((multi / items.length) * 100).toFixed(0)
})

const pctSingleSite = computed(() => {
  const items = basicStats.value.apa_sites_per_transcript || []
  if (!items.length) return null
  const single = items.filter(x => x.count === 1).length
  return ((single / items.length) * 100).toFixed(0)
})

// SECTION 2 COMPUTED
const avgIsoformsPerGene = computed(() => {
  if (!detailedStats.value.total_genes || !detailedStats.value.total_transcripts) return '—'
  return (detailedStats.value.total_transcripts / detailedStats.value.total_genes).toFixed(2)
})
const avgSitesPerIsoform = computed(() => detailedStats.value.avg_apa_per_transcript || '—')

// SECTION 3 COMPUTED
const multiplicityBuckets = computed(() => {
  const items = basicStats.value.apa_sites_per_transcript || []
  const buckets = { '1': 0, '2': 0, '3': 0, '4': 0, '5+': 0 }
  let total = 0
  items.forEach(({ count }) => {
    total++
    if (count <= 0) return
    if (count >= 5) buckets['5+']++
    else buckets[String(count)]++
  })
  return { buckets, total }
})

const multiplicityChartData = computed(() => {
  if (!multiplicityBuckets.value.total) return null
  const { buckets } = multiplicityBuckets.value
  return {
    labels: ['1 PA site', '2 PA sites', '3 PA sites', '4 PA sites', '5+ PA sites'],
    datasets: [{
      label: 'Number of Isoforms',
      data: [buckets['1'], buckets['2'], buckets['3'], buckets['4'], buckets['5+']],
      backgroundColor: ['#94a3b8', '#14919B', '#0D7377', '#0A5C5F', '#064346'],
      hoverBackgroundColor: ['#64748b', '#0D7377', '#0A5C5F', '#064346', '#042f31'],
      borderRadius: 8,
      borderSkipped: false
    }]
  }
})

const multiplicityChartOptions = {
  responsive: true, 
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: 'rgba(248, 252, 252, 0.96)',
      titleColor: '#0f172a',
      bodyColor: '#334155',
      borderColor: 'rgba(13, 115, 119, 0.18)',
      borderWidth: 1,
      padding: 12,
      titleFont: { family: 'IBM Plex Sans', size: 13, weight: '700' },
      bodyFont: { family: 'IBM Plex Sans', size: 13, weight: '500' },
      callbacks: {
        afterLabel: (ctx) => {
          const total = multiplicityBuckets.value.total
          const pct = total ? ((ctx.raw / total) * 100).toFixed(1) : 0
          return `${pct}% of all isoforms`
        }
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      title: { display: true, text: 'Number of Isoforms', color: '#475569', font: { family: 'IBM Plex Sans', weight: '700' } },
      grid: { color: 'rgba(148, 163, 184, 0.22)' },
      ticks: { color: '#64748b', font: { family: 'IBM Plex Sans', size: 12 } }
    },
    x: {
      grid: { display: false },
      ticks: { color: '#475569', font: { family: 'IBM Plex Sans', size: 12, weight: '700' } }
    }
  }
}

// SECTION 4 COMPUTED
const speciesRichnessData = computed(() => {
  const apaMap = {}
  detailedStats.value.apa_sites_by_species?.forEach(s => { apaMap[s.name] = s.count })
  const speciesWithCounts = speciesList.value.map(sp => ({
    ...sp,
    apaCount: apaMap[sp.name] ?? 0
  }))
  const maxCount = Math.max(...speciesWithCounts.map(s => s.apaCount), 1)
  const colors = ['#0D7377', '#14919B', '#2F855A', '#355C7D', '#B63F5A', '#B7791F']
  return speciesWithCounts
    .sort((a, b) => b.apaCount - a.apaCount)
    .map((sp, i) => ({ ...sp, pct: (sp.apaCount / maxCount) * 100, color: colors[i % colors.length] }))
})

// SECTION 5 COMPUTED
const strandChartData = computed(() => {
  if (!detailedStats.value.apa_sites_by_strand?.length) return null
  return {
    labels: detailedStats.value.apa_sites_by_strand.map(s => s.strand || 'Unknown'),
    datasets: [{
      data: detailedStats.value.apa_sites_by_strand.map(s => s.count),
      backgroundColor: ['#0D7377', '#B63F5A', '#94A3B8'],
      borderColor: 'rgba(255, 255, 255, 0.92)',
      borderWidth: 3,
      borderWidth: 0,
      hoverOffset: 4
    }]
  }
})

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        padding: 20,
        font: { family: 'IBM Plex Sans', size: 12, weight: '700' },
        color: '#475569',
        usePointStyle: true,
        pointStyle: 'circle'
      }
    },
    tooltip: {
      backgroundColor: 'rgba(248, 252, 252, 0.96)',
      titleColor: '#0f172a',
      bodyColor: '#334155',
      borderColor: 'rgba(13, 115, 119, 0.18)',
      borderWidth: 1,
      padding: 12,
      titleFont: { family: 'IBM Plex Sans', size: 13, weight: '700' },
      bodyFont: { family: 'IBM Plex Sans', size: 13, weight: '500' }
    }
  },
  cutout: '65%'
}

const chromosomeChartData = computed(() => {
  if (!detailedStats.value.apa_sites_by_chromosome?.length) return null
  const sorted = [...detailedStats.value.apa_sites_by_chromosome].sort((a, b) => b.count - a.count).slice(0, 20)
  return {
    labels: sorted.map(c => c.chromosome || 'Unknown'),
    datasets: [{
      label: 'APA Sites',
      data: sorted.map(c => c.count),
      backgroundColor: '#14919B',
      hoverBackgroundColor: '#0D7377',
      borderRadius: 7,
      borderSkipped: false
    }]
  }
})

const chromosomeBarOptions = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y',
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: 'rgba(248, 252, 252, 0.96)',
      titleColor: '#0f172a',
      bodyColor: '#334155',
      borderColor: 'rgba(13, 115, 119, 0.18)',
      borderWidth: 1,
      padding: 12,
      titleFont: { family: 'IBM Plex Sans', size: 13, weight: '700' },
      bodyFont: { family: 'IBM Plex Sans', size: 13, weight: '500' }
    }
  },
  scales: {
    x: {
      beginAtZero: true,
      grid: { color: 'rgba(148, 163, 184, 0.22)' },
      ticks: { color: '#64748b', font: { family: 'IBM Plex Sans', size: 12 } }
    },
    y: {
      grid: { display: false },
      ticks: { color: '#475569', font: { family: 'IBM Plex Sans', size: 12, weight: '700' } }
    }
  }
}

// SECTION 6 COMPUTED
const maxGeneApaCount = computed(() => 
  Math.max(...(detailedStats.value.top_genes_by_apa?.map(g => g.apa_count) ?? [1]), 1)
)

const rankClass = (i) => {
  if (i === 0) return 'rank-gold'
  if (i === 1) return 'rank-silver'
  if (i === 2) return 'rank-bronze'
  return 'rank-default'
}

</script>

<style scoped>
.statistics-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at 10% 4%, rgba(20, 145, 155, 0.10), transparent 30%),
    linear-gradient(180deg, #f8fbfc 0%, #f5f8fa 100%);
}

.text-primary {
  color: #0D7377 !important;
}

.gap-4 {
  gap: 16px;
}

/* Data Section Base */
.data-section {
  border-radius: 20px;
  padding: 32px;
  margin-bottom: 32px;
}

.chart-shell {
  height: 320px;
  padding: 20px;
  margin-bottom: 8px;
}

.chart-shell--large {
  height: 360px;
  margin-bottom: 24px;
}

.section-header {
  margin-bottom: 32px;
}

.section-eyebrow {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #14919B;
  margin-bottom: 4px;
}

.section-title {
  font-size: 1.45rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 6px;
}

.section-subtitle {
  font-size: 0.9rem;
  color: #64748b;
  max-width: 680px;
}

/* Insight Banners */
.insight-banners-row {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 48px;
}

.insight-banner {
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(203, 213, 225, 0.72);
  border-left: 4px solid #cbd5e1;
  border-radius: 0 12px 12px 0;
  padding: 16px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  min-width: 280px;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.06);
}

.insight-banner.highlight {
  border-left-color: #14919B;
  background: #f0fdfa;
}

.insight-number {
  font-size: 2rem;
  font-weight: 800;
  color: #0D7377;
  white-space: nowrap;
  line-height: 1;
}

.insight-text {
  font-size: 0.95rem;
  color: #475569;
  line-height: 1.3;
}

/* Flow Nodes */
.flow-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  flex-wrap: wrap;
  padding: 32px;
  background: rgba(255, 255, 255, 0.78);
  border-radius: 20px;
  border: 1px solid #e2e8f0;
  margin-bottom: 48px;
}

.flow-node {
  background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(248,250,252,0.88));
  border: 1px solid #e2e8f0;
  border-top: 3px solid #14919B;
  border-radius: 12px;
  padding: 24px 32px;
  text-align: center;
  min-width: 160px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
}

.flow-node-number {
  font-size: 1.8rem;
  font-weight: 800;
  color: #0D7377;
  line-height: 1.1;
}

.flow-node-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-top: 4px;
}

.flow-node-icon {
  margin-top: 8px;
}

.flow-arrow {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 24px;
  color: #94a3b8;
}

.flow-arrow-label {
  font-size: 0.85rem;
  font-weight: 700;
  color: #14919B;
  white-space: nowrap;
}

.flow-arrow-line {
  font-size: 1.5rem;
  color: #cbd5e1;
  margin: 4px 0;
  letter-spacing: -2px;
}

.flow-arrow-sublabel {
  font-size: 0.72rem;
  color: #94a3b8;
  white-space: nowrap;
}

@media (max-width: 768px) {
  .flow-container {
    flex-direction: column;
    gap: 16px;
  }
  .flow-arrow {
    padding: 16px 0;
  }
  .flow-arrow-line {
    transform: rotate(90deg);
    margin: 16px 0;
  }
}

/* Multiplicity Annotations */
.multiplicity-annotation {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px 20px;
  flex: 1;
  min-width: 200px;
}

.multiplicity-annotation-number {
  font-size: 1.6rem;
  font-weight: 800;
  color: #0D7377;
}

/* Species Richness */
.species-richness-container {
  display: flex;
  flex-direction: column;
}

.species-richness-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px solid #f1f5f9;
}

.species-richness-row:last-child { 
  border-bottom: none; 
}

.species-name-col { 
  min-width: 160px; 
}

.species-common { 
  font-weight: 600; 
  font-size: 0.9rem; 
  color: #1e293b; 
}

.species-latin { 
  font-style: italic; 
  font-size: 0.78rem; 
  color: #94a3b8; 
}

.species-bar-col { 
  flex: 1; 
  display: flex; 
  align-items: center; 
  gap: 12px; 
}

.species-bar-track { 
  flex: 1; 
  height: 10px; 
  background: #f1f5f9; 
  border-radius: 9999px; 
  overflow: hidden; 
}

.species-bar-fill { 
  height: 100%; 
  border-radius: 9999px; 
  transition: width 0.8s ease; 
}

.species-bar-count { 
  font-size: 0.85rem; 
  font-weight: 700; 
  color: #0D7377; 
  min-width: 80px; 
  text-align: right; 
}

.species-assembly-col { 
  min-width: 80px; 
  text-align: right; 
}

@media (max-width: 600px) {
  .species-richness-row {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  .species-bar-count, .species-assembly-col {
    text-align: left;
  }
}

/* Leaderboard */
.leaderboard-container {
  display: flex;
  flex-direction: column;
}

.leaderboard-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid #f1f5f9;
}

.leaderboard-row:last-child { 
  border-bottom: none; 
}

.gene-name-link {
  font-weight: 600;
  color: #0D7377;
  text-decoration: none;
  min-width: 80px;
}

.gene-name-link:hover { 
  text-decoration: underline; 
}

.gene-id-badge {
  font-size: 0.78rem;
  background: #f1f5f9;
  color: #475569;
  padding: 3px 8px;
  border-radius: 6px;
  font-family: var(--aa-font-mono);
  border: 1px solid #e2e8f0;
  min-width: 160px;
}

.leaderboard-bar-track {
  flex: 1;
  height: 8px;
  background: #f1f5f9;
  border-radius: 9999px;
  overflow: hidden;
}

.leaderboard-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #0D7377, #14919B);
  border-radius: 9999px;
  transition: width 0.6s ease;
}

.rank-badge { 
  width: 32px; 
  height: 32px; 
  border-radius: 50%; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  font-weight: 700; 
  font-size: 0.8rem; 
  flex-shrink: 0; 
}

.rank-gold { background: linear-gradient(135deg, #F59E0B, #D97706); color: white; }
.rank-silver { background: linear-gradient(135deg, #94a3b8, #64748b); color: white; }
.rank-bronze { background: linear-gradient(135deg, #CD7F32, #A0522D); color: white; }
.rank-default { background: #f1f5f9; color: #64748b; }

@media (max-width: 600px) {
  .leaderboard-row {
    flex-wrap: wrap;
  }
  .leaderboard-bar-track {
    display: none;
  }
}
</style>
