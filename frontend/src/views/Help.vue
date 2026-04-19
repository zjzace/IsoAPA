<template>
  <div class="help-page">
    <!-- 1. Hero Section -->
    <section class="hero-section">
      <div class="hero-bg"></div>
      <v-container class="hero-content">
        <h1 class="text-h3 font-weight-bold text-white mb-2">User Guide & Documentation</h1>
        <p class="text-h6 text-white mb-6 opacity-90">Everything you need to explore isoform-level APA data</p>
        
        <div class="d-flex flex-wrap gap-4">
          <v-chip class="mr-2" variant="outlined" color="white" style="background: rgba(255,255,255,0.9);">
            <strong style="color: #0D7377;">Quick Start</strong>
          </v-chip>
          <v-chip class="mr-2" variant="outlined" color="white" style="background: rgba(255,255,255,0.9);">
            <strong style="color: #0D7377;">Feature Guides</strong>
          </v-chip>
          <v-chip class="mr-2" variant="outlined" color="white" style="background: rgba(255,255,255,0.9);">
            <strong style="color: #0D7377;">FAQ</strong>
          </v-chip>
          <v-chip variant="outlined" color="white" style="background: rgba(255,255,255,0.9);">
            <strong style="color: #0D7377;">Glossary</strong>
          </v-chip>
        </div>
      </v-container>
    </section>

    <!-- Main Content -->
    <v-container class="py-12">
      <!-- 2. Jump Navigation Cards -->
      <div class="jump-nav-row">
        <div 
          v-for="item in jumpLinks" 
          :key="item.id"
          class="jump-card" 
          @click="scrollTo(item.id)"
        >
          <div class="jump-card-icon" :style="{ background: item.gradient }">
            <v-icon :icon="item.icon" size="22" color="white"></v-icon>
          </div>
          <div>
            <div class="jump-card-title">{{ item.title }}</div>
            <div class="jump-card-desc">{{ item.sub }}</div>
          </div>
        </div>
      </div>

      <!-- 3. Quick Start Section -->
      <section id="getting-started" class="content-section">
        <div class="section-eyebrow">01 · Quick Start</div>
        <h2 class="section-heading mb-6">Get up and running in 4 steps</h2>
        
        <div class="steps-grid">
          <div v-for="(step, index) in steps" :key="index" class="glass-card step-card">
            <div class="step-number">{{ String(index + 1).padStart(2, '0') }}</div>
            <div class="step-icon-badge" :style="{ background: step.gradient }">
              <v-icon :icon="step.icon" size="28" color="white"></v-icon>
            </div>
            <h3 class="step-title">{{ step.title }}</h3>
            <p class="step-desc">{{ step.desc }}</p>
            <v-btn v-if="step.link" :to="step.link" variant="tonal" color="#0D7377" class="mt-auto" rounded="pill" flat>
              {{ step.linkLabel }}
            </v-btn>
          </div>
        </div>
      </section>

      <!-- 4. Feature Guides Section -->
      <section id="features" class="content-section">
        <div class="section-eyebrow">02 · Feature Guides</div>
        <h2 class="section-heading mb-6">How each feature works</h2>
        
        <div class="accordion-container">
          <div v-for="(guide, index) in guides" :key="index" class="glass-card accordion-item" :class="{ 'is-open': openGuide === index }">
            <button class="accordion-header" @click="openGuide = openGuide === index ? null : index">
              <div class="d-flex align-center">
                <div class="accordion-icon" :style="{ background: guide.gradient }">
                  <v-icon :icon="guide.icon" size="20" color="white"></v-icon>
                </div>
                <h3 class="accordion-title">{{ guide.title }}</h3>
              </div>
              <v-icon :icon="openGuide === index ? 'mdi-chevron-up' : 'mdi-chevron-down'" color="#64748b"></v-icon>
            </button>
            
            <v-expand-transition>
              <div v-if="openGuide === index" class="accordion-content">
                <!-- Guide 0 — Search & Filter -->
                <template v-if="index === 0">
                  <p class="guide-p">ApaAtlas supports four search dimensions — combine any to narrow results.</p>
                  <div class="info-tiles-grid">
                    <div class="info-tile">
                      <div class="tile-title">Gene Name</div>
                      <div class="tile-desc">Enter a symbol (GAPDH, ACTB, ARF5). Partial matches are supported and autocomplete assists as you type.</div>
                    </div>
                    <div class="info-tile">
                      <div class="tile-title">Transcript ID</div>
                      <div class="tile-desc">Use an Ensembl transcript ID (ENST00000000233) for exact single-transcript lookup.</div>
                    </div>
                    <div class="info-tile">
                      <div class="tile-title">Sample / Cell Line</div>
                      <div class="tile-desc">Filter by sample name (A549, HepG2, K562) to see tissue-specific APA patterns.</div>
                    </div>
                    <div class="info-tile">
                      <div class="tile-title">Species</div>
                      <div class="tile-desc">Select from available species to constrain the search scope when the database spans multiple organisms.</div>
                    </div>
                  </div>
                  <div class="tip-box">
                    <v-icon icon="mdi-lightbulb-on-outline" color="#0D7377" class="mr-2"></v-icon>
                    <strong>Tip:</strong> The search bar on the home page supports live autocomplete — results appear as you type.
                  </div>
                </template>

                <!-- Guide 1 — Locus Detail View -->
                <template v-if="index === 1">
                  <p class="guide-p">Click any search result to open the full Locus Detail page for that transcript. Four analysis panels are available:</p>
                  <div class="guide-rows">
                    <div class="guide-row">
                      <v-icon icon="mdi-dna" color="#5C6BC0" class="mr-3"></v-icon>
                      <div><strong>Genome Browser</strong> — Exon/intron/UTR structure with PA site markers overlaid on the transcript model.</div>
                    </div>
                    <div class="guide-row">
                      <v-icon icon="mdi-chart-bar" color="#5C6BC0" class="mr-3"></v-icon>
                      <div><strong>Site Distribution</strong> — Relative abundance of each PA site across all available samples.</div>
                    </div>
                    <div class="guide-row">
                      <v-icon icon="mdi-molecule" color="#5C6BC0" class="mr-3"></v-icon>
                      <div><strong>UTR Composition</strong> — GC%, AU-rich element (ATTTA pentamer) density, and dinucleotide frequencies for each site's 3' UTR region.</div>
                    </div>
                    <div class="guide-row">
                      <v-icon icon="mdi-account-search" color="#5C6BC0" class="mr-3"></v-icon>
                      <div><strong>RBP Motifs</strong> — Known RNA-binding protein binding site scanner (HuR, TTP, CPEB1, FMR1, PABPC1 and more).</div>
                    </div>
                  </div>
                  <v-table density="compact" class="metrics-table mt-4">
                    <tbody>
                      <tr>
                        <td><strong>Site Position</strong></td>
                        <td class="text-grey-darken-1">Genomic coordinate of the cleavage site</td>
                      </tr>
                      <tr>
                        <td><strong>Abundance</strong></td>
                        <td class="text-grey-darken-1">Fraction of reads using this site vs. all sites for this transcript</td>
                      </tr>
                      <tr>
                        <td><strong>Read Count</strong></td>
                        <td class="text-grey-darken-1">Absolute number of supporting sequencing reads</td>
                      </tr>
                    </tbody>
                  </v-table>
                </template>

                <!-- Guide 2 — Gene Detail View -->
                <template v-if="index === 2">
                  <p class="guide-p">Click any gene name in the app to open its Gene Detail page.</p>
                  <ul class="guide-ul">
                    <li>Lists all transcript isoforms for the gene with per-isoform PA site counts.</li>
                    <li>Click any transcript row to jump directly to its full Locus Detail page.</li>
                    <li>Genes with high isoform diversity are highlighted on the Statistics page leaderboard.</li>
                  </ul>
                  <div class="tip-box">
                    <v-icon icon="mdi-lightbulb-on-outline" color="#0D7377" class="mr-2"></v-icon>
                    <strong>Tip:</strong> Use the Statistics → Top Genes Leaderboard to find genes with the most PA sites — each entry links directly to its Gene Detail page.
                  </div>
                </template>

                <!-- Guide 3 — Statistics Dashboard -->
                <template v-if="index === 3">
                  <p class="guide-p">The Statistics page presents a data-story view of the entire database.</p>
                  <div class="guide-rows">
                    <div class="guide-row">
                      <div class="guide-row-bullet"></div>
                      <div><strong>Insight Banners</strong> — Key derived ratios: avg PA sites per isoform, % of isoforms with 2+ PA sites.</div>
                    </div>
                    <div class="guide-row">
                      <div class="guide-row-bullet"></div>
                      <div><strong>Data Hierarchy Flow</strong> — Visual chain showing average gene → isoform → PA site counts.</div>
                    </div>
                    <div class="guide-row">
                      <div class="guide-row-bullet"></div>
                      <div><strong>PA Site Multiplicity</strong> — Histogram bucketing isoforms by their number of PA sites (1, 2, 3, 4, 5+).</div>
                    </div>
                    <div class="guide-row">
                      <div class="guide-row-bullet"></div>
                      <div><strong>Species Richness</strong> — Horizontal bars showing PA site count per species, sorted by richness.</div>
                    </div>
                    <div class="guide-row">
                      <div class="guide-row-bullet"></div>
                      <div><strong>Top Genes Leaderboard</strong> — Genes ranked by total PA sites with gold/silver/bronze medals; each entry links to its Gene Detail page.</div>
                    </div>
                  </div>
                </template>

                <!-- Guide 4 — Download Options -->
                <template v-if="index === 4">
                  <p class="guide-p">Three distinct data products are available on the Download page.</p>
                  <div class="mini-cards-grid">
                    <div class="mini-card">
                      <div class="mini-card-title">PA Sites (CSV / TSV)</div>
                      <div class="mini-card-desc">Full annotated table — gene, transcript, site position, read count, abundance, sample.</div>
                    </div>
                    <div class="mini-card">
                      <div class="mini-card-title">Genome Browser BED</div>
                      <div class="mini-card-desc">BED6 format — ready to load in IGV, UCSC Genome Browser, or JBrowse.</div>
                    </div>
                    <div class="mini-card">
                      <div class="mini-card-title">Sample Abundance Matrix</div>
                      <div class="mini-card-desc">PA site × sample count matrix (TSV) — directly usable with DaPars, QAPA, or DEXSeq.</div>
                    </div>
                  </div>
                  <p class="guide-p mt-4 text-body-2">Use the species scope selector to filter by organism. All three datasets are accessible via browser download or the REST API (cURL, Python, R examples on the Download page).</p>
                </template>

              </div>
            </v-expand-transition>
          </div>
        </div>
      </section>

      <!-- 5. FAQ Section -->
      <section id="faq" class="content-section">
        <div class="section-eyebrow">03 · FAQ</div>
        <h2 class="section-heading mb-6">Frequently asked questions</h2>
        
        <div class="accordion-container">
          <div v-for="(faq, index) in faqs" :key="index" class="glass-card faq-item">
            <button class="faq-header" @click="openFaq = openFaq === index ? null : index">
              <div class="faq-question">{{ faq.q }}</div>
              <div class="faq-icon-wrapper">
                <v-icon :icon="openFaq === index ? 'mdi-minus' : 'mdi-plus'" color="#14919B" size="20"></v-icon>
              </div>
            </button>
            <v-expand-transition>
              <div v-if="openFaq === index" class="faq-content">
                <p>{{ faq.a }}</p>
              </div>
            </v-expand-transition>
          </div>
        </div>
      </section>

      <!-- 6. Glossary Section -->
      <section id="glossary" class="content-section">
        <div class="section-eyebrow">04 · Glossary</div>
        <h2 class="section-heading mb-6">Key terms & definitions</h2>
        
        <div class="glossary-grid">
          <div v-for="(item, index) in glossary" :key="index" class="glass-card glossary-card">
            <div class="glossary-term">{{ item.term }}</div>
            <div class="glossary-desc">{{ item.desc }}</div>
          </div>
        </div>
      </section>

      <!-- 7. Contact Section -->
      <section id="contact" class="content-section">
        <div class="section-eyebrow">05 · Contact</div>
        <h2 class="section-heading mb-6">Get in touch</h2>
        
        <div class="contact-card">
          <div class="contact-left">
            <h3 class="contact-heading">Questions or feedback?</h3>
            <p class="contact-sub">We welcome bug reports, feature requests, and general questions about ApaAtlas.</p>
            <a href="mailto:tf.chan@cuhk.edu.hk" class="contact-email-btn">
              <v-icon icon="mdi-email-outline" size="20" class="mr-2"></v-icon>
              tf.chan@cuhk.edu.hk
            </a>
          </div>
          <div class="contact-right">
            <div class="contact-tile">
              <div class="contact-tile-icon"><v-icon icon="mdi-bug-outline" color="#0D7377"></v-icon></div>
              <div>
                <div class="contact-tile-title">Report a Bug</div>
                <div class="contact-tile-desc">Found incorrect data or a broken feature? Send us details and we'll fix it.</div>
              </div>
            </div>
            <div class="contact-tile">
              <div class="contact-tile-icon"><v-icon icon="mdi-lightbulb-outline" color="#0D7377"></v-icon></div>
              <div>
                <div class="contact-tile-title">Feature Request</div>
                <div class="contact-tile-desc">Suggest a new analysis type, species, or visualization.</div>
              </div>
            </div>
          </div>
        </div>
      </section>

    </v-container>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const openGuide = ref(null)
