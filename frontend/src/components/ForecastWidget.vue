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
          <div class="price">${{ forecast.next_day.price.toFixed(2) }}</div>
          <div class="confidence">
            <span 
              class="confidence-bar" 
              :style="{ width: (forecast.next_day.confidence * 100) + '%' }"
            ></span>
            {{ (forecast.next_day.confidence * 100).toFixed(0) }}% confidence
          </div>
        </div>
        
        <!-- Week Ahead Forecast -->
        <div v-if="forecast.week_ahead" class="forecast-item week">
          <div class="label">Week Ahead</div>
          <div class="price">${{ forecast.week_ahead.price.toFixed(2) }}</div>
          <div class="range">
            Range: ${{ forecast.week_ahead.lower_bound.toFixed(2) }} - 
            ${{ forecast.week_ahead.upper_bound.toFixed(2) }}
          </div>
          <div class="confidence">
            <span 
              class="confidence-bar" 
              :style="{ width: (forecast.week_ahead.confidence * 100) + '%' }"
            ></span>
            {{ (forecast.week_ahead.confidence * 100).toFixed(0) }}% confidence
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
      <small>Updated: {{ lastUpdated }}</small>
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
        
        const apiUrl = process.env.VUE_APP_DATA_PIPELINE_URL || 'http://localhost:8004';
        const response = await axios.get(`${apiUrl}/forecasts/homepage`, {
          timeout: 5000,
        });
        
        this.forecasts = response.data;
        this.lastUpdated = new Date().toLocaleTimeString();
        this.loading = false;
        
      } catch (err) {
        console.error('Failed to fetch forecasts:', err);
        this.error = 'Unable to load forecasts. Please try again later.';
        this.loading = false;
      }
    },
    
    getTrendClass(forecast) {
      if (!forecast.next_day || !forecast.week_ahead) return 'neutral';
      
      const nextPrice = forecast.next_day.price;
      const weekPrice = forecast.week_ahead.price;
      const change = ((weekPrice - nextPrice) / nextPrice) * 100;
      
      if (change > 2) return 'trend-up';
      if (change < -2) return 'trend-down';
      return 'trend-neutral';
    },
    
    getTrendText(forecast) {
      if (!forecast.next_day || !forecast.week_ahead) return '';
      
      const nextPrice = forecast.next_day.price;
      const weekPrice = forecast.week_ahead.price;
      const change = ((weekPrice - nextPrice) / nextPrice) * 100;
      
      if (change > 2) return `📈 Rising ${change.toFixed(1)}%`;
      if (change < -2) return `📉 Falling ${Math.abs(change).toFixed(1)}%`;
      return '➡️ Stable';
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
