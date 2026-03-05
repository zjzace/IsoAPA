<template>
  <div class="coupling-panel">
    <!-- Header (unified panel style) -->
    <div class="panel-header">
      <div class="panel-title-block">
        <span class="panel-icon-wrap">
          <v-icon size="18" color="white">mdi-link-variant</v-icon>
        </span>
        <div>
          <div class="panel-title">Splicing–APA Coupling</div>
          <div class="panel-subtitle">
            How strongly is isoform identity linked to polyA site choice across cell lines?
          </div>
        </div>
      </div>
      <div class="score-badge-wrap">
        <v-tooltip location="top" max-width="280">
          <template #activator="{ props: tp }">
            <div class="global-score-badge" v-bind="tp">
              <div class="score-ring" :style="ringStyle">
                <svg viewBox="0 0 60 60" class="ring-svg">
                  <circle cx="30" cy="30" r="24" class="ring-bg" />
                  <circle
                    cx="30" cy="30" r="24"
                    class="ring-fg"
                    :stroke="scoreColor"
                    :stroke-dasharray="`${dashVal} ${dashTotal}`"
                  />
                </svg>
                <span class="ring-label">{{ globalScore }}</span>
              </div>
              <div class="score-meta">
                <div class="score-level" :style="{ color: scoreColor }">
                  {{ scoreLabel }}
                </div>
                <div class="score-caption">Coupling Score</div>
              </div>
            </div>
          </template>
          <div class="tooltip-content">
            <strong>Coupling Score (0–100)</strong><br/>
            Measures how different polyA site usage patterns are across isoforms. Computed as the mean per-sample
            Jensen–Shannon divergence between isoform APA distributions, normalised to 0–100.
            <br/><br/>
            <strong>0</strong> = All isoforms use identical polyA proportions<br/>
            <strong>100</strong> = Every isoform has a completely unique polyA profile
          </div>
        </v-tooltip>
      </div>
    </div>

    <!-- No data state -->
    <div class="panel-content">
    <div v-if="transcripts.length === 0 || allSites.length === 0" class="empty-state">
      <v-icon size="40" color="grey-lighten-1">mdi-chart-scatter-plot</v-icon>
      <div class="text-grey mt-2 text-body-2">Not enough data to compute coupling</div>
    </div>

    <!-- Single transcript notice -->
    <div v-else-if="transcripts.length === 1" class="single-notice">
      <v-icon size="18" class="mr-2" color="warning">mdi-information-outline</v-icon>
      Only one isoform detected — coupling requires ≥ 2 isoforms for comparison.
    </div>

    <template v-else>
      <!-- Per-sample breakdown -->
      <div class="breakdown-section">
        <div class="breakdown-title">Per–Cell Line APA Distribution</div>
        <div class="breakdown-subtitle">
          Each bar represents a cell line. Within each bar, segments show how polyA usage is distributed across sites.
          Isoforms with distinct segment proportions = high coupling.
        </div>

        <!-- Isoform breakdown bars -->
        <div class="isoform-breakdown-grid">
          <div
            v-for="tx in transcripts"
            :key="tx.transcript_id"
            class="isoform-row"
          >
            <div class="isoform-row-label">
              <router-link
                :to="{ name: 'LocusDetail', params: { transcriptId: tx.transcript_id } }"
                class="tx-link"
              >
                {{ tx.transcript_id }}
              </router-link>
              <div class="sites-inline">
                <span
                  v-for="site in tx.apa_sites"
                  :key="site.site_id"
                  class="site-dot"
                  :style="{ background: siteColor(site.site_id) }"
                  :title="site.site_id"
                ></span>
              </div>
            </div>

            <div class="sample-bars">
              <div
                v-for="sample in allSamples"
                :key="sample"
                class="sample-bar-wrap"
              >
                <div class="sample-bar-label">{{ sample }}</div>
                <div class="stacked-bar">
                  <div
                    v-for="site in tx.apa_sites"
                    :key="site.site_id"
                    class="bar-segment"
                    :style="barSegmentStyle(tx, site, sample)"
                    :title="`${site.site_id}\n${sample}: ${getAbundance(tx, site, sample)}%`"
                  ></div>
                  <!-- Empty state -->
                  <div
                    v-if="!txHasSample(tx, sample)"
                    class="bar-empty"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- JSD heatmap: pairwise per-sample divergence -->
      <div v-if="pairwiseJSD.length > 0" class="jsd-section">
        <div class="breakdown-title">Pairwise Isoform Divergence (JSD)</div>
        <div class="breakdown-subtitle">
          Jensen–Shannon divergence between each pair of isoforms per cell line.
          High JSD = isoforms use very different polyA sites in that cell line.
        </div>

        <div class="jsd-matrix-scroll">
          <table class="jsd-matrix">
            <thead>
              <tr>
                <th class="jsd-corner"></th>
                <th v-for="sample in allSamples" :key="sample" class="jsd-col-header">
                  {{ sample }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="pair in pairwiseJSD" :key="pair.label">
                <td class="jsd-row-label">{{ pair.label }}</td>
                <td
                  v-for="sample in allSamples"
                  :key="sample"
                  class="jsd-cell"
                  :title="`JSD = ${(pair.jsdBySample[sample] ?? 0).toFixed(3)}`"
                >
                  <div
                    class="jsd-block"
                    :style="jsdCellStyle(pair.jsdBySample[sample])"
                  >
                    <span class="jsd-value">
                      {{ formatJSD(pair.jsdBySample[sample]) }}
                    </span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Per-site coupling contribution bars -->
      <div class="site-coupling-section">
        <div class="breakdown-title">Per–Site Isoform Specificity</div>
        <div class="breakdown-subtitle">
          For each polyA site, how unevenly is it distributed across isoforms? High variance = isoform-specific.
        </div>
        <div class="site-bars">
          <div
            v-for="site in siteSpecificity"
            :key="site.site_id"
            class="site-spec-row"
          >
            <div class="site-spec-label">
              <span class="site-color-dot" :style="{ background: siteColor(site.site_id) }"></span>
              <span class="site-pos-text">{{ formatPos(site.site_position) }}</span>
              <span :class="['site-spec-badge', site.isSpecific ? 'badge-specific' : 'badge-common']">
                {{ site.isSpecific ? 'Isoform-specific' : 'Constitutive' }}
              </span>
            </div>
            <div class="site-spec-bar-track">
              <div
                class="site-spec-bar-fill"
                :style="{ width: `${site.specificityPct}%`, background: siteColor(site.site_id) }"
              ></div>
              <span class="site-spec-pct">{{ site.specificityPct }}%</span>
            </div>
          </div>
        </div>
      </div>
    </template>
    </div><!-- /panel-content -->
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  geneData: {
    type: Object,
    required: true
  }
})

