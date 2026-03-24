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

    <!-- Explore by Sample -->
    <section class="samples-section py-16 bg-grey-lighten-5">
      <v-container>
        <div class="text-center mb-12">
          <div class="section-eyebrow mb-2">Sample Coverage</div>
          <h2 class="text-h4 font-weight-bold mb-3">Explore by Sample</h2>
          <p class="text-body-1 text-grey-darken-1" style="max-width: 560px; margin: 0 auto;">
            APA landscapes profiled across cancer cell lines and primary tissue, capturing context-specific 3' end usage.
          </p>
        </div>

        <v-row>
          <v-col cols="12" sm="6" lg="3" v-for="sample in sampleProfiles" :key="sample.name">
            <div class="sample-profile-card pa-6 h-100" @click="browseSample(sample.name)" style="cursor: pointer;">
              <div class="sample-header d-flex align-center mb-4">
                <div class="sample-icon-wrap mr-3" :style="{ background: sample.gradient }">
                  <v-icon :icon="sample.icon" size="22" color="white"></v-icon>
                </div>
                <div>
                  <div class="text-h6 font-weight-bold">{{ sample.name }}</div>
                  <div class="text-caption text-grey">{{ sample.species }}</div>
                </div>
              </div>

              <div class="sample-apa-bar mb-4">
                <div class="d-flex justify-space-between mb-1">
                  <span class="text-caption text-grey">APA Sites</span>
                  <span class="text-caption font-weight-bold">{{ sample.apaCount.toLocaleString() }}</span>
                </div>
                <div class="apa-progress-track">
                  <div 
                    class="apa-progress-fill" 
                    :style="{ width: sample.barWidth + '%', background: sample.barColor }"
                  ></div>
                </div>
              </div>

              <p class="text-body-2 text-grey-darken-1 mb-4" style="line-height: 1.6;">{{ sample.description }}</p>

              <div class="d-flex flex-wrap ga-1">
                <v-chip v-for="tag in sample.tags" :key="tag" size="x-small" variant="tonal" :color="sample.tagColor">
                  {{ tag }}
                </v-chip>
              </div>

              <div class="sample-cta mt-4">
                <span class="text-caption text-primary font-weight-medium">
                  Browse {{ sample.name }} data
                  <v-icon icon="mdi-arrow-right" size="12" class="ml-1"></v-icon>
                </span>
              </div>
            </div>
          </v-col>
        </v-row>
      </v-container>
    </section>

    <!-- APA & Disease Highlights -->
    <section class="disease-section py-16">
      <v-container>
        <div class="text-center mb-12">
          <div class="section-eyebrow mb-2">Research Context</div>
          <h2 class="text-h4 font-weight-bold mb-3">APA Across the Genome</h2>
          <p class="text-body-1 text-grey-darken-1" style="max-width: 560px; margin: 0 auto;">
            Isoform-level APA analysis reveals regulatory complexity that gene-level studies miss.
          </p>
        </div>

        <v-row class="mb-8">
          <v-col cols="12" md="4" v-for="highlight in researchHighlights" :key="highlight.title">
            <div class="research-card pa-7 h-100">
              <div class="research-icon-wrap mb-5" :style="{ background: highlight.bgColor }">
                <v-icon :icon="highlight.icon" size="30" :color="highlight.iconColor"></v-icon>
              </div>
              <h3 class="text-h6 font-weight-bold mb-3">{{ highlight.title }}</h3>
              <p class="text-body-2 text-grey-darken-1" style="line-height: 1.7;">{{ highlight.body }}</p>
              <div class="research-stat mt-4 pa-3 rounded-lg" :style="{ background: highlight.statBg }">
                <div class="text-caption text-grey mb-1">{{ highlight.statLabel }}</div>
                <div class="text-h6 font-weight-bold" :style="{ color: highlight.iconColor }">{{ highlight.statValue }}</div>
              </div>
            </div>
          </v-col>
        </v-row>

        <!-- CTA Strip -->
        <div class="cta-strip pa-8 text-center rounded-xl">
          <h3 class="text-h5 font-weight-bold text-white mb-3">Ready to explore the APA landscape?</h3>
          <p class="text-body-1 mb-6" style="color: rgba(255,255,255,0.8);">
            Search across 86,280 APA sites in human and mouse transcriptomes.
          </p>
          <div class="d-flex justify-center ga-4 flex-wrap">
            <v-btn color="white" variant="flat" size="large" to="/search" class="cta-btn-primary">
              <v-icon start>mdi-magnify</v-icon>
              Start Browsing
            </v-btn>
            <v-btn color="white" variant="outlined" size="large" to="/download" class="cta-btn-secondary">
              <v-icon start>mdi-download</v-icon>
              Download Data
            </v-btn>
          </div>
        </div>
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

