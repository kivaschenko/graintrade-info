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
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  margin-top: 10px;
}
</style>