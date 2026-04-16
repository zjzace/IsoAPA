<template>
  <div class="statistics-page">
    <v-container class="py-8">
      <div class="text-center mb-8">
        <h1 class="text-h3 font-weight-bold mb-2">
          <v-icon icon="mdi-chart-box" size="40" color="primary" class="mr-3"></v-icon>
          Database Statistics
        </h1>
        <p class="text-h6 text-grey">Comprehensive overview of ApaAtlas data</p>
      </div>

      <div v-if="loading" class="d-flex justify-center align-center" style="min-height: 400px;">
        <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
      </div>

      <div v-else-if="error">
        <v-alert type="error" variant="tonal">
          {{ error }}
        </v-alert>
      </div>

      <div v-else>
        <!-- Main Stats Cards -->
        <v-row class="mb-8">
          <v-col cols="6" sm="4" md="2">
            <v-card class="stat-card pa-4 text-center" variant="tonal" color="primary">
              <div class="text-h3 font-weight-bold">{{ stats.total_genes?.toLocaleString() || 0 }}</div>
              <div class="text-body-2 text-grey-darken-1">Genes</div>
            </v-card>
          </v-col>
          <v-col cols="6" sm="4" md="2">
            <v-card class="stat-card pa-4 text-center" variant="tonal" color="primary">
              <div class="text-h3 font-weight-bold">{{ stats.total_transcripts?.toLocaleString() || 0 }}</div>
              <div class="text-body-2 text-grey-darken-1">Transcripts</div>
            </v-card>
          </v-col>
          <v-col cols="6" sm="4" md="2">
            <v-card class="stat-card pa-4 text-center" variant="tonal" color="primary">
              <div class="text-h3 font-weight-bold">{{ stats.total_apa_sites?.toLocaleString() || 0 }}</div>
              <div class="text-body-2 text-grey-darken-1">APA Sites</div>
            </v-card>
          </v-col>
          <v-col cols="6" sm="4" md="2">
            <v-card class="stat-card pa-4 text-center" variant="tonal" color="primary">
              <div class="text-h3 font-weight-bold">{{ stats.total_samples?.toLocaleString() || 0 }}</div>
              <div class="text-body-2 text-grey-darken-1">Samples</div>
            </v-card>
          </v-col>
          <v-col cols="6" sm="4" md="2">
            <v-card class="stat-card pa-4 text-center" variant="tonal" color="primary">
              <div class="text-h3 font-weight-bold">{{ stats.total_species || 0 }}</div>
              <div class="text-body-2 text-grey-darken-1">Species</div>
            </v-card>
          </v-col>
          <v-col cols="6" sm="4" md="2">
            <v-card class="stat-card pa-4 text-center" variant="tonal" color="primary">
              <div class="text-h3 font-weight-bold">{{ stats.avg_apa_per_transcript || 0 }}</div>
              <div class="text-body-2 text-grey-darken-1">Avg Sites/Transcript</div>
            </v-card>
          </v-col>
        </v-row>

        <!-- Charts Row 1 -->
        <v-row class="mb-6">
          <v-col cols="12" md="6">
            <v-card variant="outlined" class="pa-4 chart-card">
              <h3 class="text-h6 mb-4 d-flex align-center">
                <v-icon icon="mdi-globe" class="mr-2" color="primary"></v-icon>
                APA Sites by Species
              </h3>
              <div style="height: 300px;">
                <Bar v-if="speciesChartData" :data="speciesChartData" :options="barChartOptions"></Bar>
              </div>
            </v-card>
          </v-col>
          <v-col cols="12" md="6">
            <v-card variant="outlined" class="pa-4 chart-card">
              <h3 class="text-h6 mb-4 d-flex align-center">
                <v-icon icon="mdi-dna" class="mr-2" color="primary"></v-icon>
                APA Sites by Strand
              </h3>
              <div style="height: 300px;">
                <Doughnut v-if="strandChartData" :data="strandChartData" :options="doughnutOptions"></Doughnut>
              </div>
            </v-card>
          </v-col>
        </v-row>

        <!-- Charts Row 2 -->
        <v-row class="mb-6">
          <v-col cols="12" md="6">
            <v-card variant="outlined" class="pa-4 chart-card">
              <h3 class="text-h6 mb-4 d-flex align-center">
                <v-icon icon="mdi-chip" class="mr-2" color="primary"></v-icon>
                APA Sites by Sample
              </h3>
              <div style="height: 300px;">
                <Bar v-if="sampleChartData" :data="sampleChartData" :options="horizontalBarOptions"></Bar>
              </div>
            </v-card>
          </v-col>
          <v-col cols="12" md="6">
            <v-card variant="outlined" class="pa-4 chart-card">
              <h3 class="text-h6 mb-4 d-flex align-center">
                <v-icon icon="mdi-chromosome" class="mr-2" color="primary"></v-icon>
                APA Sites by Chromosome
              </h3>
              <div style="height: 300px;">
                <Bar v-if="chromosomeChartData" :data="chromosomeChartData" :options="chromosomeBarOptions"></Bar>
              </div>
            </v-card>
          </v-col>
        </v-row>

        <!-- Top Genes Table -->
        <v-card variant="outlined" class="pa-4 chart-card">
          <h3 class="text-h6 mb-4 d-flex align-center">
            <v-icon icon="mdi-star" class="mr-2" color="primary"></v-icon>
            Top 20 Genes by APA Site Count
          </h3>
          <v-table class="elegant-table">
            <thead>
              <tr>
                <th class="text-left">Rank</th>
                <th class="text-left">Gene Name</th>
                <th class="text-left">Gene ID</th>
                <th class="text-right">APA Sites</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(gene, index) in stats.top_genes_by_apa" :key="gene.gene_id">
                <td>
                  <v-chip 
                    size="small" 
                    :color="index < 3 ? 'primary' : 'default'"
                    variant="tonal"
                  >
                    {{ index + 1 }}
                  </v-chip>
                </td>
                <td>
                  <router-link 
                    :to="{ name: 'GeneDetail', params: { geneId: gene.gene_id } }"
                    class="text-primary font-weight-medium"
                  >
                    {{ gene.gene_name }}
                  </router-link>
                </td>
                <td><code>{{ gene.gene_id }}</code></td>
                <td class="text-right">
                  <v-chip size="small" color="primary" variant="tonal">
                    {{ gene.apa_count }}
                  </v-chip>
                </td>
              </tr>
            </tbody>
          </v-table>
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
const stats = ref({})

