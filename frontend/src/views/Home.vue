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
          <div class="section-eyebrow mb-2">What is Isoform-Level APA?</div>
          <h2 class="text-h4 font-weight-bold mb-3">One Gene · Multiple 3′ Ends</h2>
          <p class="text-body-1 text-grey-darken-1" style="max-width: 720px; margin: 0 auto;">
            A single gene produces multiple mRNA isoforms by selecting distinct 
            <strong>polyadenylation sites (PAS)</strong> in the 3′ UTR. These isoforms share the same 
            coding sequence but differ in 3′ UTR length — and therefore in their post-transcriptional regulatory landscape.
          </p>
        </div>
        
        <v-row justify="center" align="stretch" class="mb-6">
          <!-- Left Panel: Transcript Structure -->
          <v-col cols="12" lg="6" class="d-flex flex-column col-diagram">
            <div class="apa-diagram-card flex-grow-1 pa-6">
              <div class="d-flex justify-space-between align-center mb-6">
                <h3 class="text-h6 font-weight-bold">Same Gene · Two Distinct 3′ Ends</h3>
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
                  <div class="mb-3">
                    <span class="text-subtitle-2 font-weight-bold">Proximal PAS</span>
                  </div>
                  <div class="d-flex align-center gap-3">
                    <div class="diagram-visual flex-grow-1">
                      <div class="diagram-spine"></div>
                      <div class="diagram-exon"></div>
                      <div class="diagram-intron"></div>
                      <div class="diagram-exon"></div>
                      <div class="diagram-intron"></div>
                      <div class="diagram-exon"></div>
                      <div class="diagram-utr short"></div>
                      <div class="diagram-pas-marker">▼</div>
                    </div>
                    <v-chip size="x-small" color="primary" variant="tonal" class="flex-shrink-0">Short Isoform</v-chip>
                  </div>
                </div>

                <!-- Long Isoform -->
                <div class="diagram-track">
                  <div class="mb-3">
                    <span class="text-subtitle-2 font-weight-bold">Distal PAS</span>
                  </div>
                  <div class="d-flex align-center gap-3">
                    <div class="diagram-visual flex-grow-1">
                      <div class="diagram-spine"></div>
                      <div class="diagram-exon"></div>
                      <div class="diagram-intron"></div>
                      <div class="diagram-exon"></div>
                      <div class="diagram-intron"></div>
                      <div class="diagram-exon"></div>
                      <div class="diagram-utr long"></div>
                      <div class="diagram-pas-marker">▼</div>
                    </div>
                    <v-chip size="x-small" color="error" variant="tonal" class="flex-shrink-0">Long Isoform</v-chip>
                  </div>
                </div>
              </div>

              <div class="diagram-note mt-6 pt-5">
                <p class="text-caption text-grey-darken-1 mb-0">
                  Both isoforms encode the same protein. The longer 3′ UTR of the distal isoform,
                  however, harbors additional miRNA target sites and RNA-binding protein (RBP) motifs
                  that govern mRNA stability, localization, and translational output — regulatory
                  information invisible to gene-level expression analysis.
                </p>
              </div>
            </div>
          </v-col>
          
          <!-- Right Panel: Why APA Matters (2x2 Grid) -->
          <v-col cols="12" lg="6" class="d-flex flex-column col-why">
            <h3 class="text-h6 font-weight-bold mb-4 px-2">Why Isoform-Level APA Matters</h3>
            <v-row dense class="flex-grow-1">
              <v-col cols="12" sm="6" lg="6">
                <div class="why-mini-card h-100 pa-4">
                  <v-icon icon="mdi-chart-line" color="primary" size="28" class="mb-3"></v-icon>
                  <div class="text-subtitle-2 font-weight-bold mb-1">mRNA Stability</div>
                  <div class="text-caption text-grey-darken-1">Longer 3′ UTRs expose AU-rich elements that tune mRNA half-life and translation rate</div>
                </div>
              </v-col>
              <v-col cols="12" sm="6" lg="6">
                <div class="why-mini-card h-100 pa-4">
                  <v-icon icon="mdi-magnet" color="primary" size="28" class="mb-3"></v-icon>
                  <div class="text-subtitle-2 font-weight-bold mb-1">miRNA Escape</div>
                  <div class="text-caption text-grey-darken-1">Short isoforms lose miRNA binding sites, shielding oncogenes from repression in cancer</div>
                </div>
              </v-col>
              <v-col cols="12" sm="6" lg="6">
                <div class="why-mini-card h-100 pa-4">
                  <v-icon icon="mdi-map-marker-radius" color="primary" size="28" class="mb-3"></v-icon>
                  <div class="text-subtitle-2 font-weight-bold mb-1">Subcellular Targeting</div>
                  <div class="text-caption text-grey-darken-1">3′ UTR sequences direct mRNAs to specific compartments — dendrites, stress granules, and beyond</div>
                </div>
              </v-col>
              <v-col cols="12" sm="6" lg="6">
                <div class="why-mini-card h-100 pa-4">
                  <v-icon icon="mdi-hospital-building" color="error" size="28" class="mb-3"></v-icon>
                  <div class="text-subtitle-2 font-weight-bold mb-1">Disease Relevance</div>
                  <div class="text-caption text-grey-darken-1">APA dysregulation is a hallmark of cancer, neurodegeneration, and immune disorders</div>
                </div>
              </v-col>
            </v-row>
          </v-col>
        </v-row>

      </v-container>
    </section>

    <!-- ── Section Divider ──────────────────────────────────── -->
    <div class="section-divider" aria-hidden="true"></div>

    <!-- Database at a Glance -->
    <section class="glance-section py-16">
      <v-container>

        <!-- Header -->
        <div class="text-center mb-14">
          <div class="section-eyebrow-light mb-2">Live Database</div>
          <h2 class="text-h4 font-weight-bold text-white mb-3">The Database at a Glance</h2>
          <p class="glance-subtitle mb-0" style="max-width: 560px; margin: 0 auto;">
            Curated from high-throughput sequencing experiments across human and mouse transcriptomes.
          </p>
        </div>

        <!-- Stats Strip: unified dark grid -->
        <div class="stats-strip mb-12">
          <div v-for="stat in dbStats" :key="stat.label" class="stat-item">
            <div class="stat-item-number font-weight-black" :style="{ color: stat.lightColor }">
              {{ stat.displayValue }}
            </div>
            <div class="stat-item-label text-white font-weight-medium">{{ stat.label }}</div>
            <div class="stat-item-desc">{{ stat.desc }}</div>
          </div>
        </div>

        <!-- Coverage Cards -->
        <v-row justify="center" class="ga-5">
          <!-- Human -->
          <v-col cols="12" md="6">
            <div class="coverage-card pa-6">
              <div class="d-flex align-center ga-3 mb-6">
                <div class="coverage-species-badge coverage-badge--human">
                  <v-icon icon="mdi-human" size="22" color="white"></v-icon>
                </div>
                <div>
                  <div class="text-h6 font-weight-bold text-white">Homo sapiens</div>
                  <div class="coverage-genome-ref">GRCh38 · Bulk RNA-seq</div>
                </div>
              </div>
              <div class="coverage-stats-row mb-6">
                <div class="coverage-stat">
                  <div class="coverage-stat-num" style="color:#4DD0E1">77,784</div>
                  <div class="coverage-stat-lbl">APA Sites</div>
                </div>
                <div class="coverage-stat-divider"></div>
                <div class="coverage-stat">
                  <div class="coverage-stat-num" style="color:#80CBC4">3</div>
                  <div class="coverage-stat-lbl">Cell Lines</div>
                </div>
                <div class="coverage-stat-divider"></div>
                <div class="coverage-stat">
                  <div class="coverage-stat-num" style="color:#B2EBF2">~3.2</div>
                  <div class="coverage-stat-lbl">Sites / Gene</div>
                </div>
              </div>
              <div class="d-flex flex-wrap ga-2">
                <v-chip size="x-small" variant="outlined" class="coverage-chip">A549</v-chip>
                <v-chip size="x-small" variant="outlined" class="coverage-chip">HepG2</v-chip>
                <v-chip size="x-small" variant="outlined" class="coverage-chip">K562</v-chip>
              </div>
            </div>
          </v-col>

          <!-- Mouse -->
          <v-col cols="12" md="6">
            <div class="coverage-card pa-6">
              <div class="d-flex align-center ga-3 mb-6">
                <div class="coverage-species-badge coverage-badge--mouse">
                  <v-icon icon="mdi-rodent" size="22" color="white"></v-icon>
                </div>
                <div>
                  <div class="text-h6 font-weight-bold text-white">Mus musculus</div>
                  <div class="coverage-genome-ref">GRCm39 · Bulk RNA-seq</div>
                </div>
              </div>
              <div class="coverage-stats-row mb-6">
                <div class="coverage-stat">
                  <div class="coverage-stat-num" style="color:#4DD0E1">8,496</div>
                  <div class="coverage-stat-lbl">APA Sites</div>
                </div>
                <div class="coverage-stat-divider"></div>
                <div class="coverage-stat">
                  <div class="coverage-stat-num" style="color:#80CBC4">1</div>
                  <div class="coverage-stat-lbl">Tissue</div>
                </div>
                <div class="coverage-stat-divider"></div>
                <div class="coverage-stat">
                  <div class="coverage-stat-num" style="color:#B2EBF2">~3.5</div>
                  <div class="coverage-stat-lbl">Sites / Gene</div>
                </div>
              </div>
              <div class="d-flex flex-wrap ga-2">
                <v-chip size="x-small" variant="outlined" class="coverage-chip">Liver</v-chip>
                <v-chip size="x-small" variant="outlined" class="coverage-chip">GRCm39</v-chip>
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
  { label: 'Genes',       displayValue: '23,933', desc: 'protein-coding & lncRNA loci',   icon: 'mdi-map-marker-path',       color: '#0D7377', lightColor: '#4DD0E1', ringColor: 'rgba(13,115,119,0.12)' },
  { label: 'Transcripts', displayValue: '54,937', desc: 'annotated isoforms',              icon: 'mdi-format-list-bulleted',  color: '#14919B', lightColor: '#80CBC4', ringColor: 'rgba(20,145,155,0.12)' },
  { label: 'APA Sites',   displayValue: '86,280', desc: 'polyadenylation sites mapped',    icon: 'mdi-map-marker-multiple',   color: '#E94560', lightColor: '#FF8A80', ringColor: 'rgba(233,69,96,0.12)' },
  { label: 'Samples',     displayValue: '4',      desc: 'cell lines & tissue types',       icon: 'mdi-flask',                 color: '#5C6BC0', lightColor: '#9FA8DA', ringColor: 'rgba(92,107,192,0.12)' },
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

