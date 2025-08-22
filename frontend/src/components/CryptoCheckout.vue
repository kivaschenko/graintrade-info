<template>
  <div class="crypto-checkout">
    <h2>Оформлення підписки (Crypto)</h2>

    <label for="plan">Оберіть план:</label>
    <select id="plan" v-model="selectedPlan">
      <option value="1">Базовий — 200 UAH</option>
      <option value="2">Преміум — 500 UAH</option>
    </select>

    <button @click="startCryptoPayment" :disabled="loading">
      {{ loading ? 'Створюємо...' : 'Оплатити крипто' }}
    </button>

    <div v-if="invoiceUrl" class="crypto-invoice">
      <p>Оплатіть за посиланням:</p>
      <a :href="invoiceUrl" target="_blank">{{ invoiceUrl }}</a>
    </div>

    <div v-if="qrCode">
      <img :src="qrCode" alt="QR Code" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const selectedPlan = ref('1')
const loading = ref(false)
const invoiceUrl = ref('')
const qrCode = ref('')

const plans = {
  1: { amount: 200 },
  2: { amount: 500 }
}

const startCryptoPayment = async () => {
  loading.value = true
  invoiceUrl.value = ''
  qrCode.value = ''

  try {
    const { amount } = plans[selectedPlan.value]
    const res = await axios.post('/api/crypto/checkout', {
      user_id: 123,
      plan_id: selectedPlan.value,
      amount: amount,
      currency: 'UAH',
      crypto_currency: 'USDTTRC20'
    })

    if (res.data.ok) {
      const sub = res.data.subscription
      invoiceUrl.value = sub.invoice_url
      qrCode.value = sub.qr_code || ''
    }
  } catch (err) {
    console.error('Помилка:', err)
    alert('Не вдалося створити платіж')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.crypto-checkout {
  max-width: 600px;
  margin: auto;
  text-align: center;
  padding: 20px;
}
.crypto-invoice {
  margin-top: 15px;
}
img {
  margin-top: 10px;
  width: 200px;
}
</style>
