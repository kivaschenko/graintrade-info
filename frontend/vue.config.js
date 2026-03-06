const { defineConfig } = require('@vue/cli-service');
const dotenv = require('dotenv');

dotenv.config();

module.exports = defineConfig({
  transpileDependencies: [
    'vuetify',
    'vuex-persistedstate',
    'vue3-google-login',
    'vue3-clarity',
  ],
});