<template>
  <div class="help-page">
    <v-container class="py-8">
      <div class="text-center mb-8">
        <h1 class="text-h3 font-weight-bold mb-2">
          <v-icon icon="mdi-help-circle" size="40" color="primary" class="mr-3"></v-icon>
          Help & Documentation
        </h1>
        <p class="text-h6 text-grey">Learn how to use ApaAtlas effectively</p>
      </div>

      <v-row justify="center">
        <v-col cols="12" lg="10">
          <!-- Quick Start -->
          <v-card variant="outlined" class="mb-6">
            <v-card-title class="d-flex align-center pa-4 bg-primary-lighten-5">
              <v-icon icon="mdi-rocket-launch" class="mr-2" color="primary"></v-icon>
              <span class="text-h6">Quick Start Guide</span>
            </v-card-title>
            <v-card-text class="pa-6">
              <v-stepper alt-labels flat>
                <v-stepper-header>
                  <v-stepper-item title="Search" value="1" complete></v-stepper-item>
                  <v-divider></v-divider>
                  <v-stepper-item title="Browse" value="2" complete></v-stepper-item>
                  <v-divider></v-divider>
                  <v-stepper-item title="Analyze" value="3" complete></v-stepper-item>
                  <v-divider></v-divider>
                  <v-stepper-item title="Download" value="4" complete></v-stepper-item>
                </v-stepper-header>
              </v-stepper>
              
              <v-row class="mt-4">
                <v-col cols="12" md="3" class="text-center">
                  <v-avatar color="primary" size="48" class="mb-2">
                    <v-icon icon="mdi-magnify"></v-icon>
                  </v-avatar>
                  <h4 class="text-subtitle-1 font-weight-bold">Search</h4>
                  <p class="text-body-2 text-grey">Enter gene name, transcript ID, or sample</p>
                </v-col>
                <v-col cols="12" md="3" class="text-center">
                  <v-avatar color="primary" size="48" class="mb-2">
                    <v-icon icon="mdi-table"></v-icon>
                  </v-avatar>
                  <h4 class="text-subtitle-1 font-weight-bold">Browse</h4>
                  <p class="text-body-2 text-grey">View APA sites in the data table</p>
                </v-col>
                <v-col cols="12" md="3" class="text-center">
                  <v-avatar color="primary" size="48" class="mb-2">
                    <v-icon icon="mdi-chart-bar"></v-icon>
                  </v-avatar>
                  <h4 class="text-subtitle-1 font-weight-bold">Analyze</h4>
                  <p class="text-body-2 text-grey">Explore charts and visualizations</p>
                </v-col>
                <v-col cols="12" md="3" class="text-center">
                  <v-avatar color="primary" size="48" class="mb-2">
                    <v-icon icon="mdi-download"></v-icon>
                  </v-avatar>
                  <h4 class="text-subtitle-1 font-weight-bold">Download</h4>
                  <p class="text-body-2 text-grey">Export data for further analysis</p>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- Search Options -->
          <v-expansion-panels class="mb-6">
            <v-expansion-panel>
              <v-expansion-panel-title>
                <v-icon icon="mdi-magnify" class="mr-2"></v-icon>
                <span class="text-h6">How to Search</span>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-list>
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-avatar color="primary" size="32">
                        <span class="text-caption">1</span>
                      </v-avatar>
                    </template>
                    <v-list-item-title class="font-weight-bold">By Gene Name</v-list-item-title>
                    <v-list-item-subtitle>
                      Enter a gene symbol (e.g., "GAPDH", "ACTB") to find all transcripts and APA sites
                    </v-list-item-subtitle>
                  </v-list-item>
                  
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-avatar color="primary" size="32">
                        <span class="text-caption">2</span>
                      </v-avatar>
                    </template>
                    <v-list-item-title class="font-weight-bold">By Transcript ID</v-list-item-title>
                    <v-list-item-subtitle>
                      Use Ensembl transcript ID (e.g., "ENST00000000233") for precise results
                    </v-list-item-subtitle>
                  </v-list-item>
                  
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-avatar color="primary" size="32">
                        <span class="text-caption">3</span>
                      </v-avatar>
                    </template>
                    <v-list-item-title class="font-weight-bold">By Sample/Cell Line</v-list-item-title>
                    <v-list-item-subtitle>
                      Filter by sample name (e.g., "A549", "HepG2", "K562") to see tissue-specific APA
                    </v-list-item-subtitle>
                  </v-list-item>
                  
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-avatar color="primary" size="32">
                        <span class="text-caption">4</span>
                      </v-avatar>
                    </template>
                    <v-list-item-title class="font-weight-bold">By Species</v-list-item-title>
                    <v-list-item-subtitle>
                      Select species (Human, Mouse, Rat, Zebrafish) to narrow results
                    </v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <v-expansion-panel>
              <v-expansion-panel-title>
                <v-icon icon="mdi-chart-bar" class="mr-2"></v-icon>
                <span class="text-h6">Understanding APA Sites Analysis</span>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-alert type="info" variant="tonal" class="mb-4">
                  <strong>APA Loci Distribution</strong> - Shows abundance of all APA sites in a transcript for a selected sample
                </v-alert>
                <v-alert type="info" variant="tonal" class="mb-4">
                  <strong>Abundance by Sample</strong> - Shows how a specific APA site is used across different samples
                </v-alert>
                
                <h4 class="text-subtitle-1 font-weight-bold mt-4 mb-2">Key Metrics</h4>
                <v-list density="compact">
                  <v-list-item prepend-icon="mdi-information">
                    <v-list-item-title><strong>Site Position</strong> - Genomic coordinate of the polyadenylation site</v-list-item-title>
                  </v-list-item>
                  <v-list-item prepend-icon="mdi-information">
                    <v-list-item-title><strong>Abundance</strong> - Fraction of total transcripts using this site (0-100%)</v-list-item-title>
                  </v-list-item>
                  <v-list-item prepend-icon="mdi-information">
                    <v-list-item-title><strong>Read Count</strong> - Number of sequencing reads supporting this site</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <v-expansion-panel>
              <v-expansion-panel-title>
                <v-icon icon="mdi-download" class="mr-2"></v-icon>
                <span class="text-h6">Downloading Data</span>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <p class="text-body-1 mb-4">
                  Use the Download page to export data in CSV or TSV format. You can filter by:
                </p>
                <v-list>
                  <v-list-item prepend-icon="mdi-check-circle">
                    <v-list-item-title>Species (Human, Mouse, Rat, Zebrafish)</v-list-item-title>
                  </v-list-item>
                  <v-list-item prepend-icon="mdi-check-circle">
                    <v-list-item-title>Sample/Cell Line</v-list-item-title>
                  </v-list-item>
                  <v-list-item prepend-icon="mdi-check-circle">
                    <v-list-item-title>Gene Name</v-list-item-title>
                  </v-list-item>
                </v-list>
                
                <h4 class="text-subtitle-1 font-weight-bold mt-4 mb-2">API Access</h4>
                <p class="text-body-2">
                  Programmatic access is available via our REST API. See the Download page for examples in cURL, Python, and R.
                </p>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <v-expansion-panel>
              <v-expansion-panel-title>
                <v-icon icon="mdi-faq" class="mr-2"></v-icon>
                <span class="text-h6">Frequently Asked Questions</span>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-list>
                  <v-list-item>
                    <v-list-item-title class="font-weight-bold">What is Alternative Polyadenylation (APA)?</v-list-item-title>
                    <v-list-item-subtitle>
                      APA is a post-transcriptional mechanism where mRNAs have different polyadenylation sites, producing isoforms with varying 3' UTR lengths.
                    </v-list-item-subtitle>
                  </v-list-item>
                  
                  <v-list-item>
                    <v-list-item-title class="font-weight-bold">What data sources are used?</v-list-item-title>
                    <v-list-item-subtitle>
                      ApaAtlas contains APA sites identified from 3' end sequencing data (3'READS) and RNA-seq datasets.
                    </v-list-item-subtitle>
                  </v-list-item>
                  
                  <v-list-item>
                    <v-list-item-title class="font-weight-bold">How is abundance calculated?</v-list-item-title>
                    <v-list-item-subtitle>
                      Abundance = (reads at specific site) / (total reads at all sites for that transcript) × 100%
                    </v-list-item-subtitle>
                  </v-list-item>
                  
                  <v-list-item>
                    <v-list-item-title class="font-weight-bold">Can I use this data for publication?</v-list-item-title>
                    <v-list-item-subtitle>
                      Yes! ApaAtlas data is freely available. Please cite our database in your publications.
                    </v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>

          <!-- Glossary -->
          <v-card variant="outlined">
            <v-card-title class="d-flex align-center pa-4 bg-primary-lighten-5">
              <v-icon icon="mdi-book-open-variant" class="mr-2" color="primary"></v-icon>
              <span class="text-h6">Glossary</span>
            </v-card-title>
            <v-card-text class="pa-6">
              <v-table class="glossary-table">
                <tbody>
                  <tr v-for="term in glossary" :key="term.term">
                    <td class="font-weight-bold text-primary" style="width: 200px;">{{ term.term }}</td>
                    <td>{{ term.definition }}</td>
                  </tr>
                </tbody>
              </v-table>
            </v-card-text>
          </v-card>

          <!-- Contact -->
          <v-card variant="outlined" class="mt-6">
            <v-card-title class="d-flex align-center pa-4">
              <v-icon icon="mdi-email" class="mr-2" color="primary"></v-icon>
              <span class="text-h6">Contact & Feedback</span>
            </v-card-title>
            <v-card-text class="pa-6">
              <p class="text-body-1 mb-4">
                For questions, bug reports, or feature requests, please contact us:
              </p>
              <v-row>
                <v-col cols="12" md="6">
                  <v-card variant="tonal" class="pa-4" color="surface-variant">
                    <div class="d-flex align-center mb-2">
                      <v-icon icon="mdi-bug" class="mr-2"></v-icon>
                      <span class="font-weight-bold">Report Issues</span>
                    </div>
                    <p class="text-body-2">Found a bug or incorrect data? Let us know!</p>
                  </v-card>
                </v-col>
                <v-col cols="12" md="6">
                  <v-card variant="tonal" class="pa-4" color="surface-variant">
                    <div class="d-flex align-center mb-2">
                      <v-icon icon="mdi-lightbulb" class="mr-2"></v-icon>
                      <span class="font-weight-bold">Feature Requests</span>
                    </div>
                    <p class="text-body-2">Have a suggestion? We'd love to hear from you!</p>
                  </v-card>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup>
