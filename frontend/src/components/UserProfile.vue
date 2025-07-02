<template>
  <div class="container mt-4">
    <div class="card">
      <div class="card-header bg-primary text-white">
        <h3>{{ $t('profile.title') }}</h3>
      </div>
      <div class="card-body">
        <div class="row">
          <!-- User Info Section -->
          <div class="col-md-6">
            <h4>{{ $t('profile.userInfo') }}</h4>
            <div class="mb-3">
              <strong>{{ $t('profile.username') }}:</strong> {{ user.username }}
            </div>
						<div class="mb-3">
							<strong>{{ $t('profile.fullName') }}:</strong> {{ user.full_name }}
						</div>
            <div class="mb-3">
              <strong>{{ $t('profile.email') }}:</strong> {{ user.email }}
            </div>
						<div class="mb-3">
							<strong>{{ $t('profile.phone') }}:</strong> {{ user.phone }}
						</div>
          </div>
          
          <!-- Subscription Info Section -->
          <div class="col-md-6">
            <h4>{{ $t('profile.subscription') }}</h4>
            <div class="subscription-details">
              <div class="mb-2">
                <strong>{{ $t('profile.plan') }}:</strong> 
                <span class="badge bg-primary">{{ subscription.tarif.name }}</span>
              </div>
              <div class="mb-2">
                <strong>{{ $t('profile.status') }}:</strong>
                <span :class="['badge', subscription.status === 'active' ? 'bg-success' : 'bg-warning']">
                  {{ subscription.status }}
                </span>
              </div>
              <div class="mb-2">
                <strong>{{ $t('profile.price') }}:</strong> 
                {{ subscription.tarif.price }} {{ subscription.tarif.currency }}
              </div>
              <div class="mb-2">
                <strong>{{ $t('profile.description') }}:</strong>
                {{ subscription.tarif.description }}
              </div>
              <div class="mb-2">
                <strong>{{ $t('profile.startDate') }}:</strong>
                {{ formatDate(subscription.start_date) }}
              </div>
              <div class="mb-2">
                <strong>{{ $t('profile.endDate') }}:</strong>
                {{ formatDate(subscription.end_date) }}
              </div>
              <div class="mb-2">
                <strong>{{ $t('profile.features') }}:</strong>
                <ul class="list-unstyled">
                  <li><i class="bi bi-check-circle text-success"></i> {{ $t('profile.basicFeatures') }}</li>
                  <li v-if="subscription.tarif.scope !== 'basic'">
                    <i class="bi bi-check-circle text-success"></i> {{ $t('profile.advancedFeatures') }}
                  </li>
                </ul>
              </div>
            </div>
            <!-- Usage Info Section -->
            <div class="usage-details mt-4">
              <h5>{{ $t('profile.usageTitle') }}</h5>
              <div class="card">
                <div class="card-body">
                  <!-- Items Count -->
                  <div class="mb-2">
                    <strong>{{ $t('profile.itemsUsage') }}:</strong>
                    <div class="progress">
                      <div 
                        class="progress-bar" 
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
                  </div>
                  <!-- Map Views Usage -->
                  <div class="mb-2">
                    <strong>{{ $t('profile.mapViewsUsage') }}:</strong>
                    <div class="progress">
                      <div 
                        class="progress-bar" 
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
                  </div>
                  <!-- Geo Search Count -->
                  <div class="mb-2">
                    <strong>{{ $t('profile.geoSearchUsage') }}:</strong>
                    <div class="progress">
                      <div 
                        class="progress-bar" 
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
                  </div>
                  <!-- Navigation Count -->
                  <div class="mb-2">
                    <strong>{{ $t('profile.navigationUsage') }}:</strong>
                    <div class="progress">
                      <div 
                        class="progress-bar" 
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
                  </div>
                  <!-- Usage Warnings -->
                  <div class="usage-warnings mt-3">
                    <div v-if="usage.items_count >= subscription.tarif.items_limit" class="alert alert-danger">
                      {{ $t('profile.itemLimitReached') }}
                    </div>
                    <div v-if="usage.map_views >= subscription.tarif.map_views_limit" class="alert alert-danger">
                      {{ $t('profile.mapViewsLimitReached') }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Upgrade Button -->
            <button v-if="subscription.tarif.scope === 'basic'" 
                    class="btn btn-warning mt-3"
                    @click="upgradePlan">
              {{ $t('profile.upgrade') }}
            </button>
          </div>
        </div>
        <div class="row mt-4">
          <div class="col-md-12">
            <item-by-user-table 
              v-if="Array.isArray(itemByUser) && itemByUser.length > 0"
              :items="itemByUser" 
              :ref="itemTable"
              @delete-item="fetchItemByUser"
              @itemUpdated="handleItemUpdate"
            />
            <div v-else class="text-muted text-center">
              {{ $t('profile.noItems') }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex';
import api from '@/services/api';
import ItemByUserTable from './ItemByUserTable.vue';

export default {
  name: 'UserProfile',
  components: {
    ItemByUserTable
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
          terms: ''
        },
        status: '',
        start_date: '',
        end_date: ''
      },
      usage: {
        items_count: 0,
        map_views: 0,
        tarif_scope: '',
        // geo_search_count: 0,
        // navigation_count: 0,
        is_active: false
      },
      itemByUser: []
    }
  },
  computed: {
    ...mapState(['isAuthenticated'])
  },
  methods: {
    formatDate(date) {
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
        // Fetch subscription data after user data
        await this.fetchSubscription();
        await this.fetchUsageData();
      } catch (error) {
        console.error('Error fetching user data:', error);
        this.error = 'Failed to load user data';
      }
    },
    async fetchSubscription() {
      try {
        // Make sure we have user data before fetching subscription
        if (!this.user.id) {
          throw new Error('User ID is not available');
        }
        const response = await api.get(`/subscriptions/user/${this.user.id}`);
        this.subscription = response.data;
        console.log('Subscription data:', this.subscription);
      } catch (error) {
        console.error('Error fetching subscription:', error);
        this.error = 'Failed to load subscription data';
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
    async upgradePlan() {
      // Implement upgrade logic here
      this.$router.get('/tarifs');
    },
    async fetchItemByUser() {
      try {
        const response = await api.get(`/items-by-user/${this.user.id}`);
        this.itemByUser = response.data;
        console.log('Items by user:', this.itemByUser);
      } catch (error) {
        console.error('Error fetching items by user:', error);
        this.itemByUser = [];
        this.error = 'Failed to load items';
      }
    },
    async handleItemUpdate() {
      // This method can be used to refresh items after an update
      await this.fetchItemByUser();
    }
  },
  async created() {
    if (this.isAuthenticated) {
      this.isLoading = true;
      try {
        await this.fetchUserData();
        await this.fetchSubscription(),
        await this.fetchUsageData(),
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
.subscription-details {
  padding: 15px;
  border-radius: 8px;
  background-color: #f8f9fa;
}

.badge {
  font-size: 0.9em;
  padding: 8px;
  margin-left: 5px;
}

.bi {
  margin-right: 5px;
}

.usage-details {
  margin-top: 20px;
}

.progress {
  height: 25px;
  margin-top: 8px;
}

.progress-bar {
  line-height: 25px;
  font-weight: bold;
}
</style>
