<template>
  <div class="container mt-5">
    <h1 class="mb-4 text-center">{{ $t('common_text.categories') }}</h1>
    <div class="row justify-content-center">
      <div class="col-md-3 mb-3" v-for="category in categories" :key="category.id">
        <button
          class="btn btn-primary btn-block category-button"
          @click="navigateToCategory(category.id)"
        >
          {{ getCategoryName(category) }}
        </button>
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
      return currentLocale === 'ua' ? category.ua_name : category.name;
    },
    async fetchCategories() {
      try {
        const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/categories`);
        this.categories = response.data;
      } catch (error) {
        console.log('Error fetching categories', error);
      }
    },
    navigateToCategory(categoryId) {
      this.$router.push({ name: 'Category', params: { id: categoryId } });
    },
  },
  async created() {
    await this.fetchCategories();
  },
};
</script>

<style scoped>
.category-button {
  width: 100%;
  padding: 1rem;
  font-size: 1.2rem;
  text-transform: capitalize;
}
</style>