const chartColors = [
  '#0D7377', '#14919B', '#323232', '#E94560', '#FF6B6B', 
  '#4ECDC4', '#5C6BC0', '#AB47BC', '#26A69A', '#FFA726'
]

const speciesChartData = computed(() => {
  if (!stats.value.apa_sites_by_species?.length) return null
  return {
    labels: stats.value.apa_sites_by_species.map(s => s.name),
    datasets: [{
      label: 'APA Sites',
      data: stats.value.apa_sites_by_species.map(s => s.count),
      backgroundColor: chartColors,
      borderRadius: 8
    }]
  }
})

const strandChartData = computed(() => {
  if (!stats.value.apa_sites_by_strand?.length) return null
  return {
    labels: stats.value.apa_sites_by_strand.map(s => s.strand || 'Unknown'),
    datasets: [{
      data: stats.value.apa_sites_by_strand.map(s => s.count),
      backgroundColor: ['#0D7377', '#E94560', '#323232']
    }]
  }
})

const sampleChartData = computed(() => {
  if (!stats.value.apa_sites_by_sample?.length) return null
  const sorted = [...stats.value.apa_sites_by_sample].sort((a, b) => b.count - a.count).slice(0, 10)
  return {
    labels: sorted.map(s => s.name),
    datasets: [{
      label: 'APA Sites',
      data: sorted.map(s => s.count),
      backgroundColor: chartColors.slice(0, sorted.length),
      borderRadius: 6
    }]
  }
})

const chromosomeChartData = computed(() => {
  if (!stats.value.apa_sites_by_chromosome?.length) return null
  return {
    labels: stats.value.apa_sites_by_chromosome.map(c => c.chromosome || 'Unknown'),
    datasets: [{
      label: 'APA Sites',
      data: stats.value.apa_sites_by_chromosome.map(c => c.count),
      backgroundColor: '#0D7377',
      borderRadius: 4
    }]
  }
})

const barChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false }
  },
  scales: {
    y: {
      beginAtZero: true,
      title: { display: true, text: 'APA Sites' }
    }
  }
}

const horizontalBarOptions = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y',
  plugins: {
    legend: { display: false }
  },
  scales: {
    x: {
      beginAtZero: true,
      title: { display: true, text: 'APA Sites' }
    }
  }
}

const chromosomeBarOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false }
  },
  scales: {
    y: {
      title: { display: true, text: 'APA Sites' }
    }
  }
}

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom'
    }
  }
}

onMounted(async () => {
  try {
    loading.value = true
    stats.value = await apiService.getDetailedStats()
  } catch (err) {
    console.error('Failed to load stats:', err)
    error.value = 'Failed to load statistics. Please try again.'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.statistics-page {
  min-height: 100vh;
  background: rgb(var(--v-theme-background));
}

.stat-card {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.chart-card {
  transition: box-shadow 0.3s ease;
}

.chart-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
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
  font-size: 0.95em;
}

.elegant-table {
  background: transparent !important;
}

.elegant-table :deep(th) {
  background: rgba(var(--v-theme-surface-variant), 0.3) !important;
  font-weight: 600;
}

.elegant-table :deep(tr:hover) {
  background: rgba(var(--v-theme-primary), 0.04) !important;
}
</style>
