<template>
  <div class="container my-5">
    <h1 class="text-center mb-4">{{ $t('create_form.form_title') }}</h1>

    <div class="row">
      <div class="col-lg-6 mb-4">
        <div class="card h-100 shadow-sm">
          <div class="card-body">
            <h2 class="card-title text-center mb-3">{{ $t('create_form.map_title') }}</h2>
            <div id="map" class="map mb-3 border rounded"></div>
          </div>
        </div>
      </div>

      <div class="col-lg-6 mb-4">
        <div class="card h-100 shadow-sm">
          <div class="card-body">
            <form @submit.prevent="createItem">
              <div v-if="successMessage" class="alert alert-success" role="alert">
                {{ successMessage }}
              </div>
              <div v-if="errorMessage" class="alert alert-danger" role="alert">
                {{ errorMessage }}
              </div>

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
                  maxlength="600"
                  rows="4"
                  class="form-control"
                  id="description"
                  v-model="description"
                  :placeholder="$t('create_form.description_placeholder')"
                ></textarea>
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

              <div class="d-grid gap-2">
                <button type="submit" class="btn btn-primary btn-lg">{{ $t('create_form.submit') }}</button>
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
      zoom: 6,
    });

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
      console.log("Categories response:", response);
      this.categories = response.data;
    } catch (error) {
      console.error('Error fetching categories:', error);
    }

    window.addEventListener('resize', () => {
      this.map.resize();
    });
  },
  methods: {
    getCategoryName(category) {
      return this.$store.state.currentLocale === 'ua' ? category.ua_name : category.name;
    },
    async createItem() {
      this.successMessage = '';
      this.errorMessage = '';
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
        console.log('Item created:', response.status, response.data);
        this.successMessage = 'Offer created successfully!';
      } catch (error) {
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
        } else {
          this.errorMessage = this.$t('create_form.error_message');
        }
        console.error('Error creating offer:', error);
      }
    },
  },
};
</script>

<style scoped> /* Added 'scoped' to prevent global style leakage */
.container {
  max-width: 1200px;
}

.map {
  width: 100%;
  height: 400px; /* Adjusted height for better visual balance */
}

.card {
  border: none;
  border-radius: 0.75rem; /* Slightly rounded corners for a softer look */
}

.card-body {
  padding: 2rem; /* More internal padding */
}

.form-label {
  font-weight: 600; /* Make labels a bit bolder */
  margin-bottom: 0.5rem; /* Add some space below labels */
  color: #343a40; /* Darker text for labels */
}

.form-control,
.form-select {
  border-radius: 0.35rem; /* Slightly rounded input fields */
  border-color: #ced4da; /* A standard border color */
}

.form-control:focus,
.form-select:focus {
  border-color: #80bdff; /* Bootstrap's default focus color */
  box-shadow: 0 0 0 0.25rem rgba(0, 123, 255, 0.25); /* Bootstrap's default focus shadow */
}

.btn-primary {
  background-color: #007bff; /* Bootstrap primary blue */
  border-color: #007bff;
  transition: background-color 0.2s ease-in-out, border-color 0.2s ease-in-out; /* Smooth transition on hover */
}

.btn-primary:hover {
  background-color: #0056b3; /* Darker blue on hover */
  border-color: #004085;
}

.alert {
  margin-bottom: 1.5rem; /* Space below alerts */
}

/* Specific styles for the form card background */
.col-lg-6 > .card:last-child { /* Targets the card containing the form */
  background-color: #f8f9fa; /* Light grey background for the form area */
}

.text-center {
  text-align: center;
}
</style>