const browseSample = (sampleName) => {
  router.push({ path: '/search', query: { sample: sampleName } })
}

// Database at a Glance — static values from live DB
const dbStats = [
  { label: 'Genes', displayValue: '23,933', icon: 'mdi-dna', color: '#0D7377', ringColor: 'rgba(13,115,119,0.12)' },
  { label: 'Transcripts', displayValue: '54,937', icon: 'mdi-format-list-bulleted', color: '#14919B', ringColor: 'rgba(20,145,155,0.12)' },
  { label: 'APA Sites', displayValue: '86,280', icon: 'mdi-map-marker-multiple', color: '#E94560', ringColor: 'rgba(233,69,96,0.12)' },
  { label: 'Samples', displayValue: '4', icon: 'mdi-flask', color: '#5C6BC0', ringColor: 'rgba(92,107,192,0.12)' },
]

// Sample profiles with biological context
const maxApa = 37679
const sampleProfiles = [
  {
    name: 'A549',
    species: 'Human · Lung carcinoma',
    apaCount: 30451,
    barWidth: Math.round((30451 / maxApa) * 100),
    barColor: 'linear-gradient(90deg, #0D7377, #14919B)',
    gradient: 'linear-gradient(135deg, #0D7377, #14919B)',
    icon: 'mdi-lungs',
    description: 'Non-small cell lung carcinoma line derived from a 58-year-old Caucasian male. Extensively used in APA regulation and alternative 3\' end processing studies.',
    tags: ['Lung cancer', 'NSCLC', 'GRCh38'],
    tagColor: 'primary',
  },
  {
    name: 'HepG2',
    species: 'Human · Hepatocellular carcinoma',
    apaCount: 36016,
    barWidth: Math.round((36016 / maxApa) * 100),
    barColor: 'linear-gradient(90deg, #AB47BC, #7B1FA2)',
    gradient: 'linear-gradient(135deg, #AB47BC, #7B1FA2)',
    icon: 'mdi-water',
    description: 'Hepatocellular carcinoma line widely used as a liver metabolism model. Exhibits tissue-specific 3\' UTR regulation tied to metabolic gene expression.',
    tags: ['Liver cancer', 'HCC', 'GRCh38'],
    tagColor: 'purple',
  },
  {
    name: 'K562',
    species: 'Human · Chronic myelogenous leukemia',
    apaCount: 37679,
    barWidth: 100,
    barColor: 'linear-gradient(90deg, #E94560, #C62828)',
    gradient: 'linear-gradient(135deg, #E94560, #C62828)',
    icon: 'mdi-water-outline',
    description: 'CML blast crisis line with the BCR-ABL1 fusion. One of the most APA-profiled human cell lines, providing a reference for hematopoietic isoform regulation.',
    tags: ['Leukemia', 'CML', 'GRCh38'],
    tagColor: 'error',
  },
  {
    name: 'Liver',
    species: 'Mouse · Primary tissue',
    apaCount: 8496,
    barWidth: Math.round((8496 / maxApa) * 100),
    barColor: 'linear-gradient(90deg, #26A69A, #00695C)',
    gradient: 'linear-gradient(135deg, #26A69A, #00695C)',
    icon: 'mdi-rodent',
    description: 'Primary mouse liver tissue (Mus musculus, GRCm39). Offers a non-cancerous reference for comparing tissue-specific APA patterns against human cell lines.',
    tags: ['Primary tissue', 'Mouse', 'GRCm39'],
    tagColor: 'teal',
  },
]