const openFaq = ref(null)

const scrollTo = (id) => {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
}

const jumpLinks = [
  { id: 'getting-started', icon: 'mdi-rocket-launch', gradient: 'linear-gradient(135deg,#0D7377,#14919B)', title: 'Quick Start', sub: '4-step guide' },
  { id: 'features', icon: 'mdi-book-open-variant', gradient: 'linear-gradient(135deg,#5C6BC0,#7986CB)', title: 'Feature Guides', sub: 'Detailed how-tos' },
  { id: 'faq', icon: 'mdi-help-circle-outline', gradient: 'linear-gradient(135deg,#2E7D32,#388E3C)', title: 'FAQ', sub: 'Common questions' },
  { id: 'glossary', icon: 'mdi-book-alphabet', gradient: 'linear-gradient(135deg,#E65100,#EF6C00)', title: 'Glossary', sub: 'Key terms' }
]

const steps = [
  { 
    icon: 'mdi-magnify', 
    gradient: 'linear-gradient(135deg,#0D7377,#14919B)', 
    title: 'Search for a Gene or Transcript', 
    desc: 'Enter a gene symbol (GAPDH, ACTB) or Ensembl transcript ID. Autocomplete helps narrow your query.', 
    link: '/search', 
    linkLabel: 'Open Search' 
  },
  { 
    icon: 'mdi-table-eye', 
    gradient: 'linear-gradient(135deg,#2E7D32,#388E3C)', 
    title: 'Browse Results', 
    desc: 'Scan the results table and click any row to open the full Locus Detail page for that transcript.', 
    link: null, 
    linkLabel: null 
  },
  { 
    icon: 'mdi-chart-bar', 
    gradient: 'linear-gradient(135deg,#5C6BC0,#7986CB)', 
    title: 'Inspect APA Sites', 
    desc: 'Explore the genome browser, sample abundance charts, UTR composition, and RBP motif scanner.', 
    link: null, 
    linkLabel: null 
  },
  { 
    icon: 'mdi-download', 
    gradient: 'linear-gradient(135deg,#E65100,#EF6C00)', 
    title: 'Download Data', 
    desc: 'Export PA sites as CSV/TSV, a BED genome track, or a sample abundance matrix for downstream analysis.', 
    link: '/download', 
    linkLabel: 'Go to Download' 
  }
]