.diagram-note {
  border-top: 1px solid rgba(13, 115, 119, 0.18);
}

/* 6.4/12 = 53.33% — fractional column width for the diagram panel */
@media (min-width: 1280px) {
  .col-diagram {
    flex: 0 0 53.33%;
    max-width: 53.33%;
  }
  .col-why {
    flex: 0 0 46.67%;
    max-width: 46.67%;
  }
}

.v-theme--apaAtlasDarkTheme .diagram-note {
  border-top-color: rgba(77, 208, 225, 0.18);
}

/* ── Section Divider ──────────────────────────────────────── */
.section-divider {
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(13, 115, 119, 0.35) 20%,
    rgba(20, 145, 155, 0.55) 50%,
    rgba(13, 115, 119, 0.35) 80%,
    transparent 100%
  );
}

/* ── Glance Section (dark panel) ──────────────────────────── */
.glance-section {
  background: linear-gradient(160deg, #061518 0%, #091d28 55%, #0b1828 100%);
  position: relative;
}

.glance-subtitle {
  color: rgba(255, 255, 255, 0.55);
  font-size: 1rem;
  line-height: 1.6;
}

/* Eyebrow variant for dark backgrounds */
.section-eyebrow-light {
  display: inline-block;
  font-size: 0.80rem;
  font-weight: 700;
  letter-spacing: 0.13em;
  text-transform: uppercase;
  color: #4DD0E1;
  padding: 4px 14px;
  background: rgba(77, 208, 225, 0.12);
  border-radius: 20px;
}

/* ── Stats Strip ──────────────────────────────────────────── */
.stats-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 20px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.07);
}

