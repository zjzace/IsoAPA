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
    
    <section class="info-section py-12 bg-grey-lighten-5">
      <v-container>
        <h2 class="text-h4 text-center mb-8">What is Isoform-Level APA?</h2>
        
        <v-row justify="center">
          <v-col cols="12" lg="10">
            <v-card class="pa-6" variant="outlined">
              <p class="text-body-1 mb-6">
                <strong>Alternative Polyadenylation (APA)</strong> is a post-transcriptional regulatory mechanism 
                that generates multiple mRNA isoforms from a single gene by selecting different polyadenylation 
                sites in the 3' untranslated region (UTR). This results in transcripts with different 3' end points.
              </p>
              
              <v-row align="center" class="my-6">
                <v-col cols="12" md="7">
                  <div class="apa-diagram pa-4 rounded-lg">
                    <!-- Gene label -->
                    <div class="text-caption text-grey mb-2">Gene Structure</div>
                    
                    <!-- Short Isoform -->
                    <div class="isoform mb-4">
                      <div class="isoform-label text-caption mb-1">
                        <v-chip size="x-small" color="primary" class="mr-2">Proximal PAS</v-chip>
                        <span>Short isoform (3' UTR shortening)</span>
                      </div>
                      <div class="transcript-row">
                        <!-- Exon 1 -->
                        <div class="exon-box exon-1">Exon 1</div>
                        <!-- Intron line -->
                        <div class="intron-line"></div>
                        <!-- Exon 2 -->
                        <div class="exon-box exon-2">Exon 2</div>
                        <!-- Intron line -->
                        <div class="intron-line"></div>
                        <!-- Exon 3 with short UTR -->
                        <div class="exon-box exon-3">
                          Exon 3
                          <div class="utr-region short-utr">
                            <span class="pas-marker">▼</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <!-- Long Isoform -->
                    <div class="isoform">
                      <div class="isoform-label text-caption mb-1">
                        <v-chip size="x-small" color="secondary" class="mr-2">Distal PAS</v-chip>
                        <span>Long isoform (3' UTR lengthening)</span>
                      </div>
                      <div class="transcript-row">
                        <!-- Exon 1 -->
                        <div class="exon-box exon-1">Exon 1</div>
                        <!-- Intron line -->
                        <div class="intron-line"></div>
                        <!-- Exon 2 -->
                        <div class="exon-box exon-2">Exon 2</div>
                        <!-- Intron line -->
                        <div class="intron-line"></div>
                        <!-- Exon 3 with extended UTR -->
                        <div class="exon-box exon-3 long">
                          Exon 3
                          <div class="utr-region long-utr">
                            <span class="utr-extended"></span>
                            <span class="pas-marker">▼</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <!-- Legend -->
                    <div class="diagram-legend mt-4">
                      <div class="d-flex align-center ga-4">
                        <div class="d-flex align-center">
                          <div class="legend-exon"></div>
                          <span class="text-caption ml-1">Coding Exon</span>
                        </div>
                        <div class="d-flex align-center">
                          <div class="legend-utr"></div>
                          <span class="text-caption ml-1">3' UTR</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </v-col>
                <v-col cols="12" md="5">
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
                  
                  <v-alert type="info" variant="tonal" class="mt-4">
                    <strong>Key Insight:</strong> Both isoforms share the same coding sequence (CDS) 
                    but differ in their 3' UTR length, affecting post-transcriptional regulation.
                  </v-alert>
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiService } from '@/services/api'

const router = useRouter()

const searchQuery = ref('')
const selectedField = ref('gene_name')
const selectedGene = ref(null)
const featuredGenes = ref([])

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
    featuredGenes.value = await apiService.getGenes(1, 10)
  } catch (error) {
    console.error('Failed to load featured genes:', error)
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

/* APA Diagram - Genome Browser Style */
.apa-diagram {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.isoform {
  position: relative;
}

.isoform-label {
  display: flex;
  align-items: center;
  min-height: 24px;
}

.transcript-row {
  display: flex;
  align-items: center;
  position: relative;
}

.exon-box {
  background: linear-gradient(180deg, #0D7377 0%, #14919B 100%);
  color: white;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  min-width: 80px;
  text-align: center;
  position: relative;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
  z-index: 2;
}

.exon-box.long {
  background: linear-gradient(180deg, #E94560 0%, #FF6B6B 100%);
}

.intron-line {
  flex: 1;
  height: 3px;
  background: linear-gradient(90deg, #0D7377 0%, #14919B 100%);
  position: relative;
  min-width: 30px;
}

.intron-line::before,
.intron-line::after {
  content: '▼';
  position: absolute;
  top: -8px;
  font-size: 8px;
  color: #0D7377;
}

.intron-line::before {
  left: 0;
}

.intron-line::after {
  right: 0;
}

.utr-region {
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: flex-start;
  justify-content: center;
}

.short-utr {
  width: 30px;
}

.long-utr {
  width: 120px;
  display: flex;
  align-items: center;
}

.utr-extended {
  flex: 1;
  height: 4px;
  background: linear-gradient(90deg, #E94560 0%, #FF6B6B 100%);
  border-radius: 2px;
  margin-right: 4px;
}

.pas-marker {
  color: #E94560;
  font-size: 14px;
  font-weight: bold;
}

.short-utr .pas-marker {
  position: absolute;
  bottom: -14px;
  left: 50%;
  transform: translateX(-50%);
}

.long-utr .pas-marker {
  color: #E94560;
}

.diagram-legend {
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  padding-top: 12px;
}

.legend-exon {
  width: 20px;
  height: 12px;
  background: linear-gradient(180deg, #0D7377 0%, #14919B 100%);
  border-radius: 2px;
}

.legend-utr {
  width: 20px;
  height: 4px;
  background: #E94560;
  border-radius: 2px;
}

.gene-card {
  cursor: pointer;
  transition: all 0.3s ease;
}

.gene-card:hover {
  transform: scale(1.05);
}
</style>
