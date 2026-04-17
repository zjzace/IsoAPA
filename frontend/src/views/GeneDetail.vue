<template>
  <div class="gene-detail-page">
    <v-container class="py-8">
      <v-btn 
        variant="text" 
        @click="$router.back()" 
        class="mb-4"
      >
        <v-icon start>mdi-arrow-left</v-icon>
        Back to Search
      </v-btn>
      
      <div v-if="loading" class="d-flex justify-center align-center" style="min-height: 400px;">
        <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
      </div>
      
      <div v-else-if="error">
        <v-alert type="error" variant="tonal">
          {{ error }}
        </v-alert>
      </div>
      
      <div v-else-if="geneData">

        <!-- ── Gene header card ─────────────────────────────────── -->
        <div class="gene-header-card mb-6">
          <div class="gene-header-title">
            <v-icon icon="mdi-dna" size="22" class="mr-2" style="color: #0D7377; opacity: 0.85;"></v-icon>
            <span class="gene-name-text">{{ geneData.gene_name }}</span>
          </div>
          <div class="gene-meta-row">
            <div class="gene-meta-item gene-meta-item--centered">
              <span class="gene-meta-label">Chromosome</span>
              <v-chip size="small" variant="tonal" color="primary">{{ geneData.chromosome }}</v-chip>
            </div>
            <div class="gene-meta-item gene-meta-item--centered">
              <span class="gene-meta-label">Strand</span>
              <v-chip size="small" variant="tonal" color="secondary">{{ geneData.strand }}</v-chip>
            </div>
            <div class="gene-meta-item">
              <span class="gene-meta-label">Total Transcripts</span>
              <span class="gene-meta-value gene-meta-accent">{{ geneData.transcripts.length }}</span>
            </div>
            <div class="gene-meta-item">
              <span class="gene-meta-label">Total PA Sites</span>
              <span class="gene-meta-value gene-meta-accent">{{ totalAPASites }}</span>
            </div>
            <div class="gene-meta-item" v-if="speciesInfo">
              <span class="gene-meta-label">Species</span>
              <span class="gene-meta-value">
                {{ speciesInfo.name }}
                <span style="font-style: italic; opacity: 0.65; font-size: 13.5px;">{{ speciesInfo.latin_name }}</span>
                <v-chip size="x-small" variant="tonal" color="secondary" class="ml-1">{{ speciesInfo.assembly }}</v-chip>
              </span>
            </div>
          </div>
        </div>

        <!-- ── Gene Summary (MyGene.info) ───────────────────────── -->
        <div class="section-card mb-6">
          <div class="section-title">
            <v-icon size="18" class="mr-2" style="color: #0D7377;">mdi-text-box-outline</v-icon>
            Gene Summary
          </div>

          <div class="panel-box">
            <!-- Panel header -->
            <div class="panel-header">
              <div class="panel-header-left">
                <span class="panel-icon-wrap panel-icon-teal">
                  <v-icon size="18" color="white">mdi-dna</v-icon>
                </span>
                <div>
                  <div class="panel-title-text">{{ geneSummaryData?.symbol || geneData.gene_name }}</div>
                  <div class="panel-subtitle-text">
                    {{ geneSummaryData?.fullName || 'Gene information from NCBI / MyGene.info' }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Panel body -->
            <div class="panel-body">

              <!-- Loading -->
              <div v-if="geneSummaryLoading" class="d-flex align-center py-4">
                <v-progress-circular indeterminate color="primary" size="22" width="2" class="mr-3"></v-progress-circular>
                <span class="text-caption text-medium-emphasis">Fetching gene information…</span>
              </div>

              <!-- Error -->
              <v-alert v-else-if="geneSummaryError" type="warning" variant="tonal" density="compact" class="text-caption">
                Gene summary not available for this gene.
              </v-alert>

              <!-- No hit -->
              <div v-else-if="!geneSummaryData" class="text-caption text-medium-emphasis py-2">
                No gene summary found.
              </div>

              <!-- Data — NCBI-style definition list -->
              <template v-else>
                <dl class="gs-deflist">

                  <!-- Also known as -->
                  <div v-if="geneSummaryData.aliases?.length" class="gs-row">
                    <dt class="gs-dt">Also known as</dt>
                    <dd class="gs-dd">{{ geneSummaryData.aliases.join('; ') }}</dd>
                  </div>

                  <!-- Gene type -->
                  <div v-if="geneSummaryData.geneType" class="gs-row">
                    <dt class="gs-dt">Gene type</dt>
                    <dd class="gs-dd">{{ geneSummaryData.geneType.replace(/-/g, ' ') }}</dd>
                  </div>

                   <!-- See related — smart Ensembl / RefSeq / UniProt / NCBI links -->
                   <div class="gs-row">
                     <dt class="gs-dt">See related</dt>
                      <dd class="gs-dd gs-related-dd">
                        <span v-if="geneSummaryData.ensemblGene || geneData.gene_id?.startsWith('ENS')" class="gs-id-entry">
                          <span class="gs-id-source">Ensembl</span>
                          <a :href="`https://www.ensembl.org/id/${geneSummaryData.ensemblGene || geneData.gene_id}`" target="_blank" class="gs-id-code gs-id-href">{{ geneSummaryData.ensemblGene || geneData.gene_id }}</a>
                        </span>
                        <span v-if="geneSummaryData.refseqMrna" class="gs-id-entry">
                          <span class="gs-id-source">RefSeq</span>
                          <a :href="`https://www.ncbi.nlm.nih.gov/nuccore/${geneSummaryData.refseqMrna}`" target="_blank" class="gs-id-code gs-id-href">{{ geneSummaryData.refseqMrna }}</a>
                        </span>
                        <span v-if="geneSummaryData.uniprot" class="gs-id-entry">
                          <span class="gs-id-source">UniProtKB</span>
                          <a :href="`https://www.uniprot.org/uniprot/${geneSummaryData.uniprot}`" target="_blank" class="gs-id-code gs-id-href">{{ geneSummaryData.uniprot }}</a>
                        </span>
                        <span v-if="geneSummaryData.entrezgene" class="gs-id-entry">
                          <span class="gs-id-source">NCBI Gene</span>
                          <a :href="`https://www.ncbi.nlm.nih.gov/gene/${geneSummaryData.entrezgene}`" target="_blank" class="gs-id-code gs-id-href">{{ geneSummaryData.entrezgene }}</a>
                        </span>
                      </dd>
                   </div>

                  <!-- Summary text -->
                  <div class="gs-row">
                    <dt class="gs-dt">Summary</dt>
                    <dd class="gs-dd">
                      <p v-if="geneSummaryData.summary" class="gs-summary-text">{{ geneSummaryData.summary }}</p>
                      <p v-else class="gs-summary-text gs-summary-empty">No functional summary available from NCBI Gene.</p>
                    </dd>
                  </div>

                  <!-- KEGG Pathways — bottom -->
                  <div v-if="geneSummaryData.pathways?.length" class="gs-row">
                    <dt class="gs-dt">KEGG Pathways</dt>
                    <dd class="gs-dd">
                      <div class="gs-chip-row">
                        <span
                          v-for="pw in (showAllPathways ? geneSummaryData.pathways : geneSummaryData.pathways.slice(0, 10))"
                          :key="pw.id"
                          class="gs-chip gs-chip-pathway"
                        >{{ pw.name }}</span>
                        <button
                          v-if="geneSummaryData.pathways.length > 10"
                          class="gs-chip gs-chip-more"
                          @click="showAllPathways = !showAllPathways"
                        >
                          {{ showAllPathways ? '− show less' : `+${geneSummaryData.pathways.length - 10} more` }}
                        </button>
                      </div>
                    </dd>
                  </div>

                </dl>
              </template>
            </div>
          </div>
        </div>

        <!-- ── Transcripts and APA Sites ────────────────────────── -->
        <div class="section-card">

          <!-- Section title -->
          <div class="section-title">
            <v-icon size="18" class="mr-2" style="color: #0D7377;">mdi-source-branch</v-icon>
            Transcripts and PA Sites
          </div>

          <!-- ── Panel 1: Transcript Details ──────────────────── -->
          <div class="panel-box mb-5">
            <div class="panel-header">
              <div class="panel-header-left">
                <span class="panel-icon-wrap panel-icon-teal">
                  <v-icon size="18" color="white">mdi-table</v-icon>
                </span>
                <div>
                  <div class="panel-title-text">Transcript Details</div>
                  <div class="panel-subtitle-text">PA sites and sample coverage per transcript isoform</div>
                </div>
                <v-chip size="x-small" color="primary" variant="tonal" class="ml-2">
                  {{ geneData.transcripts.length }}
                </v-chip>
              </div>
            </div>

            <!-- Table -->
            <div class="tx-table-container">
              <table class="tx-table">
                <thead>
                  <tr>
                    <th class="tx-th" style="width: 30%;">Transcript</th>
                    <th class="tx-th" style="width: 10%; text-align: center;">PA Sites</th>
                     <th class="tx-th">Site Ranges</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="tx in geneData.transcripts"
                    :key="tx.transcript_id"
                    class="tx-row"
                  >
                    <!-- Transcript ID -->
                    <td class="tx-td">
                      <router-link
                        :to="{ name: 'LocusDetail', params: { transcriptId: tx.transcript_id } }"
                        class="tx-id-link"
                      >{{ tx.transcript_id }}</router-link>
                    </td>

                     <!-- PA site count -->
                      <td class="tx-td" style="text-align: center;">
                        <span class="tx-count-badge">{{ tx.apa_site_count }}</span>
                      </td>

                      <!-- Site ranges -->
                      <td class="tx-td">
                        <div class="tx-pos-list">
                          <span
                            v-for="site in tx.apa_sites"
                            :key="site.unified_id"
                            class="tx-pos-tag"
                            :title="site.unified_id"
                          >{{ siteRange(site.unified_id) }}</span>
                        </div>
                      </td>
                  </tr>
                  <tr v-if="geneData.transcripts.length === 0">
                    <td colspan="4" class="tx-empty">No transcripts found</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- ── Panel 2: Isoform–APA Fingerprint ─────────────── -->
          <div class="panel-box mb-5">
            <div class="panel-header">
              <div class="panel-header-left">
                <span class="panel-icon-wrap panel-icon-teal">
                  <v-icon size="18" color="white">mdi-fingerprint</v-icon>
                </span>
                <div>
                  <div class="panel-title-text">Isoform–APA Fingerprint</div>
                  <div class="panel-subtitle-text" style="white-space: nowrap;">Genome-aligned PA sites per isoform, coloured by Shared / Private classification</div>
                </div>
              </div>
            </div>
            <div class="panel-body">
              <div v-if="structuresLoading" class="d-flex justify-center align-center py-8">
                <v-progress-circular indeterminate color="primary" size="40"></v-progress-circular>
                <span class="ml-3 text-caption text-grey">Loading transcript structures…</span>
              </div>
              <MultiIsoformBrowser
                v-else
                :geneData="geneData"
                :transcriptStructures="transcriptStructures"
              />
            </div>
          </div>

        </div>
      </div>
    </v-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { apiService } from '@/services/api'
import MultiIsoformBrowser from '@/components/MultiIsoformBrowser.vue'

const route = useRoute()

const loading = ref(true)
const structuresLoading = ref(true)
const error = ref(null)
const geneData = ref(null)
const transcriptStructures = ref({})
const speciesInfo = ref(null)

// ── Gene summary (MyGene.info) ─────────────────────────────────────────────
const geneSummaryLoading = ref(false)
const geneSummaryError = ref(null)
const geneSummaryData = ref(null)
const showAllPathways = ref(false)

const fetchGeneSummary = async (geneSymbol) => {
  geneSummaryLoading.value = true
  geneSummaryError.value = null
  try {
    const url = `https://mygene.info/v3/query?q=symbol:${encodeURIComponent(geneSymbol)}&fields=name,summary,pathway.kegg,uniprot,entrezgene,HGNC,symbol,alias,type_of_gene,refseq,ensembl&species=human&size=1`
    const res = await fetch(url)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const json = await res.json()
    const hit = json?.hits?.[0]
    if (!hit) {
      geneSummaryData.value = null
      return
    }
    const uniprotRaw = hit.uniprot?.['Swiss-Prot']
    const uniprot = Array.isArray(uniprotRaw) ? uniprotRaw[0] : uniprotRaw ?? null
    const pathways = hit.pathway?.kegg
      ? (Array.isArray(hit.pathway.kegg) ? hit.pathway.kegg : [hit.pathway.kegg])
      : []
    // Aliases — normalise to array
    const aliasRaw = hit.alias
    const aliases = Array.isArray(aliasRaw) ? aliasRaw : (aliasRaw ? [aliasRaw] : [])
    // RefSeq: pick first NM_ mRNA accession (curated mRNA)
    const rnaList = hit.refseq?.rna ?? []
    const rnaArr  = Array.isArray(rnaList) ? rnaList : [rnaList]
    const refseqMrna = rnaArr.find(r => r.startsWith('NM_')) ?? rnaArr[0] ?? null
    // Ensembl gene ID from hit (may differ from query if mouse gene resolved differently)
    const ensemblGene = hit.ensembl?.gene ?? null
    geneSummaryData.value = {
      symbol:      hit.symbol      ?? null,
      fullName:    hit.name        ?? null,
      aliases,
      geneType:    hit.type_of_gene ?? null,
      summary:     hit.summary     ?? null,
      pathways,
      entrezgene:  hit.entrezgene  ?? null,
      uniprot,
      hgnc:        hit.HGNC        ?? null,
      refseqMrna,
      ensemblGene,
    }
  } catch (err) {
    console.warn('Gene summary fetch failed:', err)
    geneSummaryError.value = 'fetch_failed'
  } finally {
    geneSummaryLoading.value = false
  }
}

const totalAPASites = computed(() => {
  if (!geneData.value) return 0
  return geneData.value.transcripts.reduce((sum, t) => sum + t.apa_sites.length, 0)
})

const siteRange = (unifiedId) => {
  const m = unifiedId?.match(/:(\d+)-(\d+):/)
  if (!m) return unifiedId ?? ''
  return `${Number(m[1]).toLocaleString()}–${Number(m[2]).toLocaleString()}`
}

onMounted(async () => {
  const geneId = route.params.geneId
  
  try {
    loading.value = true
    geneData.value = await apiService.getGeneDetail(geneId)

    // Fire gene summary fetch (non-blocking)
    fetchGeneSummary(geneData.value.gene_name)

    // Fetch species info from first transcript's locus detail (non-fatal)
    if (geneData.value?.transcripts?.length) {
      try {
        const firstTx = await apiService.getLocusDetail(geneData.value.transcripts[0].transcript_id)
        speciesInfo.value = firstTx?.apa_sites?.[0]?.species ?? null
      } catch {
        // Non-fatal — species badge is optional
      }
    }
  } catch (err) {
    console.error('Failed to load gene detail:', err)
    error.value = 'Failed to load gene details. Please try again.'
  } finally {
    loading.value = false
  }

  if (geneData.value?.transcripts?.length) {
    try {
      structuresLoading.value = true
      const entries = await Promise.all(
        geneData.value.transcripts.map(tx =>
          apiService.getTranscriptStructure(tx.transcript_id)
            .then(s => [tx.transcript_id, s])
            .catch(() => [tx.transcript_id, null])
        )
      )
      transcriptStructures.value = Object.fromEntries(
        entries.filter(([, s]) => s !== null)
      )
    } finally {
      structuresLoading.value = false
    }
  } else {
    structuresLoading.value = false
  }
})
</script>

<style scoped>
.gene-detail-page {
  min-height: 100vh;
  background: rgb(var(--v-theme-background));
}

a { text-decoration: none; }
a:hover { text-decoration: underline; }

code {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
}

/* ── Gene header card ────────────────────────────────────────────── */
.gene-header-card {
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(16px) saturate(160%);
  -webkit-backdrop-filter: blur(16px) saturate(160%);
  border: 1px solid rgba(255, 255, 255, 0.62);
  border-radius: 16px;
  padding: 20px 24px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.07), 0 1px 4px rgba(0, 0, 0, 0.04);
}

