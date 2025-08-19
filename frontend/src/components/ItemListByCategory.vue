<template>
  <div>
    <div class="container mt-5">
      <div class="card" style="width: auto;">
        <div class="card-body">
          <h1 class="card-title">{{ getCategoryName(category) }}</h1>
          <p class="card-text">{{ getCategoryDescription(category) }}</p>
        </div>
      </div>
    </div>

    <!-- ItemFilter Component -->
    <ItemFilter 
      :initialCategoryId="selectedCategory"
      @filters-changed="handleFiltersChanged" 
      ref="itemFilter" 
      class="mt-4 mb-4"
    />

    <!-- Item Table -->
    <ItemTable :items="items" />

    <div class="pagination-controls" v-if="totalItems > pageSize">
      <button
        :disabled="page === 1"
        @click="handlePageChange(page -1)"
        class="btn btn-outline-secondary btn-sm"
      >&lt; Prev</button>
      <span> {{ page }} / {{ Math.ceil(totalItems /pageSize) }}</span>
      <button
        :disabled="page * pageSize >= totalItems"
        @click="handlePageChange(page + 1)"
        class="btn btn-outline-secondary btn-sm"
      >Next &gt;</button>
    </div>
    
    <!-- View on Map Button -->
    <div class="text-center mt-4">
      <button 
        @click="viewOnMap"
        class="btn btn-primary btn-lg" 
        :disabled="items.length === 0 || loadingItems"
      >
        {{ $t('map.viewFilteredOnMap') }} ({{ items.length }} {{ $t('common_text.items') }})
      </button>
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
/* Filter Controls Styles (removed from here, now in ItemFilter.vue) */

/* Pagination controls (from original ItemListByCategory) */
.pagination-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin: 20px 0;
}

.pagination-controls button {
  min-width: 70px;
  margin: 0 4px;
  padding: 6px 16px;
  border-radius: 20px;
  border: 1px solid #ced4da;
  color:#333;
  transition: background 0.2s, color 0.2s, border 0.2s;
  font-weight: 500;
  cursor: pointer;
}

.pagination-controls button:disabled {
  background: #e9ecef;
  color: #aaa;
  border-color: #e9ecef;
  cursor: not-allowed;
}

.pagination-controls button:not(:disabled):hover {
  background: #007bff;
  color: #fff;
  border-color: #007bff;
}

/* Base styling for the page */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 15px;
}
.card {
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.08);
}
.card-title {
  color: #007bff;
  font-weight: 700;
}
.card-text {
  color: #6c757d;
}

/* Table styles */
.table {
  background-color: #ffffff;
  border-radius: 12px;
  overflow: hidden; /* Ensures rounded corners apply to content */
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
}
.table thead th {
  background-color: #e9ecef;
  color: #495057;
  font-weight: 600;
  border-bottom: 1px solid #dee2e6;
  padding: 15px;
}
.table tbody tr:hover {
  background-color: #f8f9fa;
}
.table tbody td, .table tbody th {
  padding: 12px 15px;
  vertical-align: middle;
}
.table tbody th a {
  color: #007bff;
  text-decoration: none;
  font-weight: 500;
}
.table tbody th a:hover {
  text-decoration: underline;
}

/* Responsive adjustments for filters (moved to ItemFilter.vue) */
/* The styles for .filters-container and its children should be in ItemFilter.vue */
</style>
