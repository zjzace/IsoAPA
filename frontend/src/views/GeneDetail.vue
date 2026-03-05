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
            <div class="gene-meta-item">
              <span class="gene-meta-label">Gene ID</span>
              <span class="gene-meta-value">{{ geneData.gene_id }}</span>
            </div>
            <div class="gene-meta-item">
              <span class="gene-meta-label">Chromosome</span>
              <span class="gene-meta-value">
                <v-chip size="small" variant="tonal" color="primary" class="mr-1">{{ geneData.chromosome }}</v-chip>
                <v-chip size="small" variant="tonal" color="secondary">{{ geneData.strand }}</v-chip>
              </span>
            </div>
            <div class="gene-meta-item">
              <span class="gene-meta-label">Total Transcripts</span>
              <span class="gene-meta-value gene-meta-accent">{{ geneData.transcripts.length }}</span>
            </div>
            <div class="gene-meta-item">
              <span class="gene-meta-label">Total APA Sites</span>
              <span class="gene-meta-value gene-meta-accent">{{ totalAPASites }}</span>
            </div>
            <div class="gene-meta-item" v-if="speciesInfo">
              <span class="gene-meta-label">Species</span>
              <span class="gene-meta-value">
                {{ speciesInfo.name }}
                <span style="font-style: italic; opacity: 0.65; font-size: 12px;">{{ speciesInfo.latin_name }}</span>
                <v-chip size="x-small" variant="tonal" color="secondary" class="ml-1">{{ speciesInfo.assembly }}</v-chip>
              </span>
            </div>
          </div>
        </div>

        <!-- ── Transcripts and APA Sites ────────────────────────── -->
        <div class="section-card">

          <!-- Section title -->
          <div class="section-title">
            <v-icon size="18" class="mr-2" style="color: #0D7377;">mdi-source-branch</v-icon>
            Transcripts and APA Sites
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
                  <div class="panel-subtitle-text">APA sites and sample coverage per transcript isoform</div>
                </div>
                <v-chip size="x-small" color="primary" variant="tonal" class="ml-2">
                  {{ geneData.transcripts.length }}
                </v-chip>
              </div>
              <v-text-field
                v-model="tableSearch"
                placeholder="Filter transcripts…"
                prepend-inner-icon="mdi-magnify"
                density="compact"
                variant="outlined"
                hide-details
                clearable
                style="max-width: 220px;"
                class="tx-filter-field"
              ></v-text-field>
            </div>

            <!-- Table -->
            <div class="tx-table-container">
              <table class="tx-table">
                <thead>
                  <tr>
                    <th class="tx-th" style="width: 34%;">Transcript ID</th>
                    <th class="tx-th" style="width: 10%; text-align: center;">APA Sites</th>
                    <th class="tx-th" style="width: 24%;">Samples</th>
                    <th class="tx-th" style="width: 32%;">APA Site Details</th>
                  </tr>
                </thead>
                <tbody>
                  <template v-for="tx in filteredTranscripts" :key="tx.transcript_id">
                    <tr class="tx-row" :class="{ 'tx-row--expanded': expandedRows.has(tx.transcript_id) }">
                      <td class="tx-td">
                        <div class="d-flex align-center gap-2">
                          <router-link
                            :to="{ name: 'LocusDetail', params: { transcriptId: tx.transcript_id } }"
                            class="tx-id-link"
                          >
                            <v-icon size="14" class="mr-1" style="opacity: 0.5;">mdi-dna</v-icon>
                            {{ tx.transcript_id }}
                          </router-link>
                        </div>
                      </td>
                      <td class="tx-td" style="text-align: center;">
                        <v-chip size="small" color="primary" variant="tonal" class="font-weight-bold">
                          {{ tx.apa_site_count }}
                        </v-chip>
                      </td>
                      <td class="tx-td">
                        <div class="d-flex flex-wrap gap-1">
                          <v-chip
                            v-for="s in tx.samples.slice(0, 4)"
                            :key="s"
                            size="x-small"
                            variant="tonal"
                            color="secondary"
                          >{{ s }}</v-chip>
                          <v-chip v-if="tx.samples.length > 4" size="x-small" variant="outlined">
                            +{{ tx.samples.length - 4 }}
                          </v-chip>
                        </div>
                      </td>
                      <td class="tx-td">
                        <button
                          v-if="tx.apa_sites.length > 0"
                          class="tx-expand-btn"
                          @click="toggleRow(tx.transcript_id)"
                        >
                          <v-icon size="14" class="mr-1">
                            {{ expandedRows.has(tx.transcript_id) ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
                          </v-icon>
                          {{ expandedRows.has(tx.transcript_id) ? 'Hide' : 'Show' }} {{ tx.apa_sites.length }} site{{ tx.apa_sites.length !== 1 ? 's' : '' }}
                        </button>
                        <span v-else class="text-caption text-medium-emphasis">—</span>
                      </td>
                    </tr>
                    <tr
                      v-if="expandedRows.has(tx.transcript_id)"
                      v-for="site in tx.apa_sites"
                      :key="site.site_id"
                      class="tx-site-row"
                    >
                      <td class="tx-site-td" colspan="4">
                        <div class="tx-site-inner">
                          <div class="tx-site-id">
                            <v-icon size="12" class="mr-1" style="color: #0D7377;">mdi-map-marker</v-icon>
                            <code class="tx-code">{{ site.site_id }}</code>
                            <span class="tx-site-pos">pos. {{ site.site_position.toLocaleString() }}</span>
                          </div>
                          <div class="tx-site-samples">
                            <v-chip
                              v-for="sd in site.sample_details"
                              :key="sd.sample_name"
                              size="x-small"
                              variant="tonal"
                              color="primary"
                              class="mr-1"
                            >
                              {{ sd.sample_name }}: <strong class="ml-1">{{ (sd.site_abundance * 100).toFixed(1) }}%</strong>
                            </v-chip>
                          </div>
                        </div>
                      </td>
                    </tr>
                  </template>
                  <tr v-if="filteredTranscripts.length === 0">
                    <td colspan="4" class="tx-empty">
                      <v-icon size="20" class="mr-2" style="opacity: 0.4;">mdi-filter-off</v-icon>
                      No transcripts match "{{ tableSearch }}"
                    </td>
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
                  <div class="panel-subtitle-text">Genome-aligned APA sites per isoform, coloured by Shared / Private classification</div>
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

          <!-- ── Panel 3: Splicing–APA Coupling ────────────────── -->
          <div class="panel-box">
            <SplicingApaCouplingPanel :geneData="geneData" />
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
import SplicingApaCouplingPanel from '@/components/SplicingApaCouplingPanel.vue'

const route = useRoute()

const loading = ref(true)
const structuresLoading = ref(true)
const error = ref(null)
const geneData = ref(null)
const transcriptStructures = ref({})
const tableSearch = ref('')
const expandedRows = ref(new Set())
const speciesInfo = ref(null)

const toggleRow = (txId) => {
  const s = new Set(expandedRows.value)
  s.has(txId) ? s.delete(txId) : s.add(txId)
  expandedRows.value = s
}

const filteredTranscripts = computed(() => {
  if (!geneData.value) return []
  const q = tableSearch.value?.toLowerCase().trim()
  if (!q) return geneData.value.transcripts
  return geneData.value.transcripts.filter(tx =>
    tx.transcript_id.toLowerCase().includes(q) ||
    tx.samples.some(s => s.toLowerCase().includes(q))
  )
})

const totalAPASites = computed(() => {
  if (!geneData.value) return 0
  return geneData.value.transcripts.reduce((sum, t) => sum + t.apa_sites.length, 0)
})

onMounted(async () => {
  const geneId = route.params.geneId
  
  try {
    loading.value = true
    geneData.value = await apiService.getGeneDetail(geneId)

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
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.10);
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

.gene-header-title {
  display: flex;
  align-items: center;
  margin-bottom: 14px;
}

.gene-name-text {
  font-size: 1.45rem;
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

.gene-meta-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(0,0,0,0.42);
}

.gene-meta-value {
  font-size: 14px;
  font-weight: 500;
  color: rgba(0,0,0,0.80);
  display: flex;
  align-items: center;
  gap: 4px;
}

.gene-meta-accent {
  font-size: 16px;
  font-weight: 700;
  color: #0D7377;
}

/* ── Outer section card ──────────────────────────────────────────── */
.section-card {
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.10);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

.section-title {
  display: flex;
  align-items: center;
  font-size: 1.05rem;
  font-weight: 700;
  color: rgba(0,0,0,0.80);
  margin-bottom: 20px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(0,0,0,0.07);
}

/* ── Panel box (each of the 3 sections) ─────────────────────────── */
.panel-box {
  border: 1px solid rgba(13, 115, 119, 0.15);
  border-radius: 10px;
  overflow: hidden;
  background: #fafcfc;
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
  font-size: 0.92rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.82);
  line-height: 1.3;
}

.panel-subtitle-text {
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.46);
  margin-top: 2px;
  max-width: 480px;
}

/* Panel body padding for browser/coupling */
.panel-body {
  padding: 16px;
}

/* ── Filter field ────────────────────────────────────────────────── */
.tx-filter-field :deep(.v-field) {
  font-size: 13px;
  border-radius: 7px;
  background: #fff;
}

.tx-filter-field :deep(.v-field__outline) {
  --v-field-border-opacity: 0.2;
}

/* ── Transcript table ────────────────────────────────────────────── */
.tx-table-container {
  overflow-x: auto;
}

.tx-table {
  width: 100%;
  border-collapse: collapse;
  font-family: 'Roboto', sans-serif;
  font-size: 13px;
}

.tx-th {
  padding: 9px 16px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  color: rgba(0, 0, 0, 0.50);
  background: rgba(13, 115, 119, 0.04);
  border-bottom: 1px solid rgba(13, 115, 119, 0.10);
  white-space: nowrap;
}

.tx-row {
  border-bottom: 1px solid rgba(0, 0, 0, 0.055);
  transition: background 0.12s ease;
}

.tx-row:hover {
  background: rgba(13, 115, 119, 0.04);
}

.tx-row--expanded {
  background: rgba(13, 115, 119, 0.05);
}

.tx-row:last-child:not(.tx-row--expanded) {
  border-bottom: none;
}

.tx-td {
  padding: 11px 16px;
  vertical-align: middle;
  color: rgba(0, 0, 0, 0.82);
}

.tx-id-link {
  font-weight: 600;
  font-size: 13px;
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

.tx-expand-btn {
  display: inline-flex;
  align-items: center;
  font-size: 12px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.54);
  background: none;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 6px;
  padding: 3px 10px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: 'Roboto', sans-serif;
}

.tx-expand-btn:hover {
  background: rgba(13, 115, 119, 0.08);
  border-color: rgba(13, 115, 119, 0.4);
  color: #0D7377;
}

.tx-site-row {
  border-bottom: 1px solid rgba(0, 0, 0, 0.045);
  background: rgba(13, 115, 119, 0.025);
}

.tx-site-row:last-child {
  border-bottom: 1px solid rgba(0, 0, 0, 0.055);
}

.tx-site-td { padding: 0; }

.tx-site-inner {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 8px 16px 8px 36px;
  flex-wrap: wrap;
}

.tx-site-id {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.tx-code {
  background: rgba(13, 115, 119, 0.08);
  color: #0D7377;
  padding: 2px 7px;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'Roboto Mono', 'Courier New', monospace;
}

.tx-site-pos {
  font-size: 11px;
  color: rgba(0, 0, 0, 0.38);
}

.tx-site-samples {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tx-empty {
  padding: 32px 16px;
  text-align: center;
  color: rgba(0, 0, 0, 0.38);
  font-size: 13px;
}
</style>
