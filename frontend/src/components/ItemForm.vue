<template>
  <div class="container my-5">
    <h1 class="text-center mb-4 graintrade-title">{{ $t('create_form.form_title') }}</h1>

    <div class="row">
      <div class="col-lg-6 mb-4">
        <div class="card h-100 graintrade-card">
          <div class="card-header text-center">
            <h2 class="mb-0">{{ $t('create_form.map_title') }}</h2>
          </div>
          <div class="card-body">
            <div id="map" class="map mb-3"></div>
          </div>
        </div>
      </div>

      <div class="col-lg-6 mb-4">
        <div class="card h-100 graintrade-card">
          <div class="card-header text-center">
            <h2 class="mb-0">{{ $t('create_form.form_title') }}</h2>
          </div>
          <div class="card-body">
            <form @submit.prevent="createItem">
              <div class="mb-3">
                <label for="offer_type" class="form-label">{{ $t('create_form.offer_type') }}</label>
                <select class="form-select" id="offer_type" v-model="offer_type" required>
                  <option value="sell">{{ $t('create_form.sell') }}</option>
                  <option value="buy">{{ $t('create_form.buy') }}</option>
                </select>
              </div>

              <div class="mb-3">
                <label for="category_id" class="form-label">{{ $t('create_form.category') }}</label>
                <select class="form-select" id="category_id" v-model="category_id" required>
                  <option v-for="category in categories" :key="category.id" :value="category.id">
                    {{ getCategoryName(category) }}
                  </option>
                </select>
              </div>

              <div class="mb-3">
                <label for="title" class="form-label">{{ $t('common_text.title') }}</label>
                <input type="text" class="form-control" id="title" v-model="title" readonly required>
              </div>

              <div class="mb-3">
                <label for="description" class="form-label">{{ $t('common_text.description') }}</label>
                <textarea
                  type="text"
                  maxlength="300"
                  rows="4"
                  class="form-control"
                  id="description"
                  v-model="description"
                  :placeholder="$t('create_form.description_placeholder')"
                  @input="validateDescription"
                ></textarea>
                <div v-if="descriptionError" class="text-danger mt-1">{{descriptionError}}</div>
              </div>

              <div class="row mb-3">
                <div class="col-md-6">
                  <label for="price" class="form-label">{{ $t('common_text.price') }}</label>
                  <input type="number" class="form-control" id="price" v-model="price" step="0.01" required>
                </div>
                <div class="col-md-6">
                  <label for="currency" class="form-label">{{ $t('common_text.currency') }}</label>
                  <select class="form-select" id="currency" v-model="currency" required>
                    <option value="UAH">UAH</option>
                    <option value="EUR">EUR</option>
                    <option value="USD">USD</option>
                  </select>
                </div>
              </div>

              <div class="row mb-3">
                <div class="col-md-6">
                  <label for="amount" class="form-label">{{ $t('create_form.amount') }}</label>
                  <input type="number" class="form-control" id="amount" v-model="amount" required>
                </div>
                <div class="col-md-6">
                  <label for="measure" class="form-label">{{ $t('create_form.measure') }}</label>
                  <select class="form-select" id="measure" v-model="measure" required>
                    <option value="metric ton">{{ $t('create_form.metric_ton') }}</option>
                    <option value="kg">{{ $t('create_form.kg') }}</option>
                    <option value="liter">{{ $t('create_form.liter') }}</option>
                  </select>
                </div>
              </div>

              <div class="mb-3">
                <label for="terms_delivery" class="form-label">{{ $t('create_form.terms_delivery') }}</label>
                <select class="form-select" id="terms_delivery" v-model="terms_delivery" required>
                  <option v-for="term in incoterms" :key="term.abbreviation" :value="term.abbreviation">
                    {{ term.abbreviation }} - {{ term.description }}
                  </option>
                </select>
              </div>

              <div class="row mb-3">
                <div class="col-md-6">
                  <label for="country" class="form-label">{{ $t('create_form.country') }}</label>
                  <input
                    type="text"
                    class="form-control"
                    id="country"
                    v-model="country"
                    readonly
                    :placeholder="$t('create_form.country_placeholder')"
                  />
                </div>
                <div class="col-md-6">
                  <label for="region" class="form-label">{{ $t('create_form.region') }}</label>
                  <input
                    type="text"
                    class="form-control"
                    id="region"
                    v-model="region"
                    readonly
                    :placeholder="$t('create_form.country_placeholder')"
                  />
                </div>
              </div>

              <div class="row mb-4">
                <div class="col-md-6">
                  <label for="latitude" class="form-label">{{ $t('create_form.latitude') }}</label>
                  <input type="text" class="form-control" id="latitude" v-model="latitude" readonly :placeholder="$t('create_form.latitude_placeholder')" />
                </div>
                <div class="col-md-6">
                  <label for="longitude" class="form-label">{{ $t('create_form.longitude') }}</label>
                  <input type="text" class="form-control" id="longitude" v-model="longitude" readonly :placeholder="$t('create_form.latitude_placeholder')" />
                </div>
              </div>

              <div class="d-grid gap-2 mb-4">
                <button type="submit" class="btn btn-primary btn-lg graintrade-btn-primary">
                  {{ $t('create_form.submit') }}
                </button>
              </div>

              <div v-if="successMessage" class="alert alert-success graintrade-alert-success" role="alert">
                <i class="fas fa-check-circle me-2"></i>{{ successMessage }}
              </div>
              <div v-if="errorMessage" class="alert alert-danger graintrade-alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>{{ errorMessage }}
              </div>

            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// ... (your existing script content, just ensure the 'measure' list includes kg and liter)
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import MapboxGeocoder from '@mapbox/mapbox-gl-geocoder';
import '@mapbox/mapbox-gl-geocoder/dist/mapbox-gl-geocoder.css';
import axios from 'axios';
import { mapState } from 'vuex';

