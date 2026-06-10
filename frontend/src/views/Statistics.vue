<template>
  <div class="statistics-page">
    <section class="hero-section">
      <div class="hero-bg"></div>
      <v-container class="hero-content">
        <h1 class="text-h3 font-weight-bold text-white mb-2">IsoAPA Statistics</h1>
        <p class="text-h6 text-white opacity-90">Database-scale view of isoform-level polyadenylation complexity</p>
      </v-container>
    </section>

    <div v-if="loading" class="stats-loading-shell">
      <v-progress-circular indeterminate color="#14919B" size="58"></v-progress-circular>
      <div class="stats-loading-text">Loading database metrics</div>
    </div>

    <v-container v-else-if="error" class="py-10 py-md-12">
      <v-alert type="error" variant="tonal" class="mb-8">
        {{ error }}
      </v-alert>
    </v-container>

    <template v-else>
      <v-container class="stats-content reveal-root">
        <section class="metric-grid reveal-item" style="--delay: 80ms">
          <component
            :is="metric.to ? 'router-link' : 'div'"
            v-for="metric in heroMetrics"
            :key="metric.label"
            class="metric-card"
            :class="{ 'metric-card--link': metric.to }"
            v-bind="metric.to ? { to: metric.to } : {}"
          >
            <div class="metric-icon" :style="{ background: metric.gradient }">
              <v-icon :icon="metric.icon" size="20" color="white"></v-icon>
            </div>
            <div class="metric-value">{{ metric.value }}</div>
            <div class="metric-label">{{ metric.label }}</div>
            <div class="metric-note">{{ metric.note }}</div>
          </component>
        </section>

        <section class="section-card stats-flow-card reveal-item" style="--delay: 160ms">
          <div class="section-header compact">
            <div>
              <div class="section-eyebrow">Database Depth</div>
              <div class="stats-card-title" role="heading" aria-level="2">Resolution From Gene To Cleavage Site</div>
            </div>
          </div>
          <div class="flow-grid">
            <div class="flow-node">
              <span class="flow-node-value">{{ fmt(detailedStats.total_genes) }}</span>
              <span class="flow-node-label">Genes</span>
            </div>
            <div class="flow-connector">
              <span>avg {{ avgIsoformsPerGene }}x</span>
            </div>
            <div class="flow-node flow-node--strong">
              <span class="flow-node-value">{{ fmt(detailedStats.total_transcripts) }}</span>
              <span class="flow-node-label">Isoforms</span>
            </div>
            <div class="flow-connector">
              <span>avg {{ avgSitesPerIsoform }}x</span>
            </div>
            <div class="flow-node">
              <span class="flow-node-value">{{ fmt(detailedStats.total_apa_sites) }}</span>
              <span class="flow-node-label">PA Sites</span>
            </div>
          </div>
        </section>

        <div class="stats-card-row reveal-item" style="--delay: 240ms">
          <div class="stats-card-cell">
            <section class="section-card">
              <div class="section-header stats-filter-header">
                <div class="stats-filter-topline">
                  <div class="section-eyebrow">Regulatory Complexity</div>
                  <v-menu
                    location="bottom end"
                    :close-on-content-click="true"
                    :min-width="260"
                    content-class="stats-species-menu"
                  >
                    <template #activator="{ props }">
                      <button class="species-filter-trigger" type="button" v-bind="props">
                        <span
                          class="species-filter-value"
                          :class="{ 'is-placeholder': !selectedMultiplicitySpecies }"
                        >
                          {{ selectedMultiplicitySpeciesLabel }}
                        </span>
                        <span class="species-filter-icon">
                          <v-progress-circular
                            v-if="multiplicityLoading"
                            indeterminate
                            size="12"
                            width="2"
                            color="#0D7377"
                          />
                          <v-icon v-else icon="mdi-chevron-down" size="14" />
                        </span>
                      </button>
                    </template>

                    <div class="species-menu-card">
                      <div class="species-menu-header">
                        <span>Filter multiplicity</span>
                        <small>{{ multiplicitySpeciesOptions.length }} choices</small>
                      </div>
                      <button
                        v-for="option in multiplicitySpeciesOptions"
                        :key="option.value || 'all'"
                        class="species-menu-option"
                        :class="{ 'is-active': selectedMultiplicitySpecies === option.value }"
                        type="button"
                        @click="selectMultiplicitySpecies(option.value)"
                      >
                        <span class="species-menu-option-main">{{ option.title }}</span>
                        <v-icon
                          v-if="selectedMultiplicitySpecies === option.value"
                          icon="mdi-check"
                          size="17"
                        />
                      </button>
                    </div>
                  </v-menu>
                </div>
                <div>
                  <div class="stats-card-title" role="heading" aria-level="2">PA Site Multiplicity Per Isoform</div>
                  <p class="section-subtitle">{{ multiplicitySubtitle }}</p>
                </div>
              </div>
              <div class="chart-shell chart-shell--large">
                <Bar v-if="multiplicityChartData" :data="multiplicityChartData" :options="multiplicityChartOptions" />
                <div v-else class="empty-chart">No multiplicity data available</div>
              </div>
              <div class="complexity-cards">
                <div class="complexity-card">
                  <span class="complexity-value">{{ pctSingleSite }}%</span>
                  <span class="complexity-label">Single-site isoforms</span>
                </div>
                <div class="complexity-card complexity-card--accent">
                  <span class="complexity-value">{{ pctWithMultiPA }}%</span>
                  <span class="complexity-label">Isoforms with 2+ PA sites</span>
                </div>
                <div class="complexity-card">
                  <span class="complexity-value">{{ fmt(multiplicityBuckets.buckets?.['5+']) }}</span>
                  <span class="complexity-label">Isoforms with 5+ sites</span>
                </div>
              </div>
            </section>
          </div>

          <div class="stats-card-cell">
            <section class="section-card">
              <div class="section-header stats-filter-header">
                <div class="stats-filter-topline">
                  <div class="section-eyebrow">Motif Composition</div>
                  <v-menu
                    location="bottom end"
                    :close-on-content-click="true"
                    :min-width="260"
                    content-class="stats-species-menu"
                  >
                    <template #activator="{ props }">
                      <button class="species-filter-trigger" type="button" v-bind="props">
                        <span
                          class="species-filter-value"
                          :class="{ 'is-placeholder': !selectedMotifSpecies }"
                        >
                          {{ selectedMotifSpeciesLabel }}
                        </span>
                        <span class="species-filter-icon">
                          <v-progress-circular
                            v-if="motifLoading"
                            indeterminate
                            size="12"
                            width="2"
                            color="#0D7377"
                          />
                          <v-icon v-else icon="mdi-chevron-down" size="14" />
                        </span>
                      </button>
                    </template>

                    <div class="species-menu-card">
                      <div class="species-menu-header">
                        <span>Filter motifs</span>
                        <small>{{ motifSpeciesOptions.length }} choices</small>
                      </div>
                      <button
                        v-for="option in motifSpeciesOptions"
                        :key="option.value || 'all'"
                        class="species-menu-option"
                        :class="{ 'is-active': selectedMotifSpecies === option.value }"
                        type="button"
                        @click="selectMotifSpecies(option.value)"
                      >
                        <span class="species-menu-option-main">{{ option.title }}</span>
                        <v-icon
                          v-if="selectedMotifSpecies === option.value"
                          icon="mdi-check"
                          size="17"
                        />
                      </button>
                    </div>
                  </v-menu>
                </div>
                <div>
                  <div class="stats-card-title" role="heading" aria-level="2">PAS Motif Distribution</div>
                  <p class="section-subtitle">{{ motifSubtitle }}</p>
                </div>
              </div>
              <div class="chart-shell chart-shell--large motif-chart-shell">
                <Pie v-if="motifChartData" :data="motifChartData" :options="motifChartOptions" />
                <div v-else class="empty-chart">No PAS motif data available</div>
              </div>
              <div class="complexity-cards">
                <div class="complexity-card">
                  <span class="complexity-value">{{ fmt(motifStats?.total) }}</span>
                  <span class="complexity-label">Annotated PA sites</span>
                </div>
                <div class="complexity-card complexity-card--accent">
                  <span class="complexity-value">{{ noMotifPct }}%</span>
                  <span class="complexity-label">Sites with no motif</span>
                </div>
                <div class="complexity-card">
                  <span class="complexity-value">{{ topMotifPct }}%</span>
                  <span class="complexity-label">{{ topMotifLabel }} share</span>
                </div>
              </div>
            </section>
          </div>
        </div>

        <div class="stats-card-row reveal-item" style="--delay: 400ms">
          <div class="stats-card-cell">
            <section class="section-card">
              <div class="section-header stats-filter-header">
                <div>
                  <div class="section-eyebrow">Taxonomic Scope</div>
                  <div class="stats-card-title" role="heading" aria-level="2">Top 10 Species Richness</div>
                  <p class="section-subtitle">The ten species with the most profiled cleavage events.</p>
                </div>
              </div>
              <div class="leaderboard-container">
                <div v-for="(sp, i) in speciesRichnessData" :key="sp.name" class="leaderboard-row">
                  <div class="rank-badge" :class="rankClass(i)">{{ i + 1 }}</div>
                  <div class="species-leader-name">
                    <div class="species-common">{{ sp.displayName }}</div>
                    <div v-if="sp.subtitle" class="species-latin">{{ sp.subtitle }}</div>
                  </div>
                  <div class="leaderboard-bar-track">
                    <div class="leaderboard-bar-fill species-leader-bar-fill" :style="{ width: sp.pct + '%' }"></div>
                  </div>
                  <v-chip size="small" color="#14919B" variant="tonal" class="font-weight-bold">{{ fmt(sp.apaCount) }}</v-chip>
                </div>
                <div v-if="!speciesRichnessData.length" class="empty-chart py-8">No species data available</div>
              </div>
            </section>
          </div>

          <div class="stats-card-cell">
            <section class="section-card">
              <div class="section-header stats-filter-header">
                <div class="stats-filter-topline">
                  <div class="section-eyebrow">Database Highlights</div>
                  <v-menu
                    location="bottom end"
                    :close-on-content-click="true"
                    :min-width="260"
                    content-class="stats-species-menu"
                  >
                    <template #activator="{ props }">
                      <button class="species-filter-trigger" type="button" v-bind="props">
                        <span
                          class="species-filter-value"
                          :class="{ 'is-placeholder': !selectedGeneSpecies }"
                        >
                          {{ selectedGeneSpeciesLabel }}
                        </span>
                        <span class="species-filter-icon">
                          <v-progress-circular
                            v-if="topGeneLoading"
                            indeterminate
                            size="12"
                            width="2"
                            color="#0D7377"
                          />
                          <v-icon v-else icon="mdi-chevron-down" size="14" />
                        </span>
                      </button>
                    </template>

                    <div class="species-menu-card">
                      <div class="species-menu-header">
                        <span>Filter genes</span>
                        <small>{{ geneSpeciesOptions.length }} choices</small>
                      </div>
                      <button
                        v-for="option in geneSpeciesOptions"
                        :key="option.value || 'all'"
                        class="species-menu-option"
                        :class="{ 'is-active': selectedGeneSpecies === option.value }"
                        type="button"
                        @click="selectGeneSpecies(option.value)"
                      >
                        <span class="species-menu-option-main">{{ option.title }}</span>
                        <v-icon
                          v-if="selectedGeneSpecies === option.value"
                          icon="mdi-check"
                          size="17"
                        />
                      </button>
                    </div>
                  </v-menu>
                </div>
                <div>
                  <div class="stats-card-title" role="heading" aria-level="2">Top 10 Gene Richness</div>
                  <p class="section-subtitle">Genes with the highest number of distinct PA sites across their transcripts.</p>
                </div>
              </div>
              <div class="leaderboard-container">
                <div v-for="(gene, i) in topGenesByApa" :key="`${gene.gene_db_id}-${gene.species}`" class="leaderboard-row">
                  <div class="rank-badge" :class="rankClass(i)">{{ i + 1 }}</div>
                  <router-link
                    :to="{ name: 'GeneDetail', params: { geneId: gene.gene_db_id }, query: { species: gene.species } }"
                    class="gene-name-link"
                  >
                    {{ gene.gene_name || 'Unknown' }}
                  </router-link>
                  <span class="gene-species-chip">{{ formatSpeciesName(gene.species) }}</span>
                  <div class="leaderboard-bar-track">
                    <div class="leaderboard-bar-fill" :style="{ width: ((gene.apa_count / maxGeneApaCount) * 100) + '%' }"></div>
                  </div>
                  <v-chip size="small" color="#14919B" variant="tonal" class="font-weight-bold">{{ fmt(gene.apa_count) }}</v-chip>
                </div>
                <div v-if="!topGenesByApa.length" class="empty-chart py-8">No top genes available</div>
              </div>
            </section>
          </div>
        </div>
      </v-container>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Bar, Pie } from 'vue-chartjs'
