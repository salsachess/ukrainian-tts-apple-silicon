import { createApp } from 'vue'
import { 
  Quasar, 
  Notify,
  QLayout,
  QHeader,
  QToolbar,
  QToolbarTitle,
  QPageContainer,
  QPage,
  QCard,
  QCardSection,
  QInput,
  QCardActions,
  QBtn
} from 'quasar'

import '@quasar/extras/material-icons/material-icons.css'
import 'quasar/dist/quasar.css'

import App from './App.vue'

const app = createApp(App)

app.use(Quasar, {
  components: {
    QLayout,
    QHeader,
    QToolbar,
    QToolbarTitle,
    QPageContainer,
    QPage,
    QCard,
    QCardSection,
    QInput,
    QCardActions,
    QBtn
  },
  plugins: { Notify },
  config: {
    notify: {}
  }
})

app.mount('#app')
