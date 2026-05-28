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
              <p class="hero-subtitle mb-8">
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
        <div class="text-center mb-12">
          <div class="section-eyebrow mb-2">The Database at a Glance</div>
          <h2 class="text-h4 font-weight-bold mb-3">Isoform-Resolved Polyadenylome Atlas</h2>
        </div>

        <!-- Stats: 5 glassmorphism cards -->
        <div class="stats-glass-row mb-14">
          <div v-for="stat in dbStats" :key="stat.label" class="stat-glass-card">
            <div class="stat-glass-number font-weight-black" :style="{ color: stat.color }">
              {{ stat.displayValue }}
            </div>
            <div class="stat-glass-label">{{ stat.label }}</div>
            <div class="stat-glass-desc">{{ stat.desc }}</div>
          </div>
        </div>

        <!-- Taxonomy Breakdown -->
        <div class="d-flex align-center justify-space-between flex-wrap ga-2 mb-6">
          <div>
            <h3 class="text-h6 font-weight-bold mb-1">Species Coverage</h3>
            <p class="text-caption text-grey-darken-1 mb-0">Grouped by taxonomic class · expanding continuously</p>
          </div>
          <v-chip color="primary" variant="tonal" size="small" prepend-icon="mdi-earth">
            {{ dbStats.find(s => s.label === 'Species').displayValue }} Species Covered
          </v-chip>
        </div>

        <v-row>
          <v-col v-for="group in taxonomyGroups" :key="group.class" cols="12" sm="6" lg="4">
            <div class="taxonomy-card pa-5">
              <!-- Group header -->
              <div class="d-flex align-center ga-3 mb-4">
                <div class="taxonomy-icon-badge" :style="{ background: `linear-gradient(135deg, ${group.color}, ${group.colorAlt})` }">
                  <v-icon :icon="group.icon" size="20" color="white"></v-icon>
                </div>
                <div class="flex-grow-1" style="min-width:0">
                  <div class="text-subtitle-1 font-weight-bold">{{ group.class }}</div>
                  <div class="text-caption text-grey-darken-1">{{ group.phylum }}</div>
                </div>
                <v-chip size="x-small" color="primary" variant="tonal">
                  {{ group.species.length }} sp.
                </v-chip>
              </div>
              <!-- Species rows -->
              <div v-for="sp in group.species" :key="sp.latin" class="taxonomy-species-row d-flex align-center ga-3">
                <div class="flex-grow-1" style="min-width:0">
                  <div class="text-body-2 font-weight-medium">{{ sp.name }}</div>
                  <div class="text-caption text-grey-darken-1 font-italic">{{ sp.latin }}</div>
                </div>
                <div class="text-right flex-shrink-0">
                  <div class="text-caption font-weight-bold" :style="{ color: group.color }">{{ sp.apaSites }}</div>
                  <div class="taxonomy-site-sublabel">APA sites</div>
                </div>
              </div>
              <!-- Footer: assembly + sample count chips -->
              <div class="taxonomy-footer mt-3 pt-3 d-flex flex-wrap ga-1 align-center">
                <v-chip v-for="sp in group.species" :key="sp.assembly"
                        size="x-small" variant="outlined" class="taxonomy-chip">
                  {{ sp.assembly }}
                </v-chip>
                <v-chip v-for="sp in group.species" :key="sp.name + '-samples'"
                        size="x-small" variant="tonal" color="primary" class="ml-1">
                  {{ sp.samples }} samples
                </v-chip>
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

// Database at a Glance — live counts from DB (updated 2026-04)
const dbStats = [
  { label: 'Species',     displayValue: '1',       desc: 'test species loaded',               color: '#2E7D32' },
  { label: 'Samples',     displayValue: '71',      desc: 'mouse tissue samples',              color: '#355C7D' },
  { label: 'Genes',       displayValue: '22,888',  desc: 'protein-coding & lncRNA loci',      color: '#0D7377' },
  { label: 'Transcripts', displayValue: '67,929',  desc: 'annotated isoforms',                color: '#14919B' },
  { label: 'PA Sites',    displayValue: '157,982', desc: 'polyadenylation clusters mapped',   color: '#B63F5A' },
]

const taxonomyGroups = [
  {
    icon: 'mdi-paw',
    class: 'Mammalia',
    phylum: 'Chordata',
    color: '#0D7377',
    colorAlt: '#14919B',
    species: [
      { name: 'Mouse', latin: 'Mus musculus', assembly: 'GRCm39', apaSites: '157,982', samples: 71 },
    ],
  },
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

.hero-subtitle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  max-width: 780px;
  color: rgba(255, 255, 255, 0.96);
  font-size: clamp(1.22rem, 2.3vw, 1.65rem);
  font-weight: 600;
  line-height: 1.45;
  letter-spacing: 0.01em;
  text-shadow: 0 2px 12px rgba(4, 47, 49, 0.55);
  background: rgba(4, 67, 70, 0.22);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 999px;
  padding: 8px 22px;
  backdrop-filter: blur(10px) saturate(140%);
  -webkit-backdrop-filter: blur(10px) saturate(140%);
}

