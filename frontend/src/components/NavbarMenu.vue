<template>
  <nav class="navbar navbar-expand-lg navbar-light bg-white">
    <div class="container-fluid">
      <router-link class="navbar-brand d-flex align-items-center" to="/">
        <img src="@/assets/logo.png" alt="GrainTrade Logo" class="navbar-logo me-2">
        <span class="brand-text">Graintrade.Info</span>
      </router-link>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0">
          <li class="nav-item">
            <router-link class="nav-link" to="/">{{ $t('navbar.home') }}</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/items/new">{{ $t('navbar.addNew') }}</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/tariffs">{{ $t('navbar.tariffs') }}</router-link>
          </li>
          <!--
          <li class="nav-item">
            <router-link class="nav-link" to="/crypto-checkout">{{ $t('navbar.cryptoTariffs') }}</router-link>
          </li>
          -->
        </ul>
        <ul class="navbar-nav">
          <li class="nav-item" v-if="!isAuthenticated">
            <router-link class="btn btn-outline-primary me-2" to="/login">{{ $t('navbar.login') }}</router-link>
            <router-link class="btn btn-primary me-2" to="/register">{{ $t('navbar.register') }}</router-link>
          </li>
          <li class="nav-item" v-if="isAuthenticated">
            <router-link class="btn btn-outline-primary me-2" to="/profile">{{ $t('navbar.profile') }}</router-link>
          </li>
          <li class="nav-item" v-if="isAuthenticated">
            <a class="btn btn-outline-secondary me-2" href="#" @click="logout">{{ $t('navbar.logout') }}</a>
          </li>
          <li class="nav-item">
            <div class="lang-switcher">
              <a href="#" 
                 @click.prevent="setLocale('en')" 
                 :class="['lang-link', { 'active': selectedLocale === 'en' }]">
                EN
              </a>
              <span class="lang-separator">|</span>
              <a href="#" 
                 @click.prevent="setLocale('ua')" 
                 :class="['lang-link', { 'active': selectedLocale === 'ua' }]">
                УКР
              </a>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script>
import { mapState } from 'vuex';
import * as bootstrap from 'bootstrap'; // Import Bootstrap JavaScript

export default {
  name: 'NavbarMenu',
  data() {
    return {
      selectedLocale: this.$store.state.currentLocale, // Initialize with current locale
    };
  },
  computed: {
    ...mapState(['isAuthenticated', 'currentLocale']),
  },
  watch: {
    currentLocale(newLocale) {
      this.selectedLocale = newLocale; // Update selectedLocale when currentLocale changes in store
    },
  },
  methods: {
    logout() {
      this.$store.dispatch('logout'); // Dispatch logout action
      this.$store.commit('setLocale', 'ua'); // Reset locale to default on logout
      this.$router.push('/');
      this.collapseNavbar(); // Collapse navbar after logout
    },
    changeLocale(newLocale) {
      this.$store.commit('setLocale', newLocale);
      this.$i18n.locale = newLocale;
      this.collapseNavbar(); // Collapse navbar after changing locale
    },
    setLocale(locale) {
      this.selectedLocale = locale;
      this.changeLocale(locale);
    },
    collapseNavbar() {
      const navbarCollapse = document.getElementById('navbarNav');
      if (navbarCollapse && navbarCollapse.classList.contains('show')) {
        const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse) || new bootstrap.Collapse(navbarCollapse, { toggle: false });
        bsCollapse.hide();
      }
    },
  },
  mounted() {
    // This ensures that the Bootstrap JavaScript is loaded and can handle the collapse behavior.
    // If you are using a global Bootstrap import, this might not be strictly necessary here,
    // but it ensures the collapse functionality is available for this component.
  }
}
</script>

<style scoped>
/* Navbar brand with logo styling */
.navbar-brand {
  font-weight: 700;
  font-size: 1.5rem;
  color: var(--graintrade-secondary) !important;
  text-decoration: none;
  transition: var(--graintrade-transition);
}

.navbar-brand:hover {
  color: var(--graintrade-primary) !important;
}

.navbar-logo {
  height: 40px;
  width: auto;
  transition: var(--graintrade-transition);
}

.navbar-logo:hover {
  transform: scale(1.05);
}

.brand-text {
  font-weight: 700;
  letter-spacing: -0.5px;
}

/* Responsive logo sizing */
@media (max-width: 768px) {
  .navbar-logo {
    height: 32px;
  }
  
  .brand-text {
    font-size: 1.25rem;
  }
}

@media (max-width: 576px) {
  .navbar-logo {
    height: 28px;
  }
  
  .brand-text {
    font-size: 1.1rem;
  }
}

/* Language switcher styling to match landing service */
.lang-switcher {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.lang-link {
  padding: 0.25rem 0.5rem;
  border-radius: var(--graintrade-border-radius);
  font-weight: 500;
  color: var(--graintrade-text-light);
  text-decoration: none;
  transition: var(--graintrade-transition);
  cursor: pointer;
}

.lang-link:hover {
  color: var(--graintrade-primary);
  text-decoration: none;
}

.lang-link.active {
  background: var(--graintrade-primary);
  color: white;
}

.lang-link.active:hover {
  background: var(--graintrade-primary-dark);
  color: white;
}

.lang-separator {
  color: var(--graintrade-border);
  font-weight: 300;
}
</style>