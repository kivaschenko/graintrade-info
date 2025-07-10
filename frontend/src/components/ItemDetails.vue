<template>
  <div class="container my-5">
    <div class="row g-4">
      <div class="col-md-6">
        <div class="card item-details-card">
          <div class="card-body">
            <h3 class="card-title text-primary mb-4">{{ $t('itemDetails.title', { title: item.title }) }}</h3>
            <div class="detail-group">
              <p><strong>ID:</strong> <span class="text-muted">{{ item.uuid }}</span></p>
              <p><strong>{{ $t('common_text.type') }}:</strong> <span class="badge bg-secondary">{{ $t(`offer_type.${item.offer_type}`) }}</span></p>
              <p><strong>{{ $t('common_text.description') }}:</strong> {{ item.description }}</p>
              <p><strong>{{ $t('common_text.price') }}:</strong> <span class="text-success fs-5">{{ item.price }} {{ item.currency }}</span></p>
              <p><strong>{{ $t('common_text.amount') }}:</strong> {{ item.amount }} {{ item.measure }}</p>
              <p><strong>{{ $t('common_text.incoterms') }}:</strong> {{ item.terms_delivery }} ({{ item.country }} {{ item.region }})</p>
              <p><strong>{{ $t('registration.username') }}:</strong> <span class="text-info">{{ item.owner_id }}</span></p>
            </div>

            <div class="mt-4 pt-3 border-top">
              <div v-if="!isAuthenticated">
                <p class="text-info">{{ $t('itemDetails.locationInfo') }}</p>
                <a :href="googleMapsUrl" target="_blank" class="btn btn-outline-primary mb-3" :class="{ 'disabled': !item.latitude || !item.longitude }" :disabled="!item.latitude || !item.longitude">
                  <i class="bi bi-geo-alt-fill me-2"></i>{{ $t('itemDetails.viewOnGoogleMaps') }}
                </a>
                <div class="alert alert-warning text-center">
                  <i class="bi bi-info-circle me-2"></i>{{ $t('itemDetails.registerToAccessMap') }}
                </div>
              </div>
              <div v-else>
                <div class="mb-3">
                  <button v-if="!showMap" @click="toggleMap" class="btn btn-primary">
                    <i class="bi bi-map me-2"></i>{{ $t('itemDetails.showMapWithMarker') }}
                  </button>
                  <button v-else @click="toggleMap" class="btn btn-primary">
                    <i class="bi bi-map me-2"></i>{{ $t('itemDetails.hideMap') }}
                  </button>
                </div>
                <div class="mb-3" v-if="showMap">  
                  <label for="searchLocation" class="form-label">{{ $t('itemDetails.enterLocation') }}</label>
                  <input class="form-control" type="text" id="searchLocation" v-model="searchLocation" @change="geocodeLocation" :placeholder="$t('itemDetails.enterAddressOrCoordinates')">
                </div>
                <div class="mb-3" v-if="showMap">
                  <label for="tariffRate" class="form-label">{{ $t('itemDetails.tariffRatePerKilometer') }}</label>
                  <input class="form-control" type="number" id="tariffRate" v-model="tariffRate" @input="calculateTariff" :placeholder="$t('itemDetails.enterTariffRate')">
                </div>
                <div v-if="directions && showMap" class="directions-info p-3 mt-4 rounded">
                  <h5 class="text-primary mb-3">{{ $t('itemDetails.directions') }}</h5>
                  <p><strong>{{ $t('itemDetails.distance') }}:</strong> <span class="text-success">{{ (directions.distance / 1000).toFixed(2) }} {{ $t('itemDetails.kilometers') }}</span></p>
                  <p><strong>{{ $t('itemDetails.duration') }}:</strong> <span class="text-success">{{ formatDuration(directions.duration) }}</span></p>
                  <p><strong>{{ $t('itemDetails.tariff') }}:</strong> <span class="text-danger fs-5">{{ tariff.toFixed(2) }}</span></p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-md-6" v-if="isAuthenticated && showMap">
        <div class="card map-card">
          <div class="card-body p-0">
            <div id="map" class="map-instance"></div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="isAuthenticated && item.uuid" class="mt-5">
      <div class="card chat-card">
        <div class="card-body">
          <div v-if="isOwner">
            <h5>{{ $t('chat.chatsWithOtherUsers') }}</h5>
            <OwnerChatSwitcher :itemId="item.uuid" :ownerId="currentUserId" />
          </div>
          <div v-else>
            <h5>{{ $t('chat.chatWithOwnerOfItem') }}</h5>
            <ItemChat :itemId="item.uuid" :userId="currentUserId" :otherUserId="otherUserId"/>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import MapboxGeocoder from '@mapbox/mapbox-gl-geocoder';