.search-card {
  --home-search-radius: 22px;
  --home-search-inset: 8px;
  --home-search-inner-radius: calc(var(--home-search-radius) - var(--home-search-inset));
  background: rgba(255, 255, 255, 0.92) !important;
  backdrop-filter: blur(20px) saturate(160%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(160%) !important;
  border: 1px solid rgba(255, 255, 255, 0.70) !important;
  border-radius: var(--home-search-radius) !important;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.18), 0 2px 8px rgba(0, 0, 0, 0.10) !important;
  overflow: hidden;
}

.search-card :deep(.v-field) {
  border-radius: var(--home-search-inner-radius) !important;
  overflow: hidden;
}

.search-card :deep(.v-field__overlay),
.search-card :deep(.v-field__outline),
.search-card :deep(.v-field__loader) {
  border-radius: inherit !important;
}

.search-card :deep(.v-btn) {
  border-radius: var(--home-search-inner-radius) !important;
}

/* ── Section Eyebrow ──────────────────────────────────────── */
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
  border: 1px solid rgba(13, 115, 119, 0.18);
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
.bg-utr-gradient { background: linear-gradient(90deg, #B63F5A, #C9821A); }

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
  background: linear-gradient(90deg, #B63F5A, #C9821A);
  border-radius: 0 4px 4px 0;
  box-shadow: 0 2px 4px rgba(233, 69, 96, 0.2);
  z-index: 1;
}

.diagram-utr.short { width: 40px; }
.diagram-utr.long { width: 140px; }

.diagram-pas-marker {
  color: #B63F5A;
  font-size: 14px;
  margin-left: 2px;
  margin-top: -12px;
  text-shadow: 0 2px 4px rgba(233, 69, 96, 0.3);
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

/* ── Section Divider ──────────────────────────────────────── */
.section-divider {
  height: 1px;
  margin: 0 8%;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(13, 115, 119, 0.18) 20%,
    rgba(20, 145, 155, 0.32) 50%,
    rgba(13, 115, 119, 0.18) 80%,
    transparent 100%
  );
}

/* ── Glance Section ───────────────────────────────────────── */
.glance-section {
  background: linear-gradient(
    180deg,
    rgb(var(--v-theme-background)) 0%,
    rgba(13, 115, 119, 0.04) 50%,
    rgb(var(--v-theme-background)) 100%
  );
  position: relative;
}

/* ── Stats Glass Row ──────────────────────────────────────── */
.stats-glass-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

@media (max-width: 959px) {
  .stats-glass-row { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 599px) {
  .stats-glass-row { grid-template-columns: repeat(2, 1fr); }
}

.stat-glass-card {
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(16px) saturate(150%);
  -webkit-backdrop-filter: blur(16px) saturate(150%);
  border: 1px solid rgba(255, 255, 255, 0.55);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06), 0 1px 4px rgba(0, 0, 0, 0.04);
  padding: 28px 16px;
  text-align: center;
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}

.stat-glass-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.09);
}

.stat-glass-number {
  font-size: clamp(1.4rem, 2.8vw, 2.2rem);
  line-height: 1;
  overflow-wrap: break-word;
  word-break: break-all;
  margin-bottom: 8px;
}

.stat-glass-label {
  font-size: 0.88rem;
  font-weight: 600;
  margin-bottom: 4px;
  letter-spacing: 0.01em;
}

.stat-glass-desc {
  font-size: 0.72rem;
  color: rgba(0, 0, 0, 0.45);
  line-height: 1.35;
}

/* ── Taxonomy Cards ───────────────────────────────────────── */
.taxonomy-card {
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(16px) saturate(150%);
  -webkit-backdrop-filter: blur(16px) saturate(150%);
  border: 1px solid rgba(255, 255, 255, 0.55);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06), 0 1px 4px rgba(0, 0, 0, 0.04);
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}

.taxonomy-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.09);
}

.taxonomy-icon-badge {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.taxonomy-species-row {
  padding: 10px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.taxonomy-species-row:last-of-type {
  border-bottom: none;
}

.taxonomy-site-sublabel {
  font-size: 0.65rem;
  color: rgba(0, 0, 0, 0.38);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.taxonomy-footer {
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.taxonomy-chip {
  border-color: rgba(0, 0, 0, 0.18) !important;
  color: rgba(0, 0, 0, 0.54) !important;
  font-size: 0.70rem !important;
}
</style>
