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
              
              <v-row class="my-6">
                <!-- Left Panel: Transcript Structure -->
                <v-col cols="12" md="7">
                  <div class="apa-diagram pa-5 rounded-lg">
                    <!-- Transcript label -->
                    <div class="text-caption text-grey mb-3">Transcript Structure</div>
                    
                    <!-- Short Isoform -->
                    <div class="isoform mb-4">
                      <div class="isoform-label text-caption mb-2">
                        <v-chip size="x-small" color="primary" class="mr-2">Proximal PAS</v-chip>
                        <span>Short isoform (3' UTR shortening)</span>
                      </div>
                      <div class="transcript-row align-center">
                        <div class="exon-box">Exon 1</div>
                        <div class="intron-line"></div>
                        <div class="exon-box">Exon 2</div>
                        <div class="intron-line"></div>
                        <div class="exon-box">Exon 3</div>
                        <div class="utr-box short"></div>
                        <div class="pas-marker">▼</div>
                      </div>
                    </div>
                    
                    <!-- Long Isoform -->
                    <div class="isoform">
                      <div class="isoform-label text-caption mb-2">
                        <v-chip size="x-small" color="error" class="mr-2">Distal PAS</v-chip>
                        <span>Long isoform (3' UTR lengthening)</span>
                      </div>
                      <div class="transcript-row align-center">
                        <div class="exon-box">Exon 1</div>
                        <div class="intron-line"></div>
                        <div class="exon-box">Exon 2</div>
                        <div class="intron-line"></div>
                        <div class="exon-box">Exon 3</div>
                        <div class="utr-box long"></div>
                        <div class="pas-marker">▼</div>
                      </div>
                    </div>
                    
                    <!-- Legend -->
                    <div class="diagram-legend mt-4">
                      <div class="d-flex align-center ga-4">
                        <div class="d-flex align-center">
                          <div class="legend-exon"></div>
                          <span class="text-caption ml-2">Coding Exon</span>
                        </div>
                        <div class="d-flex align-center">
                          <div class="legend-utr"></div>
                          <span class="text-caption ml-2">3' UTR</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </v-col>
                
                <!-- Right Panel: Why APA Matters -->
                <v-col cols="12" md="5">
                  <div class="why-apa-section pa-5 rounded-lg h-100">
                    <h4 class="text-h6 mb-4">Why APA Matters</h4>
                    
                    <div class="why-item mb-4">
                      <v-icon icon="mdi-check-circle" color="primary" size="small" class="mr-2"></v-icon>
                      <span class="text-body-2">Regulates mRNA stability and translation efficiency</span>
                    </div>
                    
                    <div class="why-item mb-4">
                      <v-icon icon="mdi-check-circle" color="primary" size="small" class="mr-2"></v-icon>
                      <span class="text-body-2">Impacts miRNA binding sites in 3' UTR</span>
                    </div>
                    
                    <div class="why-item mb-4">
                      <v-icon icon="mdi-check-circle" color="primary" size="small" class="mr-2"></v-icon>
                      <span class="text-body-2">Influences protein localization signals</span>
                    </div>
                    
                    <div class="why-item mb-0">
                      <v-icon icon="mdi-check-circle" color="primary" size="small" class="mr-2"></v-icon>
                      <span class="text-body-2">Dysregulated in cancer and other diseases</span>
                    </div>
                  </div>
                </v-col>
              </v-row>
              
              <!-- Key Insight - Separate Frame -->
              <div class="key-insight-section mt-6">
                <v-alert type="info" variant="tonal" class="mb-0 pa-4">
                  <strong>Key Insight:</strong> Both isoforms share the same coding sequence (CDS) 
                  but differ in their 3' UTR length, affecting post-transcriptional regulation.
                </v-alert>
              </div>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </section>
    
    <!-- Database at a Glance -->
    <section class="glance-section py-16">
      <v-container>
        <div class="text-center mb-12">
          <div class="section-eyebrow mb-2">Live Database</div>
          <h2 class="text-h4 font-weight-bold mb-3">The Database at a Glance</h2>
          <p class="text-body-1 text-grey-darken-1" style="max-width: 560px; margin: 0 auto;">
            Curated from high-throughput sequencing experiments across human and mouse transcriptomes.
          </p>
        </div>

        <v-row justify="center" class="mb-10">
          <v-col cols="6" sm="3" v-for="stat in dbStats" :key="stat.label">
            <div class="stat-glance-card text-center pa-6">
              <div class="stat-icon-ring mb-4" :style="{ background: stat.ringColor }">
                <v-icon :icon="stat.icon" size="28" :color="stat.color"></v-icon>
              </div>
              <div class="stat-number font-weight-black" :style="{ color: stat.color }">
                {{ stat.displayValue }}
              </div>
              <div class="stat-label text-body-2 text-grey-darken-1 mt-1">{{ stat.label }}</div>
            </div>
          </v-col>
        </v-row>

        <!-- Species Coverage -->
        <v-row justify="center" class="ga-4">
          <v-col cols="12" md="5">
            <div class="species-card pa-6 d-flex align-center ga-5">
              <div class="species-avatar species-human">
                <v-icon icon="mdi-human" size="36" color="white"></v-icon>
              </div>
              <div class="flex-grow-1">
                <div class="text-overline text-grey mb-1">Homo sapiens · GRCh38</div>
                <div class="text-h5 font-weight-bold">Human</div>
                <div class="text-body-2 text-grey-darken-1 mt-1">
                  <strong class="text-primary">77,784</strong> APA sites across 3 cell lines
                </div>
              </div>
              <div class="species-badge">
                <v-chip color="primary" variant="tonal" size="small">3 samples</v-chip>
              </div>
            </div>
          </v-col>
          <v-col cols="12" md="5">
            <div class="species-card pa-6 d-flex align-center ga-5">
              <div class="species-avatar species-mouse">
                <v-icon icon="mdi-rodent" size="36" color="white"></v-icon>
              </div>
              <div class="flex-grow-1">
                <div class="text-overline text-grey mb-1">Mus musculus · GRCm39</div>
                <div class="text-h5 font-weight-bold">Mouse</div>
                <div class="text-body-2 text-grey-darken-1 mt-1">
                  <strong class="text-primary">8,496</strong> APA sites from liver tissue
                </div>
              </div>
              <div class="species-badge">
                <v-chip color="secondary" variant="tonal" size="small">1 sample</v-chip>
              </div>
            </div>
          </v-col>
        </v-row>
      </v-container>
    </section>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const searchQuery = ref('')
const selectedField = ref('gene_name')

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

// Database at a Glance — static values from live DB
const dbStats = [
  { label: 'Genes', displayValue: '23,933', icon: 'mdi-dna', color: '#0D7377', ringColor: 'rgba(13,115,119,0.12)' },
  { label: 'Transcripts', displayValue: '54,937', icon: 'mdi-format-list-bulleted', color: '#14919B', ringColor: 'rgba(20,145,155,0.12)' },
  { label: 'APA Sites', displayValue: '86,280', icon: 'mdi-map-marker-multiple', color: '#E94560', ringColor: 'rgba(233,69,96,0.12)' },
  { label: 'Samples', displayValue: '4', icon: 'mdi-flask', color: '#5C6BC0', ringColor: 'rgba(92,107,192,0.12)' },
]

</script>

<style scoped>
/* ── Hero ─────────────────────────────────────────────────── */
.hero-section {
  position: relative;
  min-height: 520px;
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
  padding: 56px 0 64px;
}

.search-card {
  background: rgba(255, 255, 255, 0.92) !important;
  backdrop-filter: blur(20px) saturate(160%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(160%) !important;
  border: 1px solid rgba(255, 255, 255, 0.70) !important;
  border-radius: 18px !important;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.18), 0 2px 8px rgba(0, 0, 0, 0.10) !important;
}

/* ── APA Diagram ──────────────────────────────────────────── */
.apa-diagram {
  background: rgba(248, 250, 252, 0.80);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(0, 0, 0, 0.07);
  border-radius: 12px;
}

.isoform { position: relative; }

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
  padding: 8px 24px;
  font-size: 13.5px;
  font-weight: 600;
  min-width: 70px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
  z-index: 2;
}

.intron-line {
  flex: 1;
  height: 2px;
  background: #0D7377;
  min-width: 35px;
  max-width: 60px;
}

.utr-box {
  height: 10px;
  background: #D64545;
  display: flex;
  align-items: center;
}

.utr-box.short { width: 30px; }
.utr-box.long  { width: 100px; }

.pas-marker {
  color: #D64545;
  font-size: 13.5px;
  font-weight: bold;
  margin-left: 2px;
}

.diagram-legend {
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  padding-top: 12px;
}

.legend-exon {
  width: 20px;
  height: 10px;
  background: linear-gradient(180deg, #0D7377 0%, #14919B 100%);
}

.legend-utr {
  width: 20px;
  height: 10px;
  background: #D64545;
}

.why-apa-section {
  background: rgba(248, 250, 252, 0.80);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(0, 0, 0, 0.07);
  border-radius: 12px;
}

.why-item {
  display: flex;
  align-items: flex-start;
}

/* ── Sections layout ──────────────────────────────────────── */
.glance-section {
  background: rgb(var(--v-theme-background));
}

/* ── Section eyebrow ──────────────────────────────────────── */
.section-eyebrow {
  display: inline-block;
  font-size: 0.80rem;
  font-weight: 700;
  letter-spacing: 0.13em;
  text-transform: uppercase;
  color: #0D7377;
  padding: 4px 14px;
  background: rgba(13, 115, 119, 0.09);
  border-radius: 20px;
}

/* ── Stat cards (glassmorphism) ───────────────────────────── */
.stat-glance-card {
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(16px) saturate(150%);
  -webkit-backdrop-filter: blur(16px) saturate(150%);
  border: 1px solid rgba(255, 255, 255, 0.55);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06), 0 1px 4px rgba(0, 0, 0, 0.04);
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}

.stat-glance-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 14px 36px rgba(0, 0, 0, 0.10);
}

.v-theme--apaAtlasDarkTheme .stat-glance-card {
  background: rgba(24, 28, 37, 0.82);
  border: 1px solid rgba(255, 255, 255, 0.07);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.28);
}

.stat-icon-ring {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}

.stat-number {
  font-size: 2.3rem;
  line-height: 1.1;
}

.stat-label {
  font-size: 0.92rem;
}

/* ── Species cards ────────────────────────────────────────── */
.species-card {
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(16px) saturate(150%);
  -webkit-backdrop-filter: blur(16px) saturate(150%);
  border: 1px solid rgba(255, 255, 255, 0.55);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  transition: box-shadow 0.22s ease, transform 0.22s ease;
}

.species-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.09);
}

.v-theme--apaAtlasDarkTheme .species-card {
  background: rgba(24, 28, 37, 0.82);
  border: 1px solid rgba(255, 255, 255, 0.07);
}

.species-avatar {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.species-human { background: linear-gradient(135deg, #0D7377, #14919B); }
.species-mouse  { background: linear-gradient(135deg, #26A69A, #00695C); }

</style>