import {
  Chart as ChartJS,
  BarElement,
  ArcElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  Title
} from 'chart.js'
import { apiService } from '@/services/api'
import { formatSpeciesName, formatSpeciesSubtitle } from '@/utils/formatters'

ChartJS.register(BarElement, ArcElement, CategoryScale, LinearScale, Tooltip, Legend, Title)

const loading = ref(true)
const error = ref(null)
const detailedStats = ref({})
const speciesList = ref([])
const selectedMultiplicitySpecies = ref('')
const multiplicityStats = ref(null)
const multiplicityLoading = ref(false)
const selectedMotifSpecies = ref('')
const motifStats = ref(null)
const motifLoading = ref(false)
const selectedGeneSpecies = ref('')
const topGeneStats = ref(null)
const topGeneLoading = ref(false)

const fmt = (value) => Number(value ?? 0).toLocaleString()

onMounted(async () => {
  try {
    loading.value = true
    const [detailed, species] = await Promise.all([
      apiService.getDetailedStats(),
      apiService.getSpecies()
    ])
    detailedStats.value = detailed || {}
    speciesList.value = species || []
    multiplicityStats.value = detailed?.apa_site_multiplicity || null
    topGeneStats.value = detailed?.top_genes_by_apa?.slice(0, 10) || []
  } catch (err) {
    console.error('Failed to load stats:', err)
    error.value = 'Failed to load statistics. Please try again.'
  } finally {
    loading.value = false
  }

  await Promise.allSettled([
    loadMotifStats(),
    loadTopGeneStats()
  ])
})

