<template>
  <div class="container my-5 position-relative">
    <!-- Close button (top right, only if used as modal) -->
    <button
      v-if="showClose"
      type="button"
      class="btn-close position-absolute end-0 top-0 m-3"
      aria-label="Close"
      @click="$emit('close')"
    ></button>
    <div class="row justify-content-center">
      <div class="col-lg-6 col-md-10">
        <div class="card shadow-sm border-0">
          <div class="card-body p-4">
            <h2 class="card-title text-center mb-4 text-primary">{{ $t('userUpdate.title') }}</h2>
            <form @submit.prevent="handleSubmit">
              <div class="mb-3">
                <label for="username" class="form-label">{{ $t('userUpdate.username') }}</label>
                <input
                  type="text"
                  id="username"
                  v-model="formData.username"
                  class="form-control"
                  :class="{ 'is-invalid': errors.username }"
                  disabled
                  required
                />
                <div class="invalid-feedback" v-if="errors.username">
                  {{ errors.username }}
                </div>
              </div>
              <div class="mb-3">
                <label for="email" class="form-label">{{ $t('userUpdate.email') }}</label>
                <input
                  type="email"
                  id="email"
                  v-model="formData.email"
                  class="form-control"
                  :class="{ 'is-invalid': errors.email }"
                  required
                />
                <div class="invalid-feedback" v-if="errors.email">
                  {{ errors.email }}
                </div>
              </div>
              <div class="mb-3">
                <label for="full_name" class="form-label">{{ $t('userUpdate.fullName') }}</label>
                <input
                  type="text"
                  id="full_name"
                  v-model="formData.full_name"
                  class="form-control"
                  :class="{ 'is-invalid': errors.full_name }"
                />
                <div class="invalid-feedback" v-if="errors.full_name">
                  {{ errors.full_name }}
                </div>
              </div>
              <div class="mb-3">
                <label for="phone" class="form-label">{{ $t('userUpdate.phone') }}</label>
                <input
                  type="tel"
                  id="phone"
                  v-model="formData.phone"
                  class="form-control"
                  :class="{ 'is-invalid': errors.phone }"
                />
                <div class="invalid-feedback" v-if="errors.phone">
                  {{ errors.phone }}
                </div>
              </div>
              <div class="mb-3">
                <label for="password" class="form-label">{{ $t('userUpdate.password') }}</label>
                <input
                  type="password"
                  id="password"
                  v-model="formData.password"
                  class="form-control"
                  :class="{ 'is-invalid': errors.password }"
                />
                <div class="invalid-feedback" v-if="errors.password">
                  {{ errors.password }}
                </div>
              </div>
              <div class="mb-3">
                <label for="confirm_password" class="form-label">{{ $t('userUpdate.confirmPassword') }}</label>
                <input
                  type="password"
                  id="confirm_password"
                  v-model="formData.confirm_password"
                  class="form-control"
                  :class="{ 'is-invalid': errors.confirm_password }"
                />
                <div class="invalid-feedback" v-if="errors.confirm_password">
                  {{ errors.confirm_password }}
                </div>
              </div>
              <button type="submit" class="btn btn-primary w-100" :disabled="isSubmitting">
                {{ isSubmitting ? $t('userUpdate.submitting') : $t('userUpdate.submit') }}
              </button>
              <div v-if="submitError" class="alert alert-danger mt-3">
                {{ submitError }}
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import { mapState } from 'vuex';
import axios from 'axios';

export default {
  name: 'UserUpdateForm',
  props: {
    showClose: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      formData: {
        id: this.user ? this.user.id : null,
        username: this.user ? this.user.username : '',
        email: '',
        full_name: '',
        phone: '',
        password: '',
        confirm_password: ''
      },
      errors: {},
      isSubmitting: false,
      submitError: ''
    };
  },
  computed: {
    ...mapState(['user', 'currentLocale']),
  },
  methods: {
    validateForm() {
      this.errors = {};
      // Email validation
      if (!this.formData.email) {
        this.errors.email = this.$t('userUpdate.emailRequired') || 'Email is required';
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.formData.email)) {
        this.errors.email = this.$t('userUpdate.emailInvalid') || 'Invalid email format';
      }
      // Password validation (only if provided)
      if (this.formData.password) {
        if (this.formData.password.length < 8) {
          this.errors.password = this.$t('userUpdate.passwordLength') || 'Password must be at least 8 characters';
        }
        if (this.formData.password !== this.formData.confirm_password) {
          this.errors.confirm_password = this.$t('userUpdate.passwordsMismatch') || 'Passwords do not match';
        }
      }
      // Username validation (should always be present)
      if (!this.formData.username) {
        this.errors.username = this.$t('userUpdate.usernameRequired') || 'Username is required';
      }
      // Optionally validate phone format
      if (this.formData.phone && !/^[\d+\-\s()]{6,}$/.test(this.formData.phone)) {
        this.errors.phone = this.$t('userUpdate.phoneInvalid') || 'Invalid phone format';
      }
      // Optionally validate full name
      if (this.formData.full_name && this.formData.full_name.length < 2) {
        this.errors.full_name = this.$t('userUpdate.fullNameShort') || 'Full name is too short';
      }
      return Object.keys(this.errors).length === 0;
    },
    async handleSubmit() {
      this.submitError = '';
      if (!this.validateForm()) {
        return;
      }
      this.isSubmitting = true;
      try {
        const response = await axios.put(
          `${process.env.VUE_APP_BACKEND_URL}/users`,
          this.formData,
          {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          }
        );
        this.$store.commit('setUser', response.data);
        this.$emit('update-success', response.data);
        if (this.showClose) this.$emit('close');
      } catch (error) {
        if (error.response && error.response.data) {
          this.submitError = error.response.data.detail || 'Update failed';
          this.errors = error.response.data.errors || {};
        } else {
          this.submitError = 'An unexpected error occurred';
          console.error('Update error:', error);
        }
      } finally {
        this.isSubmitting = false;
      }
    }
  },
  mounted() {
    if (this.user) {
      this.formData.id = this.user.id;
      this.formData.username = this.user.username;
      this.formData.email = this.user.email;
      this.formData.full_name = this.user.full_name || '';
      this.formData.phone = this.user.phone || '';
    }
  },
  watch: {
    currentLocale() {
      this.$i18n.locale = this.currentLocale;
    }
  }
};
</script>
<style scoped>
.btn-close {
  position: absolute !important;
  top: 1rem;
  right: 1rem;
  z-index: 10;
}
@media (max-width: 576px) {
  .container {
    padding: 0 1rem;
  }
  .btn-close {
    top: 0.5rem;
    right: 0.5rem;
  }
}
.card {
  position: relative;
  border-radius: 12px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
  background-color: #f8f9fa;
}

.card-title {
  font-weight: 600;
  color: #007bff;
  margin-bottom: 1.5rem;
}

.form-label {
  font-weight: 500;
  color: #343a40;
}

.form-control {
  border-radius: 0.35rem;
  border-color: #ced4da;
  font-size: 1rem;
}

.form-control:focus {
  border-color: #80bdff;
  box-shadow: 0 0 0 0.25rem rgba(0,123,255,0.25);
}

.btn-primary {
  background-color: #007bff;
  border-color: #007bff;
  font-weight: 600;
  transition: background-color 0.2s, border-color 0.2s;
}

.btn-primary:hover {
  background-color: #0056b3;
  border-color: #004085;
}

.invalid-feedback {
  color: #dc3545;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

.is-invalid {
  border-color: #dc3545;
  box-shadow: 0 0 0 0.25rem rgba(220,53,69,0.25);
}
</style>