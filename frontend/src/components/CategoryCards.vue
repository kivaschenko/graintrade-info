<template>
  <div class="container mt-5">
    <h1 class="mb-4">{{ $t('common_text.categories') }}</h1>
    <div class="row">
      <div class="col-md-4 mb-4" v-for="category in categories" :key="category.id">
        <div class="card h-100">
          <div class="card-body">
            <h5 class="card-title">{{ getCategoryName(category) }}</h5>
            <p class="card-text">{{ getCategoryDescription(category) }}</p>
            <router-link :to="{ name: 'Category', params: { id: category.id } }" class="btn btn-primary">
              {{ $t('common_text.offers') }}
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { mapState } from 'vuex';

export default {
  name: 'CategoryCards',
  data() {
    return {
      categories: [],
    };
  },
  computed: {
    ...mapState(['currentLocale']),
  },
  methods: {
    getCategoryName(category) {
      const currentLocale = this.$store.state.currentLocale;
      console.log('currentLocale', currentLocale);
      return currentLocale === 'ua' ? category.ua_name : category.name;
    },
    getCategoryDescription(category) {
      const currentLocale = this.$store.state.currentLocale;
      return currentLocale === 'ua' ? category.ua_description : category.description;
    },
  },
  async created() {
    try {
      const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/categories`);
      this.categories = response.data;
    } catch (error) {
      console.log('Error fetching categories', error);
    }
  },
};
</script>

<style scoped>
.card {
  height: 100%;
}
</style>