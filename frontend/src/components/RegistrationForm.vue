<template>
  <div class="container mt-5 mb-5">
    <div class="row justify-content-center">
      <div class="col-md-8 col-lg-6">
        <div class="card shadow-graintrade">
          <div class="card-header text-center bg-graintrade-primary text-white">
            <h2 class="mb-0 text-white">{{ $t('registration.title') }}</h2>
          </div>
          <div class="card-body p-4">
            <form @submit.prevent="handleSubmit" class="registration-form">
              <div class="row">
                <div class="col-12">
                  <div class="mb-3">
                    <label for="email" class="form-label">{{ $t('registration.email') }}</label>
                    <input
                      type="email"
                      id="email"
                      v-model="formData.email"
                      class="form-control"
                      :class="{ 'is-invalid': errors.email }"
                      required
                      :placeholder="$t('registration.emailPlaceholder') || 'Enter your email'"
                    />
                    <div class="invalid-feedback" v-if="errors.email">
                      {{ errors.email }}
                    </div>
                  </div>
                </div>
              </div>

              <p class="text-muted small mb-4">
                {{ $t('registration.autoNicknameInfo') || 'We will generate a nickname for you automatically after registration.' }}
              </p>

              <div class="row">
                <div class="col-md-6">
                  <div class="mb-3">
                    <label for="full_name" class="form-label">{{ $t('registration.fullName') }}</label>
                    <input
                      type="text"
                      id="full_name"
                      v-model="formData.full_name"
                      class="form-control"
                      :class="{ 'is-invalid': errors.full_name }"
                      :placeholder="$t('registration.fullNamePlaceholder') || 'Enter your full name'"
                    />
                    <div class="invalid-feedback" v-if="errors.full_name">
                      {{ errors.full_name }}
                    </div>
                  </div>
                </div>
                
                <div class="col-md-6">
                  <div class="mb-3">
                    <label for="phone" class="form-label">{{ $t('registration.phone') }}</label>
                    <input
                      type="tel"
                      id="phone"
                      v-model="formData.phone"
                      class="form-control"
                      :class="{ 'is-invalid': errors.phone }"
                      :placeholder="$t('registration.phonePlaceholder') || 'Enter your phone number'"
                    />
                    <div class="invalid-feedback" v-if="errors.phone">
                      {{ errors.phone }}
                    </div>
                  </div>
                </div>
              </div>

              <div class="row">
                <div class="col-md-6">
                  <div class="mb-3">
                    <label for="password" class="form-label">{{ $t('registration.password') }}</label>
                    <input
                      type="password"
                      id="password"
                      v-model="formData.password"
                      class="form-control"
                      :class="{ 'is-invalid': errors.password }"
                      required
                      :placeholder="$t('registration.passwordPlaceholder') || 'Enter your password'"
                    />
                    <div class="invalid-feedback" v-if="errors.password">
                      {{ errors.password }}
                    </div>
                  </div>
                </div>
                
                <div class="col-md-6">
                  <div class="mb-3">
                    <label for="confirmPassword" class="form-label">{{ $t('registration.confirmPassword') }}</label>
                    <input
                      type="password"
                      id="confirmPassword"
                      v-model="formData.confirmPassword"
                      class="form-control"
                      :class="{ 'is-invalid': errors.confirmPassword }"
                      required
                      :placeholder="$t('registration.confirmPasswordPlaceholder') || 'Confirm your password'"
                    />
                    <div class="invalid-feedback" v-if="errors.confirmPassword">
                      {{ errors.confirmPassword }}
                    </div>
                  </div>
                </div>
              </div>

              <button type="submit" class="btn btn-primary w-100 py-2 mt-3" :disabled="isSubmitting">
                <span v-if="isSubmitting" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                {{ isSubmitting ? $t('registration.submitting') : $t('registration.submit') }}
              </button>

              <div v-if="submitError" class="alert alert-danger mt-3">
                {{ submitError }}
              </div>
              
              <hr class="my-4">
              
              <div class="text-center">
                <p class="mb-2">{{ $t('auth.hasAccount') || 'Already have an account?' }}</p>
                <router-link to="/login" class="btn btn-outline-primary">
                  {{ $t('navbar.login') }}
                </router-link>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>

import publicApi from '@/services/publicApi';
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useStore } from 'vuex';

export default {
  name: 'RegistrationForm',
  setup() {
    const router = useRouter();
    const store = useStore();
    
    const formData = reactive({
      email: '',
      full_name: '',
      phone: '',
      password: '',
      confirmPassword: ''
    });

    const errors = reactive({});
    const isSubmitting = ref(false);
    const submitError = ref('');

    const validateForm = () => {
      // Clear previous errors
      Object.keys(errors).forEach(key => delete errors[key]);
      
      formData.email = formData.email.trim();

      if (!formData.email) {
        errors.email = 'Email is required';
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
        errors.email = 'Invalid email format';
      }
      
      if (!formData.password) {
        errors.password = 'Password is required';
      } else if (formData.password.length < 8) {
        errors.password = 'Password must be at least 8 characters';
      }
      
      if (formData.password !== formData.confirmPassword) {
        errors.confirmPassword = 'Passwords do not match';
      }
      
      return Object.keys(errors).length === 0;
    };

    const handleSubmit = async () => {
      if (!validateForm()) {
        return;
      }

      isSubmitting.value = true;
      submitError.value = '';

      try {
        const response = await publicApi.post('/users/', {
          email: formData.email.trim().toLowerCase(),
          full_name: formData.full_name ? formData.full_name.trim() : null,
          phone: formData.phone ? formData.phone.trim() : null,
          password: formData.password
        });

        // Store the token if returned
        if (response.data.token) {
          store.commit('setToken', response.data.token);
        }

        // Redirect to home page or login
        router.push('/');
      } catch (error) {
        submitError.value = error.response?.data?.detail || 'Registration failed';
        console.error('Registration error:', error);
      } finally {
        isSubmitting.value = false;
      }
    };

    return {
      formData,
      errors,
      isSubmitting,
      submitError,
      handleSubmit
    };
  }
};
</script>

<style scoped>
.card {
  transition: var(--graintrade-transition);
  border: none;
}

.card:hover {
  transform: translateY(-2px);
}

.card-header {
  border-radius: var(--graintrade-border-radius-large) var(--graintrade-border-radius-large) 0 0 !important;
  border-bottom: none;
}

.form-control:focus {
  border-color: var(--graintrade-primary);
  box-shadow: 0 0 0 0.2rem rgba(39, 174, 96, 0.25);
}

.form-control.is-invalid {
  border-color: var(--graintrade-accent);
}

.form-control.is-invalid:focus {
  border-color: var(--graintrade-accent);
  box-shadow: 0 0 0 0.2rem rgba(231, 76, 60, 0.25);
}

.invalid-feedback {
  color: var(--graintrade-accent);
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

.btn-primary {
  font-weight: 500;
  font-size: 1.1rem;
}

.btn-outline-primary:hover {
  transform: translateY(-1px);
}

.spinner-border-sm {
  width: 1rem;
  height: 1rem;
}

hr {
  border-color: var(--graintrade-border);
  opacity: 0.5;
}

.alert-danger {
  background: rgba(231, 76, 60, 0.1);
  border: 1px solid rgba(231, 76, 60, 0.2);
  color: var(--graintrade-accent);
  border-radius: var(--graintrade-border-radius);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .card-body {
    padding: 1.5rem !important;
  }
  
  .btn {
    font-size: 1rem;
  }
}
</style>