<template>
  <div class="container mt-4">
    <div class="card shadow-sm border-0">
      <div class="card-header bg-primary text-white text-center py-3">
        <h3 class="mb-0">{{ $t('profile.title') }}</h3>
      </div>
      <div class="card-body p-4">
        <div class="row g-4">
          <div class="col-md-6">
            <div class="card h-100 border-0 shadow-sm custom-card-nested">
                <div class="card-body">
                    <h4 class="card-title text-primary mb-3">{{ $t('profile.userInfo') }}</h4>
                    <div class="mb-3 d-flex align-items-center">
                        <i class="bi bi-person-fill me-2 text-muted"></i>
                        <strong>{{ $t('profile.username') }}:</strong> <span class="ms-1">{{ user.username }}</span>
                    </div>
                    <div class="mb-3 d-flex align-items-center">
                        <i class="bi bi-person-badge me-2 text-muted"></i>
                        <strong>{{ $t('profile.fullName') }}:</strong> <span class="ms-1">{{ user.full_name }}</span>
                    </div>
                    <div class="mb-3 d-flex align-items-center">
                        <i class="bi bi-envelope-fill me-2 text-muted"></i>
                        <strong>{{ $t('profile.email') }}:</strong> <span class="ms-1">{{ user.email }}</span>
                    </div>
                    <div class="mb-3 d-flex align-items-center">
                        <i class="bi bi-phone-fill me-2 text-muted"></i>
                        <strong>{{ $t('profile.phone') }}:</strong> <span class="ms-1">{{ user.phone }}</span>
                    </div>
                </div>
            </div>
          </div>
          
          <div class="col-md-6">
            <div class="card h-100 border-0 shadow-sm custom-card-nested">
                <div class="card-body">
                    <h4 class="card-title text-primary mb-3">{{ $t('profile.subscription') }}</h4>
                    <div class="mb-3 d-flex align-items-center">
                        <i class="bi bi-gem me-2 text-muted"></i>
                        <strong>{{ $t('profile.plan') }}:</strong> 
                        <span :class="['badge ms-2', subscription.tarif.scope === 'basic' ? 'bg-info' : 'bg-primary']">{{ subscription.tarif.name }}</span>
                    </div>
                    <div class="mb-2 d-flex align-items-center">
                        <i class="bi bi-patch-check-fill me-2 text-muted"></i>
                        <strong>{{ $t('profile.status') }}:</strong>
                        <span :class="['badge ms-2', subscription.status === 'active' ? 'bg-success' : 'bg-warning']">
                            {{ subscription.status }}
                        </span>
                    </div>
                    <div class="mb-2 d-flex align-items-center">
                        <i class="bi bi-currency-dollar me-2 text-muted"></i>
                        <strong>{{ $t('profile.price') }}:</strong> 
                        <span class="ms-1">{{ subscription.tarif.price }} {{ subscription.tarif.currency }}</span>
                    </div>
                    <div class="mb-2 d-flex align-items-center">
                        <i class="bi bi-info-circle-fill me-2 text-muted"></i>
                        <strong>{{ $t('profile.description') }}:</strong>
                        <span class="ms-1">{{ subscription.tarif.description }}</span>
                    </div>
                    <div class="mb-2 d-flex align-items-center">
                        <i class="bi bi-calendar-check me-2 text-muted"></i>
                        <strong>{{ $t('profile.startDate') }}:</strong>
                        <span class="ms-1">{{ formatDate(subscription.start_date) }}</span>
                    </div>
                    <div class="mb-2 d-flex align-items-center">
                        <i class="bi bi-calendar-x me-2 text-muted"></i>
                        <strong>{{ $t('profile.endDate') }}:</strong>
                        <span class="ms-1">{{ formatDate(subscription.end_date) }}</span>
                    </div>
                    <div class="mb-2">
                        <strong>{{ $t('profile.features') }}:</strong>
                        <ul class="list-unstyled mt-2 ms-4">
                            <li><i class="bi bi-check-circle text-success me-2"></i> {{ $t('profile.basicFeatures') }}</li>
                            <li v-if="subscription.tarif.scope !== 'basic'">
                                <i class="bi bi-check-circle text-success me-2"></i> {{ $t('profile.advancedFeatures') }}
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
          </div>
        </div>

        <div class="card shadow-sm border-0 mt-4 custom-card-nested">
            <div class="card-body">
                <h4 class="card-title text-primary mb-3">{{ $t('profile.usageTitle') }}</h4>
                <div class="row g-3">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <strong>{{ $t('profile.itemsUsage') }}:</strong>
                            <div class="progress mt-1" style="height: 28px;">
                                <div 
                                    class="progress-bar progress-bar-striped progress-bar-animated"
                                    role="progressbar"
                                    :style="{ width: (usage.items_count / subscription.tarif.items_limit * 100) + '%' }"
                                    :class="{
                                        'bg-success': usage.items_count < subscription.tarif.items_limit * 0.7,
                                        'bg-warning': usage.items_count >= subscription.tarif.items_limit * 0.7 && usage.items_count < subscription.tarif.items_limit,
                                        'bg-danger': usage.items_count >= subscription.tarif.items_limit
                                    }"
                                >
                                    {{ usage.items_count }} / {{ subscription.tarif.items_limit }}
                                </div>
                            </div>
                            <div v-if="usage.items_count >= subscription.tarif.items_limit" class="alert alert-danger alert-sm mt-2 p-2">
                                <i class="bi bi-exclamation-triangle-fill me-2"></i>{{ $t('profile.itemLimitReached') }}
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <strong>{{ $t('profile.mapViewsUsage') }}:</strong>
                            <div class="progress mt-1" style="height: 28px;">
                                <div 
                                    class="progress-bar progress-bar-striped progress-bar-animated"
                                    role="progressbar"
                                    :style="{ width: (usage.map_views / subscription.tarif.map_views_limit * 100) + '%' }"
                                    :class="{
                                        'bg-success': usage.map_views < subscription.tarif.map_views_limit * 0.7,
                                        'bg-warning': usage.map_views >= subscription.tarif.map_views_limit * 0.7 && usage.map_views < subscription.tarif.map_views_limit,
                                        'bg-danger': usage.map_views >= subscription.tarif.map_views_limit
                                    }"
                                >
                                    {{ usage.map_views }} / {{ subscription.tarif.map_views_limit }}
                                </div>
                            </div>
                            <div v-if="usage.map_views >= subscription.tarif.map_views_limit" class="alert alert-danger alert-sm mt-2 p-2">
                                <i class="bi bi-exclamation-triangle-fill me-2"></i>{{ $t('profile.mapViewsLimitReached') }}
                            </div>
                        </div>
                    </div>
                     <div class="col-md-6" v-if="subscription.tarif.geo_search_limit !== undefined">
                        <div class="mb-3">
                            <strong>{{ $t('profile.geoSearchUsage') }}:</strong>
                            <div class="progress mt-1" style="height: 28px;">
                                <div 
                                    class="progress-bar progress-bar-striped progress-bar-animated" 
                                    role="progressbar"
                                    :style="{ width: (usage.geo_search_count / subscription.tarif.geo_search_limit * 100) + '%' }"
                                    :class="{
                                        'bg-success': usage.geo_search_count < subscription.tarif.geo_search_limit * 0.7,
                                        'bg-warning': usage.geo_search_count >= subscription.tarif.geo_search_limit * 0.7 && usage.geo_search_count < subscription.tarif.geo_search_limit,
                                        'bg-danger': usage.geo_search_count >= subscription.tarif.geo_search_limit
                                    }"
                                >
                                    {{ usage.geo_search_count }} / {{ subscription.tarif.geo_search_limit }}
                                </div>
                            </div>
                            <div v-if="usage.geo_search_count >= subscription.tarif.geo_search_limit" class="alert alert-danger alert-sm mt-2 p-2">
                                <i class="bi bi-exclamation-triangle-fill me-2"></i>{{ $t('profile.geoSearchLimitReached') }}
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6" v-if="subscription.tarif.navigation_limit !== undefined">
                        <div class="mb-3">
                            <strong>{{ $t('profile.navigationUsage') }}:</strong>
                            <div class="progress mt-1" style="height: 28px;">
                                <div 
                                    class="progress-bar progress-bar-striped progress-bar-animated" 
                                    role="progressbar"
                                    :style="{ width: (usage.navigation_count / subscription.tarif.navigation_limit * 100) + '%' }"
                                    :class="{
                                        'bg-success': usage.navigation_count < subscription.tarif.navigation_limit * 0.7,
                                        'bg-warning': usage.navigation_count >= subscription.tarif.navigation_limit * 0.7 && usage.navigation_count < subscription.tarif.navigation_limit,
                                        'bg-danger': usage.navigation_count >= subscription.tarif.navigation_limit
                                    }"
                                >
                                    {{ usage.navigation_count }} / {{ subscription.tarif.navigation_limit }}
                                </div>
                            </div>
                            <div v-if="usage.navigation_count >= subscription.tarif.navigation_limit" class="alert alert-danger alert-sm mt-2 p-2">
                                <i class="bi bi-exclamation-triangle-fill me-2"></i>{{ $t('profile.navigationLimitReached') }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
            
        <div class="text-center mt-4" v-if="subscription.tarif.scope === 'basic'">
            <button class="btn btn-warning btn-lg px-5 py-3" @click="upgradePlan">
                <i class="bi bi-arrow-up-circle me-2"></i>{{ $t('profile.upgrade') }}
            </button>
        </div>

        <!-- Preferences Section -->
        <div class="row g-4">
          <div class="col-md-6">
            <div class="card shadow-sm border-0 mt-4 custom-card-nested">
              <div class="card-body">
                <h4 class="card-title text-primary mb-3">{{ $t('preferences.notificationPreferencesStatus') }}</h4>
                <div v-if="preferences">
                  <div class="row g-3 mb-3">
                    <div class="col-md-6">
                      <div class="d-flex align-items-center">
                        <i class="bi bi-bell-fill me-2 text-muted"></i>
                        <strong>{{ $t('preferences.notifyMeAboutNewMessages') }}:</strong>
                        <span :class="['badge ms-2', preferences.notify_new_messages ? 'bg-success' : 'bg-secondary']">
                          {{ preferences.notify_new_messages ? 'Yes / Так' : 'No / Ні' }}
                        </span>
                      </div>
                    </div>
                    <div class="col-md-6">
                      <div class="d-flex align-items-center">
                        <i class="bi bi-bell-fill me-2 text-muted"></i>
                        <strong>{{ $t('preferences.notifyMeAboutNewItems') }}:</strong>
                        <span :class="['badge ms-2', preferences.notify_new_items ? 'bg-success' : 'bg-secondary']">
                          {{ preferences.notify_new_items ? 'Yes / Так' : 'No / Ні' }}
                        </span>
                      </div>
                    </div>
                    <div class="col-12">
                      <div class="d-flex align-items-start">
                        <i class="bi bi-tags-fill me-2 text-muted mt-1"></i>
                        <strong>{{ $t('preferences.interestedCategories') }}:</strong>
                        <div class="ms-2">
                          <span v-if="preferences.interested_categories && preferences.interested_categories.length">
                            <span v-for="(category, index) in preferences.interested_categories" :key="index" class="badge bg-info me-1 mb-1">
                              {{ category }}
                            </span>
                          </span>
                          <span v-else class="text-muted">
                            None selected
                          </span>
                        </div>
                      </div>
                    </div>
                    <div class="col-12">
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
          </div>
          <div class="col-md-6">
            <PreferencesForm :initialPreferences="preferences" @updated="fetchPreferences" :key="preferences.country" />
          </div>
        </div>

        <hr class="my-5">

        <h4 class="card-title text-primary mb-3">{{ $t('profile.myItems') }}</h4>
        <ItemByUserTable
          :items="itemByUser" 
          :ref="itemTable"
          @delete-item="handleItemDeletion"
          @itemUpdated="handleItemUpdate"
        />
        <div class="d-flex justify-content-center align-items-center mt-4" v-if="totalItems > pageSize">
            <button
                :disabled="page === 1"
                @click="handlePageChange(page -1)"
                class="btn btn-outline-primary btn-sm me-2 rounded-pill"
            >&lt; {{ $t('pagination.prev') }}</button>
            <span class="text-muted mx-2"> {{ page }} / {{ Math.ceil(totalItems /pageSize) }}</span>
            <button
                :disabled="page * pageSize >= totalItems"
                @click="handlePageChange(page + 1)"
                class="btn btn-outline-primary btn-sm ms-2 rounded-pill"
            >{{ $t('pagination.next') }} &gt;</button>
        </div>
      </div>
    </div>


  </div>
</template>

<script>
import { mapState } from 'vuex';
import api from '@/services/api';
import ItemByUserTable from './ItemByUserTable.vue';
import PreferencesForm from './PreferencesForm.vue';

export default {
  name: 'UserProfile',
  components: {
    ItemByUserTable,
    PreferencesForm, // Add this line to include the PreferencesForm component
  },
  data() {
    return {
      isLoading: false,
      error: null,
      user: {},
      subscription: {
        tarif: {
          name: '',
          description: '',
          price: 0,
          currency: 'EUR',
          scope: '',
          terms: '',
          items_limit: 0, // Added for usage calculations
          map_views_limit: 0, // Added for usage calculations
          geo_search_limit: 0,
          navigation_limit: 0
        },
        status: '',
        start_date: '',
        end_date: ''
      },
      usage: {
        items_count: 0,
        map_views: 0,
        geo_search_count: 0, // Ensure these are initialized
        navigation_count: 0, // Ensure these are initialized
        tarif_scope: '',
        is_active: false
      },
      itemByUser: [],

      // Pagination state
      totalItems: 0,
      page: 1,
      pageSize: 10,

      loadingItems: false,

      // Preferences form state
      preferences: {
        notify_new_messages: false,
        notify_new_items: false,
        interested_categories: [],
        country: '',
      },
    }
  },
  computed: {
    ...mapState(['isAuthenticated'])
  },
  methods: {
    formatDate(date) {
      if (!date) return ''; // Handle empty date
      return new Date(date).toLocaleDateString(this.$i18n.locale, {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    },
    async fetchUserData() {
      try {
        const response = await api.get('/users/me');
        this.user = response.data;
        console.log('User data:', this.user);
        await this.fetchSubscription();
        await this.fetchUsageData();
        await this.fetchPreferences(); // Fetch preferences after user data is available
      } catch (error) {
        console.error('Error fetching user data:', error);
        this.error = 'Failed to load user data';
      }
    },
    async fetchSubscription() {
      try {
        if (!this.user.id) {
          throw new Error('User ID is not available');
        }
        const response = await api.get(`/subscriptions/user/${this.user.id}`);
        this.subscription = {
            ...this.subscription, // Keep initial structure
            ...response.data
        };
        console.log('Subscription data:', this.subscription);
      } catch (error) {
        console.error('Error fetching subscription:', error);
        this.error = 'Failed to load subscription data';
        // Provide default tarif limits if subscription fails to load fully
        this.subscription.tarif = { 
            ...this.subscription.tarif, 
            items_limit: 0, 
            map_views_limit: 0,
            geo_search_limit: 0,
            navigation_limit: 0
        };
      }
    },
    async fetchUsageData() {
      try {
        if (!this.user.id) {
          throw new Error('User ID is not available');
        }
        const response = await api.get(`/subscriptions/usage/${this.user.id}`);
        this.usage = response.data || {
          items_count: 0,
          map_views: 0,
          geo_search_count: 0,
          navigation_count: 0,
          tarif_scope: '',
          is_active: false
        };
        console.log('Usage data:', this.usage);
      } catch (error) {
        console.error('Error fetching usage data:', error);
        this.error = 'Failed to load usage data';
        this.usage = {
          items_count: 0,
          map_views: 0,
          geo_search_count: 0,
          navigation_count: 0,
          tarif_scope: '',
          is_active: false
        };
      }
    },
    upgradePlan() {
      this.$router.push('/tarifs'); // Correct usage for navigation
    },
    async fetchItemByUser() {
      this.loadingItems = true;
      try {
        // Ensure user.id is available before making the request
        if (!this.user.id) {
            console.warn('User ID not available for fetching items. Retrying after user data fetch.');
            return; // Exit and wait for user data to be fetched first
        }
        const params = {
          offset: (this.page - 1) * this.pageSize,
          limit: this.pageSize
        };
        const response = await api.get(`/items-by-user/${this.user.id}`, { params }, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`
          }
        });
        this.itemByUser = response.data.items || [];
        this.totalItems = response.data.total_items || 0;
        console.log('Items by user:', this.itemByUser);
      } catch (error) {
        console.error('Error fetching items by user:', error);
        this.itemByUser = [];
        this.error = 'Failed to load items';
      } finally {
        this.loadingItems = false;
      }
    },
    async handleItemUpdate() {
      await this.fetchItemByUser();
      // Potentially also refetch usage if item update can affect usage (e.g., changing item status that affects count)
    },
    async handleItemDeletion() {
      // Re-fetch the list of items
      await this.fetchItemByUser();
      // Re-fetch the usage data to update item count
      await this.fetchUsageData();
    },
    async handlePageChange(newPage) {
      this.page = newPage;
      await this.fetchItemByUser();
    },
    async fetchPreferences() {
      try {
        if (!this.user.id) {
          console.warn('User ID not available for fetching preferences.');
          return;
        }
        const response = await api.get(`/preferences`);
        this.preferences = response.data || {
          notify_new_messages: false,
          notify_new_items: false,
          interested_categories: [],
          country: ''
        };
      } catch (error) {
        console.error('Error fetching preferences:', error);
        this.error = 'Failed to load preferences';
      }
    },
    getCategoryName(category) {
      return this.$store.state.currentLocale === 'ua' ? category.ua_name : category.name;
    },
  },
  async created() {
    if (this.isAuthenticated) {
      this.isLoading = true;
      try {
        await this.fetchUserData(); // This now also fetches subscription, usage, and preferences
        await this.fetchItemByUser();
      } catch (error) {
        console.error('Error during created lifecycle:', error);
        this.error = 'Failed to load data';
      } finally {
        this.isLoading = false;
      }
    } else {
      this.$router.push('/login');
    }
  }
}
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

/* Progress Bars */
.progress {
  height: 28px;
  border-radius: 0.5rem;
  background-color: #e9ecef;
  overflow: hidden; /* Ensure progress bar content stays within bounds */
}

.progress-bar {
  line-height: 28px;
  font-weight: 600;
  color: white;
  transition: width 0.6s ease;
  border-radius: 0.5rem;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.2); /* Slight text shadow for readability */
}

/* Alert for Usage Warnings */
.alert.alert-sm {
  font-size: 0.85rem;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  margin-top: 0.75rem;
  display: flex;
  align-items: center;
  background-color: #f8d7da; /* Light red for danger alerts */
  color: #721c24; /* Dark red text */
  border-color: #f5c6cb;
}

/* Upgrade Button */
.btn-warning {
  background-color: #ffc107;
  border-color: #ffc107;
  color: #343a40;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  box-shadow: 0 4px 10px rgba(255, 193, 7, 0.3);
  transition: all 0.3s ease;
}

.btn-warning:hover {
  background-color: #e0a800;
  border-color: #e0a800;
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(255, 193, 7, 0.4);
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