<template>
  <div class="filters-container">
    <div class="filter-group">
      <label for="category-filter">{{ $t('common.category') }}:</label>
      <select id="category-filter" v-model="currentSelectedCategory" @change="applyFilters">
        <option value="">{{ $t('common.allCategories') }}</option>
        <option v-for="cat in categories" :key="cat.id" :value="cat.id">
          {{ currentLocale === 'ua' ? cat.ua_name : cat.name }}
        </option>
      </select>
    </div>

    <div class="filter-group offer-type-group">
      <label>{{ $t('common.offerType') }}:</label>
      <button
        @click="setOfferType('all')"
        :class="{ 'active-filter': currentSelectedOfferType === 'all' }"
      >
        {{ $t('common.all') }}
      </button>
      <button
        @click="setOfferType('buy')"
        :class="{ 'active-filter': currentSelectedOfferType === 'buy' }"
      >
        {{ $t('common.buy') }}
      </button>
      <button
        @click="setOfferType('sell')"
        :class="{ 'active-filter': currentSelectedOfferType === 'sell' }"
      >
        {{ $t('common.sell') }}
      </button>
    </div>

    <div class="filter-group price-group">
      <label>{{ $t('common.price') }} (USD):</label>
      <input type="number" v-model.number="currentMinPrice" :placeholder="$t('common.from')" @input="debounceApplyFilters">
      <span class="price-separator">-</span>
      <input type="number" v-model.number="currentMaxPrice" :placeholder="$t('common.to')" @input="debounceApplyFilters">
    </div>

    <div class="filter-group country-group">
      <label for="country-filter">{{ $t('common.country') }}:</label>
      <select id="country-filter" v-model="currentSelectedCountry" @change="applyFilters">
        <option value="">{{ $t('common.allCountries') }}</option>
        <option value="Ukraine">Ukraine</option>
        <!-- Add more countries dynamically if available from backend -->
      </select>
    </div>
    
    <button class="btn-apply-filters" @click="applyFilters" :disabled="loadingCategories">
      <span v-if="loadingCategories">{{ $t('common.loading') }}...</span>
      <span v-else>{{ $t('common.applyFilters') }}</span>
    </button>
    <button class="btn-clear-filters" @click="clearFilters">{{ $t('common.clearFilters') }}</button>
  </div>
</template>

<script>
import axios from 'axios';
import { mapState } from 'vuex';

