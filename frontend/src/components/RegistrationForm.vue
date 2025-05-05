<template>
  <div class="registration-container">
    <form @submit.prevent="handleSubmit" class="registration-form">
      <h2>{{ $t('registration.title') }}</h2>
      
      <div class="form-group">
        <label for="username">{{ $t('registration.username') }}</label>
        <input
          type="text"
          id="username"
          v-model="formData.username"
          :class="{ 'is-invalid': errors.username }"
          required
        />
        <div class="invalid-feedback" v-if="errors.username">
          {{ errors.username }}
        </div>
      </div>

      <div class="form-group">
        <label for="email">{{ $t('registration.email') }}</label>
        <input
          type="email"
          id="email"
          v-model="formData.email"
          :class="{ 'is-invalid': errors.email }"
          required
        />
        <div class="invalid-feedback" v-if="errors.email">
          {{ errors.email }}
        </div>
      </div>

      <div class="form-group">
        <label for="full_name">{{ $t('registration.fullName') }}</label>
        <input
          type="text"
          id="full_name"
          v-model="formData.full_name"
          :class="{ 'is-invalid': errors.full_name }"
        />
      </div>

      <div class="form-group">
        <label for="phone">{{ $t('registration.phone') }}</label>
        <input
          type="tel"
          id="phone"
          v-model="formData.phone"
          :class="{ 'is-invalid': errors.phone }"
        />
      </div>

      <div class="form-group">
        <label for="password">{{ $t('registration.password') }}</label>
        <input
          type="password"
          id="password"
          v-model="formData.password"
          :class="{ 'is-invalid': errors.password }"
          required
        />
        <div class="invalid-feedback" v-if="errors.password">
          {{ errors.password }}
        </div>
      </div>

      <div class="form-group">
        <label for="confirmPassword">{{ $t('registration.confirmPassword') }}</label>
        <input
          type="password"
          id="confirmPassword"
          v-model="formData.confirmPassword"
          :class="{ 'is-invalid': errors.confirmPassword }"
          required
        />
        <div class="invalid-feedback" v-if="errors.confirmPassword">
          {{ errors.confirmPassword }}
        </div>
      </div>

      <button type="submit" :disabled="isSubmitting">
        {{ isSubmitting ? $t('registration.submitting') : $t('registration.submit') }}
      </button>

      <div v-if="submitError" class="alert alert-danger mt-3">
        {{ submitError }}
      </div>
    </form>
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
      username: '',
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
      
      if (!formData.username) {
        errors.username = 'Username is required';
      }
      
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
          username: formData.username,
          email: formData.email,
          full_name: formData.full_name,
          phone: formData.phone,
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
.registration-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
  background: linear-gradient(145deg, #f2f7f5, #dff1e1);
}

.registration-form {
  width: 100%;
  max-width: 400px;
  padding: 2rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.form-group {
  margin-bottom: 1rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #2c3e50;
}

input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

input.is-invalid {
  border-color: #dc3545;
}

.invalid-feedback {
  color: #dc3545;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

button {
  width: 100%;
  padding: 0.75rem;
  background-color: #3FB1CE;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

button:hover {
  background-color: #2d8ba8;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.alert {
  padding: 0.75rem;
  border-radius: 4px;
  margin-top: 1rem;
}

.alert-danger {
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  color: #721c24;
}
</style>