export default {
  data() {
    return {
      category_id: null,
      categories: [],
      title: '', // Initialize as empty, it will be computed
      description: '',
      price: 0,
      currency: 'UAH',
      amount: 0,
      measure: 'metric ton',
      terms_delivery: 'EXW',
      offer_type: 'sell',
      country: '',
      region: '',
      latitude: null,
      longitude: null,
      map: null,
      marker: null,
      successMessage: '',
      errorMessage: '',
      descriptionError: '',
    };
  },
  computed: {
    ...mapState(['user', 'currentLocale']), // Ensure currentLocale is mapped
    computedTitle() {
      const category = this.categories.find(c => c.id === this.category_id);
      const offerType = this.offer_type === 'sell' ? this.$t('create_form.sell') : this.$t('create_form.buy');
      return this.offer_type && category ? `${offerType} ${this.getCategoryName(category)}` : '';
    },
    incoterms() {
      return [
        { abbreviation: 'EXW', description: this.$t('incoterms.EXW') },
        { abbreviation: 'FCA', description: this.$t('incoterms.FCA') },
        { abbreviation: 'CPT', description: this.$t('incoterms.CPT') },
        { abbreviation: 'CIP', description: this.$t('incoterms.CIP') },
        { abbreviation: 'DAP', description: this.$t('incoterms.DAP') },
        { abbreviation: 'DPU', description: this.$t('incoterms.DPU') },
        { abbreviation: 'DDP', description: this.$t('incoterms.DDP') },
        { abbreviation: 'FAS', description: this.$t('incoterms.FAS') },
        { abbreviation: 'FOB', description: this.$t('incoterms.FOB') },
        { abbreviation: 'CFR', description: this.$t('incoterms.CFR') },
        { abbreviation: 'CIF', description: this.$t('incoterms.CIF') },
      ];
    },
  },
  watch: {
    computedTitle(newTitle) {
      this.title = newTitle;
    },
    offer_type() {
      this.title = this.computedTitle;
    },
    category_id() {
      this.title = this.computedTitle;
    },
    currentLocale() { // Watch for locale changes to update title
      this.title = this.computedTitle;
    },
  },
  async mounted() {
    mapboxgl.accessToken = process.env.VUE_APP_MAPBOX_TOKEN;
    this.map = new mapboxgl.Map({
      container: 'map',
      style: 'mapbox://styles/mapbox/streets-v12',
      center: [31.946946, 49.305825],
      zoom: 5,
      maxZoom: 10,
      minZoom: 2,
    });
    this.map.addControl(new mapboxgl.NavigationControl());
    this.map.addControl(new mapboxgl.FullscreenControl());

    const geocoder = new MapboxGeocoder({
      accessToken: mapboxgl.accessToken,
      mapboxgl: mapboxgl,
    });

    // Add the geocoder control to the map.
    this.map.addControl(geocoder);

    geocoder.on('result', (e) => {
      const { center, context } = e.result;
      this.latitude = center[1];
      this.longitude = center[0];

      const countryContext = context.find(c => c.id.startsWith('country'));
      const regionContext = context.find(c => c.id.startsWith('region'));

      this.country = countryContext ? countryContext.text : '';
      this.region = regionContext ? regionContext.text : '';

      if (this.marker) {
        this.marker.setLngLat(center);
      } else {
        this.marker = new mapboxgl.Marker().setLngLat(center).addTo(this.map);
      }

      // Center the map on the selected location.
      this.map.flyTo({ center, zoom: 10 });
    });

    this.map.on('click', async (e) => {
      const { lng, lat } = e.lngLat;
      this.latitude = lat;
      this.longitude = lng;

      if (this.marker) {
        this.marker.setLngLat([lng, lat]);
      } else {
        this.marker = new mapboxgl.Marker().setLngLat([lng, lat]).addTo(this.map);
      }

      // Center the map on the clicked location.
      this.map.flyTo({ center: [lng, lat], zoom: 10 });

      // Reverse geocode to get the country and region
      try {
        const response = await axios.get(`https://api.mapbox.com/geocoding/v5/mapbox.places/${this.longitude},${this.latitude}.json?access_token=${process.env.VUE_APP_MAPBOX_TOKEN}`);
        const context = response.data.features[0].context;
        const countryContext = context.find(c => c.id.startsWith('country'));
        const regionContext = context.find(c => c.id.startsWith('region'));

        this.country = countryContext ? countryContext.text : '';
        this.region = regionContext ? regionContext.text : '';
      } catch (error) {
        console.error('Error reverse geocoding:', error);
      }
    });

      // Fetch categories from the backend.
    try {
      const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/categories`);
      this.categories = response.data;
    } catch (error) {
      console.error('Error fetching categories:', error);
    }

    window.addEventListener('resize', () => {
      this.map.resize();
    });
  },
  methods: {
    validateDescription() {
      // Simple frontend check for common script patterns
      const scriptPattern = /<script\b[^>]*>(.*?)<\/script>|<img\b[^>]*onerror\b[^>]*>/i;
        if (scriptPattern.test(this.description)) {
          this.descriptionError = this.$t('create_form.validation_xss_description');
        } else { this.descriptionError = '';}
    },
    getCategoryName(category) {
      return this.$store.state.currentLocale === 'ua' ? category.ua_name : category.name;
    },
    async createItem() {
      this.successMessage = '';
      this.errorMessage = '';
      // Prevent submission if there's a frontend validation error
      if (this.descriptionError) {
        this.errorMessage = this.$t('create_form.error_validation_failed');
        return;
      }
      // Check the user is authenticated
      if (!this.$store.state.isAuthenticated) {
        this.errorMessage = this.$t('create_form.error_not_authenticated');
        return;
      }
      try {
        const response = await axios.post(`${process.env.VUE_APP_BACKEND_URL}/items`, {
          user_id: this.user.id,
          category_id: this.category_id,
          offer_type: this.offer_type,
          title: this.title,
          description: this.description,
          price: this.price,
          currency: this.currency,
          amount: this.amount,
          measure: this.measure,
          terms_delivery: this.terms_delivery,
          country: this.country,
          region: this.region,
          latitude: this.latitude,
          longitude: this.longitude,
        }, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
        console.log('Item created:', response.status);
        this.successMessage = 'Offer created successfully!';
      } catch (error) {
        console.error(error.response.status, "<- response.status")
        if (error.response) {
          if (error.response.status === 401) {
            this.errorMessage = this.$t('create_form.error_401');
          } else if (error.response.status === 403) {
            this.errorMessage = this.$t('create_form.error_403');
          } else if (error.response.status === 400) {
            this.errorMessage = this.$t('create_form.error_400');
          } else {
            this.errorMessage = this.$t('create_form.error_message');
          }
        }
        console.error('Error creating offer:', error);
      }
    }
  },
};
</script>

<style scoped>
/* GrainTrade ItemForm Styles */
.container {
  max-width: 1200px;
}

/* Map Styling */
.map {
  width: 100%;
  height: 400px;
  border-radius: var(--graintrade-border-radius);
  border: 1px solid var(--graintrade-border);
  overflow: hidden;
}

/* Title Styling */
.graintrade-title {
  color: var(--graintrade-secondary);
  font-weight: 700;
  font-size: 2.5rem;
  margin-bottom: 2rem;
}

/* Card Enhancements */
.graintrade-card {
  border-radius: var(--graintrade-border-radius-large);
  border: none;
  box-shadow: var(--graintrade-shadow);
  transition: var(--graintrade-transition);
  background: var(--graintrade-bg);
}

.graintrade-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--graintrade-shadow-hover);
}

.graintrade-card .card-header {
  background: var(--graintrade-bg-alt);
  border-bottom: 1px solid var(--graintrade-border);
  border-radius: var(--graintrade-border-radius-large) var(--graintrade-border-radius-large) 0 0 !important;
  font-weight: 600;
  color: var(--graintrade-secondary);
  padding: 1.25rem 1.5rem;
}

.graintrade-card .card-body {
  padding: 2rem;
}

/* Form Elements */
.form-label {
  font-weight: 600;
  color: var(--graintrade-secondary);
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
}

.form-control,
.form-select {
  border-radius: var(--graintrade-border-radius);
  border: 1px solid var(--graintrade-border);
  font-family: var(--graintrade-font-family);
  transition: var(--graintrade-transition);
  background-color: var(--graintrade-bg-light);
  padding: 0.75rem 1rem;
  font-size: 0.95rem;
}

.form-control:focus,
.form-select:focus {
  border-color: var(--graintrade-primary);
  box-shadow: 0 0 0 0.2rem rgba(39, 174, 96, 0.25);
  outline: none;
}

.form-control:read-only {
  background-color: var(--graintrade-bg-alt);
  color: var(--graintrade-text-muted);
}

/* Button Styling */
.graintrade-btn-primary {
  background: var(--graintrade-primary) !important;
  border-color: var(--graintrade-primary) !important;
  color: white !important;
  font-weight: 600;
  padding: 0.875rem 2rem;
  border-radius: var(--graintrade-border-radius);
  transition: var(--graintrade-transition);
  font-size: 1.1rem;
  box-shadow: 0 4px 8px rgba(39, 174, 96, 0.2);
}

.graintrade-btn-primary:hover,
.graintrade-btn-primary:focus,
.graintrade-btn-primary:active {
  background: var(--graintrade-primary-dark) !important;
  border-color: var(--graintrade-primary-dark) !important;
  color: white !important;
  transform: translateY(-1px);
  box-shadow: 0 6px 12px rgba(39, 174, 96, 0.3);
}

/* Alert Styling */
.graintrade-alert-success {
  border: none;
  background: linear-gradient(135deg, rgba(39, 174, 96, 0.1), rgba(39, 174, 96, 0.05));
  color: var(--graintrade-primary-dark);
  border-radius: var(--graintrade-border-radius);
  border-left: 4px solid var(--graintrade-primary);
  font-weight: 500;
}

.graintrade-alert-danger {
  border: none;
  background: linear-gradient(135deg, rgba(231, 76, 60, 0.1), rgba(231, 76, 60, 0.05));
  color: var(--graintrade-accent);
  border-radius: var(--graintrade-border-radius);
  border-left: 4px solid var(--graintrade-accent);
  font-weight: 500;
}

/* Validation Error Text */
.text-danger {
  color: var(--graintrade-accent) !important;
  font-size: 0.875rem;
  font-weight: 500;
}

/* Responsive Adjustments */
@media (max-width: 768px) {
  .graintrade-title {
    font-size: 2rem;
  }
  
  .graintrade-card .card-body {
    padding: 1.5rem;
  }
  
  .map {
    height: 300px;
  }
}

@media (max-width: 576px) {
  .graintrade-title {
    font-size: 1.75rem;
  }
  
  .graintrade-card .card-body {
    padding: 1rem;
  }
  
  .graintrade-btn-primary {
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
  }
}
</style>
