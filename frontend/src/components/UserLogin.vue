<template>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-6 col-lg-4">
        <div class="card shadow-graintrade">
          <div class="card-header text-center bg-graintrade-primary text-white">
            <h5 class="card-title mb-0 text-white">{{ $t('auth.login') || 'Login' }}</h5>
          </div>
          <div class="card-body p-4">
            <form @submit.prevent="handleLogin">
              <div class="mb-3">
                <label for="email" class="form-label">{{ $t('auth.email') || 'Email' }}:</label>
                <input 
                  type="email" 
                  id="email" 
                  v-model="email" 
                  class="form-control" 
                  required
                  :placeholder="$t('auth.emailPlaceholder') || 'Enter your email'"
                />
              </div>
              <div class="mb-3">
                <label for="password" class="form-label">{{ $t('auth.password') || 'Password' }}:</label>
                <input 
                  type="password" 
                  id="password" 
                  v-model="password" 
                  class="form-control" 
                  required
                  :placeholder="$t('auth.passwordPlaceholder') || 'Enter your password'"
                />
              </div>
              <button type="submit" class="btn btn-outline-primary w-100 mb-3">
                {{ $t('auth.loginButton') || 'Login' }}
              </button>
            </form>
            
            <div class="text-center">
              <router-link to="/reset-password" class="text-graintrade-primary text-decoration-none">
                {{ $t('navbar.forgotPassword') }}
              </router-link>
            </div>
            
            <hr class="my-3">
            
            <div class="text-center">
              <p class="mb-2">{{ $t('auth.noAccount') || "Don't have an account?" }}</p>
              <router-link to="/register" class="btn btn-outline-primary">
                {{ $t('navbar.register') }}
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'; 

export default {
  data() {
    return {
      email: '',
      password: '',
    };
  },
    methods: {
        ...mapActions(['login']),
        async handleLogin() {
      await this.login({ email: this.email, password: this.password });
            if (this.$store.state.isAuthenticated) {
                // Redirect to the intended page or home
                const redirect = this.$route.query.redirect || '/';
                this.$router.push(redirect);
            } else {
        alert('Invalid email or password');
            }
        },
    },
};
</script>

<style scoped>
.card {
  transition: var(--graintrade-transition);
}

.card:hover {
  transform: translateY(-2px);
}

.card-header {
  border-radius: var(--graintrade-border-radius-large) var(--graintrade-border-radius-large) 0 0 !important;
}

.form-control:focus {
  border-color: var(--graintrade-primary);
  box-shadow: 0 0 0 0.2rem rgba(39, 174, 96, 0.25);
}

.btn-primary {
  font-weight: 500;
}

.btn-outline-primary:hover {
  transform: translateY(-1px);
}

hr {
  border-color: var(--graintrade-border);
}
</style>