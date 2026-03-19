<template>
  <div class="cookie-consent">
    <transition name="slide-up">
      <div
        v-if="shouldShowBanner"
        class="cookie-banner shadow-lg"
        role="dialog"
        aria-live="polite"
      >
        <div class="cookie-banner__content">
          <h2 class="cookie-banner__title">{{ $t('cookieConsent.title') }}</h2>
          <p class="cookie-banner__text">{{ $t('cookieConsent.description') }}</p>
          <div class="cookie-banner__links">
            <router-link class="cookie-banner__link" to="/privacy-policy">
              {{ $t('cookieConsent.privacyLink') }}
            </router-link>
          </div>
        </div>
        <div class="cookie-banner__actions">
          <button type="button" class="btn btn-outline-light" @click="rejectAll">
            {{ $t('cookieConsent.reject') }}
          </button>
          <button type="button" class="btn btn-outline-light" @click="openSettingsPanel">
            {{ $t('cookieConsent.manage') }}
          </button>
          <button type="button" class="btn btn-primary" @click="acceptAll">
            {{ $t('cookieConsent.accept') }}
          </button>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="settingsOpen" class="cookie-settings" role="dialog" aria-modal="true">
        <div class="cookie-settings__backdrop" @click="closeSettings"></div>
        <div class="cookie-settings__dialog shadow-lg">
          <header class="cookie-settings__header">
            <h2 class="cookie-settings__title">{{ $t('cookieConsent.settingsTitle') }}</h2>
            <button
              type="button"
              class="btn-close"
              aria-label="Close"
              @click="closeSettings"
            ></button>
          </header>

          <section class="cookie-settings__section">
            <h3 class="cookie-settings__section-title">{{ $t('cookieConsent.necessaryTitle') }}</h3>
            <p class="cookie-settings__section-text">{{ $t('cookieConsent.necessaryDescription') }}</p>
            <div class="form-check form-switch">
              <input
                class="form-check-input"
                type="checkbox"
                id="necessary-cookies"
                checked
                disabled
              >
              <label class="form-check-label" for="necessary-cookies">
                {{ $t('cookieConsent.necessaryLabel') }}
              </label>
            </div>
          </section>

          <section class="cookie-settings__section">
            <div class="d-flex align-items-start justify-content-between">
              <div>
                <h3 class="cookie-settings__section-title">{{ $t('cookieConsent.analyticsTitle') }}</h3>
                <p class="cookie-settings__section-text">{{ $t('cookieConsent.analyticsDescription') }}</p>
              </div>
              <div class="form-check form-switch">
                <input
                  class="form-check-input"
                  type="checkbox"
                  id="analytics-cookies"
                  v-model="analyticsEnabled"
                >
                <label class="form-check-label" for="analytics-cookies">
                  {{ $t('cookieConsent.analyticsLabel') }}
                </label>
              </div>
            </div>
          </section>

          <footer class="cookie-settings__footer">
            <button type="button" class="btn btn-outline-secondary" @click="rejectAll">
              {{ $t('cookieConsent.reject') }}
            </button>
            <div class="d-flex gap-2">
              <button type="button" class="btn btn-outline-primary" @click="closeSettings">
                {{ $t('cookieConsent.cancel') }}
              </button>
              <button type="button" class="btn btn-primary" @click="savePreferences">
                {{ $t('cookieConsent.save') }}
              </button>
            </div>
          </footer>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
export default {
  name: 'CookieConsentBanner',
  props: {
    status: {
      type: String,
      default: 'pending',
    },
    openSettings: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['update-consent', 'close-settings'],
  data() {
    return {
      bannerDismissed: false,
      settingsOpen: false,
      analyticsEnabled: false,
    };
  },
  computed: {
    shouldShowBanner() {
      return this.status === 'pending' && !this.bannerDismissed && !this.settingsOpen;
    },
  },
  watch: {
    status: {
      immediate: true,
      handler(newStatus) {
        const granted = newStatus === 'granted';
        this.analyticsEnabled = granted;
        if (newStatus !== 'pending') {
          this.bannerDismissed = true;
        }
      },
    },
    openSettings(val) {
      if (val) {
        this.openSettingsPanel();
      }
    },
  },
  methods: {
    acceptAll() {
      this.analyticsEnabled = true;
      this.submitConsent();
    },
    rejectAll() {
      this.analyticsEnabled = false;
      this.submitConsent();
    },
    openSettingsPanel() {
      this.settingsOpen = true;
      this.bannerDismissed = true;
    },
    closeSettings() {
      this.settingsOpen = false;
      this.$emit('close-settings');
      if (this.status === 'pending') {
        this.bannerDismissed = false;
      }
    },
    savePreferences() {
      this.submitConsent();
    },
    submitConsent() {
      this.$emit('update-consent', {
        analytics: this.analyticsEnabled,
      });
      this.settingsOpen = false;
      this.$emit('close-settings');
      this.bannerDismissed = true;
    },
  },
};
</script>

<style scoped>
.cookie-banner {
  position: fixed;
  bottom: 1.5rem;
  left: 50%;
  transform: translateX(-50%);
  width: min(960px, calc(100% - 2rem));
  background: rgba(24, 26, 30, 0.94);
  color: #fff;
  border-radius: 0.75rem;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  z-index: 1080;
}

.cookie-banner__content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.cookie-banner__title {
  font-size: 1.25rem;
  margin: 0;
}

.cookie-banner__text {
  margin: 0;
}

.cookie-banner__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.cookie-banner__actions .btn {
  flex: 1 1 160px;
}

.cookie-banner__link {
  color: #9ad7ff;
  text-decoration: underline;
}

.cookie-settings {
  position: fixed;
  inset: 0;
  z-index: 1090;
}

.cookie-settings__backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
}

.cookie-settings__dialog {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: min(640px, calc(100% - 2rem));
  background: #fff;
  border-radius: 0.75rem;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.cookie-settings__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.cookie-settings__title {
  margin: 0;
  font-size: 1.5rem;
}

.cookie-settings__section {
  padding: 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  background: #f9fafb;
}

.cookie-settings__section-title {
  margin: 0 0 0.5rem;
  font-size: 1.1rem;
}

.cookie-settings__section-text {
  margin: 0 0 0.75rem;
  color: #4b5563;
}

.cookie-settings__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translate(-50%, 10px);
  opacity: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 576px) {
  .cookie-banner {
    padding: 1.25rem;
  }
  .cookie-banner__actions {
    flex-direction: column;
  }
}
</style>