.gene-header-title {
  display: flex;
  align-items: center;
  margin-bottom: 14px;
}

.gene-name-text {
  font-size: 1.6rem;
  font-weight: 700;
  color: rgba(0,0,0,0.87);
  letter-spacing: -0.01em;
}

.gene-meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 28px;
}

.gene-meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.gene-meta-item--centered {
  align-items: center;
}

.gene-meta-label {
  font-size: 12.5px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(0,0,0,0.42);
}

.gene-meta-value {
  font-size: 15px;
  font-weight: 500;
  color: rgba(0,0,0,0.80);
  display: flex;
  align-items: center;
  gap: 4px;
}

.gene-meta-accent {
  font-size: 18px;
  font-weight: 700;
  color: #0D7377;
}

/* ── Outer section card ──────────────────────────────────────────── */
.section-card {
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(16px) saturate(160%);
  -webkit-backdrop-filter: blur(16px) saturate(160%);
  border: 1px solid rgba(255, 255, 255, 0.58);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06), 0 1px 4px rgba(0, 0, 0, 0.04);
}

.section-title {
  display: flex;
  align-items: center;
  font-size: 1.15rem;
  font-weight: 700;
  color: rgba(0,0,0,0.80);
  margin-bottom: 20px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(0,0,0,0.07);
}

