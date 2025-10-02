<template>
  <div id="app">
    <NavbarMenu />
    <router-view />
    <FooterPage />
  </div>
</template>

<script>
import NavbarMenu from './components/NavbarMenu.vue'; // Adjust path as needed
import FooterPage from './components/FooterPage.vue';

export default {
  name: 'App',
  components: {
    NavbarMenu,
    FooterPage,
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