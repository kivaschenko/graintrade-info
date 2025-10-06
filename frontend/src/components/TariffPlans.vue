<template>
  <div class="container mt-4">

    <!-- Page Header -->
    <div class="page-header mb-3">
      <h1 class="display-5 fw-bold">{{ $t('tariffs.pageTitle') }}</h1>
      <p class="lead text-muted">{{ $t('tariffs.pageSubtitle') }}</p>
    </div>

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
            <h3 class="mb-1">{{ getTariffName(tariff) }}</h3>
            <h4 class="mb-0">
              {{ $t( 'common_text.price' ) }}: 
              <span class="fw-bold">
                {{ getTariffPrice(tariff) }} {{ formatCurrency(getTariffCurrency(tariff)) }}/{{ getTariffTerms(tariff) }}
              </span>
            </h4>
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
              <li v-if="tariff.allow_import_export">
                <i class="bi bi-check-circle text-success"></i> 
                {{ $t('tariffs.importExport') }}
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

    <!-- Cost Analysis Section -->
    <div class="cost-analysis-section mt-5">
      <div class="section-header mb-4">
        <h2 class="display-6 fw-bold text-center text-primary">{{ $t('tariffs.costAnalysisTitle') }}</h2>
      </div>

      <!-- Tariff Overview Table -->
      <div class="mb-5">
        <h3 class="h4 mb-3">{{ $t('tariffs.tariffOverviewTitle') }}</h3>
        <div class="table-responsive">
          <table class="table table-striped table-hover">
            <thead class="table-primary">
              <tr>
                <th>{{ $t('tariffs.plan') }}</th>
                <th>{{ $t('tariffs.duration') }}</th>
                <th>{{ $t('common_text.price') }} (USD)</th>
                <th>{{ $t('common_text.price') }} (UAH)</th>
                <th>{{ $t('tariffs.items') }}</th>
                <th>{{ $t('tariffs.mapViews') }}</th>
                <th>{{ $t('tariffs.geoSearch') }}</th>
                <th>{{ $t('tariffs.navigation') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="tariff in sortedTariffs" :key="tariff.id" :class="{ 'table-success': tariff.scope === currentTariff }">
                <td class="fw-bold">{{ getTariffName(tariff) }}</td>
                <td>{{ getTariffDuration(tariff) }}</td>
                <td>${{ tariff.price.toFixed(2) }}</td>
                <td>₴{{ getTariffPrice(tariff) }}</td>
                <td>{{ formatLimit(tariff.items_limit) }}</td>
                <td>{{ formatLimit(tariff.map_views_limit) }}</td>
                <td>{{ formatLimit(tariff.geo_search_limit) }}</td>
                <td>{{ formatLimit(tariff.navigation_limit) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Cost Per Service Analysis -->
      <div class="mb-5">
        <h3 class="h4 mb-3">{{ $t('tariffs.costPerServiceTitle') }}</h3>
        
        <!-- Cost Per Item -->
        <div class="mb-4">
          <h4 class="h5">{{ $t('tariffs.costPerItemTitle') }}</h4>
          <ul class="list-group">
            <li v-for="tariff in sortedTariffs" :key="'item-' + tariff.id" 
                class="list-group-item d-flex justify-content-between align-items-center"
                :class="{ 'list-group-item-success': tariff.scope === currentTariff }">
              <strong>{{ getTariffName(tariff) }}:</strong>
              <span class="badge bg-primary rounded-pill">
                ${{ getCostPerService(tariff, 'items_limit') }} {{ $t('tariffs.perItem') }}
              </span>
            </li>
          </ul>
        </div>

        <!-- Cost Per Map View -->
        <div class="mb-4">
          <h4 class="h5">{{ $t('tariffs.costPerMapViewTitle') }}</h4>
          <ul class="list-group">
            <li v-for="tariff in sortedTariffs" :key="'map-' + tariff.id" 
                class="list-group-item d-flex justify-content-between align-items-center"
                :class="{ 'list-group-item-success': tariff.scope === currentTariff }">
              <strong>{{ getTariffName(tariff) }}:</strong>
              <span class="badge bg-primary rounded-pill">
                ${{ getCostPerService(tariff, 'map_views_limit') }} {{ $t('tariffs.perView') }}
              </span>
            </li>
          </ul>
        </div>

        <!-- Cost Per Geo-Search -->
        <div class="mb-4">
          <h4 class="h5">{{ $t('tariffs.costPerGeoSearchTitle') }}</h4>
          <ul class="list-group">
            <li v-for="tariff in sortedTariffs" :key="'geo-' + tariff.id" 
                class="list-group-item d-flex justify-content-between align-items-center"
                :class="{ 'list-group-item-success': tariff.scope === currentTariff }">
              <strong>{{ getTariffName(tariff) }}:</strong>
              <span class="badge bg-primary rounded-pill">
                ${{ getCostPerService(tariff, 'geo_search_limit') }} {{ $t('tariffs.perSearch') }}
              </span>
            </li>
          </ul>
        </div>

        <!-- Cost Per Navigation -->
        <div class="mb-4">
          <h4 class="h5">{{ $t('tariffs.costPerNavigationTitle') }}</h4>
          <ul class="list-group">
            <li v-for="tariff in sortedTariffs" :key="'nav-' + tariff.id" 
                class="list-group-item d-flex justify-content-between align-items-center"
                :class="{ 'list-group-item-success': tariff.scope === currentTariff }">
              <strong>{{ getTariffName(tariff) }}:</strong>
              <span class="badge bg-primary rounded-pill">
                ${{ getCostPerService(tariff, 'navigation_limit') }} {{ $t('tariffs.perNavigation') }}
              </span>
            </li>
          </ul>
        </div>
      </div>

      <!-- Monthly Cost Comparison -->
      <div class="mb-5">
        <h3 class="h4 mb-3">{{ $t('tariffs.monthlyCostTitle') }}</h3>
        <div class="table-responsive">
          <table class="table table-striped">
            <thead class="table-info">
              <tr>
                <th>{{ $t('tariffs.plan') }}</th>
                <th>{{ $t('tariffs.monthlyEquivalent') }} (USD)</th>
                <th>{{ $t('tariffs.monthlyEquivalent') }} (UAH)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="tariff in sortedTariffs" :key="'monthly-' + tariff.id" 
                  :class="{ 'table-success': tariff.scope === currentTariff }">
                <td class="fw-bold">{{ getTariffName(tariff) }}</td>
                <td>${{ getMonthlyCost(tariff) }}</td>
                <td>₴{{ (getMonthlyCost(tariff) * 45).toFixed(2) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <small class="text-muted">
          <em>{{ $t('tariffs.businessMonthlyCalc') }}</em>
        </small>
      </div>

      <!-- Value Analysis -->
      <div class="mb-5">
        <h3 class="h4 mb-3">{{ $t('tariffs.valueAnalysisTitle') }}</h3>
        
        <div class="row">
          <div class="col-md-6 mb-4">
            <h4 class="h5">{{ $t('tariffs.bestValueTitle') }}</h4>
            <div class="card">
              <div class="card-body">
                <ul class="list-unstyled">
                  <li class="mb-2">
                    <strong>{{ $t('tariffs.casualUsers') }}:</strong> 
                    <span class="badge bg-success ms-2">{{ $t('tariff.free') }}</span><br>
                    <small class="text-muted">{{ $t('tariffs.casualUsersDesc') }}</small>
                  </li>
                  <li class="mb-2">
                    <strong>{{ $t('tariffs.smallBusinesses') }}:</strong> 
                    <span class="badge bg-primary ms-2">{{ $t('tariff.basic') }}</span><br>
                    <small class="text-muted">{{ $t('tariffs.smallBusinessesDesc') }}</small>
                  </li>
                  <li class="mb-2">
                    <strong>{{ $t('tariffs.mediumBusinesses') }}:</strong> 
                    <span class="badge bg-warning ms-2">{{ $t('tariff.premium') }}</span><br>
                    <small class="text-muted">{{ $t('tariffs.mediumBusinessesDesc') }}</small>
                  </li>
                  <li class="mb-2">
                    <strong>{{ $t('tariffs.largeEnterprises') }}:</strong> 
                    <span class="badge bg-dark ms-2">Business</span><br>
                    <small class="text-muted">{{ $t('tariffs.largeEnterprisesDesc') }}</small>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <div class="col-md-6 mb-4">
            <h4 class="h5">{{ $t('tariffs.costEfficiencyTitle') }}</h4>
            <div class="card">
              <div class="card-body">
                <ol class="list-group list-group-numbered list-group-flush">
                  <li class="list-group-item d-flex justify-content-between align-items-start">
                    <div class="ms-2 me-auto">
                      <div class="fw-bold">Business Plan</div>
                      $0.05 {{ $t('tariffs.perSearch') }}
                    </div>
                    <span class="badge bg-success rounded-pill">{{ $t('tariffs.bestValue') }}</span>
                  </li>
                  <li class="list-group-item d-flex justify-content-between align-items-start">
                    <div class="ms-2 me-auto">
                      <div class="fw-bold">Premium Plan</div>
                      $0.075 {{ $t('tariffs.perSearch') }}
                    </div>
                  </li>
                  <li class="list-group-item d-flex justify-content-between align-items-start">
                    <div class="ms-2 me-auto">
                      <div class="fw-bold">Basic Plan</div>
                      $0.10 {{ $t('tariffs.perSearch') }}
                    </div>
                  </li>
                  <li class="list-group-item d-flex justify-content-between align-items-start">
                    <div class="ms-2 me-auto">
                      <div class="fw-bold">Free Plan</div>
                      $0.00 {{ $t('tariffs.perSearch') }}
                    </div>
                    <span class="badge bg-info rounded-pill">Limited</span>
                  </li>
                </ol>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Key Insights -->
      <div class="mb-5">
        <h3 class="h4 mb-3">{{ $t('tariffs.keyInsightsTitle') }}</h3>
        <div class="card">
          <div class="card-body">
            <ul class="list-unstyled">
              <li class="mb-3">
                <i class="bi bi-graph-up text-primary me-2"></i>
                <strong>{{ $t('tariffs.volumeDiscounts') }}</strong>
              </li>
              <li class="mb-3">
                <i class="bi bi-currency-dollar text-success me-2"></i>
                <strong>{{ $t('tariffs.uniformPricing') }}</strong>
              </li>
              <li class="mb-3">
                <i class="bi bi-currency-exchange text-info me-2"></i>
                <strong>{{ $t('tariffs.currencyExchange') }}</strong>
              </li>
              <li class="mb-3">
                <i class="bi bi-calendar-check text-warning me-2"></i>
                <strong>{{ $t('tariffs.longTermCommitment') }}</strong>
              </li>
              <li class="mb-3">
                <i class="bi bi-arrow-up-circle text-secondary me-2"></i>
                <strong>{{ $t('tariffs.featureProgression') }}</strong>
              </li>
            </ul>
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
      currentTariff: null,
      liqpayForm: null,
      paymentProvider: 'liqpay', // Default payment provider
    }
  },
  computed: {
    ...mapState(['user']),
    sortedTariffs() {
      // Sort tariffs by price to show them in logical order
      const order = ['free', 'basic', 'premium', 'business'];
      return [...this.tariffs].sort((a, b) => {
        return order.indexOf(a.scope) - order.indexOf(b.scope);
      });
    },
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
          language: this.$i18n.locale,
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
    formatCurrency(currency) {
      const currencyMap = {
        'USD': '$',
        'EUR': '€',
        'UAH': 'грн.',
        // Add more currencies as needed
      };
      return currencyMap[currency] || currency;
    },
    getCostPerService(tariff, serviceType) {
      if (tariff.price === 0) {
        return '0.00';
      }
      const limit = tariff[serviceType];
      if (limit === 0) {
        return '0.00';
      }
      return (tariff.price / limit).toFixed(3);
    },
    getMonthlyCost(tariff) {
      if (tariff.scope === 'business') {
        // Business plan is for 180 days, so divide by 6 to get monthly cost
        return (tariff.price / 6).toFixed(2);
      }
      // All other plans are for 30 days (monthly)
      return tariff.price.toFixed(2);
    },
    getTariffDuration(tariff) {
      if (this.$i18n.locale === 'ua' && tariff.ua_terms) {
        return tariff.ua_terms;
      }
      return tariff.terms;
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
.page-header {
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
  margin-bottom: 25px;
}

.card {
  transition: transform 0.2s, box-shadow 0.2s;
  border-radius: 12px;
}

.card:hover {
  transform: translateY(-5px) scale(1.02);
  box-shadow: 0 6px 24px rgba(0,0,0,0.08);
}

.card-header {
  border-radius: 12px 12px 0 0;
}

.btn {
  width: 80%;
  font-size: 1.1em;
}

#tariff-description {
  min-height: 60px;
  margin-bottom: 15px;
  font-size: 0.98em;
  color: #555;
}

.list-unstyled li {
  margin-bottom: 8px;
  font-size: 0.97em;
}

.liqpay-form {
  text-align: center;
}

/* Cost Analysis Section Styles */
.cost-analysis-section {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 15px;
  padding: 2rem;
  margin-top: 3rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
}

.cost-analysis-section .section-header {
  border-bottom: 3px solid var(--graintrade-primary, #007bff);
  padding-bottom: 1rem;
  margin-bottom: 2rem;
}

.cost-analysis-section .table {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.cost-analysis-section .table thead th {
  border: none;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.875rem;
  letter-spacing: 0.5px;
}

.cost-analysis-section .table tbody tr:hover {
  background-color: rgba(0, 123, 255, 0.05);
}

.cost-analysis-section .list-group-item {
  border: none;
  border-radius: 8px !important;
  margin-bottom: 0.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.cost-analysis-section .list-group-item:hover {
  transform: translateX(5px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.cost-analysis-section .card {
  border: none;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
  transition: all 0.3s ease;
}

.cost-analysis-section .card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
}

.cost-analysis-section .badge {
  font-size: 0.875rem;
  padding: 0.5rem 1rem;
}

.cost-analysis-section h3, .cost-analysis-section h4, .cost-analysis-section h5 {
  color: var(--graintrade-secondary, #6c757d);
  margin-bottom: 1rem;
}

.cost-analysis-section .text-primary {
  color: var(--graintrade-primary, #007bff) !important;
}

.cost-analysis-section .list-group-numbered .list-group-item::before {
  font-weight: bold;
  color: var(--graintrade-primary, #007bff);
}

.cost-analysis-section .table-success {
  background-color: rgba(25, 135, 84, 0.1);
  border-left: 4px solid #198754;
}

.cost-analysis-section .list-group-item-success {
  background-color: rgba(25, 135, 84, 0.1);
  border-left: 4px solid #198754;
}

@media (max-width: 768px) {
  .cost-analysis-section {
    padding: 1rem;
    margin-top: 2rem;
  }
  
  .cost-analysis-section .table-responsive {
    font-size: 0.875rem;
  }
}
</style>