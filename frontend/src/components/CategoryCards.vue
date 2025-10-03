<template>
  <div class="container mt-5">
    <h1 class="mb-5 text-center text-graintrade-secondary">{{ $t('common_text.categories') }}</h1>

    <!-- Parent Categories -->
    <div v-for="(group, parentCategory) in groupedCategories" :key="parentCategory" class="mb-5">

      <!-- Parent Category title -->
      <h2 class="mb-4 category-group-title">
        <i class="bi bi-grid-3x3-gap me-2"></i>
        {{ getParentCategoryName(parentCategory) }}
      </h2>
      
      <!-- Categories Grid -->
      <div class="row g-3">
        <div class="col-sm-6 col-md-4 col-lg-3" v-for="category in group" :key="category.id">
          <div class="category-card" @click="navigateToCategory(category.id)">
            <div class="category-card-body">
              <i class="bi bi-tag category-icon"></i>
              <h6 class="category-name">{{ getCategoryName(category) }}</h6>
              <div class="category-arrow">
                <i class="bi bi-arrow-right"></i>
              </div>
            </div>
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
        console.error('Error fetching categories', error);
      }
    },
    navigateToCategory(categoryId) {
      this.$router.push({ name: 'ItemListByCategory', params: { id: categoryId } });
    },
  },
  async created() {
    await this.fetchCategories();
  },
};
</script>


<style scoped>
.category-group-title {
  color: var(--graintrade-secondary);
  font-size: 1.75rem;
  font-weight: 600;
  padding-bottom: 1rem;
  border-bottom: 3px solid var(--graintrade-primary);
  margin-bottom: 2rem;
  position: relative;
}

.category-group-title::after {
  content: '';
  position: absolute;
  bottom: -3px;
  left: 0;
  width: 60px;
  height: 3px;
  background: var(--graintrade-primary);
  border-radius: 2px;
}

.category-card {
  background: white;
  border: 2px solid var(--graintrade-border);
  border-radius: var(--graintrade-border-radius-large);
  transition: var(--graintrade-transition);
  cursor: pointer;
  overflow: hidden;
  height: 120px;
  display: flex;
  align-items: center;
  position: relative;
}

.category-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--graintrade-shadow-hover);
  border-color: var(--graintrade-primary);
}

.category-card:hover .category-arrow {
  transform: translateX(5px);
  opacity: 1;
}

.category-card:hover .category-icon {
  color: var(--graintrade-primary);
  transform: scale(1.1);
}

.category-card-body {
  padding: 1.5rem;
  text-align: center;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.category-icon {
  font-size: 2rem;
  color: var(--graintrade-text-light);
  transition: var(--graintrade-transition);
}

.category-name {
  color: var(--graintrade-secondary);
  font-weight: 500;
  margin: 0;
  font-size: 1rem;
  line-height: 1.3;
  text-align: center;
  word-wrap: break-word;
  hyphens: auto;
}

.category-arrow {
  position: absolute;
  bottom: 1rem;
  right: 1rem;
  color: var(--graintrade-primary);
  font-size: 1.2rem;
  opacity: 0;
  transition: var(--graintrade-transition);
}

/* Hover effects */
.category-card:active {
  transform: translateY(-2px);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .category-group-title {
    font-size: 1.5rem;
    margin-bottom: 1.5rem;
  }
  
  .category-card {
    height: 100px;
  }
  
  .category-card-body {
    padding: 1rem;
    gap: 0.5rem;
  }
  
  .category-icon {
    font-size: 1.5rem;
  }
  
  .category-name {
    font-size: 0.9rem;
  }
}

@media (max-width: 576px) {
  .category-group-title {
    font-size: 1.25rem;
    margin-bottom: 1rem;
  }
  
  .category-card {
    height: 80px;
  }
  
  .category-card-body {
    padding: 0.75rem;
    gap: 0.25rem;
  }
  
  .category-icon {
    font-size: 1.25rem;
  }
  
  .category-name {
    font-size: 0.8rem;
    line-height: 1.2;
  }
  
  .category-arrow {
    bottom: 0.5rem;
    right: 0.5rem;
    font-size: 1rem;
  }
}

/* Animation for page load */
.category-card {
  animation: fadeInUp 0.6s ease forwards;
}

.category-card:nth-child(1) { animation-delay: 0.1s; }
.category-card:nth-child(2) { animation-delay: 0.2s; }
.category-card:nth-child(3) { animation-delay: 0.3s; }
.category-card:nth-child(4) { animation-delay: 0.4s; }
.category-card:nth-child(5) { animation-delay: 0.5s; }
.category-card:nth-child(6) { animation-delay: 0.6s; }
</style>
