<template>
  <div id="app">
    <nav class="navbar navbar-expand-lg navbar-light"  style="background-color:aquamarine;">
      <div class="container-fluid">
        <a class="navbar-brand" href="#">Graintrade.Info</a>
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
              <router-link class="btn btn-primary" to="/login">{{ $t('navbar.login') }}</router-link>
              <router-link class="btn btn-warning" to="/register">{{ $t('navbar.register') }}</router-link>
            </li>
            <li class="nav-item" v-if="isAuthenticated">
              <a class="btn btn-primary" href="#" @click="$router.push('/profile')">{{ $t('navbar.profile') }}</a>
            </li>
            <li class="nav-item" v-if="isAuthenticated">
              <a class="btn btn-dark" href="#" @click="logout">{{ $t('navbar.logout') }}</a>
            </li>
            <li class="nav-item">
              <select v-mobel="currentLocale" @change="changeLocale" class="form-select">
                <option value="en">EN</option>
                <option value="ua">UA</option>
              </select>
            </li>
          </ul>
        </div>
      </div>
    </nav>
    <router-view />
  </div>
</template>

<script>
import { mapState } from 'vuex';

export default {
  name: 'App',
  computed: {
    ...mapState(['isAuthenticated', 'currentLocale']),
  },
  methods: {
    logout() {
      this.$store.commit('setAuthenticated', false);
      this.$router.push('/');
    },
    changeLocale(event) {
      const newLocale = event.target.value;
      this.$store.commit('setLocale', newLocale);
      this.$i18n.locale = newLocale;
    },
  },
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  /* text-align: center; */
  color: #2c3e50;
  margin-top: 10px;
}
</style>
