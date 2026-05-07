<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
        <q-toolbar-title>Stream Voices API</q-toolbar-title>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <q-page class="q-pa-md row items-center justify-center">
        <div class="col-12 col-md-6">
          <q-card class="my-card q-pa-md">
            <q-card-section>
              <div class="text-h6">Консоль озвучки</div>
              <div class="text-subtitle2">Введіть персонажа та текст</div>
            </q-card-section>

            <q-card-section>
              <q-input v-model="character" label="Персонаж (напр. Гном)" outlined class="q-mb-md" />
              <q-input v-model="text" type="textarea" label="Текст для озвучки" outlined class="q-mb-md" />
            </q-card-section>

            <q-card-actions align="right">
              <q-btn :loading="isWarming" color="secondary" icon="whatshot" label="Прогріти AI" @click="preWarm" />
              <q-btn :loading="isGenerating" color="primary" icon="play_arrow" label="Озвучити" @click="generateTTS" :disable="!character || !text" />
            </q-card-actions>
            
            <q-card-section v-if="audioSrc">
              <div class="text-subtitle2 q-mb-sm">Останнє згенероване аудіо:</div>
              <audio :src="audioSrc" controls class="full-width" autoplay></audio>
            </q-card-section>
          </q-card>

          <q-card class="my-card q-pa-md q-mt-md">
            <q-card-section>
              <div class="text-h6">Статус системи</div>
              <div class="bg-dark text-white q-pa-sm rounded-borders q-mt-sm" style="min-height: 100px; max-height: 300px; overflow-y: auto; white-space: pre-wrap; font-family: monospace;">
                {{ systemStatus || 'Натисніть кнопку для отримання статусу...' }}
              </div>
            </q-card-section>

            <q-card-actions align="left">
              <q-btn :loading="isFetchingStatus" color="info" icon="info" label="STATUS" @click="fetchStatus" />
            </q-card-actions>
          </q-card>
        </div>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const character = ref('salsachess')
const text = ref('Вітаю на стрімі salsachess! ❤️ Слава Україні! 🇺🇦 ЗСУ та СБУ — наші красунчики 🔥. УНР та УПА — наша легендарна історія. Граємо у шахи разом з FSO 👍.')
const isWarming = ref(false)
const isGenerating = ref(false)
const audioSrc = ref(null)

const systemStatus = ref('')
const isFetchingStatus = ref(false)

const API_BASE = `http://${window.location.hostname}:3000`

const preWarm = async () => {
  isWarming.value = true
  try {
    const res = await axios.post(`${API_BASE}/api/pre-warm`)
    $q.notify({ type: 'positive', message: 'AI успішно прогрітий! Доступні голоси: ' + res.data.voicesCount })
  } catch (error) {
    console.error(error)
    $q.notify({ type: 'negative', message: 'Помилка прогріву AI: ' + (error.response?.data?.error || error.message) })
  } finally {
    isWarming.value = false
  }
}

const generateTTS = async () => {
  isGenerating.value = true
  audioSrc.value = null
  try {
    const response = await axios.post(`${API_BASE}/api/tts`, {
      character: character.value,
      text: text.value
    }, {
      responseType: 'arraybuffer'
    })
    
    const blob = new Blob([response.data], { type: 'audio/wav' })
    const url = URL.createObjectURL(blob)
    audioSrc.value = url
    
    // Аудіо відтвориться автоматично завдяки атрибуту autoplay
    $q.notify({ type: 'positive', message: 'Аудіо згенеровано та відтворюється' })
  } catch (error) {
    console.error(error)
    $q.notify({ type: 'negative', message: 'Помилка генерації: ' + (error.response?.data?.error || error.message) })
  } finally {
    isGenerating.value = false
  }
}

const fetchStatus = async () => {
  isFetchingStatus.value = true
  systemStatus.value = 'Завантаження статусу...'
  try {
    const response = await axios.get(`${API_BASE}/api/status`)
    systemStatus.value = JSON.stringify(response.data, null, 2)
  } catch (error) {
    console.error(error)
    systemStatus.value = 'Помилка отримання статусу:\n' + (error.response?.data?.error || error.message)
    $q.notify({ type: 'negative', message: 'Помилка отримання статусу' })
  } finally {
    isFetchingStatus.value = false
  }
}

</script>

<style>
.my-card {
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
}
body {
  background-color: #f5f5f5;
}
</style>
