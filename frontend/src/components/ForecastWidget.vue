// Frontend Integration Example - Vue.js Component
// File: frontend/src/components/ForecastWidget.vue

<template>
  <div class="forecast-widget">
    <h2 class="widget-title">📊 Price Forecasts</h2>

    <div v-if="loading" class="loading">
      <span class="spinner"></span> Loading forecasts...
    </div>

    <div v-else-if="error" class="error">
      ⚠️ {{ error }}
    </div>

    <!-- Empty state: DB has no future predictions yet -->
    <div v-else-if="forecasts.length === 0" class="empty-state">
      <p>📭 No forecasts available yet. Pipeline may not have run today.</p>
    </div>

    <div v-else class="forecasts-grid">
      <div
        v-for="forecast in forecasts"
        :key="forecast.commodity"
        class="forecast-card"
      >
        <h3 class="commodity-name">{{ forecast.commodity }}</h3>
        <div class="region">{{ forecast.region }}</div>

        <!-- Tomorrow's Forecast -->
        <div v-if="forecast.next_day" class="forecast-item tomorrow">
          <div class="label">Tomorrow</div>
          <div class="price">${{ safePrice(forecast.next_day.price) }}</div>
          <div class="confidence">
            <span
              class="confidence-bar"
              :style="{ width: safePercent(forecast.next_day.confidence) }"
            ></span>
            {{ safeConfidenceLabel(forecast.next_day.confidence) }} confidence
          </div>
        </div>

        <!-- Week Ahead Forecast -->
        <div v-if="forecast.week_ahead" class="forecast-item week">
          <div class="label">Week Ahead</div>
          <div class="price">${{ safePrice(forecast.week_ahead.price) }}</div>
          <!-- Only show range if both bounds are present -->
          <div v-if="forecast.week_ahead.lower_bound != null && forecast.week_ahead.upper_bound != null" class="range">
            Range: ${{ safePrice(forecast.week_ahead.lower_bound) }} –
            ${{ safePrice(forecast.week_ahead.upper_bound) }}
          </div>
          <div class="confidence">
            <span
              class="confidence-bar"
              :style="{ width: safePercent(forecast.week_ahead.confidence) }"
            ></span>
            {{ safeConfidenceLabel(forecast.week_ahead.confidence) }} confidence
          </div>
        </div>

        <!-- Price Change Indicator -->
        <div
          v-if="forecast.next_day && forecast.week_ahead"
          class="trend"
          :class="getTrendClass(forecast)"
        >
          {{ getTrendText(forecast) }}
        </div>
      </div>
    </div>

    <div class="widget-footer">
      <small>Updated: {{ lastUpdated || '—' }}</small>
      <a href="/forecasts" class="view-all-link">View All Forecasts →</a>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'ForecastWidget',

  data() {
    return {
      forecasts: [],
      loading: true,
      error: null,
      lastUpdated: null,
      refreshInterval: null,
    };
  },

  mounted() {
    this.fetchForecasts();
    // Refresh every 5 minutes
    this.refreshInterval = setInterval(this.fetchForecasts, 5 * 60 * 1000);
  },

  beforeUnmount() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  },

  methods: {
    async fetchForecasts() {
      try {
        this.loading = true;
        this.error = null;

        // ✅ Fixed: use /forecasts/homepage for the simplified homepage format
        const apiUrl = process.env.VUE_APP_DATA_PIPELINE_API_URL || 'http://localhost:8004';
        const response = await axios.get(`${apiUrl}/forecasts/homepage`, {
          timeout: 8000,
        });

        this.forecasts = response.data;
        this.lastUpdated = new Date().toLocaleTimeString();
      } catch (err) {
        console.error('Failed to fetch forecasts:', err);

        // Show more specific error messages to help diagnose issues
        if (err.response) {
          this.error = `Server error ${err.response.status}: ${err.response.data?.detail || 'Unknown error'}`;
        } else if (err.code === 'ECONNABORTED') {
          this.error = 'Request timed out. The pipeline server may be unavailable.';
        } else {
          this.error = 'Unable to load forecasts. Please try again later.';
        }
      } finally {
        this.loading = false;
      }
    },

    // ── Safe formatting helpers ──────────────────────────────────────────────

    safePrice(value) {
      if (value == null || isNaN(value)) return '—';
      return Number(value).toFixed(2);
    },

    safePercent(value) {
      if (value == null || isNaN(value)) return '0%';
      return `${Math.round(value * 100)}%`;
    },

    safeConfidenceLabel(value) {
      if (value == null || isNaN(value)) return '—';
      return `${Math.round(value * 100)}%`;
    },

    // ── Trend helpers ────────────────────────────────────────────────────────

    getTrendClass(forecast) {
      const change = this._priceChange(forecast);
      if (change === null) return 'trend-neutral';
      if (change > 2) return 'trend-up';
      if (change < -2) return 'trend-down';
      return 'trend-neutral';
    },

    getTrendText(forecast) {
      const change = this._priceChange(forecast);
      if (change === null) return '➡️ Stable';
      if (change > 2) return `📈 Rising ${change.toFixed(1)}%`;
      if (change < -2) return `📉 Falling ${Math.abs(change).toFixed(1)}%`;
      return '➡️ Stable';
    },

    _priceChange(forecast) {
      const nextPrice = forecast.next_day?.price;
      const weekPrice = forecast.week_ahead?.price;
      if (nextPrice == null || weekPrice == null || nextPrice === 0) return null;
      return ((weekPrice - nextPrice) / nextPrice) * 100;
    },
  },
};
</script>

<style scoped>
.forecast-widget {
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin: 20px 0;
}

.widget-title {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 20px;
  color: #2c3e50;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #7f8c8d;
}

.spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error {
  text-align: center;
  padding: 20px;
  color: #e74c3c;
  background: #ffebee;
  border-radius: 8px;
}

/* Empty state shown when DB has no future predictions */
.empty-state {
  text-align: center;
  padding: 32px;
  color: #7f8c8d;
  background: #f9f9f9;
  border-radius: 8px;
  font-size: 15px;
}

.forecasts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.forecast-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  padding: 20px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.forecast-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}

.commodity-name {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 4px;
}

.region {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 16px;
}

.forecast-item {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}

.forecast-item .label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 1px;
  opacity: 0.8;
  margin-bottom: 4px;
}

.forecast-item .price {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 8px;
}

.forecast-item .range {
  font-size: 13px;
  opacity: 0.9;
  margin-bottom: 8px;
}

.confidence {
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.confidence-bar {
  height: 4px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 2px;
  display: inline-block;
  transition: width 0.3s;
}

.trend {
  text-align: center;
  padding: 8px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: bold;
}

.trend-up {
  background: rgba(39, 174, 96, 0.3);
}

.trend-down {
  background: rgba(231, 76, 60, 0.3);
}

.trend-neutral {
  background: rgba(149, 165, 166, 0.3);
}

.widget-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #ecf0f1;
}

.widget-footer small {
  color: #7f8c8d;
}

.view-all-link {
  color: #3498db;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}

.view-all-link:hover {
  color: #2980b9;
}

/* Responsive */
@media (max-width: 768px) {
  .forecasts-grid {
    grid-template-columns: 1fr;
  }

  .widget-footer {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }
}
</style>