export default {
  name: 'ItemFilter',
  props: {
    // Initial category ID passed from the parent (e.g., ItemListByCategory route param)
    initialCategoryId: {
      type: [String, Number],
      default: ''
    }
  },
  data() {
    return {
      categories: [],
      currentSelectedCategory: this.initialCategoryId,
      currentSelectedOfferType: 'all',
      currentMinPrice: null,
      currentMaxPrice: null,
      currentSelectedCountry: '',
      
      loadingCategories: false,
      debounceTimeout: null,
    };
  },
  computed: {
    ...mapState(['currentLocale']),
    // Get current filter parameters as a computed property
    currentFilterParams() {
      const params = {};
      if (this.currentSelectedCategory) {
        params.category_id = this.currentSelectedCategory;
      }
      if (this.currentSelectedOfferType !== 'all') {
        params.offer_type = this.currentSelectedOfferType;
      }
      if (this.currentMinPrice !== null && this.currentMinPrice !== '') {
        params.min_price = this.currentMinPrice;
      }
      if (this.currentMaxPrice !== null && this.currentMaxPrice !== '') {
        params.max_price = this.currentMaxPrice;
      }
      if (this.currentSelectedCountry) {
        params.country = this.currentSelectedCountry;
      }
      return params;
    }
  },
  watch: {
    // Watch for changes in initialCategoryId prop to update the internal state
    initialCategoryId(newVal) {
      this.currentSelectedCategory = newVal;
    },
    // Watch for changes in route query parameters and update filters (for map page)
    '$route.query': {
      immediate: true, // Run on component creation
      handler(newQuery) {
        // Only apply if the current page is the map page or if we need to sync filters
        // This is primarily for the AllItemsMap component, which will read query params
        // For ItemListByCategory, the filters are driven by user interaction here.
        if (this.$route.name === 'FilteredItemsMap') {
          this.currentSelectedCategory = newQuery.category_id || '';
          this.currentSelectedOfferType = newQuery.offer_type || 'all';
          this.currentMinPrice = newQuery.min_price ? parseFloat(newQuery.min_price) : null;
          this.currentMaxPrice = newQuery.max_price ? parseFloat(newQuery.max_price) : null;
          this.currentSelectedCountry = newQuery.country || '';
        }
      }
    }
  },
  async created() {
    await this.fetchCategories();
  },
  methods: {
    async fetchCategories() {
      this.loadingCategories = true;
      try {
        const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/categories`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
        this.categories = response.data;
        console.log('Categories fetched in ItemFilter:', this.categories);
      } catch (error) {
        console.error('Error fetching categories in ItemFilter:', error);
      } finally {
        this.loadingCategories = false;
      }
    },
    setOfferType(type) {
      this.currentSelectedOfferType = type;
      this.applyFilters();
    },
    debounceApplyFilters() {
      clearTimeout(this.debounceTimeout);
      this.debounceTimeout = setTimeout(() => {
        this.applyFilters();
      }, 500); // Debounce for 500ms
    },
    applyFilters() {
      console.log('Filters applied in ItemFilter:', this.currentFilterParams);
      // Emit the current filter parameters to the parent component
      this.$emit('filters-changed', this.currentFilterParams);
    },
    clearFilters() {
      this.currentSelectedCategory = this.initialCategoryId; // Reset to initial category from prop
      this.currentSelectedOfferType = 'all';
      this.currentMinPrice = null;
      this.currentMaxPrice = null;
      this.currentSelectedCountry = '';
      this.applyFilters(); // Emit cleared filters
    },
  },
};
</script>

<style scoped>
.filters-container {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  justify-content: center;
  align-items: flex-end;
  margin-bottom: 25px;
  padding: 20px;
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.filter-group {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.filter-group label {
  font-size: 0.9em;
  color: #555;
  margin-bottom: 6px;
  font-weight: 600;
}

.filters-container select,
.filters-container input[type="number"] {
  padding: 10px 12px;
  border: 1px solid #ced4da;
  border-radius: 8px;
  font-size: 1em;
  color: #333;
  min-width: 120px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.filters-container select:focus,
.filters-container input[type="number"]:focus {
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
  outline: none;
}

.offer-type-group button {
  padding: 10px 15px;
  border: 1px solid #007bff;
  background-color: #fff;
  color: #007bff;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  font-weight: 500;
  margin-right: 5px;
}

.offer-type-group button:last-child {
  margin-right: 0;
}

.offer-type-group button.active-filter {
  background-color: #007bff;
  color: #fff;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.2);
}

.offer-type-group button:hover:not(.active-filter) {
  background-color: #e9f5ff;
}

.price-group {
  flex-direction: row;
  align-items: center;
  gap: 8px;
}

.price-group input {
  width: 90px;
}

.price-separator {
  font-size: 1.2em;
  color: #666;
  font-weight: bold;
}

.btn-apply-filters,
.btn-clear-filters {
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease-in-out;
  min-width: 120px;
}

.btn-apply-filters {
  background-color: #28a745;
  color: #fff;
  border: 1px solid #28a745;
  box-shadow: 0 2px 8px rgba(40, 167, 69, 0.2);
}

.btn-apply-filters:hover:not(:disabled) {
  background-color: #218838;
  border-color: #1e7e34;
  transform: translateY(-2px);
}

.btn-apply-filters:disabled {
  background-color: #95d6a7;
  border-color: #95d6a7;
  cursor: not-allowed;
  opacity: 0.8;
}

.btn-clear-filters {
  background-color: #dc3545;
  color: #fff;
  border: 1px solid #dc3545;
  box-shadow: 0 2px 8px rgba(220, 53, 69, 0.2);
}

.btn-clear-filters:hover {
  background-color: #c82333;
  border-color: #bd2130;
  transform: translateY(-2px);
}

@media (max-width: 768px) {
  .filters-container {
    flex-direction: column;
    align-items: stretch;
    padding: 15px;
    gap: 10px;
  }

  .filter-group {
    width: 100%;
  }

  .filters-container select,
  .filters-container input[type="number"],
  .offer-type-group button,
  .btn-apply-filters,
  .btn-clear-filters {
    width: 100%;
    min-width: unset;
    margin-right: 0;
  }

  .offer-type-group {
    flex-direction: row;
    justify-content: stretch;
    width: 100%;
  }
  .offer-type-group button {
      flex-grow: 1;
      margin-right: 5px;
  }
  .offer-type-group button:last-child {
      margin-right: 0;
  }

  .price-group {
    flex-direction: row;
    width: 100%;
    justify-content: space-between;
  }
  .price-group input {
    flex-grow: 1;
  }
}
</style>