/* ── Panel box (each of the 3 sections) ─────────────────────────── */
.panel-box {
  border: 1px solid rgba(13, 115, 119, 0.14);
  border-radius: 12px;
  overflow: hidden;
  background: rgba(250, 252, 252, 0.85);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

/* ── Unified panel header ────────────────────────────────────────── */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
  background: rgba(13, 115, 119, 0.06);
  border-bottom: 1px solid rgba(13, 115, 119, 0.12);
  flex-wrap: wrap;
}

.panel-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* Coloured icon pill */
.panel-icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  flex-shrink: 0;
}

.panel-icon-teal {
  background: #0D7377;
}

.panel-title-text {
  font-size: 14.5px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.87);
  line-height: 1.3;
  font-family: 'Roboto', sans-serif;
}

.panel-subtitle-text {
  font-size: 13.5px;
  color: rgba(0, 0, 0, 0.60);
  margin-top: 2px;
  max-width: 480px;
  font-family: 'Roboto', sans-serif;
}

/* Panel body padding for browser/coupling */
.panel-body {
  padding: 16px;
}

/* ── Transcript table ────────────────────────────────────────────── */
.tx-table-container {
  overflow-x: auto;
}

.tx-table {
  width: 100%;
  border-collapse: collapse;
  font-family: 'Roboto', sans-serif;
  font-size: 14.5px;
}

