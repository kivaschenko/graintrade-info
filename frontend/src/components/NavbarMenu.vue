<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
    <div class="container-fluid">
      <router-link class="navbar-brand" to="/">Graintrade.Info</router-link>
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
          <li class="nav-item" v-if="isAuthenticated">
            <router-link class="nav-link" to="/tariffs">{{ $t('navbar.tariffs') }}</router-link>
          </li>
        </ul>
        <ul class="navbar-nav">
          <li class="nav-item" v-if="!isAuthenticated">
            <router-link class="btn btn-outline-light me-2" to="/login">{{ $t('navbar.login') }}</router-link>
            <router-link class="btn btn-warning me-2" to="/register">{{ $t('navbar.register') }}</router-link>
          </li>
          <li class="nav-item" v-if="isAuthenticated">
            <router-link class="btn btn-outline-light me-2" to="/profile">{{ $t('navbar.profile') }}</router-link>
          </li>
          <li class="nav-item" v-if="isAuthenticated">
            <a class="btn btn-danger me-2" href="#" @click="logout">{{ $t('navbar.logout') }}</a>
          </li>
          <li class="nav-item">
            <select v-model="selectedLocale" @change="changeLocale" class="form-select bg-primary text-white border-0">
              <option value="ua">UA</option>
              <option value="en">EN</option>
            </select>
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
    changeLocale(event) {
      const newLocale = event.target.value;
      this.$store.commit('setLocale', newLocale);
      this.$i18n.locale = newLocale;
      this.collapseNavbar(); // Collapse navbar after changing locale
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
.navbar {
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,.05);
}

.navbar-brand {
  font-weight: bold;
  font-size: 1.5rem;
}

.nav-link {
  font-weight: 500;
  transition: color 0.3s ease;
}

.nav-link:hover {
  color: var(--bs-warning) !important; /* Example hover effect */
}

.btn {
  font-weight: 500;
}

.form-select {
  cursor: pointer;
}
</style>