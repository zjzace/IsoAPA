<template>
  <div>
    <section class="hero-section">
      <div class="hero-bg"></div>
      <v-container class="hero-content">
        <v-row justify="center">
          <v-col cols="12" md="10" lg="8">
            <div class="text-center mb-8">
              <h1 class="text-h2 text-white font-weight-bold mb-4">
                <v-icon icon="mdi-dna" size="48" class="mr-3"></v-icon>
                ApaAtlas
              </h1>
              <p class="text-h5 text-white-lighten-1 mb-8">
                Isoform-Level Alternative Polyadenylation Database
              </p>
            </div>
            
            <v-card class="search-card pa-2" elevation="8">
              <v-text-field
                v-model="searchQuery"
                placeholder="Search by gene name, transcript ID, sample..."
                prepend-inner-icon="mdi-magnify"
                variant="solo"
                flat
                hide-details
                @keyup.enter="performSearch"
                @update:model-value="onSearchInput"
              ></v-text-field>
              <v-card-actions class="px-4 pb-4">
                <v-chip-group v-model="selectedField" mandatory>
                  <v-chip value="gene_name" variant="outlined">Gene Name</v-chip>
                  <v-chip value="transcript_id" variant="outlined">Transcript ID</v-chip>
                  <v-chip value="sample" variant="outlined">Sample</v-chip>
                  <v-chip value="species" variant="outlined">Species</v-chip>
                </v-chip-group>
                <v-spacer></v-spacer>
                <v-btn color="primary" size="large" @click="performSearch">
                  Search
                </v-btn>
              </v-card-actions>
            </v-card>
            
            <div class="text-center mt-6">
              <v-btn variant="text" color="white" to="/search" class="mr-4">
                <v-icon start>mdi-view-list</v-icon>
                Browse All Data
              </v-btn>
            </div>
          </v-col>
        </v-row>
      </v-container>
    </section>
    
    <section class="stats-section py-12">
      <v-container>
        <h2 class="text-h4 text-center mb-8">Database Statistics</h2>
        
        <v-row justify="center">
          <v-col cols="6" sm="4" md="2">
            <v-card class="text-center pa-4 stat-card" variant="tonal">
              <div class="text-h3 text-primary font-weight-bold">{{ stats.total_genes }}</div>
              <div class="text-body-2 text-grey-darken-1">Genes</div>
            </v-card>
          </v-col>
          <v-col cols="6" sm="4" md="2">
            <v-card class="text-center pa-4 stat-card" variant="tonal">
              <div class="text-h3 text-primary font-weight-bold">{{ stats.total_transcripts }}</div>
              <div class="text-body-2 text-grey-darken-1">Transcripts</div>
            </v-card>
          </v-col>
          <v-col cols="6" sm="4" md="2">
            <v-card class="text-center pa-4 stat-card" variant="tonal">
              <div class="text-h3 text-primary font-weight-bold">{{ stats.total_apa_sites }}</div>
              <div class="text-body-2 text-grey-darken-1">APA Sites</div>
            </v-card>
          </v-col>
          <v-col cols="6" sm="4" md="2">
            <v-card class="text-center pa-4 stat-card" variant="tonal">
              <div class="text-h3 text-primary font-weight-bold">{{ stats.total_cell_lines }}</div>
              <div class="text-body-2 text-grey-darken-1">Samples</div>
            </v-card>
          </v-col>
          <v-col cols="6" sm="4" md="2">
            <v-card class="text-center pa-4 stat-card" variant="tonal">
              <div class="text-h3 text-primary font-weight-bold">{{ stats.total_species }}</div>
              <div class="text-body-2 text-grey-darken-1">Species</div>
            </v-card>
          </v-col>
        </v-row>
        
        <v-row class="mt-8">
          <v-col cols="12" md="6">
            <v-card class="pa-4" variant="outlined">
              <h3 class="text-h6 mb-4">APA Sites by Species</h3>
              <Bar :data="speciesChartData" :options="chartOptions"></Bar>
            </v-card>
          </v-col>
          <v-col cols="12" md="6">
            <v-card class="pa-4" variant="outlined">
              <h3 class="text-h6 mb-4">APA Sites by Sample</h3>
              <Doughnut :data="sampleChartData" :options="chartOptions"></Doughnut>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </section>
    
    <section class="info-section py-12 bg-grey-lighten-5">
      <v-container>
        <h2 class="text-h4 text-center mb-8">What is Isoform-Level APA?</h2>
        
        <v-row justify="center">
          <v-col cols="12" lg="10">
            <v-card class="pa-6" variant="outlined">
              <p class="text-body-1 mb-4">
                <strong>Alternative Polyadenylation (APA)</strong> is a post-transcriptional regulatory mechanism 
                that generates multiple mRNA isoforms from a single gene by selecting different polyadenylation 
                sites in the 3' untranslated region (UTR).
              </p>
              
              <v-row align="center" class="my-6">
                <v-col cols="12" md="6">
                  <div class="apa-diagram pa-4 bg-primary-lighten-5 rounded">
                    <div class="d-flex flex-column align-center">
                      <div class="gene-block text-body-1 font-weight-bold mb-2">Gene</div>
                      <div class="exon-container d-flex">
                        <div class="exon">Exon 1</div>
                        <div class="exon">Exon 2</div>
                        <div class="exon">Exon 3</div>
                        <div class="exon utr-short">UTR</div>
                      </div>
                      <div class="apa-sites mt-2">
                        <v-chip size="small" color="primary">Proximal PAS</v-chip>
                        <v-chip size="small" color="secondary" class="ml-2">Distal PAS</v-chip>
                      </div>
                      <div class="transcripts mt-4">
                        <div class="transcript-label text-caption">Short isoform (3' UTR shortening)</div>
                        <div class="transcript-bar short"></div>
                      </div>
                      <div class="transcripts mt-2">
                        <div class="transcript-label text-caption">Long isoform (3' UTR lengthening)</div>
                        <div class="transcript-bar long"></div>
                      </div>
                    </div>
                  </div>
                </v-col>
                <v-col cols="12" md="6">
                  <h4 class="text-h6 mb-3">Why APA Matters</h4>
                  <v-list density="compact">
                    <v-list-item prepend-icon="mdi-check-circle" class="px-0">
                      <v-list-item-title>Regulates mRNA stability and translation efficiency</v-list-item-title>
                    </v-list-item>
                    <v-list-item prepend-icon="mdi-check-circle" class="px-0">
                      <v-list-item-title>Impacts miRNA binding sites in 3' UTR</v-list-item-title>
                    </v-list-item>
                    <v-list-item prepend-icon="mdi-check-circle" class="px-0">
                      <v-list-item-title>Influences protein localization signals</v-list-item-title>
                    </v-list-item>
                    <v-list-item prepend-icon="mdi-check-circle" class="px-0">
                      <v-list-item-title>Dysregulated in cancer and other diseases</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-col>
              </v-row>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </section>
    
    <section class="howto-section py-12">
      <v-container>
        <h2 class="text-h4 text-center mb-8">How to Use</h2>
        
        <v-row>
          <v-col cols="12" md="4">
            <v-card class="pa-6 text-center h-100" variant="tonal">
              <v-avatar color="primary" size="64" class="mb-4">
                <v-icon icon="mdi-magnify" size="32"></v-icon>
              </v-avatar>
              <h3 class="text-h6 mb-2">Search</h3>
              <p class="text-body-2">
                Use the search bar to find genes, transcripts, samples, or species. 
                Filter by multiple criteria for precise results.
              </p>
            </v-card>
          </v-col>
          <v-col cols="12" md="4">
            <v-card class="pa-6 text-center h-100" variant="tonal">
              <v-avatar color="primary" size="64" class="mb-4">
                <v-icon icon="mdi-chart-bar" size="32"></v-icon>
              </v-avatar>
              <h3 class="text-h6 mb-2">Explore</h3>
              <p class="text-body-2">
                Browse APA sites for each transcript. View genomic coordinates, 
                abundance levels, and sample-specific patterns.
              </p>
            </v-card>
          </v-col>
          <v-col cols="12" md="4">
            <v-card class="pa-6 text-center h-100" variant="tonal">
              <v-avatar color="primary" size="64" class="mb-4">
                <v-icon icon="mdi-download" size="32"></v-icon>
              </v-avatar>
              <h3 class="text-h6 mb-2">Export</h3>
              <p class="text-body-2">
                Download search results in CSV format for further analysis. 
                Export data for gene set enrichment or other analyses.
              </p>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </section>
    
    <section class="featured-section py-12 bg-grey-lighten-5">
      <v-container>
        <h2 class="text-h4 text-center mb-6">Explore Example Genes</h2>
        
        <v-slide-group v-model="selectedGene" class="pa-4" show-arrows>
          <v-slide-group-item v-for="gene in featuredGenes" :key="gene.gene_id">
            <v-card 
              class="ma-4 gene-card" 
              width="200" 
              @click="goToGene(gene)"
              hover
            >
              <v-card-text class="text-center">
                <div class="text-h6 text-primary">{{ gene.gene_name }}</div>
                <div class="text-caption text-grey">{{ gene.gene_id }}</div>
                <div class="text-caption mt-2">
                  <v-chip size="x-small">{{ gene.chromosome }}</v-chip>
                  <v-chip size="x-small" class="ml-1">{{ gene.strand }}</v-chip>
                </div>
              </v-card-text>
            </v-card>
          </v-slide-group-item>
        </v-slide-group>
      </v-container>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Bar, Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js'
import { apiService } from '@/services/api'

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend)

const router = useRouter()

const searchQuery = ref('')
const selectedField = ref('gene_name')
const stats = ref({
  total_genes: 0,
  total_transcripts: 0,
  total_apa_sites: 0,
  total_cell_lines: 0,
  total_species: 0,
  apa_sites_by_species: [],
  apa_sites_by_cell_line: []
})

const speciesChartData = computed(() => ({
  labels: stats.value.apa_sites_by_species.map(s => s.name),
  datasets: [{
    label: 'APA Sites',
    data: stats.value.apa_sites_by_species.map(s => s.count),
    backgroundColor: ['#0D7377', '#14919B', '#323232', '#E94560']
  }]
}))

const sampleChartData = computed(() => ({
  labels: stats.value.apa_sites_by_cell_line.map(t => t.name),
  datasets: [{
    label: 'APA Sites',
    data: stats.value.apa_sites_by_cell_line.map(t => t.count),
    backgroundColor: [
      '#0D7377', '#14919B', '#323232', '#E94560',
      '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
      '#FFEAA7', '#DDA0DD'
    ]
  }]
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: {
      position: 'bottom'
    }
  }
}

const onSearchInput = (value) => {
  // Could add autocomplete here
}

const performSearch = () => {
  if (searchQuery.value.trim()) {
    router.push({
      path: '/search',
      query: { 
        [selectedField.value]: searchQuery.value 
      }
    })
  } else {
    router.push('/search')
  }
}

const goToGene = (gene) => {
  router.push({
    path: `/gene/${gene.gene_id}`
  })
}

onMounted(async () => {
  try {
    stats.value = await apiService.getStats()
    featuredGenes.value = await apiService.getGenes(1, 10)
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
})
</script>

<style scoped>
.hero-section {
  position: relative;
  min-height: 500px;
  display: flex;
  align-items: center;
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #0D7377 0%, #14919B 50%, #1A1A2E 100%);
  background-size: 400% 400%;
  animation: gradientShift 15s ease infinite;
}

@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.hero-content {
  position: relative;
  z-index: 1;
}

.search-card {
  border-radius: 16px !important;
}

.stat-card {
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.apa-diagram {
  min-height: 200px;
}

.exon-container {
  gap: 4px;
}

.exon {
  background: #0D7377;
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 12px;
}

.exon.utr-short {
  background: #14919B;
}

.transcripts {
  width: 100%;
}

.transcript-bar {
  height: 8px;
  border-radius: 4px;
  background: linear-gradient(to right, #0D7377, #14919B);
}

.transcript-bar.short {
  width: 60%;
}

.transcript-bar.long {
  width: 100%;
}

.gene-card {
  cursor: pointer;
  transition: all 0.3s ease;
}

.gene-card:hover {
  transform: scale(1.05);
}
</style>
