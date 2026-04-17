<template>
  <v-app>
    <!-- Glassmorphism navbar -->
    <v-app-bar
      :elevation="0"
      class="glass-navbar"
      height="60"
    >
      <v-container class="d-flex align-center py-0" style="max-width:1280px;">
        <router-link to="/" class="text-decoration-none d-flex align-center">
          <div class="nav-logo-wrap mr-2">
            <ApaAtlasIcon :size="20" style="color:#0D7377;" />
          </div>
          <span class="nav-brand">ApaAtlas</span>
        </router-link>

        <v-spacer></v-spacer>

        <nav class="nav-links d-none d-md-flex align-center">
          <router-link to="/" class="nav-link" active-class="nav-link--active">Home</router-link>
          <router-link to="/search" class="nav-link" active-class="nav-link--active">Browse</router-link>
          <router-link to="/statistics" class="nav-link" active-class="nav-link--active">Statistics</router-link>
          <router-link to="/download" class="nav-link" active-class="nav-link--active">Download</router-link>
          <router-link to="/help" class="nav-link" active-class="nav-link--active">Help</router-link>
        </nav>

        <button class="theme-toggle ml-4" @click="toggleTheme" :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'">
          <v-icon size="18">{{ isDark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
        </button>
      </v-container>
    </v-app-bar>

    <v-main>
      <router-view></router-view>
    </v-main>

    <!-- Footer -->
    <footer class="app-footer">
      <v-container style="max-width:1280px;">
        <div class="footer-grid">
          <div class="footer-col">
            <div class="footer-brand d-flex align-center mb-3">
              <ApaAtlasIcon :size="18" style="color:#0D7377;" class="mr-2" />
              <span class="footer-brand-name">ApaAtlas</span>
            </div>
            <p class="footer-desc">A comprehensive database for isoform-level Alternative Polyadenylation (APA) loci.</p>
            <span class="footer-version">v1.0.0</span>
          </div>
          <div class="footer-col">
            <h4 class="footer-heading">Quick Links</h4>
            <div class="footer-links">
              <router-link to="/" class="footer-link">Home</router-link>
              <router-link to="/search" class="footer-link">Browse Data</router-link>
              <router-link to="/statistics" class="footer-link">Statistics</router-link>
              <router-link to="/download" class="footer-link">Download</router-link>
              <router-link to="/help" class="footer-link">Help &amp; Docs</router-link>
            </div>
          </div>
          <div class="footer-col">
            <h4 class="footer-heading">Contact</h4>
            <p class="footer-desc">For questions or feedback, please contact:</p>
            <a href="mailto:tf.chan@cuhk.edu.hk" class="footer-email">tf.chan@cuhk.edu.hk</a>
          </div>
        </div>
        <div class="footer-divider"></div>
        <p class="footer-copy">&copy; 2026 ApaAtlas. All rights reserved.</p>
      </v-container>
    </footer>
  </v-app>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useTheme } from 'vuetify'
import ApaAtlasIcon from '@/components/ApaAtlasIcon.vue'

const theme = useTheme()
const isDark = computed(() => theme.global.name.value === 'apaAtlasDarkTheme')

const toggleTheme = () => {
  theme.global.name.value = isDark.value ? 'apaAtlasTheme' : 'apaAtlasDarkTheme'
}
</script>

<style>
html, body, #app {
  font-family: 'Inter', 'Roboto', sans-serif !important;
  overflow-y: auto !important;
}
* {
  font-family: 'Inter', 'Roboto', sans-serif;
}
:root {
  --v-font-family: 'Inter', 'Roboto', sans-serif;
}
a {
  color: inherit;
}

/* ── Glassmorphism navbar ─────────────────────────────────── */
.glass-navbar {
  background: rgba(255, 255, 255, 0.72) !important;
  backdrop-filter: blur(18px) saturate(180%) !important;
  -webkit-backdrop-filter: blur(18px) saturate(180%) !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.07) !important;
}

.v-theme--apaAtlasDarkTheme .glass-navbar {
  background: rgba(15, 17, 23, 0.78) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07) !important;
}