const guides = [
  { title: 'Search & Filter', icon: 'mdi-magnify', gradient: 'linear-gradient(135deg,#0D7377,#14919B)' },
  { title: 'Locus Detail View', icon: 'mdi-eye-outline', gradient: 'linear-gradient(135deg,#5C6BC0,#7986CB)' },
  { title: 'Gene Detail View', icon: 'mdi-dna', gradient: 'linear-gradient(135deg,#2E7D32,#388E3C)' },
  { title: 'Statistics Dashboard', icon: 'mdi-chart-line', gradient: 'linear-gradient(135deg,#AD1457,#E91E63)' },
  { title: 'Download Options', icon: 'mdi-download', gradient: 'linear-gradient(135deg,#E65100,#EF6C00)' }
]

const faqs = [
  { 
    q: 'What is Alternative Polyadenylation (APA)?', 
    a: 'APA is a post-transcriptional mechanism where the same pre-mRNA is cleaved and polyadenylated at different sites, producing isoforms with varying 3′ UTR lengths. This affects mRNA stability, translational efficiency, and sub-cellular localization.' 
  },
  { 
    q: 'What makes ApaAtlas isoform-level?', 
    a: 'Most APA databases aggregate PA sites at the gene level. ApaAtlas tracks every PA site individually per transcript isoform — so a gene with 10 isoforms maintains separate PA site records for each, preserving isoform-specific regulatory information.' 
  },
  { 
    q: 'What data sources are used?', 
    a: 'ApaAtlas integrates long-read transcriptomic data derived from Oxford Nanopore Technologies (ONT) direct RNA sequencing and Pacific Biosciences (PacBio) Iso-Seq platforms. These datasets encompass a diverse collection of human and multi-species cell lines and tissues, enabling high-resolution, isoform-level identification of polyadenylation sites. All transcript coordinates are anchored to NCBI/RefSeq reference annotations.' 
  },
  { 
    q: 'How is site abundance calculated?', 
    a: 'Abundance = (reads at a specific PA site) ÷ (total reads at all PA sites for that transcript) × 100%. It represents the fractional usage of each cleavage site within a transcript in a given sample.' 
  },
  { 
    q: 'Can I use ApaAtlas data in publications?', 
    a: 'Yes. ApaAtlas data is freely available for research and publication. Please cite our database when using it in your work.' 
  },
  { 
    q: 'What do \'proximal\' and \'distal\' PAS mean?', 
    a: 'Proximal PAS is the polyadenylation site closest to the stop codon, producing a shorter 3′ UTR (UTR shortening). Distal PAS is farthest from the stop codon, producing a longer 3′ UTR (UTR lengthening). Cells dynamically shift between these under stress, development, or disease conditions.' 
  }
]

