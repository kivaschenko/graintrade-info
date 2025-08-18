<template>
  <div class="user-update-container">
    <form @submit.prevent="handleSubmit" class="user-update-form">
      <h2>{{ $t('userUpdate.title') }}</h2>
        <div class="form-group">
            <label for="email">{{ $t('userUpdate.email') }}</label>
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
            <label for="full_name">{{ $t('userUpdate.fullName') }}</label>
            <input
            type="text"
            id="full_name"
            v-model="formData.full_name"
            :class="{ 'is-invalid': errors.full_name }"
            />
        </div>
        <div class="form-group">
            <label for="phone">{{ $t('userUpdate.phone') }}</label>
            <input
            type="tel"
            id="phone"
            v-model="formData.phone"
            :class="{ 'is-invalid': errors.phone }"
            />
        </div>
        <div class="form-group">
            <label for="password">{{ $t('userUpdate.password') }}</label>
            <input
            type="password"
            id="password"
            v-model="formData.password"
            :class="{ 'is-invalid': errors.password }"
            />
            <div class="invalid-feedback" v-if="errors.password">
            {{ errors.password }}
            </div>
        </div>
        <div class="form-group">
            <label for="confirm_password">{{ $t('userUpdate.confirmPassword') }}</label>
            <input
            type="password"
            id="confirm_password"
            v-model="formData.confirm_password"
            :class="{ 'is-invalid': errors.confirm_password }"
            />
            <div class="invalid-feedback" v-if="errors.confirm_password">
            {{ errors.confirm_password }}
            </div>
        </div>
        <button type="submit" class="btn btn-primary">
            {{ $t('userUpdate.submit') }}
        </button>
    </form>
  </div>
</template>
<script>
import { mapState } from 'vuex';
import api from '@/services/api'; // Adjust the import based on your project structure

export default {
  name: 'UserUpdateForm',
  data() {
    return {
      formData: {
        email: '',
        full_name: '',
        phone: '',
        password: '',
        confirm_password: ''
      },
      errors: {}
    };
  },
	computed: {
		...mapState(['user', 'currentLocale']),
	},
	methods: {
		async handleSubmit() {
			this.errors = {};
			try {
				const response = await api.put('/users/me', this.formData);
				this.$store.commit('setUser', response.data);
				this.$emit('update-success', response.data);
			} catch (error) {
				if (error.response && error.response.data) {
					this.errors = error.response.data;
				} else {
					console.error('An unexpected error occurred:', error);
				}
			}
		}
	},
	mounted() {
		// Initialize form data with current user info
		if (this.user) {
			this.formData.email = this.user.email;
			this.formData.full_name = this.user.full_name || '';
			this.formData.phone = this.user.phone || '';
		}
	},
	watch: {
		currentLocale() {
			this.$i18n.locale = this.currentLocale; // Update i18n locale dynamically
		}
	}	
};
</script>
<style scoped>
.container {
  max-width: 1200px;
}

.card {
  border: none;
  border-radius: 0.75rem; /* Slightly rounded corners for a softer look */
}

.card-body {
  padding: 2rem; /* More internal padding */
}

.form-label {
  font-weight: 600; /* Make labels a bit bolder */
  margin-bottom: 0.5rem; /* Add some space below labels */
  color: #343a40; /* Darker text for labels */
}

.form-control,
.form-select {
  border-radius: 0.35rem; /* Slightly rounded input fields */
  border-color: #ced4da; /* A standard border color */
}

.form-control:focus,
.form-select:focus {
  border-color: #80bdff; /* Bootstrap's default focus color */
  box-shadow: 0 0 0 0.25rem rgba(0, 123, 255, 0.25); /* Bootstrap's default focus shadow */
}

.btn-primary {
  background-color: #007bff; /* Bootstrap primary blue */
  border-color: #007bff;
  transition: background-color 0.2s ease-in-out, border-color 0.2s ease-in-out; /* Smooth transition on hover */
}

.btn-primary:hover {
  background-color: #0056b3; /* Darker blue on hover */
  border-color: #004085;
}

.alert {
  margin-bottom: 1.5rem; /* Space below alerts */
}

/* Specific styles for the form card background */
.col-lg-6 > .card:last-child { /* Targets the card containing the form */
  background-color: #f8f9fa; /* Light grey background for the form area */
}

.text-center {
  text-align: center;
}

</style>