// Research Highlights
const researchHighlights = [
  {
    title: '3\' UTR Isoform Diversity',
    icon: 'mdi-transit-connection-variant',
    iconColor: '#0D7377',
    bgColor: 'rgba(13,115,119,0.10)',
    statBg: 'rgba(13,115,119,0.06)',
    statLabel: 'Transcripts with multiple APA sites',
    statValue: '~57% of transcripts',
    body: 'Alternative polyadenylation generates 3\' UTR isoforms that differ in length and regulatory element content — miRNA binding sites, RBP motifs, and stability signals — without changing protein sequence.',
  },
  {
    title: 'Cancer Rewiring of 3\' Ends',
    icon: 'mdi-alert-circle-outline',
    iconColor: '#E94560',
    bgColor: 'rgba(233,69,96,0.10)',
    statBg: 'rgba(233,69,96,0.06)',
    statLabel: 'Human APA sites catalogued',
    statValue: '77,784 sites',
    body: 'Cancer cells broadly shift toward proximal PAS usage, shortening 3\' UTRs to escape miRNA suppression and enhance oncogene translation. ApaAtlas profiles this shift in A549, HepG2 and K562.',
  },
  {
    title: 'Cross-Species Conservation',
    icon: 'mdi-vector-intersection',
    iconColor: '#5C6BC0',
    bgColor: 'rgba(92,107,192,0.10)',
    statBg: 'rgba(92,107,192,0.06)',
    statLabel: 'Mouse APA sites (liver)',
    statValue: '8,496 sites',
    body: 'Comparing human cell-line APA against mouse liver tissue enables identification of evolutionarily conserved polyadenylation signals and tissue-specific isoform switching across species.',
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
  font-size: 12px;
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
  font-size: 12px;
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
.glance-section,
.disease-section {
  background: rgb(var(--v-theme-background));
}

.samples-section {
  background: #E8ECF0;
}

.v-theme--apaAtlasDarkTheme .samples-section {
  background: #13161E;
}

/* ── Section eyebrow ──────────────────────────────────────── */
.section-eyebrow {
  display: inline-block;
  font-size: 0.71rem;
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
  font-size: 2rem;
  line-height: 1.1;
}

.stat-label {
  font-size: 0.82rem;
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

/* ── Sample cards ─────────────────────────────────────────── */
.sample-profile-card {
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(14px) saturate(150%);
  -webkit-backdrop-filter: blur(14px) saturate(150%);
  border: 1px solid rgba(255, 255, 255, 0.58);
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.06);
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}

.sample-profile-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.10);
}

.v-theme--apaAtlasDarkTheme .sample-profile-card {
  background: rgba(24, 28, 37, 0.82);
  border: 1px solid rgba(255, 255, 255, 0.07);
}

.sample-icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.apa-progress-track {
  height: 5px;
  border-radius: 3px;
  background: rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.v-theme--apaAtlasDarkTheme .apa-progress-track {
  background: rgba(255, 255, 255, 0.10);
}

.apa-progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 1s ease;
}

.sample-cta {
  border-top: 1px solid rgba(0, 0, 0, 0.07);
  padding-top: 12px;
}

.v-theme--apaAtlasDarkTheme .sample-cta {
  border-top-color: rgba(255, 255, 255, 0.07);
}

/* ── Research cards ───────────────────────────────────────── */
.research-card {
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(16px) saturate(150%);
  -webkit-backdrop-filter: blur(16px) saturate(150%);
  border: 1px solid rgba(255, 255, 255, 0.55);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}

.research-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 14px 36px rgba(0, 0, 0, 0.10);
}

.v-theme--apaAtlasDarkTheme .research-card {
  background: rgba(24, 28, 37, 0.82);
  border: 1px solid rgba(255, 255, 255, 0.07);
}

.research-icon-wrap {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.research-stat { border-radius: 10px; }

/* ── CTA strip ────────────────────────────────────────────── */
.cta-strip {
  background: linear-gradient(135deg, #0a4f53 0%, #0D7377 50%, #1a2744 100%);
  box-shadow: 0 8px 40px rgba(13, 115, 119, 0.25);
}

.cta-btn-primary {
  color: #0D7377 !important;
  font-weight: 700;
}

.cta-btn-secondary {
  border-color: rgba(255, 255, 255, 0.55) !important;
  color: white !important;
}

.cta-btn-secondary:hover {
  background: rgba(255, 255, 255, 0.10) !important;
}
</style>