.tx-th {
  padding: 9px 16px;
  text-align: left;
  font-size: 13.5px;
  font-weight: 600;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  color: rgba(0, 0, 0, 0.60);
  background: rgba(13, 115, 119, 0.04);
  border-bottom: 1px solid rgba(13, 115, 119, 0.10);
  white-space: nowrap;
  font-family: 'Roboto', sans-serif;
}

.tx-row {
  border-bottom: 1px solid rgba(0, 0, 0, 0.055);
  transition: background 0.12s ease;
}

.tx-row:hover {
  background: rgba(13, 115, 119, 0.04);
}

.tx-row:last-child {
  border-bottom: none;
}

.tx-td {
  padding: 11px 16px;
  vertical-align: middle;
  color: rgba(0, 0, 0, 0.82);
}

.tx-id-link {
  font-weight: 600;
  font-size: 14.5px;
  color: #0D7377;
  text-decoration: none;
  font-family: 'Roboto Mono', 'Courier New', monospace;
  display: inline-flex;
  align-items: center;
}

.tx-id-link:hover {
  color: #14919B;
  text-decoration: underline;
}

.tx-count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  padding: 0 8px;
  background: rgba(13, 115, 119, 0.12);
  color: #0D7377;
  border: 1px solid rgba(13, 115, 119, 0.25);
  border-radius: 12px;
  font-size: 13px;
  font-weight: 700;
  font-family: 'Inter', sans-serif;
}

