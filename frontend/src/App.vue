<template>
  <div id="app">
    <NavbarMenu />
    <router-view />
    <FooterPage @open-cookie-settings="openCookieSettings" />
    <CookieConsentBanner
      :status="cookieStatus"
      :open-settings="showCookieSettings"
      @update-consent="updateConsent"
      @close-settings="closeCookieSettings"
    />
  </div>
</template>

<script>
import NavbarMenu from './components/NavbarMenu.vue'; // Adjust path as needed
import FooterPage from './components/FooterPage.vue';
import CookieConsentBanner from './components/CookieConsentBanner.vue';
import { initAnalytics, disableAnalytics } from './config/analytics';
import {
  loadConsent,
  saveConsent,
  getConsentStatus,
  hasAnalyticsConsent,
} from './utils/cookie-consent';

export default {
  name: 'App',
  components: {
    NavbarMenu,
    FooterPage,
    CookieConsentBanner,
  },
  data() {
    const storedConsent = loadConsent();
    return {
      cookieStatus: getConsentStatus(storedConsent),
      showCookieSettings: false,
    };
  },
  methods: {
    updateConsent(preferences) {
      const consent = {
        analytics: Boolean(preferences?.analytics),
      };
      saveConsent(consent);
      const normalized = loadConsent();
      const analyticsEnabled = hasAnalyticsConsent(normalized);
      this.cookieStatus = getConsentStatus(normalized);
      this.showCookieSettings = false;

      if (analyticsEnabled) {
        initAnalytics();
      } else {
        disableAnalytics();
      }
    },
    openCookieSettings() {
      this.showCookieSettings = true;
    },
    closeCookieSettings() {
      this.showCookieSettings = false;
    },
  },
}
</script>

<style>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  /* Theme styles are handled by graintrade-theme.css */
}

/* Ensure main content area grows to fill space */
.router-view {
  flex: 1;
}
</style>