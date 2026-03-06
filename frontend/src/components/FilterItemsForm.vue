<template>
  <form @submit.prevent="applyFilters" class="filter-form">
    <div>
      <label>Min Price:</label>
      <input type="number" v-model="filters.min_price" step="0.01" />
    </div>
    <div>
      <label>Max Price:</label>
      <input type="number" v-model="filters.max_price" step="0.01" />
    </div>
    <div>
      <label>Currency:</label>
      <input type="text" v-model="filters.currency" />
    </div>
    <div>
      <label>Min Amount:</label>
      <input type="number" v-model="filters.min_amount" />
    </div>
    <div>
      <label>Max Amount:</label>
      <input type="number" v-model="filters.max_amount" />
    </div>
    <div>
      <label>Measure:</label>
      <input type="text" v-model="filters.measure" />
    </div>
    <div>
      <label>Delivery Terms:</label>
      <input type="text" v-model="filters.terms_delivery" />
    </div>
    <div>
      <label>Country:</label>
      <input type="text" v-model="filters.country" />
    </div>
    <div>
      <label>Region:</label>
      <input type="text" v-model="filters.region" />
    </div>

    <button type="submit">Apply Filters</button>
  </form>

  <div v-if="items.length">
    <h3>Filtered Items:</h3>
    <ul>
      <li v-for="item in items" :key="item.id">{{ item.name }}</li>
    </ul>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import axios from 'axios'

const filters = reactive({
  min_price: null,
  max_price: null,
  currency: '',
  min_amount: null,
  max_amount: null,
  measure: '',
  terms_delivery: '',
  country: '',
  region: ''
})

const items = ref([])

const applyFilters = async () => {
  try {
    const params = { ...filters }
    // Remove empty/null filters
    Object.keys(params).forEach(
      key => (params[key] === null || params[key] === '') && delete params[key]
    )

    const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/filter-items`, { params })
    items.value = response.data
  } catch (err) {
    console.error('Failed to fetch filtered items:', err)
  }
}
</script>

<style scoped>
.filter-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}
</style>