import '@mapbox/mapbox-gl-geocoder/dist/mapbox-gl-geocoder.css';
import ItemChat from './ItemChat.vue';
import OwnerChatSwitcher from './OwnerChatSwitcher.vue';

export default {
  name: 'ItemDetails',
  components: {
    ItemChat,
    OwnerChatSwitcher,
  },
  data() {
    let currUser = localStorage.getItem('user');
    let currentUserId = null;
    if (currUser) {
      try {
        currUser = JSON.parse(currUser);
        currentUserId = currUser.username; // or currUser.id if you want numeric id
      } catch (e) {
        console.error('failed to parse user from localstorage:', e);
      }
    }
    return {
      item: {},
      searchLocation: '',
      directions: null,
      tariff: 0,
      tariffRate: 25.0, // Default tariff rate
      map: null,
      marker: null,
      currentUserId,
      ownerId: null,
      isAuthenticated: false, // Initialize isAuthenticated
      showMap: false,
      mapInitialized: false,
    };
  },
  watch: {
    tariffRate() {
      this.calculateTariff();
    },
  },
  async created() {
    this.checkAuthentication();
    try {
      const itemId = this.$route.params.id;
      const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/items/${itemId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      this.item = response.data;
      this.ownerId = response.data["owner_id"];
    } catch (error) {
      console.error('Error fetching item details:', error);
    }
  },
  methods: {
    checkAuthentication() {
      const token = localStorage.getItem('access_token');
      this.isAuthenticated = !!token;
    },
    // Toggle map visibility and initialize if not already
    async toggleMap() {
      this.showMap = !this.showMap;
      if (this.showMap && !this.mapInitialized && this.isAuthenticated) {
        // Ensure map container is rendered before initializing Mapbox
        await this.$nextTick();
        const isAllowed = await this.incrementCounter('map_views');
        if (isAllowed) {
          this.initializeMap();
          this.mapInitialized = true;  // Mark as initialized
        }
      } else if (!this.showMap && this.map) {
        // Optional: Remove map instance if hiding to free  up resources
        this.map.remove();
        this.map = null;
        this.marker = null;
        this.mapInitialized = false; // Reset initialized state
      }
    },
    async incrementCounter(counterName) {
      try {
        const accessToken = localStorage.getItem('access_token');
        if (!accessToken) {
          console.error('No access token found. User not authenticated.');
          // Optionally, throw an error or redirect to login
          throw new Error('No access token');
        }
        const response = await axios.post(
          `${process.env.VUE_APP_BACKEND_URL}/mapbox/increment-counter?counter=${counterName}`,
          {}, // <--- This is the empty request body
          {   // <--- This is the config object for headers
            headers: {
              Authorization: `Bearer ${accessToken}`
            }
          }
        );
        if (response.data.status === 'success') {
          console.log('Counter:', counterName, ' updated by value:', response.data.counter);
          // You might want to update your local usage state here
          // e.g., if you have userUsage data property
          // if (counterName === 'map_views') this.userUsage.map_views = response.data.counter;
          // ... similar for geo_search_count and navigation_count
          return true;
        } else if (response.data.status === 'denied') {
          console.log('Counter:', counterName, ' updated by value:', response.data.counter);
          alert(`${this.$t('profile.serviceLimitReached')}`)
          return false;
        }
      } catch (error) {
        console.error('Error sending signal to counters:', error.response ? error.response.data : error.message);
        // Handle specific errors like 401 Unauthorized or 403 Forbidden (if you implement limits)
        if (error.response && error.response.status === 401) {
          alert('Your session has expired or you are not authorized. Please log in again.');
          // Redirect to login page
        } else if (error.response && error.response.status === 503) { // As per your backend error
            alert(`Service unavailable: ${error.response.data.detail}`);
        }
      }
    },
    initializeMap() {
      // Prevent map re-initialization if already exists
      if (this.map) {
        return;
      }
      mapboxgl.accessToken = process.env.VUE_APP_MAPBOX_TOKEN;
      this.map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/streets-v12',
        center: [this.item.longitude, this.item.latitude],
        zoom: 5,
        maxZoom: 10,
        minZoom: 2,
      });
      this.map.on('load', () => {
        this.map.resize();
        this.map.setCenter([this.item.longitude, this.item.latitude]);
        this.map.setZoom(10);
      });
      this.map.addControl(new mapboxgl.NavigationControl(), 'bottom-right');
      this.map.addControl(new mapboxgl.FullscreenControl(), 'bottom-right');

      this.marker = new mapboxgl.Marker()
        .setLngLat([this.item.longitude, this.item.latitude])
        .addTo(this.map);

      const geocoder = new MapboxGeocoder({
        accessToken: mapboxgl.accessToken,
        mapboxgl: mapboxgl,
      });

      this.map.addControl(geocoder, 'top-left'); // Place geocoder at top-left for better visibility

      geocoder.on('result', (e) => {
        const { center } = e.result;
        this.searchLocation = `${center[1]},${center[0]}`;
        this.calculateDirections(center);
        this.incrementCounter('geo_search_count'); // Increment geo search counter on result
      });
    },
    async geocodeLocation() {
      const isAllowed = this.incrementCounter('geo_search_count'); // Increment geo search counter
      if (!isAllowed) {return;} // Dont allow if limit reached
      try {
        const response = await axios.get(`https://api.mapbox.com/geocoding/v5/mapbox.places/${this.searchLocation}.json?access_token=${process.env.VUE_APP_MAPBOX_TOKEN}`);
        const coordinates = response.data.features[0].geometry.coordinates;
        this.calculateDirections(coordinates);
      } catch (error) {
        console.error('Error geocoding location:', error);
      }
    },
    async calculateDirections(coordinates) {
      const isAllowed = this.incrementCounter('navigation_count'); // Increment navigation counter
      if (!isAllowed) {return;} // Dont allow if limit reached
      try {
        const response = await axios.get(`https://api.mapbox.com/directions/v5/mapbox/driving/${coordinates[0]},${coordinates[1]};${this.item.longitude},${this.item.latitude}?alternatives=true&geometries=geojson&language=en&overview=full&steps=true&access_token=${process.env.VUE_APP_MAPBOX_TOKEN}`);
        const route = response.data.routes[0];
        this.directions = {
          distance: route.distance,
          duration: route.duration,
        };

        this.calculateTariff();

        if (this.map.getSource('route')) {
          this.map.getSource('route').setData(route.geometry);
        } else {
          this.map.addLayer({
            id: 'route',
            type: 'line',
            source: {
              type: 'geojson',
              data: route.geometry,
            },
            layout: {
              'line-join': 'round',
              'line-cap': 'round',
            },
            paint: {
              'line-color': '#007bff', // Bootstrap primary color
              'line-width': 6,
              'line-opacity': 0.8,
            },
          });
        }
      } catch (error) {
        console.error('Error calculating directions:', error);
      }
    },
    calculateTariff() {
      if (this.directions) {
        this.tariff = (this.directions.distance / 1000) * this.tariffRate;
      }
    },
    formatDuration(duration) {
      const hours = Math.floor(duration / 3600);
      const minutes = Math.floor((duration % 3600) / 60);
      return `${hours} ${this.$t('itemDetails.hours')} ${minutes} ${this.$t('itemDetails.minutes')}`;
    },
  },
  computed: {
    isOwner() {
      return this.currentUserId && this.item && this.currentUserId === this.item.owner_id;
    },
    otherUserId() {
      if (this.currentUserId !== this.item.owner_id) {return this.item.owner_id} else return null;
    },
    googleMapsUrl() {
      if (!this.item.latitude || !this.item.longitude) return '#';
      return `https://www.google.com/maps/search/?api=1&query=${this.item.latitude},${this.item.longitude}`; // Corrected Google Maps URL
    }
  },
  beforeUnmount() {
    if (this.map) {
      this.map.remove();
    }
  }
};
</script>