.nav-logo-wrap {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(13, 115, 119, 0.10);
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-brand {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.3px;
  color: #0D7377;
}

.v-theme--apaAtlasDarkTheme .nav-brand {
  color: #2AA8AE;
}

.nav-links {
  gap: 4px;
}

.nav-link {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 14.5px;
  font-weight: 500;
  color: #4B5563;
  text-decoration: none;
  transition: background 150ms, color 150ms;
  letter-spacing: 0.1px;
}

.nav-link:hover {
  background: rgba(13, 115, 119, 0.08);
  color: #0D7377;
}

.nav-link--active {
  background: rgba(13, 115, 119, 0.10);
  color: #0D7377 !important;
  font-weight: 600;
}

.v-theme--apaAtlasDarkTheme .nav-link {
  color: #94A3B8;
}

.v-theme--apaAtlasDarkTheme .nav-link:hover,
.v-theme--apaAtlasDarkTheme .nav-link--active {
  background: rgba(42, 168, 174, 0.12);
  color: #2AA8AE !important;
}

.theme-toggle {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(0, 0, 0, 0.03);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #4B5563;
  transition: background 150ms, border-color 150ms;
}

.theme-toggle:hover {
  background: rgba(13, 115, 119, 0.08);
  border-color: rgba(13, 115, 119, 0.20);
  color: #0D7377;
}

.v-theme--apaAtlasDarkTheme .theme-toggle {
  border-color: rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  color: #94A3B8;
}

/* ── Footer ───────────────────────────────────────────────── */
.app-footer {
  background: #F8FAFB;
  border-top: 1px solid rgba(0, 0, 0, 0.07);
  padding: 48px 0 28px;
}

.v-theme--apaAtlasDarkTheme .app-footer {
  background: #13161E;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.footer-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr 1fr;
  gap: 40px;
  margin-bottom: 32px;
}

@media (max-width: 768px) {
  .footer-grid {
    grid-template-columns: 1fr;
    gap: 28px;
  }
}

.footer-brand-name {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.2px;
  color: #1E293B;
}

.v-theme--apaAtlasDarkTheme .footer-brand-name {
  color: #E2E8F0;
}

.footer-heading {
  font-size: 13.5px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: #94A3B8;
  margin-bottom: 14px;
}

.footer-desc {
  font-size: 14.5px;
  color: #64748B;
  line-height: 1.6;
  margin: 0 0 8px;
}

.footer-version {
  font-size: 12.5px;
  color: #94A3B8;
  font-family: 'Fira Code', monospace;
}

.footer-links {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.footer-link {
  font-size: 14.5px;
  color: #64748B;
  text-decoration: none;
  transition: color 150ms;
}

.footer-link:hover {
  color: #0D7377;
}

.footer-email {
  font-size: 14.5px;
  color: #0D7377;
  text-decoration: none;
  font-weight: 500;
}

.footer-email:hover {
  text-decoration: underline;
}

.footer-divider {
  height: 1px;
  background: rgba(0, 0, 0, 0.07);
  margin-bottom: 20px;
}

.v-theme--apaAtlasDarkTheme .footer-divider {
  background: rgba(255, 255, 255, 0.06);
}

.footer-copy {
  font-size: 13.5px;
  color: #94A3B8;
  text-align: center;
  margin: 0;
}

/* ── Global glass card system (used across all pages) ─────── */
.glass-card {
  background: rgba(255, 255, 255, 0.70) !important;
  backdrop-filter: blur(16px) saturate(160%) !important;
  -webkit-backdrop-filter: blur(16px) saturate(160%) !important;
  border: 1px solid rgba(255, 255, 255, 0.60) !important;
  border-radius: 16px !important;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06), 0 1px 4px rgba(0, 0, 0, 0.04) !important;
}

.v-theme--apaAtlasDarkTheme .glass-card {
  background: rgba(24, 28, 37, 0.80) !important;
  border: 1px solid rgba(255, 255, 255, 0.07) !important;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.30), 0 1px 4px rgba(0, 0, 0, 0.20) !important;
}

.glass-card-subtle {
  background: rgba(255, 255, 255, 0.50) !important;
  backdrop-filter: blur(10px) !important;
  -webkit-backdrop-filter: blur(10px) !important;
  border: 1px solid rgba(255, 255, 255, 0.45) !important;
  border-radius: 12px !important;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05) !important;
}

.v-theme--apaAtlasDarkTheme .glass-card-subtle {
  background: rgba(30, 36, 50, 0.70) !important;
  border: 1px solid rgba(255, 255, 255, 0.06) !important;
}
</style>
