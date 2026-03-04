import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import Search from '@/views/Search.vue'
import LocusDetail from '@/views/LocusDetail.vue'
import GeneDetail from '@/views/GeneDetail.vue'
import Statistics from '@/views/Statistics.vue'
import Download from '@/views/Download.vue'
import Help from '@/views/Help.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/search',
    name: 'Search',
    component: Search
  },
  {
    path: '/locus/:transcriptId',
    name: 'LocusDetail',
    component: LocusDetail
  },
  {
    path: '/gene/:geneId',
    name: 'GeneDetail',
    component: GeneDetail
  },
  {
    path: '/statistics',
    name: 'Statistics',
    component: Statistics
  },
  {
    path: '/download',
    name: 'Download',
    component: Download
  },
  {
    path: '/help',
    name: 'Help',
    component: Help
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