<style>
/* General Page Styling */
body {
  background-color: #f8f9fa; /* Light background for the whole page */
}

.container {
  max-width: 1200px; /* Limit container width for better readability */
}

/* Card Styles */
.card {
  border: none;
  border-radius: 0.75rem; /* More pronounced rounded corners */
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08); /* Soft shadow for depth */
  transition: transform 0.2s ease-in-out; /* Slight hover effect */
}

.card:hover {
  transform: translateY(-3px);
}

.item-details-card .card-body {
  padding: 2rem; /* Increased padding */
}

.map-card {
  height: 500px; /* Fixed height for the map card */
}

.map-card .card-body {
  padding: 0; /* Remove padding for map to fill the card */
}

.chat-card {
  margin-top: 2.5rem; /* Space above chat card */
}

.chat-card .card-body {
  padding: 2rem;
}

/* Item Details Specifics */
.item-details-card h3 {
  font-weight: 700;
  color: #007bff; /* Primary brand color */
  margin-bottom: 1.5rem;
  font-size: 2.25rem; /* Larger title */
}

.detail-group p {
  margin-bottom: 0.75rem; /* Spacing between detail lines */
  font-size: 1.05rem;
  color: #343a40; /* Darker text for details */
}

.detail-group strong {
  color: #495057; /* Slightly darker for labels */
  min-width: 120px; /* Align labels */
  display: inline-block;
}

