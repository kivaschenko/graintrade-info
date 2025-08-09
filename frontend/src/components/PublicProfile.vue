<template>
  <div class="container mt-4">
    <div class="card shadow-sm border-0">
      <div class="card-header bg-primary text-white text-center py-3">
        <h3 class="mb-0"> {{ $t('profile.title') }}: {{ user.full_name || user.username }}</h3>
      </div>
      <div class="card-body p-4">
        <div v-if="isLoading" class="text-center">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
        </div>
        <div v-else-if="error" class="alert alert-danger" role="alert">
          {{ error }}
        </div>
        <div v-else>
          <div class="row g-4">
            <!-- User Info Section -->
            <div class="col-md-6">
              <div class="card h-100 border-0 shadow-sm custom-card-nested">
                <div class="card-body">
                  <h4 class="card-title text-primary mb-3">{{ $t('profile.userInfo') }}</h4>
                  <div class="mb-3 d-flex align-items-center">
                    <i class="bi bi-person-fill me-2 text-muted"></i>
                    <strong>{{ $t('profile.username') }}:</strong>
                    <span class="ms-1">{{ user.username }}</span>
                  </div>
                  <div class="mb-3 d-flex align-items-center">
                    <i class="bi bi-person-badge me-2 text-muted"></i>
                    <strong>{{ $t('profile.fullName') }}:</strong>
                    <span class="ms-1">{{ user.full_name }}</span>
                  </div>
                  <div class="mb-3 d-flex align-items-center">
                    <i class="bi bi-envelope-fill me-2 text-muted"></i>
                    <strong>{{ $t('profile.email') }}:</strong>
                    <span class="ms-1">{{ user.email }}</span>  
                  </div>
                  <div class="mb-3 d-flex align-items-center">
                    <i class="bi bi-telephone-fill me-2 text-muted"></i>
                    <strong>{{ $t('profile.phone') }}:</strong>
                    <span class="ms-1">{{ user.phone }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Preferences Section -->
            <div class="col-md-6">
              <div class="card h-100 border-0 shadow-sm custom-card-nested">
                <div class="card-body">
                  <h4 class="card-title text-primary mb-3">{{ $t('profile.preferences') }}</h4>
                  <div class="mb-3">
                    <div class="d-flex align-items-start">
                      <i class="bi bi-tags-fill me-2 text-muted mt-1"></i>
                      <strong>{{ $t('preferences.interestedCategories') }}:</strong>
                      <div class="ms-2">
                        <span v-if="preferences.interested_categories && preferences.interested_categories.length">
                          <span
                            v-for="(category, index) in preferences.interested_categories"
                            :key="index"
                            class="badge bg-info me-1 mb-1"
                          >
                            {{ category }}
                          </span>
                        </span>
                        <span v-else class="text-muted">
                          None selected
                        </span>
                      </div>
                    </div>
                  </div>
                  <div class="mb-3">
                    <div class="d-flex align-items-start">
                      <i class="bi bi-globe2 me-2 text-muted mt-1"></i>
                      <strong>{{ $t('common_text.country') }}:</strong>
                      <span class="badge bg-warning ms-2">{{ preferences.country }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <hr class="my-5" />

          <!-- User's Items Section -->
          <h4 class="card-title text-primary mb-3">{{ $t('profile.allItems') }} {{ user.username }}</h4>
          <ItemTable :items="items" />

          <!-- Pagination -->
          <div class="d-flex justify-content-center align-items-center mt-4" v-if="totalItems > pageSize">
            <button
              :disabled="page === 1"
              @click="handlePageChange(page - 1)"
              class="btn btn-outline-primary btn-sm me-2 rounded-pill"
            >
              &lt; Previous
            </button>
            <span class="text-muted mx-2">{{ page }} / {{ Math.ceil(totalItems / pageSize) }}</span>
            <button
              :disabled="page * pageSize >= totalItems"
              @click="handlePageChange(page + 1)"
              class="btn btn-outline-primary btn-sm ms-2 rounded-pill"
            >
              Next &gt;
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api';
import axios from 'axios';
import ItemTable from './ItemTable.vue';

export default {
  name: 'PublicProfile',
  components: {
    ItemTable,
  },
  data() {
    return {
      isLoading: false,
      error: null,
      user: {},
      preferences: {},
      items: [],
      totalItems: 0,
      page: 1,
      pageSize: 10,
    };
  },
  watch: {
    // Watch for changes in the route params, specifically 'id'
    '$route.params.id': {
      handler(newId, oldId) {
        if (newId && newId !== oldId) {
          console.log(`Fetching data for user ID: ${newId}`);
          this.fetchData(newId);
        }
      },
      immediate: true, // Fetch data immediately when the component is created
    },
  },
  methods: {
    async fetchData(userId) {
      this.isLoading = true;
      this.error = null;
      try {
        await this.fetchUserData(userId);
        await this.fetchUserPreferences(userId);
        await this.fetchItems(userId);
      } catch (error) {
        console.error('Error fetching public profile data:', error);
        this.error = 'Failed to load user profile.';
      } finally {
        this.isLoading = false;
      }
    },
    async fetchUserData(userId) {
      try {
        const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/users/${userId}`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
        this.user = response.data;
      } catch (error) {
        console.error('Error fetching user data:', error);
        throw new Error('Failed to load user data.');
      }
    },
    async fetchUserPreferences(userId) {
      try {
        // The API endpoint for preferences is assumed to be `preferences/{userId}`
        const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/preferences/${userId}`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
        this.preferences = response.data || { interested_categories: [], country: '' };
      } catch (error) {
        // Log the error but don't stop the app, as preferences might be missing
        console.warn('Could not fetch user preferences:', error);
        this.preferences = { interested_categories: [], country: '' };
      }
    },
    async fetchItems(userId) {
      try {
        const params = {
          offset: (this.page - 1) * this.pageSize,
          limit: this.pageSize,
        };
        // The API endpoint for fetching items by user is assumed to be `items-by-user/{userId}`
        const response = await api.get(`/items-by-user/${userId}`, { params });
        this.items = response.data.items || [];
        this.totalItems = response.data.total_items || 0;
      } catch (error) {
        console.error('Error fetching user items:', error);
        throw new Error('Failed to load user items.');
      }
    },
    async handlePageChange(newPage) {
      this.page = newPage;
      await this.fetchItems(this.$route.params.id);
    },
  },
};
</script>

<style scoped>
/* Main Card Styling */
.card {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08); /* More prominent shadow for main card */
}

.card-header {
  border-bottom: none;
  border-radius: 12px 12px 0 0;
  font-weight: 600;
  letter-spacing: 0.5px;
  background-image: linear-gradient(to right, #007bff, #0056b3); /* Subtle gradient */
}

.card-body {
  padding: 2.5rem;
}

/* Section Titles */
.card-title {
  font-weight: 600;
  margin-bottom: 1.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08); /* Slightly stronger separator */
  color: #007bff; /* Primary color for titles */
}

/* Nested Card Styling (for User Info, Subscription, Usage) */
.custom-card-nested {
    background-color: #fcfdff; /* Slightly different background for nested cards */
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
}

.custom-card-nested:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 15px rgba(0, 0, 0, 0.1); /* Subtle lift and shadow on hover */
}