.tx-sample-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tx-sample-pill {
  display: inline-block;
  background: rgba(13, 115, 119, 0.10);
  color: #0D7377;
  border: 1px solid rgba(13, 115, 119, 0.22);
  border-radius: 10px;
  font-size: 12.5px;
  font-weight: 500;
  padding: 2px 9px;
  font-family: 'Inter', sans-serif;
  white-space: nowrap;
}

.tx-pos-list {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.tx-pos-tag {
  display: inline-block;
  background: rgba(13, 115, 119, 0.06);
  color: rgba(0, 0, 0, 0.70);
  border: 1px solid rgba(13, 115, 119, 0.15);
  border-radius: 6px;
  font-size: 12.5px;
  font-family: 'Inter', 'Roboto Mono', monospace;
  font-weight: 500;
  padding: 2px 8px;
  white-space: nowrap;
  cursor: default;
}

.tx-empty {
  padding: 32px 16px;
  text-align: center;
  color: rgba(0, 0, 0, 0.38);
  font-size: 14.5px;
}

/* ── Gene Summary definition list ───────────────────────────────── */
.gs-deflist {
  margin: 0;
  padding: 0;
  display: table;
  width: 100%;
  border-spacing: 0;
  border: 1px solid rgba(13, 115, 119, 0.10);
  border-radius: 8px;
  overflow: hidden;
}

.gs-row {
  display: table-row;
}

.gs-row:not(:last-child) .gs-dt,
.gs-row:not(:last-child) .gs-dd {
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.gs-dt {
  display: table-cell;
  width: 160px;
  min-width: 130px;
  padding: 10px 14px 10px 16px;
  font-size: 14.5px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.62);
  vertical-align: top;
  white-space: nowrap;
  background: rgba(13, 115, 119, 0.04);
  border-right: 1px solid rgba(13, 115, 119, 0.10);
}

.gs-dd {
  display: table-cell;
  padding: 10px 16px;
  font-size: 14.5px;
  color: rgba(0, 0, 0, 0.80);
  vertical-align: middle;
  line-height: 1.55;
}

.gs-summary-text {
  margin: 0;
  font-size: 14.5px;
  line-height: 1.75;
  color: rgba(0, 0, 0, 0.72);
}

.gs-summary-empty {
  color: rgba(0, 0, 0, 0.38);
  font-style: italic;
}

/* "See related" inline links */
.gs-related-dd {
  display: table-cell;
  padding: 10px 16px;
  vertical-align: middle;
}

.gs-id-entry {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  margin-right: 20px;
  white-space: nowrap;
  vertical-align: middle;
}

.gs-id-source {
  font-size: 12.5px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.38);
  background: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
  padding: 1px 5px;
  line-height: 1.4;
}