// Palette for APA sites
const SITE_PALETTE = [
  '#1565c0', '#c62828', '#2e7d32', '#6a1b9a',
  '#e65100', '#00838f', '#4e342e', '#283593',
  '#ad1457', '#558b2f', '#1565c0', '#ff6f00'
]

const siteColorMap = new Map()

function siteColor(siteId) {
  if (!siteColorMap.has(siteId)) {
    siteColorMap.set(siteId, SITE_PALETTE[siteColorMap.size % SITE_PALETTE.length])
  }
  return siteColorMap.get(siteId)
}

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

const transcripts = computed(() => props.geneData?.transcripts ?? [])

const allSamples = computed(() => {
  const s = new Set()
  for (const tx of transcripts.value) {
    for (const site of tx.apa_sites ?? []) {
      for (const sd of site.sample_details ?? []) {
        s.add(sd.sample_name)
      }
    }
  }
  return [...s].sort()
})

const allSites = computed(() => {
  const s = new Map()
  for (const tx of transcripts.value) {
    for (const site of tx.apa_sites ?? []) {
      if (!s.has(site.site_id)) {
        s.set(site.site_id, { site_id: site.site_id, site_position: site.site_position })
      }
    }
  }
  return [...s.values()].sort((a, b) => a.site_position - b.site_position)
})

