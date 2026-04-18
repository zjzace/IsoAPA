<template>
  <div>
    <section class="hero-section">
      <div class="hero-bg"></div>
      <v-container class="hero-content">
        <v-row justify="center">
          <v-col cols="12" md="10" lg="8">
            <div class="text-center mb-8">
              <h1 class="text-h2 text-white font-weight-bold mb-4">
                <ApaAtlasIcon :size="48" class="mr-3" style="color:white;" />
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
    
    <section class="info-section py-16">
      <v-container>
        <div class="text-center mb-12">
          <div class="section-eyebrow mb-2">What is APA?</div>
          <h2 class="text-h4 font-weight-bold mb-3">Isoform-Level Alternative Polyadenylation</h2>
          <p class="text-body-1 text-grey-darken-1" style="max-width: 800px; margin: 0 auto;">
            <strong>Alternative Polyadenylation (APA)</strong> is a post-transcriptional regulatory mechanism 
            that generates multiple mRNA isoforms from a single gene by selecting different polyadenylation 
            sites in the 3' untranslated region (UTR).
          </p>
        </div>
        
        <v-row justify="center" align="stretch" class="mb-6">
          <!-- Left Panel: Transcript Structure -->
          <v-col cols="12" lg="7" class="d-flex flex-column">
            <div class="apa-diagram-card flex-grow-1 pa-6">
              <div class="d-flex justify-space-between align-center mb-6">
                <h3 class="text-h6 font-weight-bold">Transcript Structure</h3>
                <div class="diagram-legend">
                  <div class="legend-item">
                    <div class="legend-color-box bg-teal-gradient"></div>
                    <span>CDS Exon</span>
                  </div>
                  <div class="legend-item">
                    <div class="legend-color-box bg-utr-gradient"></div>
                    <span>3' UTR</span>
                  </div>
                </div>
              </div>
              
              <div class="diagram-track-container">
                <!-- Short Isoform -->
                <div class="diagram-track mb-8">
                  <div class="d-flex align-center justify-space-between mb-3">
                    <span class="text-subtitle-2 font-weight-bold">Proximal PAS</span>
                    <v-chip size="x-small" color="primary" variant="tonal">Short Isoform</v-chip>
                  </div>
                  <div class="diagram-visual">
                    <div class="diagram-spine"></div>
                    <div class="diagram-exon"></div>
                    <div class="diagram-intron"></div>
                    <div class="diagram-exon"></div>
                    <div class="diagram-intron"></div>
                    <div class="diagram-exon"></div>
                    <div class="diagram-utr short"></div>
                    <div class="diagram-pas-marker">▼</div>
                  </div>
                </div>
                
                <!-- Long Isoform -->
                <div class="diagram-track">
                  <div class="d-flex align-center justify-space-between mb-3">
                    <span class="text-subtitle-2 font-weight-bold">Distal PAS</span>
                    <v-chip size="x-small" color="error" variant="tonal">Long Isoform</v-chip>
                  </div>
                  <div class="diagram-visual">
                    <div class="diagram-spine"></div>
                    <div class="diagram-exon"></div>
                    <div class="diagram-intron"></div>
                    <div class="diagram-exon"></div>
                    <div class="diagram-intron"></div>
                    <div class="diagram-exon"></div>
                    <div class="diagram-utr long"></div>
                    <div class="diagram-pas-marker">▼</div>
                  </div>
                </div>
              </div>
            </div>
          </v-col>
          
          <!-- Right Panel: Why APA Matters (2x2 Grid) -->
          <v-col cols="12" lg="5" class="d-flex flex-column">
            <h3 class="text-h6 font-weight-bold mb-4 px-2">Why APA Matters</h3>
            <v-row dense class="flex-grow-1">
              <v-col cols="12" sm="6" lg="6">
                <div class="why-mini-card h-100 pa-4">
                  <v-icon icon="mdi-chart-line" color="primary" size="28" class="mb-3"></v-icon>
                  <div class="text-subtitle-2 font-weight-bold mb-1">Translation</div>
                  <div class="text-caption text-grey-darken-1">Regulates mRNA stability and translation efficiency</div>
                </div>
              </v-col>
              <v-col cols="12" sm="6" lg="6">
                <div class="why-mini-card h-100 pa-4">
                  <v-icon icon="mdi-magnet" color="primary" size="28" class="mb-3"></v-icon>
                  <div class="text-subtitle-2 font-weight-bold mb-1">miRNA Binding</div>
                  <div class="text-caption text-grey-darken-1">Impacts miRNA binding sites in the 3' UTR</div>
                </div>
              </v-col>
              <v-col cols="12" sm="6" lg="6">
                <div class="why-mini-card h-100 pa-4">
                  <v-icon icon="mdi-map-marker-radius" color="primary" size="28" class="mb-3"></v-icon>
                  <div class="text-subtitle-2 font-weight-bold mb-1">Localization</div>
                  <div class="text-caption text-grey-darken-1">Influences protein localization signals</div>
                </div>
              </v-col>
              <v-col cols="12" sm="6" lg="6">
                <div class="why-mini-card h-100 pa-4">
                  <v-icon icon="mdi-hospital-building" color="error" size="28" class="mb-3"></v-icon>
                  <div class="text-subtitle-2 font-weight-bold mb-1">Disease Impact</div>
                  <div class="text-caption text-grey-darken-1">Dysregulated in cancer and other diseases</div>
                </div>
              </v-col>
            </v-row>
          </v-col>
        </v-row>

        <!-- Key Insight Callout -->
        <v-row justify="center">
          <v-col cols="12">
            <div class="insight-callout pa-5 d-flex align-start mt-2">
              <div class="insight-icon mr-4">
                <v-icon icon="mdi-lightbulb-on" color="primary" size="32"></v-icon>
              </div>
              <div>
                <h4 class="text-subtitle-1 font-weight-bold mb-1" style="color: #0D7377">Key Insight</h4>
                <p class="text-body-2 text-grey-darken-1 mb-0">
                  Both isoforms share the same coding sequence (CDS) but differ in their 3' UTR length, 
                  profoundly affecting post-transcriptional regulation.
                </p>
              </div>
            </div>
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
import ApaAtlasIcon from '@/components/ApaAtlasIcon.vue'

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
  { label: 'Genes', displayValue: '23,933', icon: 'mdi-map-marker-path', color: '#0D7377', ringColor: 'rgba(13,115,119,0.12)' },
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