@media (max-width: 599px) {
  .stats-strip { grid-template-columns: repeat(2, 1fr); }
}

.stat-item {
  background: rgba(255, 255, 255, 0.03);
  padding: 32px 20px;
  text-align: center;
  transition: background 0.2s ease;
}

.stat-item:hover {
  background: rgba(77, 208, 225, 0.06);
}

.stat-item-number {
  font-size: clamp(1.6rem, 3vw, 2.5rem);
  line-height: 1;
  overflow-wrap: break-word;
  word-break: break-all;
  margin-bottom: 8px;
}

.stat-item-label {
  font-size: 0.9rem;
  margin-bottom: 5px;
  letter-spacing: 0.01em;
}

.stat-item-desc {
  font-size: 0.73rem;
  color: rgba(255, 255, 255, 0.38);
  line-height: 1.35;
}

/* ── Coverage Cards ───────────────────────────────────────── */
.coverage-card {
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.09);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  transition: background 0.22s ease, border-color 0.22s ease;
}

.coverage-card:hover {
  background: rgba(77, 208, 225, 0.06);
  border-color: rgba(77, 208, 225, 0.28);
}

.coverage-species-badge {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.coverage-badge--human { background: linear-gradient(135deg, #0D7377, #14919B); }
.coverage-badge--mouse { background: linear-gradient(135deg, #004d40, #26A69A); }

.coverage-genome-ref {
  font-size: 0.78rem;
  color: rgba(255, 255, 255, 0.45);
  margin-top: 2px;
}

.coverage-stats-row {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 16px 0;
  border-top: 1px solid rgba(255, 255, 255, 0.07);
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
}

.coverage-stat {
  flex: 1;
  text-align: center;
}

.coverage-stat-num {
  font-size: clamp(1.2rem, 2.2vw, 1.9rem);
  font-weight: 900;
  line-height: 1.05;
  overflow-wrap: break-word;
  word-break: break-all;
}

.coverage-stat-lbl {
  font-size: 0.70rem;
  color: rgba(255, 255, 255, 0.42);
  margin-top: 4px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.coverage-stat-divider {
  width: 1px;
  height: 40px;
  background: rgba(255, 255, 255, 0.09);
  flex-shrink: 0;
}

.coverage-chip {
  border-color: rgba(255, 255, 255, 0.18) !important;
  color: rgba(255, 255, 255, 0.62) !important;
  font-size: 0.70rem !important;
}
}

</style>