// ---------------------------------------------------------------------------
// Abundance helpers
// ---------------------------------------------------------------------------

function getAbundanceRaw(tx, site, sample) {
  const siteObj = tx.apa_sites?.find(s => s.site_id === site.site_id)
  if (!siteObj) return 0
  const sd = siteObj.sample_details?.find(d => d.sample_name === sample)
  return sd?.site_abundance ?? 0
}

function getAbundance(tx, site, sample) {
  return (getAbundanceRaw(tx, site, sample) * 100).toFixed(1)
}

function txHasSample(tx, sample) {
  return tx.apa_sites?.some(site =>
    site.sample_details?.some(sd => sd.sample_name === sample)
  ) ?? false
}

// Build per-transcript distribution vector over allSites for a given sample
function txDistribution(tx, sample) {
  const vec = allSites.value.map(site => getAbundanceRaw(tx, site, sample))
  const sum = vec.reduce((a, b) => a + b, 0)
  if (sum === 0) return null  // not expressed in this sample
  return vec.map(v => v / sum)
}

// ---------------------------------------------------------------------------
// Jensen-Shannon Divergence
// ---------------------------------------------------------------------------

function klDivergence(p, q, epsilon = 1e-10) {
  return p.reduce((sum, pi, i) => {
    if (pi < epsilon) return sum
    const qi = Math.max(q[i], epsilon)
    return sum + pi * Math.log2(pi / qi)
  }, 0)
}

function jsd(p, q) {
  const m = p.map((pi, i) => (pi + q[i]) / 2)
  return 0.5 * klDivergence(p, m) + 0.5 * klDivergence(q, m)
}

// ---------------------------------------------------------------------------
// Pairwise JSD matrix
// ---------------------------------------------------------------------------

const pairwiseJSD = computed(() => {
  const txs = transcripts.value
  if (txs.length < 2) return []
  const pairs = []
  for (let i = 0; i < txs.length; i++) {
    for (let j = i + 1; j < txs.length; j++) {
      const label = `${txs[i].transcript_id} vs ${txs[j].transcript_id}`
      const jsdBySample = {}
      for (const sample of allSamples.value) {
        const p = txDistribution(txs[i], sample)
        const q = txDistribution(txs[j], sample)
        if (p && q) {
          jsdBySample[sample] = Math.max(0, Math.min(1, jsd(p, q)))
        }
      }
      pairs.push({ label, jsdBySample })
    }
  }
  return pairs
})

// ---------------------------------------------------------------------------
// Global coupling score (0–100)
// ---------------------------------------------------------------------------

const globalScore = computed(() => {
  if (transcripts.value.length < 2) return 0
  let totalJSD = 0
  let count = 0
  for (const pair of pairwiseJSD.value) {
    for (const sample of allSamples.value) {
      if (pair.jsdBySample[sample] !== undefined) {
        totalJSD += pair.jsdBySample[sample]
        count++
      }
    }
  }
  if (count === 0) return 0
  return Math.round((totalJSD / count) * 100)
})

const scoreColor = computed(() => {
  const s = globalScore.value
  if (s >= 70) return '#c62828'   // red – strong coupling
  if (s >= 40) return '#e65100'   // orange – moderate
  if (s >= 15) return '#f9a825'   // amber – weak
  return '#81c784'                // green – decoupled
})

const scoreLabel = computed(() => {
  const s = globalScore.value
  if (s >= 70) return 'Strong'
  if (s >= 40) return 'Moderate'
  if (s >= 15) return 'Weak'
  return 'Decoupled'
})

// Ring chart geometry
const CIRCUMFERENCE = 2 * Math.PI * 24
const dashTotal = computed(() => CIRCUMFERENCE)
const dashVal = computed(() => (globalScore.value / 100) * CIRCUMFERENCE)
const ringStyle = computed(() => ({ '--circ': CIRCUMFERENCE }))

// ---------------------------------------------------------------------------
// Site specificity
// ---------------------------------------------------------------------------

