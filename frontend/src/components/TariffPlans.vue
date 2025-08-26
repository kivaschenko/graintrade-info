<template>
  <div class="container mt-4">

    <!-- Payment Provider section -->
    <div class="mb-4" hidden>
      <label class="form-label me-3">{{ $t('tariffs.selectPaymentProvider') }}:</label>
      <div class="form-check form-check-inline">
        <input 
          class="form-check-input" 
          type="radio" 
          id="liqpay" 
          value="liqpay" 
          v-model="paymentProvider"
        >
        <label class="form-check-label" for="liqpay">LiqPay (Card, Apple Pay, Google Pay, Privat 24)</label>
      </div>
      <div class="form-check form-check-inline">
        <input 
          class="form-check-input" 
          type="radio" 
          id="fondy" 
          value="fondy" 
          v-model="paymentProvider"
        >
        <label class="form-check-label" for="fondy">Fondy (Card, Apple Pay, Google Pay)</label>
      </div>
      <div class="form-check form-check-inline">
        <input 
          class="form-check-input" 
          type="radio" 
          id="paypal" 
          value="paypal" 
          v-model="paymentProvider"
        >
        <label class="form-check-label" for="paypal">PayPal</label>
      </div>
      <div class="form-check form-check-inline">
        <input 
          class="form-check-input" 
          type="radio" 
          id="nowpayments" 
          value="nowpayments" 
          v-model="paymentProvider"
        >
        <label class="form-check-label" for="nowpayments">NOW Payments (Crypto currency)</label>
      </div>
    </div>

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
            <h3>{{ getTariffName(tariff) }}</h3>
            <h4>{{ getTariffPrice(tariff) }} {{ getTariffCurrency(tariff) }}/{{ getTariffTerms(tariff) }}</h4>
          </div>
          <div class="card-body">
            <p id="tariff-description" class="card-text">{{ getTariffDescription(tariff) }}</p>
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
              <li v-if="tariff.notify_new_messages">
                <i class="bi bi-check-circle text-success"></i> 
                {{ $t('tariffs.notifyNewMessages') }}
              </li>
              <li v-if="tariff.notify_new_items">
                <i class="bi bi-check-circle text-success"></i> 
                {{ $t('tariffs.notifyNewItems') }}
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

    <!-- LiqPay Payment Form -->
    <div v-if="liqpayForm" class="liqpay-form mt-4">
      <form
        ref="liqpayForm"
        :action="liqpayForm.action"
        method="POST"
        accept-charset="utf-8"
        target="_blank"
      >
        <input type="hidden" name="data" :value="liqpayForm.data" />
        <input type="hidden" name="signature" :value="liqpayForm.signature" />
        <input
          type="image"
          src="//static.liqpay.ua/buttons/payUk.png"
          alt="Pay with LiqPay"
        />
      </form>
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
      currentTariff: null,
      liqpayForm: null,
      paymentProvider: 'liqpay', // Default payment provider
    }
  },
  computed: {
    ...mapState(['user']),
  },
  watch: {
    liqpayForm(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          if (this.$refs.liqpayForm) {
            this.$refs.liqpayForm.submit();
            // Reset the form after submission to avoid resubmission on next change
            this.liqpayForm = null;
          }
        })
      }
    }
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
          tarif_id: tariff.id,
          payment_provider: this.paymentProvider,
        });
        if (r.data.checkout_url) {
          // Redirect to the checkout URL in a new tab
          window.open(r.data.checkout_url, '_blank');
          // Or redirect in the same tab
          // window.location.href = r.data.checkout_url;
        } else if (r.data.status === "free") {
          alert("Your Subscription was updated to Free plan!")
        } else if (r.data.liqpay_form) {
          this.liqpayForm = r.data.liqpay_form;
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
    },
    getTariffName(tariff) {
      return this.$i18n.locale === 'ua' && tariff.ua_name ? tariff.ua_name : tariff.name;
    },
    getTariffDescription(tariff) {
      return this.$i18n.locale === 'ua' && tariff.ua_description ? tariff.ua_description : tariff.description;
    },
    getTariffTerms(tariff) {
      return this.$i18n.locale === 'ua' && tariff.ua_terms ? tariff.ua_terms : tariff.terms;
    },
    getTariffPrice(tariff) {
      return this.$i18n.locale === 'ua' && tariff.ua_price ? tariff.ua_price : tariff.price;
    },
    getTariffCurrency(tariff) {
      return this.$i18n.locale === 'ua' && tariff.ua_currency ? tariff.ua_currency : tariff.currency;
    },
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
  },
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

#tariff-description {
  min-height: 60px; /* Adjust based on expected description length */
  margin-bottom: 15px;
  font-size: smaller;
  color: #555;
}
</style>
