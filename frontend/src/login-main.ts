import { createApp } from 'vue'
import LoginApp from './LoginApp.vue'
import i18n from './i18n/vue-i18n'

const app = createApp(LoginApp)

app.use(i18n)

app.mount('#app')
