import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000
})

export const apiService = {
  async getStats() {
    const response = await api.get('/stats')
    return response.data
  },
  
  async getDetailedStats() {
    const response = await api.get('/stats/detailed')
    return response.data
  },
  
  async search(params) {
    const response = await api.get('/search', { params })
    return response.data
  },
  
  async autocomplete(q, field) {
    const response = await api.get('/autocomplete', { params: { q, field } })
    return response.data
  },
  
  async getLocusDetail(transcriptId) {
    const response = await api.get(`/transcript/${transcriptId}`)
    return response.data
  },
  
  async getGeneDetail(geneId) {
    const response = await api.get(`/gene/${geneId}`)
    return response.data
  },
  
  async getTranscriptStructure(transcriptId) {
    const response = await api.get(`/transcript/${transcriptId}/structure`)
    return response.data
  },
  
  async getSpecies() {
    const response = await api.get('/species')
    return response.data
  },
  
  async getSamples(species) {
    const response = await api.get('/samples', { params: { species } })
    return response.data
  },
  
  async getGenes(page = 1, limit = 50) {
    const response = await api.get('/genes', { params: { page, limit } })
    return response.data
  },
  
  async downloadApaSites(params) {
    const response = await api.get('/download/apa-sites', { 
      params,
      responseType: 'blob'
    })
    return response.data
  },
  
  async downloadGenes(params) {
    const response = await api.get('/download/genes', { 
      params,
      responseType: 'blob'
    })
    return response.data
  },
  
  async downloadTranscripts(params) {
    const response = await api.get('/download/transcripts', { 
      params,
      responseType: 'blob'
    })
    return response.data
  },

  async getUtrComposition(transcriptId) {
    const response = await api.get(`/transcript/${transcriptId}/utr-composition`)
    return response.data
  },

  // Returns a direct URL for the browser to navigate to (triggers file download)
  getUtrSequenceUrl(transcriptId, siteId) {
    return `/api/v1/transcript/${transcriptId}/utr-sequence/${siteId}`
  },

  async getRbpMotifs(transcriptId) {
    const response = await api.get(`/transcript/${transcriptId}/rbp-motifs`)
    return response.data
  },

  async getSiteSequence(transcriptId, siteId, flank = 50) {
    const response = await api.get(
      `/transcript/${transcriptId}/site-sequence/${encodeURIComponent(siteId)}`,
      { params: { flank } }
    )
    return response.data
  }
}

export default api