/* Info Details (strong tags and icons) */
.mb-3 strong {
  color: #343a40;
  min-width: 90px; /* Adjust as needed for alignment */
}

.bi {
  margin-right: 0.5rem;
  font-size: 1.1em;
  vertical-align: middle;
  color: #6c757d; /* Muted color for icons */
}

/* Badges */
.badge {
  font-size: 0.85em;
  padding: 0.5em 0.8em;
  border-radius: 0.5rem;
  font-weight: 600;
  min-width: 70px; /* Give badges a consistent width */
  text-align: center;
}

.badge.bg-primary { background-color: #007bff !important; }
.badge.bg-info { background-color: #17a2b8 !important; }
.badge.bg-success { background-color: #28a745 !important; }
.badge.bg-warning { 
    background-color: #ffc107 !important; 
    color: #343a40 !important; /* Ensure readable text on warning badge */
}

/* Horizontal Rule Separator */
hr {
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

/* Pagination controls */
.pagination-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin: 20px 0;
}

.pagination-controls button {
  min-width: 80px; /* Slightly wider buttons */
  padding: 8px 18px; /* More padding */
  border-radius: 50px; /* Fully rounded pills */
  font-weight: 600;
  transition: all 0.2s ease-in-out;
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
  transform: translateY(-1px); /* Subtle lift on hover */
}

.pagination-controls span {
  font-weight: 500;
  color: #6c757d;
}
</style>