const glossary = [
  { term: 'APA', desc: 'Alternative Polyadenylation — a mechanism producing multiple mRNA isoforms with different 3′ UTR lengths' },
  { term: 'PAS', desc: 'Polyadenylation Signal — hexamer sequence (typically AATAAA) that marks the cleavage and polyadenylation site' },
  { term: '3′ UTR', desc: '3′ Untranslated Region — mRNA region downstream of the stop codon; regulates stability, translation, and localization' },
  { term: 'Proximal PAS', desc: 'Polyadenylation site closest to the coding region; its use produces shorter 3′ UTRs' },
  { term: 'Distal PAS', desc: 'Polyadenylation site farthest from the coding region; its use produces longer 3′ UTRs' },
  { term: 'Abundance', desc: 'Relative usage of an APA site as a fraction of all PA site reads for a given transcript in a sample' }
]
</script>

<style scoped>
.help-page {
  min-height: 100vh;
  background-color: #f8fafc;
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
@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
.hero-content {
  position: relative;
  z-index: 1;
  padding: 48px 0 56px;
}

.section-eyebrow {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #14919B;
  margin-bottom: 4px;
}
.section-heading {
  font-size: 1.75rem;
  font-weight: 800;
  color: #1e293b;
}

.content-section {
  margin-bottom: 80px;
}

.glass-card {
  background: rgba(255, 255, 255, 0.80);
  backdrop-filter: blur(16px) saturate(150%);
  -webkit-backdrop-filter: blur(16px) saturate(150%);
  border: 1px solid rgba(255, 255, 255, 0.55);
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}

.jump-nav-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 80px;
}
@media (max-width: 960px) {
  .jump-nav-row { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .jump-nav-row { grid-template-columns: 1fr; }
}
.jump-card {
  background: rgba(255, 255, 255, 0.80);
  backdrop-filter: blur(16px) saturate(150%);
  -webkit-backdrop-filter: blur(16px) saturate(150%);
  border: 1px solid rgba(255, 255, 255, 0.55);
  border-radius: 20px;
  padding: 20px;
  cursor: pointer;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  display: flex;
  align-items: center;
  gap: 16px;
}
.jump-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(13,115,119,0.12);
}
.jump-card-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.jump-card-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 2px;
}
.jump-card-desc {
  font-size: 0.8rem;
  color: #64748b;
}

