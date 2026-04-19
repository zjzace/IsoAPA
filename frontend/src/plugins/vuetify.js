import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const apaAtlasTheme = {
  dark: false,
  colors: {
    background: '#F0F2F5',
    surface: '#FFFFFF',
    'surface-variant': '#E8ECF0',
    primary: '#0D7377',
    'primary-darken-1': '#0A5C5F',
    secondary: '#14919B',
    accent: '#4A6FA5',
    error: '#D64545',
    info: '#3D7EBF',
    success: '#3D9970',
    warning: '#C9821A',
  }
}

export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'apaAtlasTheme',
    themes: {
      apaAtlasTheme,
    }
  },
  defaults: {
    VBtn: {
      rounded: 'lg',
    },
    VCard: {
      rounded: 'xl',
      elevation: 0,
    },
    VTextField: {
      variant: 'outlined',
      density: 'comfortable',
      rounded: 'lg',
    },
    VSelect: {
      variant: 'outlined',
      density: 'comfortable',
      rounded: 'lg',
    }
  }
})
