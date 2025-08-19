import { createStore } from 'vuex';
import axios from 'axios';

const backendUrl = process.env.VUE_APP_BACKEND_URL;
// Ensure the backend URL is set corre
if (!backendUrl) {
  console.error('VUE_APP_BACKEND_URL is not defined. Please set it in your .env file.');
}
// import publicApi from '@/services/publicApi';
// import api from '@/services/api';

export default createStore({
  state: {
    backendUrl: backendUrl,
    isAuthenticated: !!localStorage.getItem('access_token'),
    accessToken: localStorage.getItem('access_token'),
    user: JSON.parse(localStorage.getItem('user')),
    currentLocale: localStorage.getItem('locale') || 'ua',
  },
  mutations: {
    setAuthenticated(state, status) {
      state.isAuthenticated = status;
    },
    setAccessToken(state, token) {
      state.accessToken = token;
    },
    setUser(state, user) {
      state.user = user;
    },
    setLocale(state, locale) {
      state.currentLocale = locale;
      localStorage.setItem('locale', locale);
    },
  },
  actions: {
    async login({ commit }, { username, password }) {
      try {
        const params = new URLSearchParams();
        params.append('username', username);
        params.append('password', password);
        const response = await axios.post(`${backendUrl}/token`, params);
        const token = response.data.access_token;
        commit('setAccessToken', token);
        commit('setAuthenticated', true);
        localStorage.setItem('access_token', token);

        // Fetch user info
        const userResponse = await axios.get(`${backendUrl}/users/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        const user = userResponse.data;
        commit('setUser', user);
        localStorage.setItem('user', JSON.stringify(user));
      } catch (error) {
        console.error('Login failed:', error.response ? error.response.data : error.message);
        commit('setAuthenticated', false);
      }
    },
    logout({ commit }) {
      commit('setAccessToken', null);
      commit('setAuthenticated', false);
      commit('setUser', null);
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
    },
  },
});