const loadMultiplicityStats = async () => {
  multiplicityLoading.value = true
  try {
    multiplicityStats.value = await apiService.getMultiplicityStats(selectedMultiplicitySpecies.value || undefined)
  } catch (err) {
    console.error('Failed to load multiplicity stats:', err)
    multiplicityStats.value = detailedStats.value.apa_site_multiplicity || null
  } finally {
    multiplicityLoading.value = false
  }
}

const loadMotifStats = async () => {
  motifLoading.value = true
  try {
    motifStats.value = await apiService.getPasMotifStats(selectedMotifSpecies.value || undefined)
  } catch (err) {
    console.error('Failed to load PAS motif stats:', err)
    motifStats.value = null
  } finally {
    motifLoading.value = false
  }
}

const loadTopGeneStats = async () => {
  topGeneLoading.value = true
  try {
    topGeneStats.value = await apiService.getTopGeneStats(selectedGeneSpecies.value || undefined)
  } catch (err) {
    console.error('Failed to load top gene stats:', err)
    topGeneStats.value = detailedStats.value.top_genes_by_apa?.slice(0, 10) || []
  } finally {
    topGeneLoading.value = false
  }
}

const avgIsoformsPerGene = computed(() => detailedStats.value.avg_isoforms_per_gene ?? '—')
const avgSitesPerIsoform = computed(() => detailedStats.value.avg_apa_per_transcript ?? '—')
const multiplicityBuckets = computed(() => multiplicityStats.value || detailedStats.value.apa_site_multiplicity || { buckets: {}, total: 0 })
const pctWithMultiPA = computed(() => multiplicityBuckets.value.pct_multi_site ?? 0)
const pctSingleSite = computed(() => multiplicityBuckets.value.pct_single_site ?? 0)
const multiplicitySpeciesOptions = computed(() => [
  { title: 'All species', value: '' },
  ...speciesList.value.map(sp => ({
    title: sp.display_name || formatSpeciesName(sp),
    value: sp.name
  }))
])
const selectedMultiplicitySpeciesLabel = computed(() =>
  selectedMultiplicitySpecies.value
    ? multiplicitySpeciesOptions.value.find(option => option.value === selectedMultiplicitySpecies.value)?.title || formatSpeciesName(selectedMultiplicitySpecies.value)
    : 'Species'
)
const motifSpeciesOptions = multiplicitySpeciesOptions
const selectedMotifSpeciesLabel = computed(() =>
  selectedMotifSpecies.value
    ? motifSpeciesOptions.value.find(option => option.value === selectedMotifSpecies.value)?.title || formatSpeciesName(selectedMotifSpecies.value)
    : 'Species'
)
const geneSpeciesOptions = multiplicitySpeciesOptions
const selectedGeneSpeciesLabel = computed(() =>
  selectedGeneSpecies.value
    ? geneSpeciesOptions.value.find(option => option.value === selectedGeneSpecies.value)?.title || formatSpeciesName(selectedGeneSpecies.value)
    : 'Species'
)
const multiplicitySubtitle = computed(() => {
  if (!selectedMultiplicitySpecies.value) {
    return 'Isoforms grouped by PA site count.'
  }
  const selected = speciesList.value.find(sp => sp.name === selectedMultiplicitySpecies.value)
  return `Distribution for ${selected ? formatSpeciesName(selected) : formatSpeciesName(selectedMultiplicitySpecies.value)} transcripts.`
})
const motifSubtitle = computed(() => {
  if (!selectedMotifSpecies.value) {
    return 'Distribution of annotated PAS motifs across all PA site clusters.'
  }
  const selected = speciesList.value.find(sp => sp.name === selectedMotifSpecies.value)
  return `Distribution for ${selected ? formatSpeciesName(selected) : formatSpeciesName(selectedMotifSpecies.value)} PA sites.`
})