.detail-group p span {
  font-weight: 500;
}

.text-success.fs-5 {
  font-weight: 600;
  color: #28a745 !important; /* Ensure strong green for price */
}

.badge {
  font-size: 0.85rem;
  padding: 0.5em 0.8em;
  border-radius: 0.5rem;
  font-weight: 600;
}

/* Inputs and Forms */
.form-label {
  font-weight: 600;
  color: #495057;
  margin-bottom: 0.5rem;
}

.form-control {
  border-radius: 0.5rem;
  padding: 0.75rem 1rem;
  border: 1px solid #ced4da;
  transition: border-color 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
}

.form-control:focus {
  border-color: #80bdff;
  box-shadow: 0 0 0 0.25rem rgba(0, 123, 255, 0.25);
  outline: none;
}

/* Buttons */
.btn-outline-primary {
  border-color: #007bff;
  color: #007bff;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 600;
  transition: all 0.2s ease-in-out;
}

.btn-outline-primary:hover:not(.disabled) {
  background-color: #007bff;
  color: #fff;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 123, 255, 0.2);
}

.btn-outline-primary.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Alerts */
.alert-warning {
  background-color: #fff3cd;
  border-color: #ffeeba;
  color: #856404;
  border-radius: 0.5rem;
  padding: 1rem 1.25rem;
  font-size: 0.95rem;
}

.alert-warning .bi {
  vertical-align: middle;
  font-size: 1.2rem;
}

/* Directions Info Box */
.directions-info {
  background-color: #e9f7ff; /* Light blue background */
  border: 1px solid #cceeff;
  border-radius: 0.75rem;
  box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
}

.directions-info h5 {
  color: #0056b3; /* Darker blue for heading */
  font-weight: 700;
  border-bottom: 1px dashed #cceeff;
  padding-bottom: 0.75rem;
}

.directions-info p {
  margin-bottom: 0.5rem;
  font-size: 1.05rem;
}

.directions-info p strong {
  min-width: 90px;
  display: inline-block;
  color: #495057;
}

.directions-info .text-danger {
  font-weight: 700;
  color: #dc3545 !important;
}

/* Mapbox specific styles */
.map-instance {
  height: 100%; /* Make map fill its container */
  width: 100%;
  border-radius: 0 0 0.75rem 0.75rem; /* Match card radius, or fill entirely */
}

/* Adjust Mapbox controls positioning if necessary */
.mapboxgl-ctrl-bottom-right,
.mapboxgl-ctrl-top-left {
  margin: 15px; /* Add some margin around controls */
}

/* Ensure map container has no padding for the map instance to fill it */
#map {
  padding: 0;
  border: none; /* Remove default border from map ID */
  border-radius: 0.75rem;
  overflow: hidden; /* Ensure rounded corners clip map content */
}
</style>
