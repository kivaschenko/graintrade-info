<template>
  <div class="container mt-4">
    <div v-if="!isAuthenticated" class="alert alert-warning text-center my-4" role="alert">
      <i class="bi bi-exclamation-triangle-fill me-2"></i>
      {{ $t('profile.loginToView') || 'Please log in to view user profiles.' }}
    </div>
    <div v-else class="card shadow-sm border-0">
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
                          <span v-if="$store.state.currentLocale === 'ua'">
                            <span v-for="(category, index) in preferences.ua_interested_categories" :key="index" class="badge bg-primary me-1 mb-1">
                              {{ category }}
                            </span>
                          </span>
                          <span v-else>
                            <span v-for="(category, index) in preferences.interested_categories" :key="index" class="badge bg-primary me-1 mb-1">
                              {{ category }}
                            </span>
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
                      <span class="badge bg-secondary ms-2">{{ preferences.country }}</span>
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
  computed: {
    isAuthenticated() {
      return !!localStorage.getItem('access_token');
    },
  },
  watch: {
    // Watch for changes in the route params, specifically 'id'
    '$route.params.id': {
      handler(newId, oldId) {
        if (newId && newId !== oldId) {
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
  border-radius: var(--graintrade-border-radius-large);
  overflow: hidden;
  box-shadow: var(--graintrade-shadow);
  transition: var(--graintrade-transition);
}

.card:hover {
  box-shadow: var(--graintrade-shadow-hover);
}

.card-header {
  border-bottom: none;
  border-radius: var(--graintrade-border-radius-large) var(--graintrade-border-radius-large) 0 0;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.card-body {
  padding: 2rem;
}

/* Section Titles */
.card-title {
  font-weight: 600;
  margin-bottom: 1.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--graintrade-border);
  color: var(--graintrade-secondary);
}

/* Nested Card Styling (for User Info, Subscription, Usage) */
.custom-card-nested {
    background-color: var(--graintrade-bg-light);
    border: 1px solid var(--graintrade-border);
    border-radius: var(--graintrade-border-radius-large);
    transition: var(--graintrade-transition);
}

.custom-card-nested:hover {
    transform: translateY(-3px);
    box-shadow: var(--graintrade-shadow-hover);
}

/* Info Details (strong tags and icons) */
.mb-3 strong {
  color: var(--graintrade-secondary);
  min-width: 90px;
}

.bi {
  margin-right: 0.5rem;
  font-size: 1.1em;
  vertical-align: middle;
  color: var(--graintrade-text-light);
}

/* Badges */
.badge {
  font-size: 0.85em;
  padding: 0.5em 0.8em;
  border-radius: var(--graintrade-border-radius);
  font-weight: 600;
  min-width: 70px;
  text-align: center;
}

.badge.bg-graintrade-primary { 
    background-color: var(--graintrade-primary) !important; 
    color: white !important;
}

.badge.bg-info { 
    background-color: #17a2b8 !important; 
    color: white !important;
}

.badge.bg-success { 
    background-color: var(--graintrade-primary) !important; 
    color: white !important;
}

.badge.bg-warning { 
    background-color: #ffc107 !important; 
    color: var(--graintrade-secondary) !important;
}

/* Progress Bars */
.progress {
  height: 28px;
  border-radius: var(--graintrade-border-radius);
  background-color: var(--graintrade-bg-alt);
  overflow: hidden;
}

.progress-bar {
  line-height: 28px;
  font-weight: 600;
  color: white;
  transition: width 0.6s ease;
  border-radius: var(--graintrade-border-radius);
  text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
}

.bg-graintrade-primary {
    background-color: var(--graintrade-primary) !important;
}

.bg-graintrade-accent {
    background-color: var(--graintrade-accent) !important;
}

/* Alert for Usage Warnings */
.alert.alert-sm {
  font-size: 0.85rem;
  padding: 0.5rem 1rem;
  border-radius: var(--graintrade-border-radius);
  margin-top: 0.75rem;
  display: flex;
  align-items: center;
  border: 1px solid transparent;
}

.alert-warning {
  background-color: rgba(255, 193, 7, 0.1);
  color: #856404;
  border-color: rgba(255, 193, 7, 0.2);
}

/* Upgrade and Action Buttons */
.btn-outline-primary.hover-lift:hover {
  transform: translateY(-2px);
  box-shadow: var(--graintrade-shadow);
}

.btn-danger {
  background-color: var(--graintrade-accent);
  border-color: var(--graintrade-accent);
  color: white;
  font-weight: 500;
  transition: var(--graintrade-transition);
}

.btn-danger:hover {
  background-color: #c82333;
  border-color: #c82333;
  transform: translateY(-2px);
  box-shadow: var(--graintrade-shadow);
}

/* Horizontal Rule Separator */
hr {
  border-top: 1px solid var(--graintrade-border);
  opacity: 0.5;
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
  min-width: 80px;
  padding: 8px 18px;
  border-radius: var(--graintrade-border-radius-large);
  font-weight: 600;
  transition: var(--graintrade-transition);
}

.pagination-controls button:disabled {
  background: var(--graintrade-bg-alt);
  color: var(--graintrade-text-muted);
  border-color: var(--graintrade-border);
  cursor: not-allowed;
}

.pagination-controls button:not(:disabled):hover {
  transform: translateY(-1px);
}

.pagination-controls span {
  font-weight: 500;
  color: var(--graintrade-text-light);
}

/* Modal styles */
.modal-backdrop {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.4);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-dialog {
  background: white;
  border-radius: var(--graintrade-border-radius-large);
  box-shadow: var(--graintrade-shadow-hover);
  max-width: 500px;
  width: 100%;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--graintrade-text-light);
  transition: var(--graintrade-transition);
}

.btn-close:hover {
  color: var(--graintrade-secondary);
}

#tariff-description {
  min-height: 60px;
  margin-bottom: 15px;
  font-size: 0.98em;
  color: var(--graintrade-text);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .card-body {
    padding: 1.5rem;
  }
  
  .badge {
    font-size: 0.75em;
    padding: 0.4em 0.6em;
    min-width: 60px;
  }
  
  .progress {
    height: 24px;
  }
  
  .progress-bar {
    line-height: 24px;
    font-size: 0.8rem;
  }
}
</style>