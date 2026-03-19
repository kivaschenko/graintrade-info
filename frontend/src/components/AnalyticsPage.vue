<template>
  <div class="analytics-page">
    <div class="container py-4">
      <!-- Page Header -->
      <div class="page-header mb-4">
        <h1 class="display-5 fw-bold text-primary">
          <i class="bi bi-graph-up me-2"></i>{{ $t('analytics.title') }}
        </h1>
        <p class="lead text-muted">{{ $t('analytics.subtitle') }}</p>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">{{ $t('common_text.loading') }}...</span>
        </div>
        <p class="mt-3 text-muted">{{ $t('analytics.loadingData') }}</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="alert alert-danger" role="alert">
        <i class="bi bi-exclamation-triangle me-2"></i>
        {{ error }}
      </div>

      <!-- Analytics Content -->
      <div v-else>
        <!-- Quick Summary Cards -->
        <div class="row g-3 mb-4">
          <div class="col-md-3" v-for="summary in summaryCards" :key="summary.title">
            <div class="card summary-card h-100">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                  <div>
                    <h6 class="card-subtitle mb-2 text-muted">{{ summary.title }}</h6>
                    <h3 class="card-title mb-0">{{ summary.value }}</h3>
                  </div>
                  <div :class="['icon-wrapper', summary.iconClass]">
                    <i :class="['bi', summary.icon]"></i>
                  </div>
                </div>
                <div v-if="summary.trend" class="mt-2">
                  <span :class="['badge', summary.trend.class]">
                    <i :class="['bi', summary.trend.icon, 'me-1']"></i>
                    {{ summary.trend.text }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Main Charts Row -->
        <div class="row g-4 mb-4">
          <!-- Price Trends Chart -->
          <div class="col-lg-8">
            <div class="card chart-card">
              <div class="card-header bg-white">
                <div class="d-flex justify-content-between align-items-center">
                  <h5 class="card-title mb-0">
                    <i class="bi bi-graph-up me-2"></i>{{ $t('analytics.priceTrends') }}
                  </h5>
                  <div class="btn-group btn-group-sm" role="group">
                    <button 
                      v-for="period in ['7d', '14d', '30d']" 
                      :key="period"
                      type="button" 
                      :class="['btn', selectedPeriod === period ? 'btn-primary' : 'btn-outline-primary']"
                      @click="changePeriod(period)"
                    >
                      {{ period }}
                    </button>
                  </div>
                </div>
              </div>
              <div class="card-body">
                <LineChart 
                  v-if="chartData.labels.length > 0"
                  :chartData="chartData"
                  :options="chartOptions"
                />
                <div v-else class="text-center text-muted py-5">
                  <i class="bi bi-graph-up fs-1"></i>
                  <p class="mt-2">{{ $t('analytics.noChartData') }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Commodity Distribution -->
          <div class="col-lg-4">
            <div class="card chart-card">
              <div class="card-header bg-white">
                <h5 class="card-title mb-0">
                  <i class="bi bi-pie-chart me-2"></i>{{ $t('analytics.distribution') }}
                </h5>
              </div>
              <div class="card-body">
                <DoughnutChart 
                  v-if="doughnutData.labels.length > 0"
                  :chartData="doughnutData"
                  :options="doughnutOptions"
                />
                <div v-else class="text-center text-muted py-5">
                  <i class="bi bi-pie-chart fs-1"></i>
                  <p class="mt-2">{{ $t('analytics.noData') }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Forecast Table -->
        <div class="card">
          <div class="card-header bg-white">
            <h5 class="card-title mb-0">
              <i class="bi bi-table me-2"></i>{{ $t('analytics.forecastTable') }}
            </h5>
          </div>
          <div class="card-body p-0">
            <div class="table-responsive">
              <table class="table table-hover mb-0">
                <thead class="table-light">
                  <tr>
                    <th>{{ $t('analytics.commodity') }}</th>
                    <th>{{ $t('analytics.region') }}</th>
                    <th>{{ $t('analytics.currentPrice') }}</th>
                    <th>{{ $t('analytics.tomorrow') }}</th>
                    <th>{{ $t('analytics.weekAhead') }}</th>
                    <th>{{ $t('analytics.trend') }}</th>
                    <th>{{ $t('analytics.confidence') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="forecast in forecastData" :key="forecast.commodity">
                    <td class="fw-semibold">{{ forecast.commodity }}</td>
                    <td><span class="badge bg-secondary">{{ forecast.region }}</span></td>
                    <td>${{ forecast.currentPrice }}</td>
                    <td>
                      <span v-if="forecast.next_day">
                        ${{ forecast.next_day.price.toFixed(2) }}
                      </span>
                      <span v-else class="text-muted">-</span>
                    </td>
                    <td>
                      <span v-if="forecast.week_ahead">
                        ${{ forecast.week_ahead.price.toFixed(2) }}
                        <small class="text-muted d-block">
                          ${{ forecast.week_ahead.lower_bound.toFixed(2) }} - 
                          ${{ forecast.week_ahead.upper_bound.toFixed(2) }}
                        </small>
                      </span>
                      <span v-else class="text-muted">-</span>
                    </td>
                    <td>
                      <span :class="['badge', getTrendBadgeClass(forecast)]">
                        <i :class="['bi', getTrendIcon(forecast), 'me-1']"></i>
                        {{ getTrendText(forecast) }}
                      </span>
                    </td>
                    <td>
                      <div class="progress" style="height: 20px;" v-if="forecast.next_day">
                        <div 
                          class="progress-bar" 
                          :class="getConfidenceClass(forecast.next_day.confidence)"
                          role="progressbar" 
                          :style="{ width: (forecast.next_day.confidence * 100) + '%' }"
                          :aria-valuenow="forecast.next_day.confidence * 100" 
                          aria-valuemin="0" 
                          aria-valuemax="100"
                        >
                          {{ (forecast.next_day.confidence * 100).toFixed(0) }}%
                        </div>
                      </div>
                      <span v-else class="text-muted">-</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Last Update Info -->
        <div class="text-center mt-4">
          <small class="text-muted">
            <i class="bi bi-clock me-1"></i>
            {{ $t('analytics.lastUpdated') }}: {{ lastUpdated }}
          </small>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import LineChart from './charts/LineChart.vue';
import DoughnutChart from './charts/DoughnutChart.vue';

export default {
  name: 'AnalyticsPage',
  components: {
    LineChart,
    DoughnutChart,
  },
  data() {
    return {
      loading: true,
      error: null,
      forecastData: [],
      selectedPeriod: '7d',
      lastUpdated: null,
      chartData: {
        labels: [],
        datasets: [],
      },
      doughnutData: {
        labels: [],
        datasets: [],
      },
    };
  },
  computed: {
    summaryCards() {
      if (!this.forecastData || this.forecastData.length === 0) return [];

      const avgPrice = this.calculateAveragePrice();
      const risingCount = this.forecastData.filter(f => this.calculateTrendPercentage(f) > 2).length;
      const fallingCount = this.forecastData.filter(f => this.calculateTrendPercentage(f) < -2).length;
      const avgConfidence = this.calculateAverageConfidence();

      return [
        {
          title: this.$t('analytics.avgPrice'),
          value: `$${avgPrice.toFixed(2)}`,
          icon: 'bi-currency-dollar',
          iconClass: 'bg-success-soft',
          trend: null,
        },
        {
          title: this.$t('analytics.risingMarkets'),
          value: risingCount,
          icon: 'bi-arrow-up-circle',
          iconClass: 'bg-success-soft',
          trend: {
            text: this.$t('analytics.bullish'),
            class: 'bg-success',
            icon: 'bi-arrow-up',
          },
        },
        {
          title: this.$t('analytics.fallingMarkets'),
          value: fallingCount,
          icon: 'bi-arrow-down-circle',
          iconClass: 'bg-danger-soft',
          trend: {
            text: this.$t('analytics.bearish'),
            class: 'bg-danger',
            icon: 'bi-arrow-down',
          },
        },
        {
          title: this.$t('analytics.avgConfidence'),
          value: `${(avgConfidence * 100).toFixed(0)}%`,
          icon: 'bi-shield-check',
          iconClass: 'bg-info-soft',
          trend: null,
        },
      ];
    },
    chartOptions() {
      return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'top',
          },
          tooltip: {
            mode: 'index',
            intersect: false,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: '#fff',
            bodyColor: '#fff',
            borderColor: 'rgba(255, 255, 255, 0.2)',
            borderWidth: 1,
            padding: 12,
            displayColors: true,
            callbacks: {
              label: function(context) {
                return `${context.dataset.label}: $${context.parsed.y.toFixed(2)}`;
              }
            }
          },
        },
        scales: {
          y: {
            beginAtZero: false,
            ticks: {
              callback: function(value) {
                return '$' + value.toFixed(2);
              }
            },
            grid: {
              color: 'rgba(0, 0, 0, 0.05)',
            }
          },
          x: {
            grid: {
              display: false,
            }
          }
        },
        interaction: {
          mode: 'nearest',
          axis: 'x',
          intersect: false
        },
      };
    },
    doughnutOptions() {
      return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'bottom',
          },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: '#fff',
            bodyColor: '#fff',
            borderColor: 'rgba(255, 255, 255, 0.2)',
            borderWidth: 1,
            padding: 12,
            callbacks: {
              label: function(context) {
                const label = context.label || '';
                const value = context.parsed || 0;
                return `${label}: ${value.toFixed(0)}%`;
              }
            }
          },
        },
      };
    },
  },
  async created() {
    await this.fetchForecastData();
    this.lastUpdated = new Date().toLocaleString(this.$i18n.locale === 'ua' ? 'uk-UA' : 'en-US');
  },
  methods: {
    async fetchForecastData() {
      try {
        this.loading = true;
        this.error = null;

        const apiUrl = process.env.VUE_APP_DATA_PIPELINE_API || 'http://localhost:8004';
        const response = await axios.get(`${apiUrl}/forecasts/homepage`, {
          timeout: 10000,
        });

        this.forecastData = response.data;
        
        // Prepare chart data
        this.prepareChartData();
        this.prepareDoughnutData();
        
        this.loading = false;
      } catch (err) {
        console.error('Failed to fetch forecast data:', err);
        this.error = this.$t('analytics.errorLoading');
        this.loading = false;
      }
    },
    prepareChartData() {
      if (!this.forecastData || this.forecastData.length === 0) return;

      const days = parseInt(this.selectedPeriod);
      const labels = [];
      const today = new Date();
      
      for (let i = 0; i <= days; i++) {
        const date = new Date(today);
        date.setDate(date.getDate() + i);
        labels.push(date.toLocaleDateString(this.$i18n.locale === 'ua' ? 'uk-UA' : 'en-US', { 
          month: 'short', 
          day: 'numeric' 
        }));
      }

      const colors = [
        { border: 'rgb(54, 162, 235)', background: 'rgba(54, 162, 235, 0.1)' },
        { border: 'rgb(255, 99, 132)', background: 'rgba(255, 99, 132, 0.1)' },
        { border: 'rgb(75, 192, 192)', background: 'rgba(75, 192, 192, 0.1)' },
        { border: 'rgb(255, 159, 64)', background: 'rgba(255, 159, 64, 0.1)' },
      ];

      const datasets = this.forecastData.slice(0, 4).map((forecast, index) => {
        // Create price progression (simplified - just showing trend)
        const data = [];
        const startPrice = forecast.next_day ? forecast.next_day.price : 100;
        const endPrice = forecast.week_ahead ? forecast.week_ahead.price : startPrice;
        
        for (let i = 0; i <= days; i++) {
          const progress = i / days;
          const price = startPrice + (endPrice - startPrice) * progress;
          data.push(price);
        }

        return {
          label: forecast.commodity,
          data: data,
          borderColor: colors[index].border,
          backgroundColor: colors[index].background,
          tension: 0.4,
          fill: true,
          pointRadius: 4,
          pointHoverRadius: 6,
        };
      });

      this.chartData = { labels, datasets };
    },
    prepareDoughnutData() {
      if (!this.forecastData || this.forecastData.length === 0) return;

      const labels = this.forecastData.map(f => f.commodity);
      const data = this.forecastData.map(() => 100 / this.forecastData.length); // Equal distribution for now

      this.doughnutData = {
        labels,
        datasets: [{
          data,
          backgroundColor: [
            'rgba(54, 162, 235, 0.8)',
            'rgba(255, 99, 132, 0.8)',
            'rgba(75, 192, 192, 0.8)',
            'rgba(255, 159, 64, 0.8)',
            'rgba(153, 102, 255, 0.8)',
            'rgba(255, 205, 86, 0.8)',
          ],
          borderWidth: 2,
          borderColor: '#fff',
        }],
      };
    },
    changePeriod(period) {
      this.selectedPeriod = period;
      this.prepareChartData();
    },
    calculateAveragePrice() {
      if (!this.forecastData || this.forecastData.length === 0) return 0;
      const sum = this.forecastData.reduce((acc, f) => {
        return acc + (f.next_day ? f.next_day.price : 0);
      }, 0);
      return sum / this.forecastData.length;
    },
    calculateAverageConfidence() {
      if (!this.forecastData || this.forecastData.length === 0) return 0;
      const sum = this.forecastData.reduce((acc, f) => {
        return acc + (f.next_day ? f.next_day.confidence : 0);
      }, 0);
      return sum / this.forecastData.length;
    },
    calculateTrendPercentage(forecast) {
      if (!forecast.next_day || !forecast.week_ahead) return 0;
      const nextPrice = forecast.next_day.price;
      const weekPrice = forecast.week_ahead.price;
      return ((weekPrice - nextPrice) / nextPrice) * 100;
    },
    getTrendBadgeClass(forecast) {
      const change = this.calculateTrendPercentage(forecast);
      if (change > 2) return 'bg-success';
      if (change < -2) return 'bg-danger';
      return 'bg-secondary';
    },
    getTrendIcon(forecast) {
      const change = this.calculateTrendPercentage(forecast);
      if (change > 2) return 'bi-arrow-up';
      if (change < -2) return 'bi-arrow-down';
      return 'bi-arrow-right';
    },
    getTrendText(forecast) {
      const change = this.calculateTrendPercentage(forecast);
      if (change > 2) return `+${change.toFixed(1)}%`;
      if (change < -2) return `${change.toFixed(1)}%`;
      return this.$t('analytics.stable');
    },
    getConfidenceClass(confidence) {
      if (confidence > 0.8) return 'bg-success';
      if (confidence > 0.6) return 'bg-info';
      if (confidence > 0.4) return 'bg-warning';
      return 'bg-danger';
    },
  },
};
</script>

<style scoped>
.analytics-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.page-header {
  text-align: center;
  padding: 2rem 0;
}

.summary-card {
  transition: transform 0.2s, box-shadow 0.2s;
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.summary-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.bg-success-soft {
  background: rgba(40, 167, 69, 0.1);
  color: var(--bs-success);
}

.bg-danger-soft {
  background: rgba(220, 53, 69, 0.1);
  color: var(--bs-danger);
}

.bg-info-soft {
  background: rgba(13, 202, 240, 0.1);
  color: var(--bs-info);
}

.chart-card {
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: box-shadow 0.2s;
  height: 100%;
}

.chart-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.chart-card .card-body {
  height: 400px;
}

.table th {
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.5px;
  color: #6c757d;
}

.table td {
  vertical-align: middle;
}

@media (max-width: 768px) {
  .page-header h1 {
    font-size: 2rem;
  }
  
  .chart-card .card-body {
    height: 300px;
  }
}
</style>
