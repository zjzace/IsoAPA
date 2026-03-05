<template>
  <div class="isoform-fingerprint-panel">
    <!-- Header -->
    <div class="panel-header">
      <div class="panel-title-row">
        <div class="panel-title-block">
          <span class="panel-icon">
            <v-icon color="primary" size="20">mdi-fingerprint</v-icon>
          </span>
          <div>
            <div class="panel-title">Isoform–APA Fingerprint</div>
            <div class="panel-subtitle">Which APA sites are shared across isoforms vs. exclusive to one?</div>
          </div>
        </div>
        <div class="legend-row">
          <span class="legend-item">
            <span class="legend-dot shared"></span> Shared
          </span>
          <span class="legend-item">
            <span class="legend-dot private"></span> Private
          </span>
          <span class="legend-item">
            <span class="legend-swatch" style="background: var(--heat-high)"></span>
            High usage
          </span>
          <span class="legend-item">
            <span class="legend-swatch" style="background: var(--heat-low)"></span>
            Low
          </span>
          <span class="legend-item">
            <span class="legend-swatch" style="background: #e9ecef"></span>
            Absent
          </span>
        </div>
      </div>
    </div>

    <!-- No APA sites or single transcript -->
    <div v-if="allSites.length === 0" class="empty-state">
      <v-icon size="40" color="grey-lighten-1">mdi-table-off</v-icon>
      <div class="text-grey mt-2 text-body-2">No APA site data available</div>
    </div>

    <template v-else>
      <!-- Matrix -->
      <div class="matrix-wrapper" ref="matrixWrapper">
        <div class="matrix-scroll">
          <table class="fingerprint-matrix">
            <!-- Transcript header row -->
            <thead>
              <tr>
                <th class="site-label-header">APA Site</th>
                <th
                  v-for="tx in transcripts"
                  :key="tx.transcript_id"
                  class="tx-header"
                  :title="tx.transcript_id"
                >
                  <div class="tx-label-rotated">
                    <router-link
                      :to="{ name: 'LocusDetail', params: { transcriptId: tx.transcript_id } }"
                      class="tx-link"
                    >
                      {{ shortId(tx.transcript_id) }}
                    </router-link>
                  </div>
                </th>
                <th class="badge-header">Classification</th>
              </tr>
            </thead>

            <tbody>
              <tr
                v-for="site in allSites"
                :key="site.site_id"
                :class="['matrix-row', isShared(site) ? 'row-shared' : 'row-private']"
              >
                <!-- Site position label -->
                <td class="site-label">
                  <div class="site-pos">
                    <span class="site-chr">{{ site.short_id }}</span>
                  </div>
                  <div class="sample-chips">
                    <span
                      v-for="s in site.samples"
                      :key="s"
                      class="sample-pill"
                    >{{ s }}</span>
                  </div>
                </td>

                <!-- Cells: one per transcript -->
                <td
                  v-for="tx in transcripts"
                  :key="tx.transcript_id"
                  class="matrix-cell"
                >
                  <div
                    class="cell-block"
                    :style="cellStyle(site, tx)"
                    :title="cellTitle(site, tx)"
                  >
                    <span v-if="getCellValue(site, tx) > 0" class="cell-pct">
                      {{ (getCellValue(site, tx) * 100).toFixed(0) }}%
                    </span>
                  </div>
                </td>

                <!-- Classification badge -->
                <td class="badge-cell">
                  <span :class="['site-badge', isShared(site) ? 'badge-shared' : 'badge-private']">
                    <v-icon size="12" class="mr-1">{{ isShared(site) ? 'mdi-share-variant' : 'mdi-lock-outline' }}</v-icon>
                    {{ isShared(site) ? `Shared (${sharedByCount(site)})` : 'Private' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Summary strip -->
      <div class="summary-strip">
        <div class="summary-stat">
          <span class="stat-num">{{ allSites.length }}</span>
          <span class="stat-label">Total Sites</span>
        </div>
        <div class="summary-divider"></div>
        <div class="summary-stat">
          <span class="stat-num text-success">{{ sharedSites.length }}</span>
          <span class="stat-label">Shared</span>
        </div>
        <div class="summary-divider"></div>
        <div class="summary-stat">
          <span class="stat-num text-warning">{{ privateSites.length }}</span>
          <span class="stat-label">Private</span>
        </div>
        <div class="summary-divider"></div>
        <div class="summary-stat">
          <span class="stat-num">{{ transcripts.length }}</span>
          <span class="stat-label">Isoforms</span>
        </div>
        <div class="summary-divider"></div>
        <div class="summary-stat">
          <span class="stat-num text-primary">{{ sharingIndex }}%</span>
          <span class="stat-label">Sharing Index</span>
        </div>
      </div>
    </template>
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

// ---------------------------------------------------------------------------
// Data derivation
// ---------------------------------------------------------------------------

const transcripts = computed(() => props.geneData?.transcripts ?? [])

// All unique APA sites across all transcripts, deduplicated by position
const allSites = computed(() => {
  const siteMap = new Map()
  for (const tx of transcripts.value) {
    for (const site of tx.apa_sites ?? []) {
      const key = site.site_id
      if (!siteMap.has(key)) {
        const allSamples = new Set()
        for (const sd of site.sample_details ?? []) {
          allSamples.add(sd.sample_name)
        }
        siteMap.set(key, {
          site_id: site.site_id,
          site_position: site.site_position,
          short_id: formatPosition(site.site_id, site.site_position),
          samples: [...allSamples],
          // map of transcript_id -> sample_details
          transcriptData: new Map([[tx.transcript_id, site.sample_details ?? []]])
        })
      } else {
        const existing = siteMap.get(key)
        existing.transcriptData.set(tx.transcript_id, site.sample_details ?? [])
        for (const sd of site.sample_details ?? []) {
          existing.samples.push(sd.sample_name)
        }
        existing.samples = [...new Set(existing.samples)]
      }
    }
  }
  // Sort by genomic position
  return [...siteMap.values()].sort((a, b) => a.site_position - b.site_position)
})

const sharedSites = computed(() => allSites.value.filter(s => isShared(s)))
const privateSites = computed(() => allSites.value.filter(s => !isShared(s)))

const sharingIndex = computed(() => {
  if (allSites.value.length === 0) return 0
  return Math.round((sharedSites.value.length / allSites.value.length) * 100)
})

// ---------------------------------------------------------------------------
// Cell helpers
// ---------------------------------------------------------------------------

function getCellValue(site, tx) {
  const details = site.transcriptData.get(tx.transcript_id) ?? []
  if (details.length === 0) return 0
  const sum = details.reduce((acc, d) => acc + (d.site_abundance ?? 0), 0)
  return sum / details.length  // mean across samples
}

function cellStyle(site, tx) {
  const val = getCellValue(site, tx)
  if (val === 0) {
    return { background: '#e9ecef', opacity: 0.5 }
  }
  // Linear interpolation from low (#c8e6c9) to high (#1b5e20)
  const intensity = Math.min(1, val)
  return {
    background: interpolateGreen(intensity),
    opacity: 1
  }
}

function cellTitle(site, tx) {
  const details = site.transcriptData.get(tx.transcript_id) ?? []
  if (details.length === 0) return `${tx.transcript_id}: absent`
  const lines = details.map(d => `${d.sample_name}: ${(d.site_abundance * 100).toFixed(1)}%`).join('\n')
  return `${tx.transcript_id}\n${lines}`
}

function isShared(site) {
  return sharedByCount(site) >= 2
}

function sharedByCount(site) {
  return transcripts.value.filter(tx => {
    const details = site.transcriptData.get(tx.transcript_id) ?? []
    return details.length > 0
  }).length
}

// ---------------------------------------------------------------------------
// Formatting
// ---------------------------------------------------------------------------

function shortId(id) {
  // ENST00000000233 → T00233
  if (id.startsWith('ENST')) {
    return id.replace('ENST', 'T').replace(/^T0+/, 'T')
  }
  return id.slice(-8)
}

function formatPosition(siteId, pos) {
  // "7:127591700:+" → "127,591,700"
  return pos.toLocaleString()
}

function interpolateGreen(t) {
  // t: 0 → 1 mapping to low → high usage
  // low: #c8e6c9 (light green), high: #1565c0 (deep blue-green via teal)
  const r1 = 200, g1 = 230, b1 = 201
  const r2 = 21,  g2 = 101, b2 = 192
  return `rgb(${Math.round(r1 + (r2-r1)*t)}, ${Math.round(g1 + (g2-g1)*t)}, ${Math.round(b1 + (b2-b1)*t)})`
}
</script>

<style scoped>
/* ── CSS Variables ─────────────────────────────────────────────────────── */
.isoform-fingerprint-panel {
  --heat-high: #1565c0;
  --heat-low: #c8e6c9;
  --shared-color: #2e7d32;
  --private-color: #e65100;
  --border: #e0e0e0;
  --row-hover: rgba(25, 118, 210, 0.04);

  font-family: inherit;
}

/* ── Panel Header ──────────────────────────────────────────────────────── */
.panel-header {
  padding: 0 0 12px 0;
  border-bottom: 1px solid var(--border);
  margin-bottom: 16px;
}

.panel-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.panel-title-block {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.panel-icon {
  margin-top: 2px;
  flex-shrink: 0;
}

.panel-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.87);
  line-height: 1.3;
}

.panel-subtitle {
  font-size: 0.78rem;
  color: rgba(0, 0, 0, 0.5);
  margin-top: 2px;
}

/* ── Legend ─────────────────────────────────────────────────────────────── */
.legend-row {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.75rem;
  color: rgba(0,0,0,0.6);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.legend-dot.shared { background: var(--shared-color); }
.legend-dot.private { background: var(--private-color); }

.legend-swatch {
  width: 18px;
  height: 10px;
  border-radius: 3px;
  flex-shrink: 0;
}

/* ── Matrix ─────────────────────────────────────────────────────────────── */
.matrix-wrapper {
  position: relative;
}

.matrix-scroll {
  overflow-x: auto;
  overflow-y: visible;
  -webkit-overflow-scrolling: touch;
}

.fingerprint-matrix {
  border-collapse: separate;
  border-spacing: 0;
  min-width: 100%;
  font-size: 0.82rem;
}

/* Column header: rotated transcript IDs */
.tx-header {
  padding: 0 4px 6px 4px;
  vertical-align: bottom;
  text-align: center;
  border-bottom: 2px solid var(--border);
  white-space: nowrap;
  min-width: 54px;
  max-width: 54px;
  width: 54px;
}

.tx-label-rotated {
  display: flex;
  justify-content: center;
  padding-bottom: 2px;
}

.tx-link {
  font-size: 0.75rem;
  color: rgb(var(--v-theme-primary));
  text-decoration: none;
  writing-mode: vertical-rl;
  text-orientation: mixed;
  transform: rotate(180deg);
  height: 78px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  letter-spacing: 0.01em;
}
.tx-link:hover { text-decoration: underline; }

.site-label-header {
  padding: 0 12px 6px 0;
  text-align: left;
  vertical-align: bottom;
  border-bottom: 2px solid var(--border);
  font-weight: 600;
  font-size: 0.78rem;
  color: rgba(0,0,0,0.6);
  white-space: nowrap;
  min-width: 140px;
}

.badge-header {
  padding: 0 0 6px 12px;
  text-align: left;
  vertical-align: bottom;
  border-bottom: 2px solid var(--border);
  font-weight: 600;
  font-size: 0.78rem;
  color: rgba(0,0,0,0.6);
  white-space: nowrap;
}

/* Matrix rows */
.matrix-row {
  transition: background 0.15s;
}
.matrix-row:hover {
  background: var(--row-hover);
}
.matrix-row:not(:last-child) td {
  border-bottom: 1px solid #f5f5f5;
}

.row-shared .site-label::before {
  content: '';
  display: block;
  width: 3px;
  height: 100%;
  background: var(--shared-color);
  position: absolute;
  left: 0;
  top: 0;
  border-radius: 0 2px 2px 0;
}

/* Site label cell */
.site-label {
  padding: 8px 12px 8px 8px;
  position: relative;
  vertical-align: middle;
  white-space: nowrap;
}

.site-pos {
  display: flex;
  align-items: center;
  gap: 6px;
}

.site-chr {
  font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
  font-size: 0.78rem;
  color: rgba(0,0,0,0.75);
  background: rgba(0,0,0,0.04);
  padding: 1px 6px;
  border-radius: 4px;
}

.sample-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
  margin-top: 4px;
}

.sample-pill {
  font-size: 0.65rem;
  background: rgba(25, 118, 210, 0.1);
  color: rgb(25, 118, 210);
  padding: 1px 5px;
  border-radius: 10px;
  font-weight: 500;
}

/* Matrix data cells */
.matrix-cell {
  padding: 4px 5px;
  text-align: center;
  vertical-align: middle;
}

.cell-block {
  width: 44px;
  height: 32px;
  border-radius: 6px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.1s, box-shadow 0.1s;
  cursor: default;
}
.cell-block:hover {
  transform: scale(1.08);
  box-shadow: 0 2px 8px rgba(0,0,0,0.18);
  z-index: 1;
  position: relative;
}

.cell-pct {
  font-size: 0.68rem;
  font-weight: 700;
  color: white;
  text-shadow: 0 1px 2px rgba(0,0,0,0.35);
  pointer-events: none;
}

/* Classification badges */
.badge-cell {
  padding: 4px 0 4px 12px;
  vertical-align: middle;
  white-space: nowrap;
}

.site-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 9px;
  border-radius: 12px;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.01em;
}

.badge-shared {
  background: rgba(46, 125, 50, 0.12);
  color: var(--shared-color);
  border: 1px solid rgba(46, 125, 50, 0.25);
}

.badge-private {
  background: rgba(230, 81, 0, 0.1);
  color: var(--private-color);
  border: 1px solid rgba(230, 81, 0, 0.22);
}

/* ── Summary Strip ──────────────────────────────────────────────────────── */
.summary-strip {
  display: flex;
  align-items: center;
  gap: 0;
  margin-top: 16px;
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.025);
  border-radius: 8px;
  border: 1px solid var(--border);
}

.summary-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.stat-num {
  font-size: 1.25rem;
  font-weight: 700;
  line-height: 1.2;
  color: rgba(0,0,0,0.85);
}

.stat-label {
  font-size: 0.7rem;
  color: rgba(0,0,0,0.5);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-top: 2px;
}

.summary-divider {
  width: 1px;
  height: 36px;
  background: var(--border);
  flex-shrink: 0;
}

/* ── Empty State ────────────────────────────────────────────────────────── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 0;
  color: rgba(0,0,0,0.4);
}
</style>