.gs-id-code {
  color: #0D7377;
  font-family: 'Roboto Mono', 'Courier New', monospace;
  font-size: 13.5px;
  font-weight: 600;
}

.gs-id-href {
  text-decoration: none;
}

.gs-id-href:hover {
  text-decoration: underline;
  color: #0a5c60;
}

/* KEGG pathway chips */
.gs-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.gs-chip {
  font-size: 12.5px;
  font-weight: 500;
  padding: 3px 9px;
  border-radius: 12px;
  border: 1px solid transparent;
}

.gs-chip-pathway {
  background: rgba(13, 115, 119, 0.08);
  color: #0D7377;
  border-color: rgba(13, 115, 119, 0.20);
}

.gs-chip-more {
  background: rgba(0, 0, 0, 0.05);
  color: rgba(0, 0, 0, 0.55);
  border-color: rgba(0, 0, 0, 0.15);
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s, color 0.15s;
}

.gs-chip-more:hover {
  background: rgba(13, 115, 119, 0.12);
  color: #0D7377;
  border-color: rgba(13, 115, 119, 0.30);
}

/* ── Dark mode ─────────────────────────────────────────────────── */
.v-theme--apaAtlasDarkTheme .gene-header-card {
  background: rgba(24, 28, 37, 0.82);
  border: 1px solid rgba(255, 255, 255, 0.07);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.35), 0 1px 4px rgba(0, 0, 0, 0.25);
}

