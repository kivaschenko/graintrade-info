<template>
    <div class="container mt-5">
      <div class="card text-dark bg-info mb-3 text-center"
            style="width: 18rem;">
        <div class="card-body">
          <h5 class="card-title">Login</h5>
          <form @submit.prevent="handleLogin">
              <div class="mb-3">
                  <label for="username"  class="form-label">Username:</label>
                  <input type="text" id="username" v-model="username"  class="form-control" />
              </div>
              <div class="mb-3">
                  <label for="password" class="form-label">Password:</label>
                  <input type="password" id="password" v-model="password" class="form-control" />
              </div>
              <button type="submit" class="btn btn-primary">Login</button>
          </form>
          <p class="mt-3">
              <router-link to="/reset-password">{{ $t('navbar.forgotPassword') }}</router-link>
            </p>
        </div>
      </div>
    </div>
</template>

<script>
import { mapActions } from 'vuex'; 

export default {
    data() {
        return {
            username: '',
            password: '',
        };
    },
    methods: {
        ...mapActions(['login']),
        async handleLogin() {
            await this.login({ username: this.username, password: this.password });
            if (this.$store.state.isAuthenticated) {
                this.$router.push('/');
            } else {
                alert('Invalid username or password');
            }
        },
    },
};
</script>