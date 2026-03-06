<template>
  <div class="password-recovery">
    <!-- Request Recovery Form -->
    <form v-if="!token" @submit.prevent="requestRecovery">
      <h2>Password Recovery</h2>
      <div class="form-group">
        <label for="email">Email</label>
        <input 
          type="email" 
          id="email" 
          v-model="email" 
          required
        />
      </div>
      <button type="submit" :disabled="loading">
        {{ loading ? 'Sending...' : 'Send Recovery Link' }}
      </button>
      <p v-if="message" :class="{ error: isError }">{{ message }}</p>
    </form>

    <!-- Reset Password Form -->
    <form v-else @submit.prevent="resetPassword">
      <h2>Reset Password</h2>
      <div class="form-group">
        <label for="password">New Password</label>
        <input 
          type="password" 
          id="password" 
          v-model="newPassword" 
          required
        />
      </div>
      <div class="form-group">
        <label for="confirmPassword">Confirm Password</label>
        <input 
          type="password" 
          id="confirmPassword" 
          v-model="confirmPassword" 
          required
        />
      </div>
      <button type="submit" :disabled="loading || !passwordsMatch">
        {{ loading ? 'Resetting...' : 'Reset Password' }}
      </button>
      <p v-if="message" :class="{ error: isError }">{{ message }}</p>
    </form>
  </div>
</template>

<script setup>
import publicApi from '@/services/publicApi';
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const email = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const message = ref('')
const isError = ref(false)
const token = ref(route.query.token)

const passwordsMatch = computed(() => newPassword.value === confirmPassword.value)

const requestRecovery = async () => {
  try {
    loading.value = true
    await publicApi.post('/password-recovery', { email: email.value })
    message.value = 'Recovery link sent to your email if account exists'
    isError.value = false
  } catch (error) {
    message.value = 'An error occurred'
    isError.value = true
  } finally {
    loading.value = false
  }
}

const resetPassword = async () => {
  if (!passwordsMatch.value) {
    message.value = 'Passwords do not match'
    isError.value = true
    return
  }

  try {
    loading.value = true
    await publicApi.post('/reset-password', {
      token: token.value,
      new_password: newPassword.value
    })
    message.value = 'Password successfully reset'
    isError.value = false
    setTimeout(() => router.push('/login'), 2000)
  } catch (error) {
    message.value = 'An error occurred'
    isError.value = true
  } finally {
    loading.value = false
  }
}
</script>


<style scoped>
.password-recovery {
  max-width: 400px;
  margin: 0 auto;
  padding: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.error {
  color: red;
}

input {
  width: 100%;
  padding: 8px;
  margin-top: 5px;
}

button {
  width: 100%;
  padding: 10px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:disabled {
  background-color: #cccccc;
}
</style>