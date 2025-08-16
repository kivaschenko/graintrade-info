<template>
  <div class="container mt-4">
    <div v-if="error" class="alert alert-danger" role="alert">
      {{ error }}
    </div>

    <div v-if="isLoading" class="d-flex justify-content-center">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>

    <div v-else class="row">
      <div v-for="tariff in tariffs" :key="tariff.id" class="col-md-4 mb-4">
        <div class="card h-100" :class="{ 'border-primary': tariff.scope === currentTariff }">
          <div class="card-header text-center" 
               :class="{ 'bg-primary text-white': tariff.scope === currentTariff }">
            <h3>{{ tariff.name }}</h3>
            <h4>{{ tariff.price }} {{ tariff.currency }}/{{ tariff.terms }}</h4>
          </div>
          <div class="card-body">
            <p class="card-text">{{ tariff.description }}</p>
            <ul class="list-unstyled">
              <li>
                <i class="bi bi-check-circle text-success"></i> 
                {{ $t('tariffs.itemsLimit', { limit: formatLimit(tariff.items_limit) }) }}
              </li>
              <li>
                <i class="bi bi-check-circle text-success"></i> 
                {{ $t('tariffs.mapViewsLimit', { limit: formatLimit(tariff.map_views_limit) }) }}
              </li>
              <li>
                <i class="bi bi-check-circle text-success"></i> 
                {{ $t('tariffs.geoSearchLimit', { limit: formatLimit(tariff.geo_search_limit) }) }}
              </li>
              <li>
                <i class="bi bi-check-circle text-success"></i> 
                {{ $t('tariffs.navigationLimit', { limit: formatLimit(tariff.navigation_limit) }) }}
              </li>
            </ul>
          </div>
          <div class="card-footer text-center">
            <button 
              class="btn"
              :class="getButtonClass(tariff)"
              :disabled="isSubscribing || tariff.scope === currentTariff"
              @click="subscribe(tariff)">
              {{ getButtonText(tariff) }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex';
import api from '@/services/api';

export default {
  name: 'TariffPlans',
  data() {
    return {
      isLoading: false,
      isSubscribing: false,
      error: null,
      tariffs: [],
      currentTariff: null
    }
  },
  computed: {
    ...mapState(['user']),
  },
  methods: {
    formatLimit(limit) {
      return limit === -1 ? this.$t('tariffs.unlimited') : limit;
    },
    getButtonClass(tariff) {
      if (tariff.scope === this.currentTariff) {
        return 'btn-success';
      }
      return 'btn-primary';
    },
    getButtonText(tariff) {
      if (tariff.scope === this.currentTariff) {
        return this.$t('tariffs.currentPlan');
      }
      return this.$t('tariffs.subscribe');
    },
    async fetchTariffs() {
      try {
        const response = await api.get('/tariffs');
        this.tariffs = response.data;
      } catch (error) {
        console.error('Error fetching tariffs:', error);
        this.error = this.$t('tariffs.errorFetching');
      }
    },
    async fetchCurrentSubscription() {
      try {
        const response = await api.get(`/subscriptions/user/${this.user.id}`);
        if (response.data.status === 'active') {
            this.currentTariff = response.data.tarif.scope;
        }
      } catch (error) {
        console.error('Error fetching current subscription:', error);
      }
    },
    async subscribe(tariff) {
      if (!this.user || !this.user.id) {
        alert(this.$t('tariffs.loginRequired'));
        return;
      }
      this.isSubscribing = true;
      try {
        let r = await api.post('/subscriptions', {
          user_id: this.user.id,
          tarif_id: tariff.id
        });
        console.log('Subscription response:', r.data);
        if (r.data.checkout_url) {
          // Redirect to the checkout URL in a new tab
          window.open(r.data.checkout_url, '_blank');
          // Or redirect in the same tab
          // window.location.href = r.data.checkout_url;
        } else if (r.data.status === "free") {
          alert("Your Subscription was updated to Free plan!")
        } else {
          alert(this.$t('tariffs.noCheckoutUrl'));
        }
        await this.fetchCurrentSubscription();
      } catch (error) {
        console.error('Error subscribing:', error);
        alert(this.$t('tariffs.subscribeError'));
      } finally {
        this.isSubscribing = false;
      }
    }
  },
  async created() {
    this.isLoading = true;
    try {
      await Promise.all([
        this.fetchTariffs(),
        this.fetchCurrentSubscription()
      ]);
    } finally {
      this.isLoading = false;
    }
  }
}
</script>

<style scoped>
.card {
  transition: transform 0.2s;
}

.card:hover {
  transform: translateY(-5px);
}

.btn {
  width: 80%;
}
</style>
