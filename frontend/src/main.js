import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';
import './assets/graintrade-theme.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';
import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import store from './store';
import i18n from './i18n';
import { initAnalytics } from './config/analytics';
import { loadConsent, hasAnalyticsConsent } from './utils/cookie-consent';
const app = createApp(App);

app.use(router).use(store).use(i18n);

const storedConsent = loadConsent();
if (hasAnalyticsConsent(storedConsent)) {
    initAnalytics();
}

app.mount('#app');