const selectMultiplicitySpecies = async (species) => {
  if (selectedMultiplicitySpecies.value === species) return
  selectedMultiplicitySpecies.value = species
  await loadMultiplicityStats()
}

const selectMotifSpecies = async (species) => {
  if (selectedMotifSpecies.value === species) return
  selectedMotifSpecies.value = species
  await loadMotifStats()
}

const selectGeneSpecies = async (species) => {
  if (selectedGeneSpecies.value === species) return
  selectedGeneSpecies.value = species
  await loadTopGeneStats()
}

const heroMetrics = computed(() => [
  {
    label: 'Species',
    value: fmt(detailedStats.value.total_species),
    note: 'organisms loaded',
    icon: 'mdi-paw',
    gradient: 'linear-gradient(135deg,#0D7377,#14919B)',
    to: { name: 'Help', hash: '#references', query: { open: 'references' } }
  },
  {
    label: 'Isoforms',
    value: fmt(detailedStats.value.total_transcripts),
    note: 'transcript-level records',
    icon: 'mdi-file-tree-outline',
    gradient: 'linear-gradient(135deg,#355C7D,#4A7898)'
  },
  {
    label: 'PA Sites',
    value: fmt(detailedStats.value.total_apa_sites),
    note: 'polyadenylation clusters',
    icon: 'mdi-map-marker-multiple-outline',
    gradient: 'linear-gradient(135deg,#2F855A,#48A36D)'
  },
  {
    label: 'Samples',
    value: fmt(detailedStats.value.total_samples),
    note: 'tissues and cell cultures',
    icon: 'mdi-flask-outline',
    gradient: 'linear-gradient(135deg,#A96F4C,#B7791F)'
  }
])