const siteSpecificity = computed(() => {
  return allSites.value.map(site => {
    // For each sample, collect abundance per transcript, compute variance
    let totalVariance = 0
    let count = 0
    for (const sample of allSamples.value) {
      const vals = transcripts.value.map(tx => getAbundanceRaw(tx, site, sample))
      const expressed = vals.filter(v => v > 0)
      if (expressed.length < 2) continue
      const mean = expressed.reduce((a, b) => a + b, 0) / expressed.length
      const variance = expressed.reduce((s, v) => s + (v - mean) ** 2, 0) / expressed.length
      totalVariance += variance
      count++
    }
    const avgVariance = count > 0 ? totalVariance / count : 0
    // Normalise: variance up to 0.25 (max for binary split) → 0–100%
    const specificityPct = Math.round(Math.min(avgVariance / 0.25, 1) * 100)
    return {
      ...site,
      specificityPct,
      isSpecific: specificityPct >= 30
    }
  })
})

// ---------------------------------------------------------------------------
// Style helpers
// ---------------------------------------------------------------------------

function barSegmentStyle(tx, site, sample) {
  const val = getAbundanceRaw(tx, site, sample)
  const color = siteColor(site.site_id)
  return {
    width: `${val * 100}%`,
    background: color,
    opacity: val > 0 ? 1 : 0,
    transition: 'width 0.4s ease'
  }
}

function jsdCellStyle(val) {
  if (val === undefined || val === null) {
    return { background: '#e9ecef', opacity: 0.4 }
  }
  // 0 = white/light, 1 = deep red
  const t = Math.min(1, Math.max(0, val))
  const r = Math.round(255 + (198 - 255) * t)
  const g = Math.round(255 + (40 - 255) * t)
  const b = Math.round(255 + (40 - 255) * t)
  return { background: `rgb(${r},${g},${b})` }
}

function formatJSD(val) {
  if (val === undefined || val === null) return '—'
  return val.toFixed(2)
}

function formatPos(pos) {
  return pos?.toLocaleString() ?? '?'
}
</script>

<style scoped>
/* ── Base ───────────────────────────────────────────────────────────────── */
.coupling-panel {
  font-family: inherit;
}

/* ── Header (unified panel style) ──────────────────────────────────────── */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
  background: rgba(13, 115, 119, 0.06);
  border-bottom: 1px solid rgba(13, 115, 119, 0.12);
  flex-wrap: wrap;
  margin: -1px -1px 16px -1px; /* bleed to panel-box edges */
}

.panel-title-block {
  display: flex;
  align-items: center;
  gap: 10px;
}

.panel-icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: #0D7377;
  flex-shrink: 0;
}

.panel-title {
  font-size: 0.92rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.82);
  line-height: 1.3;
}

.panel-subtitle {
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.46);
  margin-top: 2px;
  max-width: 480px;
}


/* ── Content body padding ───────────────────────────────────────────────── */
.panel-content {
  padding: 16px 18px;
}


.score-badge-wrap { flex-shrink: 0; }

.global-score-badge {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: help;
}

.score-ring {
  position: relative;
  width: 60px;
  height: 60px;
  flex-shrink: 0;
}

.ring-svg {
  width: 60px;
  height: 60px;
  transform: rotate(-90deg);
}

.ring-bg {
  fill: none;
  stroke: #e0e0e0;
  stroke-width: 5;
}

.ring-fg {
  fill: none;
  stroke-width: 5;
  stroke-linecap: round;
  transition: stroke-dasharray 0.6s ease;
}

.ring-label {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.05rem;
  font-weight: 700;
  color: rgba(0,0,0,0.85);
}

.score-meta { display: flex; flex-direction: column; gap: 2px; }

