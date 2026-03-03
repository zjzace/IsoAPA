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
  }
}

export default api
