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
            <div class="panel-subtitle">Which PA sites are shared across isoforms vs. exclusive to one?</div>
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
            <span class="legend-swatch" style="background: rgba(13,115,119,0.06);border:1px solid rgba(13,115,119,0.15)"></span>
            Absent
          </span>
        </div>
      </div>
    </div>

    <!-- No APA sites or single transcript -->
    <div v-if="allSites.length === 0" class="empty-state">
      <v-icon size="40" color="grey-lighten-1">mdi-table-off</v-icon>
      <div class="text-grey mt-2 text-body-2">No PA site data available</div>
    </div>

    <template v-else>
      <!-- Matrix -->
      <div class="matrix-wrapper" ref="matrixWrapper">
        <div class="matrix-scroll">
          <table class="fingerprint-matrix">
            <!-- Transcript header row -->
            <thead>
              <tr>
                <th class="site-label-header">PA Site</th>
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
                :key="site.unified_id"
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
      const key = site.unified_id
      if (!siteMap.has(key)) {
        const allSamples = new Set()
        for (const sd of site.sample_details ?? []) {
          allSamples.add(sd.sample_name)
        }
        siteMap.set(key, {
          unified_id: site.unified_id,
          mode_site_position: site.mode_site_position,
          short_id: formatPosition(site.unified_id, site.mode_site_position),
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
  return [...siteMap.values()].sort((a, b) => a.mode_site_position - b.mode_site_position)
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
    return { background: 'rgba(13,115,119,0.06)', opacity: 0.7 }
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
  // t: 0→1 mapping to low→high usage
  // low: #d0f0f1 (light teal), high: #0A5C5F (deep teal — primary-darken-1)
  const r1 = 208, g1 = 240, b1 = 241
  const r2 = 10,  g2 = 92,  b2 = 95
  return `rgb(${Math.round(r1 + (r2-r1)*t)}, ${Math.round(g1 + (g2-g1)*t)}, ${Math.round(b1 + (b2-b1)*t)})`
}
</script>

<style scoped>
/* ── CSS Variables ─────────────────────────────────────────────────────── */
.isoform-fingerprint-panel {
  --heat-high: #0A5C5F;
  --heat-low: #d0f0f1;
  --shared-color: #0D7377;
  --private-color: #C9821A;
  --border: rgba(13, 115, 119, 0.15);
  --row-hover: rgba(13, 115, 119, 0.04);

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
  font-size: 14.5px;
  font-weight: 600;
  color: #0f172a;
  line-height: 1.3;
  font-family: 'Roboto', sans-serif;
}

.panel-subtitle {
  font-size: 13.5px;
  color: #475569;
  margin-top: 2px;
  font-family: 'Roboto', sans-serif;
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
  font-size: 13px;
  color: #475569;
  font-family: 'Roboto', sans-serif;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.legend-dot.shared  { background: var(--shared-color); }
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
  font-size: 13.5px;
  font-family: 'Roboto', sans-serif;
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
  font-size: 13px;
  color: #0D7377;
  text-decoration: none;
  writing-mode: vertical-rl;
  text-orientation: mixed;
  transform: rotate(180deg);
  height: 78px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  letter-spacing: 0.01em;
  font-weight: 500;
  font-family: 'Inter', sans-serif;
}
.tx-link:hover { text-decoration: underline; }

.site-label-header {
  padding: 0 12px 6px 0;
  text-align: left;
  vertical-align: bottom;
  border-bottom: 2px solid var(--border);
  font-weight: 600;
  font-size: 13px;
  color: #475569;
  white-space: nowrap;
  min-width: 140px;
  font-family: 'Roboto', sans-serif;
}

.badge-header {
  padding: 0 0 6px 12px;
  text-align: left;
  vertical-align: bottom;
  border-bottom: 2px solid var(--border);
  font-weight: 600;
  font-size: 13px;
  color: #475569;
  white-space: nowrap;
  font-family: 'Roboto', sans-serif;
}

/* Matrix rows */
.matrix-row {
  transition: background 0.15s;
}
.matrix-row:hover {
  background: var(--row-hover);
}
.matrix-row:not(:last-child) td {
  border-bottom: 1px solid rgba(13, 115, 119, 0.07);
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
  font-family: 'Inter', sans-serif;
  font-size: 13px;
  color: #0f172a;
  background: rgba(13, 115, 119, 0.08);
  padding: 2px 7px;
  border-radius: 4px;
  font-weight: 600;
}

.sample-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
  margin-top: 4px;
}

.sample-pill {
  font-size: 12px;
  background: rgba(13, 115, 119, 0.10);
  color: #0D7377;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 500;
  font-family: 'Inter', sans-serif;
  border: 1px solid rgba(13, 115, 119, 0.20);
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
  box-shadow: 0 2px 8px rgba(13, 115, 119, 0.25);
  z-index: 1;
  position: relative;
}

.cell-pct {
  font-size: 12px;
  font-weight: 700;
  color: white;
  text-shadow: 0 1px 2px rgba(0,0,0,0.35);
  pointer-events: none;
  font-family: 'Inter', sans-serif;
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
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.03em;
  font-family: 'Inter', sans-serif;
  white-space: nowrap;
}

.badge-shared {
  background: rgba(13, 115, 119, 0.10);
  color: #0A5C5F;
  border: 1px solid rgba(13, 115, 119, 0.28);
}

.badge-private {
  background: rgba(201, 130, 26, 0.10);
  color: #7a4f00;
  border: 1px solid rgba(201, 130, 26, 0.30);
}

/* ── Summary Strip ──────────────────────────────────────────────────────── */
.summary-strip {
  display: flex;
  align-items: center;
  gap: 0;
  margin-top: 16px;
  padding: 12px 16px;
  background: rgba(13, 115, 119, 0.04);
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
  font-size: 1.35rem;
  font-weight: 700;
  line-height: 1.2;
  color: #0f172a;
  font-family: 'Inter', sans-serif;
}

.stat-label {
  font-size: 12px;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-top: 2px;
  font-family: 'Roboto', sans-serif;
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
  color: #475569;
}
</style>
