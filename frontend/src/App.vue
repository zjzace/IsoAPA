<template>
  <v-app>
    <v-app-bar color="primary" elevation="2">
      <v-container class="d-flex align-center py-0">
        <router-link to="/" class="text-decoration-none">
          <v-toolbar-title class="text-white font-weight-bold">
            <v-icon icon="mdi-dna" class="mr-2"></v-icon>
            ApaAtlas
          </v-toolbar-title>
        </router-link>
        
        <v-spacer></v-spacer>
        
        <v-btn variant="text" to="/" class="text-white">Home</v-btn>
        <v-btn variant="text" to="/search" class="text-white">Browse</v-btn>
        
        <v-btn 
          icon 
          variant="text" 
          @click="toggleTheme"
          class="ml-2"
        >
          <v-icon>{{ isDark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
        </v-btn>
      </v-container>
    </v-app-bar>
    
    <v-main>
      <router-view></router-view>
    </v-main>
    
    <v-footer class="bg-grey-lighten-4 py-6">
      <v-container>
        <v-row>
          <v-col cols="12" md="4">
            <h4 class="text-h6 mb-2">ApaAtlas</h4>
            <p class="text-body-2 text-grey-darken-1">
              A comprehensive database for isoform-level Alternative Polyadenylation (APA) loci.
            </p>
            <p class="text-caption mt-2">Version 1.0.0</p>
          </v-col>
          <v-col cols="12" md="4">
            <h4 class="text-h6 mb-2">Quick Links</h4>
            <div class="d-flex flex-column">
              <router-link to="/" class="text-decoration-none text-grey-darken-1">Home</router-link>
              <router-link to="/search" class="text-decoration-none text-grey-darken-1">Browse Data</router-link>
            </div>
          </v-col>
          <v-col cols="12" md="4">
            <h4 class="text-h6 mb-2">Contact</h4>
            <p class="text-body-2 text-grey-darken-1">
              For questions or feedback, please contact the database administrators.
            </p>
          </v-col>
        </v-row>
        <v-divider class="my-4"></v-divider>
        <p class="text-center text-caption text-grey-darken-1">
          &copy; 2024 ApaAtlas. All rights reserved.
        </p>
      </v-container>
    </v-footer>
  </v-app>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useTheme } from 'vuetify'

const theme = useTheme()
const isDark = computed(() => theme.global.name.value === 'apaAtlasDarkTheme')

const toggleTheme = () => {
  theme.global.name.value = isDark.value ? 'apaAtlasTheme' : 'apaAtlasDarkTheme'
}
</script>

<style>
html {
  overflow-y: auto !important;
}
a {
  color: inherit;
}
</style>
