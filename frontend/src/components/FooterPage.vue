<template>
  <footer class="footer bg-graintrade-secondary text-white mt-auto">
    <div class="container">
      <div class="row py-4">
        <div class="col-md-9 mb-3 mb-md-0">
          <ul class="nav flex-column flex-md-row">
            <li class="nav-item mb-2 mb-md-0">
              <router-link class="nav-link text-white-50" to="/contacts-requisites">{{ $t('footer.contactsAndRequisites') }}</router-link>
            </li>
            <li class="nav-item mb-2 mb-md-0">
              <router-link class="nav-link text-white-50" to="/privacy-policy">{{ $t('footer.privacyPolicy') }}</router-link>
            </li>
            <li class="nav-item mb-2 mb-md-0">
              <router-link class="nav-link text-white-50" to="/terms-of-service">{{ $t('footer.termsOfService') }}</router-link>
            </li>
            <li class="nav-item mb-2 mb-md-0">
              <router-link class="nav-link text-white-50" to="/tariffs">{{ $t('footer.pricing') }}</router-link>
            </li>
            <li class="nav-item mb-2 mb-md-0">
              <router-link class="nav-link text-white-50" to="/about-us">{{ $t('footer.about') }}</router-link>
            </li>
            <li class="nav-item mb-2 mb-md-0">
              <a class="nav-link text-white-50" href="https://home.graintrade.info/how-to">{{ $t('footer.howTo') }}</a>
            </li>
            <li class="nav-item mb-2 mb-md-0">
              <a class="nav-link text-white-50" href="https://home.graintrade.info/faq">{{ $t('footer.faq') }}</a>
            </li>
            <li class="nav-item mb-2 mb-md-0">
              <button
                type="button"
                class="nav-link text-white-50 cookie-settings-trigger"
                @click="openCookieSettings"
              >
                {{ $t('footer.cookieSettings') }}
              </button>
            </li>
          </ul>
        </div>
        <div class="col-md-3 text-md-end">
          <a
            href="https://t.me/graintradeinfo"
            target="_blank"
            rel="noopener noreferrer"
            class="btn btn-primary d-inline-flex align-items-center"
          >
            <i class="bi bi-telegram me-2"></i>{{ $t('footer.telegram') }}
          </a>
        </div>
      </div>
      <div class="row py-3 border-top border-secondary">
        <div class="col-12 text-center">
          <p class="mb-0 text-white-50">&copy; 2025 Graintrade.Info</p>
        </div>
      </div>
    </div>
  </footer>
</template>

<script>
import { mapState } from 'vuex';

export default {
  name: 'FooterPage',
  emits: ['open-cookie-settings'],
  data() {
    return {
      selectedLocale: this.$store.state.currentLocale, // Initialize with current locale
    };
  },
  computed: {
    ...mapState(['isAuthenticated', 'currentLocale']),
  },
  methods: {
    changeLocale() {
      this.$store.commit('setLocale', this.selectedLocale); // Commit the new locale to the store
      this.$i18n.locale = this.selectedLocale; // Update i18n locale
    },
    openCookieSettings() {
      this.$emit('open-cookie-settings');
    },
  },
};
</script>

<style scoped>
/* Footer styles are handled by graintrade-theme.css */
.nav-link:hover {
  color: white !important;
  transition: var(--graintrade-transition);
}

.cookie-settings-trigger {
  background: transparent;
  border: 0;
  padding: 0;
}

.cookie-settings-trigger:focus {
  outline: none;
  box-shadow: none;
}
</style>