const chartTooltip = {
  backgroundColor: 'rgba(248, 252, 252, 0.96)',
  titleColor: '#0f172a',
  bodyColor: '#334155',
  borderColor: 'rgba(13, 115, 119, 0.18)',
  borderWidth: 1,
  padding: 12,
  titleFont: { family: 'IBM Plex Sans', size: 13, weight: '700' },
  bodyFont: { family: 'IBM Plex Sans', size: 13, weight: '500' }
}

const multiplicityChartData = computed(() => {
  const buckets = multiplicityBuckets.value.buckets || {}
  if (!multiplicityBuckets.value.total) return null
  return {
    labels: ['1 PA site', '2 PA sites', '3 PA sites', '4 PA sites', '5+ PA sites'],
    datasets: [{
      label: 'Isoforms',
      data: [buckets['1'] || 0, buckets['2'] || 0, buckets['3'] || 0, buckets['4'] || 0, buckets['5+'] || 0],
      backgroundColor: ['#94a3b8', '#6fa8a8', '#14919B', '#0D7377', '#0A5C5F'],
      hoverBackgroundColor: ['#64748b', '#568f90', '#0D7377', '#0A5C5F', '#064346'],
      categoryPercentage: 0.70,
      barPercentage: 0.66,
      borderRadius: 0,
      borderSkipped: false
    }]
  }
})

const multiplicityChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 900, easing: 'easeOutQuart' },
  plugins: {
    legend: { display: false },
    tooltip: {
      ...chartTooltip,
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
      border: { display: true, color: 'rgba(100, 116, 139, 0.34)' },
      grid: { display: false, drawBorder: false },
      ticks: {
        color: '#64748b',
        padding: 8,
        font: { family: 'IBM Plex Sans', size: 11, weight: '500' }
      }
    },
    x: {
      border: { display: true, color: 'rgba(100, 116, 139, 0.34)' },
      grid: { display: false, drawBorder: false },
      ticks: {
        color: '#475569',
        padding: 8,
        font: { family: 'IBM Plex Sans', size: 12, weight: '700' }
      }
    }
  }
}))

const motifColors = [
  '#66C2A5', '#C5A07A', '#DE927F', '#979EC1', '#BE94C7', '#DB98AF',
  '#B2CA68', '#CED843', '#FDD738', '#ECCA78', '#D3BE9F', '#B3B3B3'
]

const motifChartData = computed(() => {
  const motifs = motifStats.value?.motifs || []
  if (!motifs.length) return null
  return {
    labels: motifs.map(item => item.motif),
    datasets: [{
      data: motifs.map(item => item.count),
      backgroundColor: motifs.map((_, i) => motifColors[i % motifColors.length]),
      hoverBackgroundColor: motifs.map((_, i) => motifColors[i % motifColors.length]),
      borderColor: '#ffffff',
      borderWidth: 3,
      hoverOffset: 8
    }]
  }
})

const noMotifPct = computed(() =>
  motifStats.value?.motifs?.find(item => item.motif === 'No motif')?.pct ?? 0
)

const topMotif = computed(() =>
  motifStats.value?.motifs?.find(item => !['No motif', 'Other motifs'].includes(item.motif)) || null
)

const topMotifLabel = computed(() => topMotif.value?.motif || 'Top motif')
const topMotifPct = computed(() => topMotif.value?.pct ?? 0)

const motifChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 900, easing: 'easeOutQuart' },
  plugins: {
    legend: {
      position: 'right',
      labels: {
        boxWidth: 10,
        boxHeight: 10,
        padding: 12,
        color: '#475569',
        font: { family: 'IBM Plex Sans', size: 11, weight: '600' }
      }
    },
    tooltip: {
      ...chartTooltip,
      callbacks: {
        label: (ctx) => {
          const item = motifStats.value?.motifs?.[ctx.dataIndex]
          return `${ctx.label}: ${fmt(ctx.raw)} sites (${item?.pct ?? 0}%)`
        }
      }
    }
  }
}))

const speciesRichnessData = computed(() => {
  const speciesMeta = new Map(speciesList.value.map(sp => [sp.name, sp]))
  const rows = detailedStats.value.apa_sites_by_species || []
  const maxCount = Math.max(...rows.map(s => s.count), 1)
  const colors = ['#0D7377', '#14919B', '#355C7D', '#2F855A', '#A96F4C', '#746A9E']
  return rows
    .map((row, i) => {
      const meta = speciesMeta.get(row.name) || row
      return {
        ...row,
        displayName: row.display_name || formatSpeciesName(meta),
        subtitle: formatSpeciesSubtitle(meta),
        assembly: meta.assembly,
        apaCount: row.count,
        pct: (row.count / maxCount) * 100,
        color: colors[i % colors.length]
      }
    })
    .sort((a, b) => b.apaCount - a.apaCount)
    .slice(0, 10)
})

