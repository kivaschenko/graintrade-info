<template>
  <div class="subscription-container">
    <h2>Оформлення підписки</h2>

    <div class="plans">
      <label for="plan">Оберіть план:</label>
      <select id="plan" v-model="selectedPlan">
        <option value="1">Базовий — 200 грн/місяць</option>
        <option value="2">Преміум — 500 грн/місяць</option>
      </select>
    </div>

    <div class="payment-methods">
      <label>Метод оплати:</label>
      <div>
        <input type="radio" id="card" value="card" v-model="method" />
        <label for="card">Картка (LiqPay)</label>
      </div>
      <div>
        <input type="radio" id="crypto" value="crypto" v-model="method" />
        <label for="crypto">Криптовалюта (NOWPayments)</label>
      </div>
    </div>

    <button @click="startPayment" :disabled="loading">
      {{ loading ? 'Створюємо...' : 'Оплатити' }}
    </button>

    <!-- LiqPay iframe -->
    <div v-if="liqpayUrl" class="liqpay-frame">
      <iframe
        :src="liqpayUrl"
        width="600"
        height="700"
        frameborder="0"
        allowfullscreen>
      </iframe>
    </div>

    <!-- Crypto invoice -->
    <div v-if="cryptoInvoiceUrl" class="crypto-info">
      <p>Оплатіть за посиланням:</p>
      <a :href="cryptoInvoiceUrl" target="_blank">{{ cryptoInvoiceUrl }}</a>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const selectedPlan = ref('1')
const method = ref('card')
const loading = ref(false)
const liqpayUrl = ref('')
const cryptoInvoiceUrl = ref('')

const plans = {
  1: { amount: 200, description: 'Базова підписка' },
  2: { amount: 500, description: 'Преміум підписка' }
}

const startPayment = async () => {
  loading.value = true
  liqpayUrl.value = ''
  cryptoInvoiceUrl.value = ''

  try {
    const { amount, description } = plans[selectedPlan.value]

    const response = await axios.post('/api/checkout', {
      user_id: 123, // заміни на ID з JWT
      plan_id: selectedPlan.value,
      method: method.value,
      amount: amount,
      currency: 'UAH',
      crypto_currency: 'USDTTRC20', // якщо crypto
      description: description
    })

    if (response.data.ok) {
      if (response.data.provider === 'liqpay') {
        liqpayUrl.value = `https://www.liqpay.ua/api/3/checkout?data=${response.data.data}&signature=${response.data.signature}`
      } else if (response.data.provider === 'nowpayments') {
        cryptoInvoiceUrl.value = response.data.subscription.invoice_url || ''
      }
    }
  } catch (error) {
    console.error('Помилка створення платежу:', error)
    alert('Не вдалося створити платіж')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.subscription-container {
  max-width: 600px;
  margin: auto;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 8px;
}

.plans, .payment-methods {
  margin-bottom: 15px;
}

.liqpay-frame, .crypto-info {
  margin-top: 20px;
  text-align: center;
}
</style>