.score-level {
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.score-caption {
  font-size: 0.7rem;
  color: rgba(0,0,0,0.45);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

/* ── Section titles ─────────────────────────────────────────────────────── */
.breakdown-section,
.jsd-section,
.site-coupling-section {
  margin-top: 20px;
}

.breakdown-title {
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: rgba(0,0,0,0.55);
  margin-bottom: 4px;
}

.breakdown-subtitle {
  font-size: 0.76rem;
  color: rgba(0,0,0,0.45);
  margin-bottom: 12px;
  max-width: 640px;
}

/* ── Isoform distribution bars ──────────────────────────────────────────── */
.isoform-breakdown-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.isoform-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 10px;
  background: rgba(0,0,0,0.02);
  border-radius: 8px;
  border: 1px solid #eeeeee;
}

.isoform-row-label {
  min-width: 160px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tx-link {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.78rem;
  color: rgb(var(--v-theme-primary));
  text-decoration: none;
  font-weight: 600;
}
.tx-link:hover { text-decoration: underline; }

.sites-inline {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.site-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.sample-bars {
  display: flex;
  gap: 10px;
  flex: 1;
  flex-wrap: wrap;
}

.sample-bar-wrap {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1;
  min-width: 80px;
}

.sample-bar-label {
  font-size: 0.68rem;
  color: rgba(0,0,0,0.5);
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.stacked-bar {
  height: 20px;
  border-radius: 4px;
  overflow: hidden;
  background: #e9ecef;
  display: flex;
  position: relative;
  border: 1px solid rgba(0,0,0,0.06);
}

.bar-segment {
  height: 100%;
  transition: width 0.4s ease;
}

.bar-empty {
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    45deg,
    transparent,
    transparent 3px,
    rgba(0,0,0,0.04) 3px,
    rgba(0,0,0,0.04) 6px
  );
}

/* ── JSD Matrix ─────────────────────────────────────────────────────────── */
.jsd-matrix-scroll {
  overflow-x: auto;
}

.jsd-matrix {
  border-collapse: separate;
  border-spacing: 4px;
  font-size: 0.8rem;
}

.jsd-corner { width: 120px; }

.jsd-col-header {
  text-align: center;
  font-size: 0.72rem;
  font-weight: 600;
  color: rgba(0,0,0,0.55);
  padding: 4px 8px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.jsd-row-label {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.72rem;
  color: rgba(0,0,0,0.65);
  padding: 4px 10px 4px 0;
  white-space: nowrap;
}

.jsd-cell {
  padding: 2px;
  vertical-align: middle;
  text-align: center;
}

.jsd-block {
  width: 70px;
  height: 30px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.1s;
  cursor: default;
}
.jsd-block:hover {
  transform: scale(1.06);
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}

.jsd-value {
  font-size: 0.72rem;
  font-weight: 700;
  color: rgba(0,0,0,0.7);
  text-shadow: 0 1px 1px rgba(255,255,255,0.6);
}

/* ── Site Specificity ───────────────────────────────────────────────────── */
.site-bars {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.site-spec-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.site-spec-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.site-color-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.site-pos-text {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.78rem;
  color: rgba(0,0,0,0.7);
}

.site-spec-badge {
  font-size: 0.68rem;
  font-weight: 600;
  padding: 1px 7px;
  border-radius: 10px;
}

.badge-specific {
  background: rgba(198, 40, 40, 0.1);
  color: #c62828;
  border: 1px solid rgba(198, 40, 40, 0.2);
}

.badge-common {
  background: rgba(46, 125, 50, 0.1);
  color: #2e7d32;
  border: 1px solid rgba(46, 125, 50, 0.2);
}

.site-spec-bar-track {
  height: 10px;
  background: #e9ecef;
  border-radius: 5px;
  overflow: hidden;
  position: relative;
}

.site-spec-bar-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.5s ease;
  opacity: 0.85;
}

.site-spec-pct {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.63rem;
  font-weight: 700;
  color: rgba(0,0,0,0.55);
}

/* ── Misc ───────────────────────────────────────────────────────────────── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 0;
  color: rgba(0,0,0,0.4);
}

.single-notice {
  display: flex;
  align-items: center;
  font-size: 0.82rem;
  color: rgba(0,0,0,0.55);
  background: rgba(255, 160, 0, 0.08);
  border: 1px solid rgba(255, 160, 0, 0.25);
  border-radius: 8px;
  padding: 10px 14px;
  margin-top: 8px;
}

.tooltip-content {
  font-size: 0.8rem;
  line-height: 1.5;
}
</style>