const maxGeneApaCount = computed(() =>
  Math.max(...(topGenesByApa.value.map(g => g.apa_count) ?? [1]), 1)
)

const topGenesByApa = computed(() =>
  topGeneStats.value || detailedStats.value.top_genes_by_apa?.slice(0, 10) || []
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
  background: linear-gradient(180deg, #f8fafc 0%, #f4f8fa 100%);
}

.stats-loading-shell {
  min-height: 460px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 18px;
}

.stats-loading-text {
  color: #64748b;
  font-weight: 600;
  letter-spacing: 0.025em;
}

.reveal-item {
  opacity: 0;
  transform: translateY(12px) scale(0.992);
  animation: statsReveal 560ms cubic-bezier(0.16, 1, 0.3, 1) forwards;
  animation-delay: var(--delay, 0ms);
  will-change: opacity, transform;
}

@keyframes statsReveal {
  to { opacity: 1; transform: translateY(0) scale(1); }
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

.hero-content {
  position: relative;
  z-index: 1;
  padding: 48px 24px 56px;
}

.hero-content :deep(.text-h3) {
  font-family: var(--aa-font-sans) !important;
  font-size: 3rem !important;
  font-weight: 700 !important;
  line-height: 1.12;
  letter-spacing: -0.01em !important;
}

.hero-content :deep(.text-h6) {
  font-family: var(--aa-font-sans) !important;
  max-width: 760px;
  font-size: 1.25rem !important;
  font-weight: 500 !important;
  line-height: 1.45;
  letter-spacing: 0 !important;
}

.stats-content {
  position: relative;
  padding-top: 48px;
  padding-bottom: 56px;
  --stats-card-gap: 28px;
  display: flex;
  flex-direction: column;
  gap: var(--stats-card-gap);
}

/*
.stats-hero {
  position: relative;
  overflow: hidden;
  min-height: 300px;
  display: flex;
  align-items: center;
  padding: 0;
  color: white;
  background: linear-gradient(135deg, #0a4f53 0%, #0D7377 40%, #1a2744 100%);
  background-size: 300% 300%;
  animation: gradientShift 18s ease infinite;
}

.stats-hero-bg {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse 80% 60% at 60% 40%, rgba(20,145,155,0.18) 0%, transparent 70%);
  pointer-events: none;
}
*/

@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.stats-hero-container {
  position: relative;
  min-height: 300px;
  display: flex;
  align-items: center;
  padding-top: 48px;
  padding-bottom: 56px;
}

.stats-hero-copy {
  position: relative;
  z-index: 1;
  max-width: 760px;
}

.stats-title {
  font-size: 3rem;
  line-height: 1.05;
  font-weight: 700;
  letter-spacing: -0.01em;
  margin: 8px 0 10px;
}

.stats-subtitle {
  max-width: 680px;
  color: rgba(255,255,255,0.90);
  font-size: 1.25rem;
  line-height: 1.45;
}

.cache-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 18px;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.22);
  color: rgba(255,255,255,0.86);
  font-size: 0.78rem;
  font-weight: 700;
}

.hero-orbit {
  position: absolute;
  right: clamp(24px, 7vw, 90px);
  top: 50%;
  width: 220px;
  height: 220px;
  transform: translateY(-50%);
  opacity: 0.78;
}

.orbit-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.22);
}

.orbit-ring--inner { inset: 48px; }
.orbit-dot {
  position: absolute;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #9FE7E3;
  box-shadow: 0 0 34px rgba(159,231,227,0.8);
}
.orbit-dot--a { top: 22px; right: 48px; }
.orbit-dot--b { bottom: 40px; left: 26px; background: #E6B06D; }

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
  margin: 0;
  position: relative;
}

.metric-card,
.section-card {
  background: #fff;
  border: 1px solid rgba(203, 213, 225, 0.72);
  box-shadow: none;
}

.statistics-page .section-card,
.statistics-page .stats-card-cell > .section-card {
  background: #ffffff !important;
  background-image: none !important;
  border: 1px solid rgba(203, 213, 225, 0.72) !important;
  box-shadow: none !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}

.metric-card {
  border-radius: 22px;
  padding: 22px;
  transition: transform 180ms ease, border-color 180ms ease, background-color 180ms ease;
}

.metric-card--link {
  color: inherit;
  cursor: pointer;
  text-decoration: none;
}

.metric-card--link:hover {
  border-color: rgba(20, 145, 155, 0.34);
  transform: translateY(-2px);
}

.metric-card--link:focus-visible {
  outline: 3px solid rgba(20, 145, 155, 0.22);
  outline-offset: 3px;
}

.metric-icon {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 18px;
}

.metric-value {
  font-family: var(--aa-font-display);
  font-size: clamp(1.65rem, 2.8vw, 2.35rem);
  line-height: 1.05;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.012em;
}

.metric-label {
  margin-top: 8px;
  color: #0D7377;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-size: 0.72rem;
}