/* ── Info Section Redesign ────────────────────────────────── */
.info-section {
  background: rgb(var(--v-theme-background));
  position: relative;
}

/* Glassmorphism Cards */
.apa-diagram-card, .why-mini-card {
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(16px) saturate(150%);
  -webkit-backdrop-filter: blur(16px) saturate(150%);
  border: 1px solid rgba(255, 255, 255, 0.55);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06), 0 1px 4px rgba(0, 0, 0, 0.04);
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}

.why-mini-card:hover, .apa-diagram-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.09);
}

.v-theme--apaAtlasDarkTheme .apa-diagram-card,
.v-theme--apaAtlasDarkTheme .why-mini-card {
  background: rgba(24, 28, 37, 0.82);
  border: 1px solid rgba(255, 255, 255, 0.07);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.28);
}

/* Diagram Specifics */
.diagram-legend {
  display: flex;
  gap: 16px;
  font-size: 0.75rem;
  color: #666;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-color-box {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.bg-teal-gradient { background: linear-gradient(135deg, #0D7377, #14919B); }
.bg-utr-gradient { background: linear-gradient(90deg, #E94560, #FF8A65); }

.diagram-track-container {
  position: relative;
  padding-left: 12px;
  border-left: 2px dashed rgba(13, 115, 119, 0.2);
}

.diagram-visual {
  display: flex;
  align-items: center;
  position: relative;
  height: 24px;
}

.diagram-spine {
  width: 12px;
  height: 2px;
  background: rgba(13, 115, 119, 0.5);
  margin-left: -12px;
}

.diagram-exon {
  height: 16px;
  width: 48px;
  background: linear-gradient(135deg, #0D7377, #14919B);
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(13, 115, 119, 0.2);
  z-index: 2;
}

.diagram-intron {
  height: 2px;
  width: 32px;
  background: #14919B;
}

.diagram-utr {
  height: 10px;
  background: linear-gradient(90deg, #E94560, #FF8A65);
  border-radius: 0 4px 4px 0;
  box-shadow: 0 2px 4px rgba(233, 69, 96, 0.2);
  z-index: 1;
}

.diagram-utr.short { width: 40px; }
.diagram-utr.long { width: 140px; }

.diagram-pas-marker {
  color: #E94560;
  font-size: 14px;
  margin-left: 2px;
  margin-top: -12px;
  text-shadow: 0 2px 4px rgba(233, 69, 96, 0.3);
}

/* Insight Callout */
.insight-callout {
  background: linear-gradient(90deg, rgba(13, 115, 119, 0.08) 0%, rgba(20, 145, 155, 0.03) 100%);
  border-left: 4px solid #0D7377;
  border-radius: 0 16px 16px 0;
  backdrop-filter: blur(8px);
}

.v-theme--apaAtlasDarkTheme .insight-callout {
  background: linear-gradient(90deg, rgba(13, 115, 119, 0.15) 0%, rgba(20, 145, 155, 0.05) 100%);
}

.v-theme--apaAtlasDarkTheme .insight-callout h4 {
  color: #4DD0E1 !important;
}

.v-theme--apaAtlasDarkTheme .diagram-legend {
  color: #aaa;
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