const glossary = [
  {
    term: 'APA',
    definition: 'Alternative Polyadenylation - a mechanism producing multiple mRNA isoforms with different 3\' ends'
  },
  {
    term: 'PAS',
    definition: 'Polyadenylation Signal - hexamer sequence (e.g., AATAAA) that marks the cleavage site'
  },
  {
    term: '3\' UTR',
    definition: '3\' Untranslated Region - mRNA region downstream of the coding sequence'
  },
  {
    term: 'Proximal PAS',
    definition: 'Polyadenylation site closest to the coding region'
  },
  {
    term: 'Distal PAS',
    definition: 'Polyadenylation site farthest from the coding region'
  },
  {
    term: 'UTR Shortening',
    definition: 'APA event resulting in shorter 3\' UTR (uses proximal PAS)'
  },
  {
    term: 'UTR Lengthening',
    definition: 'APA event resulting in longer 3\' UTR (uses distal PAS)'
  },
  {
    term: 'Abundance',
    definition: 'Relative usage of an APA site compared to all sites for a transcript'
  },
  {
    term: '3\'READS',
    definition: '3\' Region Extraction and Sequencing - method for mapping polyadenylation sites'
  }
]
</script>

<style scoped>
.help-page {
  min-height: 100vh;
  background: rgb(var(--v-theme-background));
}

.glossary-table {
  background: transparent !important;
}

.glossary-table tr:nth-child(odd) {
  background: rgba(var(--v-theme-surface-variant), 0.2);
}

.bg-primary-lighten-5 {
  background: rgba(var(--v-theme-primary), 0.05);
}
</style>