.metric-note {
  color: #64748b;
  font-size: 0.85rem;
  margin-top: 5px;
}

.section-card {
  border-radius: 24px;
  padding: 24px;
  margin-bottom: 0;
}

.stats-card-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--stats-card-gap);
  align-items: stretch;
}

.stats-card-cell,
.stats-card-cell > .section-card {
  min-width: 0;
  height: 100%;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
  margin-bottom: 20px;
}

.section-header.compact { margin-bottom: 18px; }
.stats-filter-header {
  display: block;
}

.stats-filter-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 4px;
}

.stats-filter-topline .section-eyebrow {
  min-height: 24px;
  padding-top: 0;
  padding-bottom: 0;
  line-height: 1;
}

.species-filter-trigger {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  flex: 0 0 auto;
  height: 24px;
  padding: 0 7px 0 9px;
  border: 1px solid rgba(13, 115, 119, 0.20);
  border-radius: 8px;
  background: #f8fcfc;
  box-shadow: none;
  color: #0f172a;
  cursor: pointer;
  text-align: left;
  transition: border-color 160ms ease, background 160ms ease;
}

.species-filter-trigger:hover {
  border-color: rgba(13, 115, 119, 0.34);
  background: #eff8f8;
}

.species-filter-value {
  min-width: 0;
  color: #1e293b;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.10em;
  line-height: 1;
  text-transform: uppercase;
  white-space: nowrap;
}

.species-filter-value.is-placeholder {
  color: #0D7377;
}

.species-filter-icon {
  width: 15px;
  height: 15px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #0D7377;
  background: rgba(13, 115, 119, 0.08);
}

:global(.stats-species-menu) {
  width: 280px !important;
  max-width: min(280px, calc(100vw - 32px));
  opacity: 0;
  transform: translateY(-6px) scale(0.985);
  transform-origin: top right;
  animation: statsDropdownIn 180ms cubic-bezier(0.16, 1, 0.3, 1) forwards;
  will-change: opacity, transform;
}

@keyframes statsDropdownIn {
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.species-menu-card {
  max-height: 280px;
  overflow-y: auto;
  padding: 8px;
  border: 1px solid rgba(13, 115, 119, 0.16);
  border-radius: 14px;
  background: #fff;
  box-shadow: none;
}

.species-menu-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 14px;
  padding: 8px 10px 10px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.86);
  color: #1e293b;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.species-menu-header small {
  color: #94a3b8;
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: none;
}

.species-menu-option {
  width: 100%;
  min-height: 36px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 5px;
  padding: 8px 10px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: #334155;
  cursor: pointer;
  font: inherit;
  text-align: left;
  transition: background 140ms ease, color 140ms ease, transform 140ms ease;
}

.species-menu-option:hover {
  transform: translateX(2px);
  background: rgba(13, 115, 119, 0.07);
  color: #0D7377;
}

.species-menu-option.is-active {
  background: linear-gradient(135deg, rgba(13, 115, 119, 0.12), rgba(20, 145, 155, 0.08));
  color: #0D7377;
}

.species-menu-option-main {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.88rem;
  font-weight: 600;
}
.section-eyebrow {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  color: #14919B;
}
.section-eyebrow--light { color: rgba(172, 244, 240, 0.95); }
.stats-card-title {
  font-family: var(--aa-font-sans);
  font-size: 1.38rem;
  font-weight: 600;
  font-stretch: normal;
  color: #1e293b;
  letter-spacing: 0.025em;
  font-variation-settings: normal;
  margin: 4px 0 6px;
  line-height: 1.3;
}
.section-subtitle {
  color: #64748b;
  font-size: 0.92rem;
  line-height: 1.55;
  max-width: 720px;
}

.flow-grid {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto 1fr;
  align-items: stretch;
  gap: 14px;
}

.flow-node,
.flow-connector {
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.flow-node {
  min-height: 118px;
  flex-direction: column;
  background: #f8fafc;
  border: 1px solid rgba(13, 115, 119, 0.14);
}

.flow-node--strong { border-color: rgba(20, 145, 155, 0.34); }
.flow-node-value {
  color: #0D7377;
  font-family: var(--aa-font-display);
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -0.01em;
}
.flow-node-label {
  color: #64748b;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  font-size: 0.74rem;
}
.flow-connector {
  min-width: 110px;
  color: #475569;
  font-weight: 700;
  font-size: 0.82rem;
  position: relative;
}
.flow-connector::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  border-top: 1px dashed rgba(13, 115, 119, 0.26);
}
.flow-connector span {
  position: relative;
  background: #fff;
  padding: 4px 8px;
  border-radius: 999px;
}

.chart-shell {
  height: 280px;
  padding: 8px 0 0;
}
.chart-shell--large { height: 315px; }
.chart-shell--wide { height: 400px; }
.motif-chart-shell {
  padding-top: 4px;
}
.empty-chart {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-weight: 600;
}