.steps-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}
@media (max-width: 1024px) {
  .steps-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .steps-grid { grid-template-columns: 1fr; }
}
.step-card {
  padding: 32px 24px 24px;
  position: relative;
  display: flex;
  flex-direction: column;
}
.step-number {
  position: absolute;
  top: 16px;
  right: 20px;
  font-size: 3.5rem;
  font-weight: 900;
  color: rgba(20, 145, 155, 0.08);
  line-height: 1;
}
.step-icon-badge {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.step-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 12px;
  line-height: 1.3;
}
.step-desc {
  font-size: 0.88rem;
  color: #64748b;
  line-height: 1.6;
  margin-bottom: 24px;
}

.accordion-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.accordion-item {
  transition: all 0.3s ease;
  overflow: hidden;
}
.accordion-item.is-open {
  border-left: 3px solid #14919B;
}
.accordion-header {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  background: transparent;
  border: none;
  cursor: pointer;
  text-align: left;
}
.accordion-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.accordion-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}
.accordion-content {
  padding: 0 24px 24px 76px;
}
@media (max-width: 600px) {
  .accordion-content { padding: 0 20px 20px 20px; }
}

.guide-p {
  font-size: 0.95rem;
  color: #475569;
  line-height: 1.6;
  margin-bottom: 16px;
}
.info-tiles-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
@media (max-width: 768px) {
  .info-tiles-grid { grid-template-columns: 1fr; }
}
.info-tile {
  background: rgba(248, 250, 252, 0.6);
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 12px;
  padding: 16px;
}
.tile-title {
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 6px;
  font-size: 0.95rem;
}
.tile-desc {
  font-size: 0.85rem;
  color: #64748b;
  line-height: 1.5;
}
.tip-box {
  background: rgba(240, 253, 250, 0.8);
  border: 1px solid rgba(20, 145, 155, 0.2);
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 0.9rem;
  color: #0f172a;
  display: flex;
  align-items: flex-start;
}
.guide-rows {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.guide-row {
  display: flex;
  align-items: flex-start;
  font-size: 0.9rem;
  color: #475569;
  line-height: 1.5;
}
.guide-row-bullet {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #14919B;
  margin-top: 8px;
  margin-right: 12px;
  flex-shrink: 0;
}
.guide-ul {
  padding-left: 24px;
  margin-bottom: 16px;
  color: #475569;
  font-size: 0.95rem;
  line-height: 1.6;
}
.guide-ul li { margin-bottom: 8px; }
.metrics-table {
  background: rgba(248, 250, 252, 0.5) !important;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
}
.metrics-table td {
  font-size: 0.85rem !important;
  border-bottom: 1px solid #f1f5f9 !important;
}
.mini-cards-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
@media (max-width: 768px) {
  .mini-cards-grid { grid-template-columns: 1fr; }
}
.mini-card {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}
.mini-card-title {
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 6px;
  font-size: 0.95rem;
}
.mini-card-desc {
  font-size: 0.85rem;
  color: #64748b;
  line-height: 1.5;
}

.faq-item {
  overflow: hidden;
}
.faq-header {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  background: transparent;
  border: none;
  cursor: pointer;
  text-align: left;
}
.faq-question {
  font-size: 1.05rem;
  font-weight: 700;
  color: #0D7377;
  padding-right: 16px;
}
.faq-icon-wrapper {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(20, 145, 155, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}
.faq-content {
  padding: 0 24px 20px 24px;
  font-size: 0.95rem;
  color: #475569;
  line-height: 1.6;
}

.glossary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
@media (max-width: 960px) {
  .glossary-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .glossary-grid { grid-template-columns: 1fr; }
}
.glossary-card {
  padding: 20px;
}
.glossary-term {
  display: inline-block;
  background: rgba(20, 145, 155, 0.1);
  color: #0D7377;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 700;
  margin-bottom: 12px;
}
.glossary-desc {
  font-size: 0.9rem;
  color: #475569;
  line-height: 1.5;
}

.contact-card {
  background: rgba(240, 253, 250, 0.95);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 2px solid rgba(20, 145, 155, 0.25);
  border-radius: 20px;
  padding: 40px;
  display: flex;
  gap: 40px;
  align-items: center;
}
@media (max-width: 800px) {
  .contact-card { flex-direction: column; align-items: stretch; padding: 32px 24px; gap: 32px; }
}
.contact-left {
  flex: 1;
}
.contact-heading {
  font-size: 1.5rem;
  font-weight: 800;
  color: #1e293b;
  margin-bottom: 12px;
}
.contact-sub {
  font-size: 1rem;
  color: #475569;
  margin-bottom: 24px;
  line-height: 1.5;
}
.contact-email-btn {
  display: inline-flex;
  align-items: center;
  background: linear-gradient(135deg, #0D7377, #14919B);
  color: white !important;
  text-decoration: none;
  padding: 12px 24px;
  border-radius: 999px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(13, 115, 119, 0.25);
  transition: transform 0.2s, box-shadow 0.2s;
}
.contact-email-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(13, 115, 119, 0.35);
}
.contact-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.contact-tile {
  background: white;
  border-radius: 16px;
  padding: 20px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  border: 1px solid rgba(20, 145, 155, 0.15);
}
.contact-tile-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(20, 145, 155, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.contact-tile-title {
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 4px;
  font-size: 1rem;
}
.contact-tile-desc {
  font-size: 0.85rem;
  color: #64748b;
  line-height: 1.4;
}
</style>
