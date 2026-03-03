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
        <v-card class="mb-6" variant="outlined">
          <v-card-title class="d-flex align-center">
            <v-icon icon="mdi-gene" class="mr-2" color="primary"></v-icon>
            {{ geneData.gene_name }}
          </v-card-title>
          <v-card-text>
            <v-row align="center">
              <v-col cols="12" sm="6" md="3">
                <div class="text-caption text-grey">Gene ID</div>
                <div class="text-body-1 font-weight-medium">{{ geneData.gene_id }}</div>
              </v-col>
              <v-col cols="12" sm="6" md="2">
                <div class="text-caption text-grey">Chromosome</div>
                <div class="text-body-1">
                  <v-chip size="small">{{ geneData.chromosome }}</v-chip>
                  <v-chip size="small" class="ml-1">{{ geneData.strand }}</v-chip>
                </div>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <div class="text-caption text-grey">Total Transcripts</div>
                <div class="text-body-1 font-weight-bold text-primary">
                  {{ geneData.transcripts.length }}
                </div>
              </v-col>
              <v-col cols="12" sm="6" md="4">
                <div class="text-caption text-grey">Total APA Sites</div>
                <div class="text-body-1 font-weight-bold text-primary">
                  {{ totalAPASites }}
                </div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
        
        <v-card variant="outlined">
          <v-card-title class="d-flex align-center">
            <v-icon icon="mdi-transcript" class="mr-2"></v-icon>
            Transcripts and APA Sites
          </v-card-title>
          <v-card-text>
            <v-data-table
              :headers="tableHeaders"
              :items="geneData.transcripts"
              :items-per-page="10"
              :search="tableSearch"
            >
              <template v-slot:top>
                <v-text-field
                  v-model="tableSearch"
                  label="Filter Transcripts"
                  prepend-inner-icon="mdi-filter"
                  class="mb-4"
                  style="max-width: 300px;"
                ></v-text-field>
              </template>
              
              <template v-slot:item.transcript_id="{ item }">
                <router-link 
                  :to="{ name: 'LocusDetail', params: { transcriptId: item.transcript_id } }"
                  class="text-primary font-weight-medium"
                >
                  {{ item.transcript_id }}
                </router-link>
              </template>
              
              <template v-slot:item.apa_site_count="{ item }">
                <v-chip size="small" color="primary" variant="tonal">
                  {{ item.apa_site_count }}
                </v-chip>
              </template>
              
              <template v-slot:item.samples="{ item }">
                <v-chip 
                  v-for="sample in item.samples.slice(0, 3)" 
                  :key="sample"
                  size="small" 
                  class="mr-1"
                  variant="tonal"
                >
                  {{ sample }}
                </v-chip>
                <v-chip 
                  v-if="item.samples.length > 3" 
                  size="small" 
                  variant="outlined"
                >
                  +{{ item.samples.length - 3 }}
                </v-chip>
              </template>
              
              <template v-slot:item.apa_sites="{ item }">
                <v-expansion-panels density="compact">
                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      <span class="text-caption">View {{ item.apa_sites.length }} sites</span>
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <v-table density="compact">
                        <thead>
                          <tr>
                            <th>Site ID</th>
                            <th>Position</th>
                            <th>Samples</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="site in item.apa_sites" :key="site.site_id">
                            <td><code>{{ site.site_id }}</code></td>
                            <td><code>{{ site.site_position }}</code></td>
                            <td>
                              <v-chip 
                                v-for="sd in site.sample_details" 
                                :key="sd.sample_name"
                                size="x-small" 
                                variant="tonal"
                                class="mr-1 mb-1"
                              >
                                {{ sd.sample_name }}: {{ (sd.site_abundance * 100).toFixed(1) }}%
                              </v-chip></td>
                          </tr>
                        </tbody>
                      </v-table>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </div>
    </v-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { apiService } from '@/services/api'

const route = useRoute()

const loading = ref(true)
const error = ref(null)
const geneData = ref(null)
const tableSearch = ref('')

const tableHeaders = [
  { title: 'Transcript ID', key: 'transcript_id', sortable: true },
  { title: 'APA Sites', key: 'apa_site_count', sortable: true },
  { title: 'Samples', key: 'samples', sortable: false },
  { title: 'APA Site Details', key: 'apa_sites', sortable: false }
]

const totalAPASites = computed(() => {
  if (!geneData.value) return 0
  return geneData.value.transcripts.reduce((sum, t) => sum + t.apa_sites.length, 0)
})

onMounted(async () => {
  const geneId = route.params.geneId
  
  try {
    loading.value = true
    geneData.value = await apiService.getGeneDetail(geneId)
  } catch (err) {
    console.error('Failed to load gene detail:', err)
    error.value = 'Failed to load gene details. Please try again.'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.gene-detail-page {
  min-height: 100vh;
  background: rgb(var(--v-theme-background));
}

a {
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

code {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
}
</style>