.complexity-cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 16px;
}
.complexity-card {
  border-radius: 16px;
  padding: 14px 12px;
  background: #f8fafc;
  border: 1px solid rgba(203,213,225,0.72);
}
.complexity-card--accent {
  background: #f1fafa;
  border-color: rgba(13,115,119,0.22);
}
.complexity-value {
  display: block;
  color: #0D7377;
  font-size: 1.55rem;
  font-weight: 700;
  line-height: 1;
}
.complexity-label {
  display: block;
  color: #64748b;
  font-size: 0.78rem;
  margin-top: 7px;
  white-space: nowrap;
}

.species-richness-container,
.leaderboard-container {
  display: flex;
  flex-direction: column;
}
.species-richness-row,
.leaderboard-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(226,232,240,0.78);
}
.species-richness-row:last-child,
.leaderboard-row:last-child { border-bottom: none; }
.species-name-col { min-width: 168px; }
.species-common { font-weight: 700; color: #1e293b; font-size: 0.9rem; }
.species-latin { color: #94a3b8; font-size: 0.78rem; font-style: italic; }
.species-leader-name {
  min-width: 146px;
  max-width: 146px;
  overflow: hidden;
}
.species-leader-name .species-common,
.species-leader-name .species-latin {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.species-bar-col { flex: 1; display: flex; align-items: center; gap: 12px; min-width: 0; }
.species-bar-track,
.leaderboard-bar-track {
  flex: 1;
  height: 10px;
  background: rgba(226,232,240,0.74);
  border-radius: 999px;
  overflow: hidden;
}
.species-bar-fill,
.leaderboard-bar-fill {
  height: 100%;
  border-radius: 999px;
  transform-origin: left center;
  animation: barGrow 900ms cubic-bezier(0.22, 1, 0.36, 1) both;
}
@keyframes barGrow { from { transform: scaleX(0); } to { transform: scaleX(1); } }
.species-bar-count { min-width: 86px; text-align: right; color: #0D7377; font-weight: 700; font-size: 0.84rem; }
.assembly-chip { min-width: 54px; justify-content: center; }

.leaderboard-header { align-items: flex-start; }
.rank-badge {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 0.8rem;
  flex-shrink: 0;
}
.rank-gold { background: linear-gradient(135deg, #D9A441, #A96F4C); color: white; }
.rank-silver { background: linear-gradient(135deg, #94a3b8, #64748b); color: white; }
.rank-bronze { background: linear-gradient(135deg, #B7791F, #8A5A22); color: white; }
.rank-default { background: rgba(226,232,240,0.9); color: #64748b; }
.gene-name-link { min-width: 100px; color: #0D7377; font-weight: 700; text-decoration: none; }
.gene-name-link:hover { text-decoration: underline; }
.gene-species-chip {
  min-width: 120px;
  color: #64748b;
  font-size: 0.78rem;
  font-weight: 700;
}
.leaderboard-bar-fill { background: linear-gradient(90deg, #0D7377, #14919B); }
.species-leader-bar-fill { background: linear-gradient(90deg, #355C7D, #4A7898); }

@media (max-width: 1024px) {
  .hero-content {
    padding-left: 22px !important;
    padding-right: 22px !important;
  }

  .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .stats-card-row { grid-template-columns: 1fr; }
  .hero-orbit { opacity: 0.28; }
  .flow-grid { grid-template-columns: 1fr; }
  .flow-connector { min-height: 46px; }
  .flow-connector::before { left: 50%; right: auto; top: 0; bottom: 0; border-top: none; border-left: 1px dashed rgba(13,115,119,0.26); }
  .section-card { padding: 22px; }
}

@media (max-width: 640px) {
  .hero-section {
    min-height: 240px;
  }

  .hero-content {
    padding: 36px 18px 42px;
  }

  .hero-content :deep(.text-h3) {
    font-size: 2rem !important;
    line-height: 1.15;
  }

  .hero-content :deep(.text-h6) {
    font-size: 1rem !important;
  }

  .stats-hero,
  .stats-hero-container { min-height: 300px; }
  .stats-title { font-size: 2.25rem; }
  .stats-subtitle { font-size: 1.05rem; }
  .metric-grid,
  .complexity-cards { grid-template-columns: 1fr; }
  .species-richness-row,
  .leaderboard-row { align-items: stretch; flex-direction: column; gap: 8px; }
  .species-name-col,
  .gene-species-chip,
  .species-leader-name { min-width: 0; max-width: none; }
  .species-bar-count { text-align: left; }
  .leaderboard-bar-track { width: 100%; }
  .stats-content { padding-top: 28px; }
  .section-card { padding: 18px; border-radius: 18px; }
  .stats-filter-topline {
    align-items: flex-start;
    flex-direction: column;
    gap: 8px;
  }
  .species-filter-trigger {
    max-width: 100%;
  }
  .chart-shell,
  .chart-shell--large,
  .chart-shell--wide {
    height: 300px;
  }
  .flow-node { min-height: 104px; }
  .flow-node-value { font-size: 1.65rem; }
}
</style>
