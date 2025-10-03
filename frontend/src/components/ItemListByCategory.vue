<template>
  <div class="graintrade-page">
    <!-- Category Header Section -->
    <div class="container mt-5">
      <div class="category-header-card">
        <div class="category-header-content">
          <div class="category-header-text">
            <h1 class="category-title">{{ getCategoryName(category) }}</h1>
            <p class="category-description">{{ getCategoryDescription(category) }}</p>
          </div>
          <div class="category-header-meta">
            <span class="item-count-badge">
              {{ totalItems }} {{ $t('common_text.items') }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- ItemFilter Component -->
    <div class="container">
      <ItemFilter 
        :initialCategoryId="selectedCategory"
        @filters-changed="handleFiltersChanged" 
        ref="itemFilter" 
        class="graintrade-filter"
      />
    </div>

    <!-- Item Table -->
    <div class="container">
      <ItemTable :items="items" class="graintrade-table" />
    </div>

    <!-- Pagination Controls -->
    <div class="container">
      <div class="graintrade-pagination" v-if="totalItems > pageSize">
        <button
          :disabled="page === 1"
          @click="handlePageChange(page - 1)"
          class="graintrade-btn-secondary graintrade-btn-pagination"
        >
          <i class="fas fa-chevron-left"></i>
          {{ $t('common_text.previous') || 'Previous' }}
        </button>
        
        <div class="pagination-info">
          <span class="page-current">{{ page }}</span>
          <span class="page-separator">of</span>
          <span class="page-total">{{ Math.ceil(totalItems / pageSize) }}</span>
        </div>
        
        <button
          :disabled="page * pageSize >= totalItems"
          @click="handlePageChange(page + 1)"
          class="graintrade-btn-secondary graintrade-btn-pagination"
        >
          {{ $t('common_text.next') || 'Next' }}
          <i class="fas fa-chevron-right"></i>
        </button>
      </div>
    </div>
    
    <!-- View on Map Button -->
    <div class="container">
      <div class="map-action-section">
        <button 
          @click="viewOnMap"
          class="graintrade-btn-primary graintrade-btn-map" 
          :disabled="items.length === 0 || loadingItems"
        >
          <i class="fas fa-map-marked-alt me-2"></i>
          {{ $t('map.viewFilteredOnMap') }} ({{ items.length }} {{ $t('common_text.items') }})
        </button>
        
        <div v-if="loadingItems" class="loading-indicator">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <span class="loading-text">{{ $t('common_text.loading') || 'Loading' }}...</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { mapState } from 'vuex';
import ItemTable from './ItemTable.vue';
import ItemFilter from './ItemFilter.vue'; // Import the new filter component

export default {
  name: 'ItemListByCategory',
  components: {
    ItemTable,
    ItemFilter, // Register the new component
  },
  data() {
    return {
      items: [],
      category: {},
      
      // Pagination state
      page: 1,
      pageSize: 10,
      totalItems: 0,

      // Filter states (now managed by ItemFilter, but mirrored here for API calls)
      appliedFilters: {}, // Stores the filters emitted by ItemFilter
      selectedCategory: '', // Initialized from route param
      
      loadingItems: false,
    };
  },
  computed: {
    ...mapState(['currentLocale']),
  },
  async created() {
    // Set initial category from route params for ItemFilter and API calls
    this.selectedCategory = this.$route.params.id; 
    // Initial fetch of items will be triggered by ItemFilter's initial emit after its categories are loaded
  },
  mounted() {
    // Manually trigger initial filters-changed emit if not automatically done by ItemFilter
    // (e.g., if initialCategoryId prop changes after ItemFilter is mounted)
    if (this.$refs.itemFilter) {
      this.$refs.itemFilter.applyFilters();
    }
  },
  methods: {
    // This method is now called by ItemFilter component
    handleFiltersChanged(filters) {
      this.appliedFilters = filters;
      this.page = 1; // Reset page on filter change
      this.fetchItems();
    },
    async fetchItems() {
      this.loadingItems = true;
      try {
        // Construct params using the appliedFilters
        const params = {
          offset: (this.page - 1) * this.pageSize,
          limit: this.pageSize,
          // Ensure category_id from route param is always included if applicable to this page
          // Otherwise, rely solely on appliedFilters.category_id
          ...this.appliedFilters,
        };
        // If this is a category-specific page, ensure category_id from route is respected
        if (this.$route.params.id && !params.category_id) {
             params.category_id = this.$route.params.id;
        }
        const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/categories/${this.$route.params.id}/items`, {
          params: params,
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
        this.items = response.data.items;
        this.category = response.data.category; // Ensure category data is still updated
        this.totalItems = response.data.total_items;
        
      } catch (error) {
        console.error('Error fetching items:', error);
      } finally {
        this.loadingItems = false;
      }
    },
    async handlePageChange(newPage) {
      this.page = newPage;
      await this.fetchItems();
    },
    // New method to navigate to the map page with current filters
    viewOnMap() {
      // Get the current filter parameters directly from the ItemFilter component
      const currentFilters = this.$refs.itemFilter.currentFilterParams;
      // Ensure category_id from route param is always included if applicable to this page
      if (this.$route.params.id && !currentFilters.category_id) {
        currentFilters.category_id = this.$route.params.id;
      }
      this.$router.push({
        name: 'FilteredItemsMap', // Make sure this name matches your router config
        query: currentFilters // Pass all current filter parameters
      });
    },
    getCategoryName(category) {
      const currentLocale = this.$store.state.currentLocale;
      return category ? (currentLocale === 'ua' ? category.ua_name : category.name) : '';
    },
    getCategoryDescription(category) {
      const currentLocale = this.$store.state.currentLocale;
      return category ? (currentLocale === 'ua' ? category.ua_description : category.name) : '';
    },
  },
};
</script>

<style scoped>
/* GrainTrade ItemListByCategory Styles */

.graintrade-page {
  min-height: 100vh;
  background: var(--graintrade-bg-alt);
  padding-bottom: 3rem;
}

/* Container Styling */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

/* Category Header Section */
.category-header-card {
  background: var(--graintrade-bg);
  border-radius: var(--graintrade-border-radius-large);
  box-shadow: var(--graintrade-shadow);
  border: 1px solid var(--graintrade-border);
  overflow: hidden;
  transition: var(--graintrade-transition);
  margin-bottom: 2rem;
}

.category-header-card:hover {
  box-shadow: var(--graintrade-shadow-hover);
  transform: translateY(-2px);
}

.category-header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2rem;
  gap: 2rem;
}

.category-header-text {
  flex: 1;
}

.category-title {
  color: var(--graintrade-secondary);
  font-weight: 700;
  font-size: 2.5rem;
  margin-bottom: 0.75rem;
  font-family: var(--graintrade-font-family);
  line-height: 1.2;
}

.category-description {
  color: var(--graintrade-text-light);
  font-size: 1.125rem;
  margin-bottom: 0;
  line-height: 1.5;
  font-family: var(--graintrade-font-family);
}

.category-header-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 1rem;
}

.item-count-badge {
  background: linear-gradient(135deg, var(--graintrade-primary), var(--graintrade-primary-dark));
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 50px;
  font-weight: 600;
  font-size: 1rem;
  box-shadow: 0 4px 12px rgba(39, 174, 96, 0.3);
  text-align: center;
  min-width: 120px;
}

/* Filter Section */
.graintrade-filter {
  margin-bottom: 2rem;
}

/* Table Section */
.graintrade-table {
  margin-bottom: 2rem;
}

/* Pagination Styling */
.graintrade-pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 2rem;
  margin: 2rem 0;
  padding: 1.5rem;
  background: var(--graintrade-bg);
  border-radius: var(--graintrade-border-radius-large);
  box-shadow: var(--graintrade-shadow);
  border: 1px solid var(--graintrade-border);
}

.graintrade-btn-pagination {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: 1px solid var(--graintrade-border);
  background: var(--graintrade-bg);
  color: var(--graintrade-text);
  border-radius: var(--graintrade-border-radius);
  cursor: pointer;
  transition: var(--graintrade-transition);
  font-weight: 500;
  font-family: var(--graintrade-font-family);
  min-width: 120px;
  justify-content: center;
}

.graintrade-btn-pagination:hover:not(:disabled) {
  background: var(--graintrade-primary);
  color: white;
  border-color: var(--graintrade-primary);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(39, 174, 96, 0.2);
}

.graintrade-btn-pagination:disabled {
  background: var(--graintrade-bg-alt);
  color: var(--graintrade-text-muted);
  border-color: var(--graintrade-border);
  cursor: not-allowed;
  opacity: 0.6;
}

.pagination-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-family: var(--graintrade-font-family);
  font-weight: 500;
  color: var(--graintrade-text);
}

.page-current {
  background: var(--graintrade-primary);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 50%;
  min-width: 2.5rem;
  height: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 1.1rem;
}

.page-separator {
  color: var(--graintrade-text-muted);
  font-size: 0.95rem;
}

.page-total {
  color: var(--graintrade-secondary);
  font-weight: 600;
  font-size: 1.1rem;
}

/* Map Action Section */
.map-action-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  padding: 2rem;
  background: var(--graintrade-bg);
  border-radius: var(--graintrade-border-radius-large);
  box-shadow: var(--graintrade-shadow);
  border: 1px solid var(--graintrade-border);
  margin-bottom: 2rem;
}

/* Button Styling */
.graintrade-btn-primary {
  background: linear-gradient(135deg, var(--graintrade-primary), var(--graintrade-primary-dark));
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: var(--graintrade-border-radius);
  font-weight: 600;
  font-size: 1.1rem;
  font-family: var(--graintrade-font-family);
  cursor: pointer;
  transition: var(--graintrade-transition);
  box-shadow: 0 4px 12px rgba(39, 174, 96, 0.3);
  min-width: 200px;
}

.graintrade-btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--graintrade-primary-dark), #1e8449);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(39, 174, 96, 0.4);
}

.graintrade-btn-primary:disabled {
  background: linear-gradient(135deg, rgba(39, 174, 96, 0.6), rgba(39, 174, 96, 0.4));
  cursor: not-allowed;
  opacity: 0.7;
  transform: none;
  box-shadow: none;
}

.graintrade-btn-map {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.125rem;
  padding: 1.25rem 2.5rem;
  min-width: 280px;
}

.graintrade-btn-secondary {
  background: var(--graintrade-bg);
  color: var(--graintrade-text);
  border: 1px solid var(--graintrade-border);
}

/* Loading Indicator */
.loading-indicator {
  display: flex;
  align-items: center;
  gap: 1rem;
  color: var(--graintrade-text-light);
  font-family: var(--graintrade-font-family);
}

.loading-text {
  font-weight: 500;
  font-size: 1rem;
}

.spinner-border {
  width: 1.5rem;
  height: 1.5rem;
  border-width: 0.2em;
}

/* Responsive Design */
@media (max-width: 992px) {
  .category-header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 1.5rem;
  }

  .category-header-meta {
    align-items: flex-start;
    width: 100%;
  }

  .item-count-badge {
    align-self: center;
  }

  .category-title {
    font-size: 2rem;
  }
}

@media (max-width: 768px) {
  .container {
    padding: 0 0.75rem;
  }

  .category-header-content {
    padding: 1.5rem;
  }

  .category-title {
    font-size: 1.75rem;
  }

  .category-description {
    font-size: 1rem;
  }

  .graintrade-pagination {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }

  .graintrade-btn-pagination {
    width: 100%;
    min-width: unset;
  }

  .pagination-info {
    order: -1;
  }

  .graintrade-btn-map {
    min-width: unset;
    width: 100%;
    padding: 1rem 1.5rem;
    font-size: 1rem;
  }

  .map-action-section {
    padding: 1.5rem;
  }
}

@media (max-width: 576px) {
  .category-header-content {
    padding: 1rem;
  }

  .category-title {
    font-size: 1.5rem;
  }

  .category-description {
    font-size: 0.95rem;
  }

  .item-count-badge {
    padding: 0.5rem 1rem;
    font-size: 0.9rem;
    min-width: 100px;
  }

  .graintrade-pagination {
    padding: 0.75rem;
  }

  .graintrade-btn-pagination {
    padding: 0.625rem 1rem;
    font-size: 0.9rem;
  }

  .page-current {
    min-width: 2rem;
    height: 2rem;
    font-size: 1rem;
  }

  .graintrade-btn-map {
    padding: 0.875rem 1.25rem;
    font-size: 0.95rem;
  }

  .map-action-section {
    padding: 1rem;
  }
}

/* Focus States for Accessibility */
.graintrade-btn-primary:focus-visible,
.graintrade-btn-pagination:focus-visible {
  outline: 2px solid var(--graintrade-primary);
  outline-offset: 2px;
}

/* Enhanced Visual Hierarchy */
.graintrade-page > .container:first-child {
  padding-top: 1rem;
}

.graintrade-page > .container:last-child {
  padding-bottom: 2rem;
}

/* Animation for Page Load */
.category-header-card {
  animation: slideInFromTop 0.6s ease-out;
}

.graintrade-filter {
  animation: fadeInUp 0.8s ease-out 0.2s both;
}

.graintrade-table {
  animation: fadeInUp 0.8s ease-out 0.4s both;
}

.graintrade-pagination {
  animation: fadeInUp 0.8s ease-out 0.6s both;
}

.map-action-section {
  animation: fadeInUp 0.8s ease-out 0.8s both;
}

@keyframes slideInFromTop {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* High Contrast Mode Support */
@media (prefers-contrast: high) {
  .category-header-card,
  .graintrade-pagination,
  .map-action-section {
    border-width: 2px;
  }
  
  .graintrade-btn-primary,
  .graintrade-btn-pagination {
    border-width: 2px;
  }
}
</style>
