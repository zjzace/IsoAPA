import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const apaAtlasTheme = {
  dark: false,
  colors: {
    background: '#F5F7FA',
    surface: '#FFFFFF',
    primary: '#0D7377',
    secondary: '#14919B',
    accent: '#323232',
    error: '#FF5252',
    info: '#2196F3',
    success: '#4CAF50',
    warning: '#FFC107',
    'primary-darken-1': '#0A5C5F',
  }
}

const apaAtlasDarkTheme = {
  dark: true,
  colors: {
    background: '#1A1A2E',
    surface: '#16213E',
    primary: '#0D7377',
    secondary: '#14919B',
    accent: '#E94560',
    error: '#FF5252',
    info: '#2196F3',
    success: '#4CAF50',
    warning: '#FFC107',
    'primary-darken-1': '#0A5C5F',
  }
}

export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'apaAtlasTheme',
    themes: {
      apaAtlasTheme,
      apaAtlasDarkTheme,
    }
  },
  defaults: {
    VBtn: {
      rounded: 'lg',
    },
    VCard: {
      rounded: 'lg',
    },
    VTextField: {
      variant: 'outlined',
      density: 'comfortable',
    },
    VSelect: {
      variant: 'outlined',
      density: 'comfortable',
    }
  }
})