.v-theme--apaAtlasDarkTheme .section-card {
  background: rgba(24, 28, 37, 0.80);
  border: 1px solid rgba(255, 255, 255, 0.07);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.30), 0 1px 4px rgba(0, 0, 0, 0.20);
}

.v-theme--apaAtlasDarkTheme .section-title {
  color: rgba(255, 255, 255, 0.85);
  border-bottom-color: rgba(255, 255, 255, 0.07);
}

.v-theme--apaAtlasDarkTheme .panel-box {
  background: rgba(20, 24, 33, 0.85);
  border-color: rgba(42, 168, 174, 0.15);
}

.v-theme--apaAtlasDarkTheme .panel-header {
  background: rgba(42, 168, 174, 0.07);
  border-bottom-color: rgba(42, 168, 174, 0.12);
}

.v-theme--apaAtlasDarkTheme .panel-title-text {
  color: rgba(255, 255, 255, 0.87);
}

.v-theme--apaAtlasDarkTheme .panel-subtitle-text {
  color: rgba(255, 255, 255, 0.45);
}

.v-theme--apaAtlasDarkTheme .gene-name-text {
  color: rgba(255, 255, 255, 0.90);
}

.v-theme--apaAtlasDarkTheme .gene-meta-label {
  color: rgba(255, 255, 255, 0.38);
}

.v-theme--apaAtlasDarkTheme .gene-meta-value {
  color: rgba(255, 255, 255, 0.75);
}

.v-theme--apaAtlasDarkTheme .gene-meta-accent {
  color: #2AA8AE;
}

.v-theme--apaAtlasDarkTheme .tx-th {
  color: rgba(255, 255, 255, 0.50) !important;
  background: rgba(42, 168, 174, 0.06) !important;
  border-bottom-color: rgba(42, 168, 174, 0.10) !important;
}

.v-theme--apaAtlasDarkTheme .tx-td {
  color: rgba(255, 255, 255, 0.78);
  border-bottom-color: rgba(255, 255, 255, 0.05) !important;
}

.v-theme--apaAtlasDarkTheme .tx-row:hover {
  background: rgba(42, 168, 174, 0.05);
}

.v-theme--apaAtlasDarkTheme .tx-id-link {
  color: #2AA8AE;
}

.v-theme--apaAtlasDarkTheme .tx-count-badge {
  background: rgba(42, 168, 174, 0.14);
  color: #2AA8AE;
  border-color: rgba(42, 168, 174, 0.28);
}

.v-theme--apaAtlasDarkTheme .tx-sample-pill {
  background: rgba(42, 168, 174, 0.10);
  color: #2AA8AE;
  border-color: rgba(42, 168, 174, 0.22);
}

.v-theme--apaAtlasDarkTheme .tx-pos-tag {
  background: rgba(42, 168, 174, 0.07);
  color: rgba(255, 255, 255, 0.65);
  border-color: rgba(42, 168, 174, 0.18);
}

.v-theme--apaAtlasDarkTheme .gs-dt {
  background: rgba(42, 168, 174, 0.05);
  border-right-color: rgba(42, 168, 174, 0.10);
  color: rgba(255, 255, 255, 0.55);
}

.v-theme--apaAtlasDarkTheme .gs-dd {
  color: rgba(255, 255, 255, 0.78);
}

.v-theme--apaAtlasDarkTheme .gs-deflist {
  border-color: rgba(42, 168, 174, 0.10);
}

.v-theme--apaAtlasDarkTheme .gs-row:not(:last-child) .gs-dt,
.v-theme--apaAtlasDarkTheme .gs-row:not(:last-child) .gs-dd {
  border-bottom-color: rgba(255, 255, 255, 0.05);
}

.v-theme--apaAtlasDarkTheme .gs-summary-text {
  color: rgba(255, 255, 255, 0.70);
}

.v-theme--apaAtlasDarkTheme .gs-id-source {
  background: rgba(255, 255, 255, 0.07);
  color: rgba(255, 255, 255, 0.35);
}

.v-theme--apaAtlasDarkTheme .gs-id-code {
  color: #2AA8AE;
}
</style>
