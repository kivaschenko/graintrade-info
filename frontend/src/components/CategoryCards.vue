<template>
  <div class="container mt-5">
    <h1 class="mb-4 text-center">{{ $t('common_text.categories') }}</h1>

    <!-- Parent Categories -->
     <div v-for="(group, parentCategory) in groupedCategories" :key="parentCategory" class="mb-5">

      <!-- Parent Category title -->
      <h2 class="mb-3 category-group-title">
        {{ getParentCategoryName(parentCategory) }}
      </h2>
      <!-- Categories Grid -->
      <div class="row justify-content-center">
        <div class="col-md-3 mb-3" v-for="category in group" :key="category.id">
          <button
            class="btn btn-outline-primary btn-block category-button"
            @click="navigateToCategory(category.id)"
          >
            {{ getCategoryName(category) }}
          </button>
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

    groupedCategories() {
      return this.categories.reduce((groups, category) => {
        const parent = category.parent_category || 'Other';
        if (!groups[parent]) {
          groups[parent] = [];
        }
        groups[parent].push(category);
        return groups;
      }, {});
    },
  },
  methods: {
    getCategoryName(category) {
      const currentLocale = this.$store.state.currentLocale;
      return currentLocale === 'ua' ? category.ua_name : category.name;
    },
    getParentCategoryName(parentCategory) {
      const parent = this.categories.find(c => c.parent_category === parentCategory);
      return this.currentLocale === 'ua' ? parent?.parent_category_ua || parentCategory : parentCategory;
    },
    async fetchCategories() {
      try {
        const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/categories`);
        this.categories = response.data.sort((a,b) => {
          return this.getCategoryName(a).localeCompare(this.getCategoryName(b));
        });
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
.category-group-title {
  color: #2c3e50;
  font-size: 1.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #eee;
  margin-bottom: 1.5rem;
}

.category-button {
  width: 100%;
  padding: 0.75rem;
  font-size: 1rem;
  text-align: left;
  white-space: normal;
  height: 100%;
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
}

.category-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .col-md-3 {
    padding: 0.5rem;
  }
  
  .category-group-title {
    font-size: 1.25rem;
    margin-bottom: 1rem;
  }
  
  .category-button {
    padding: 0.5rem;
    font-size: 0.9rem;
  }
}
</style>