<template>
  <div class="container mt-5">
    <div class="row">
      <div class="col-md-6 item-details">
        <h3>{{ $t('itemDetails.title', { title: item.title }) }}</h3>
        <p><strong>ID:</strong> {{ item.uuid }}</p>
        <p><strong>{{ $t('common_text.type') }}:</strong> {{ $t(`offer_type.${item.offer_type}`) }}</p>
        <p><strong>{{ $t('common_text.description') }}:</strong> {{ item.description }}</p>
        <p><strong>{{ $t('common_text.price') }}:</strong> {{ item.price }} {{ item.currency }}</p>
        <p><strong>{{ $t('common_text.amount') }}:</strong> {{ item.amount }} {{ item.measure }}</p>
        <p><strong>{{ $t('common_text.incoterms') }}:</strong> {{ item.terms_delivery }} ({{ item.country }} {{ item.region }})</p>
        <p><strong>{{ $t('registration.username') }}:</strong> {{ item.owner_id }}</p>
        <!-- Show full map features for registered users -->
        <div v-if="!isAuthenticated">
          <p>{{ $t('itemDetails.locationInfo') }}</p>
          <a :href="googleMapsUrl" target="_blank" class="btn btn-outline-success" :disabled="!item.latitude || !item.longitude">
            {{ $t('itemDetails.viewOnGoogleMaps') }}
          </a>
          <div class="mt-3 alert alert-info">{{ $t('itemDetails.registerToAccessMap') }}</div>
        </div>
        <!-- Show full map features for registered users -->
        <div v-if="isAuthenticated">
          <div>
            <label for="searchLocation">{{ $t('itemDetails.enterLocation') }}</label>
            <input class="form-control" type="text" id="searchLocation" v-model="searchLocation" @change="geocodeLocation" :placeholder="$t('itemDetails.enterAddressOrCoordinates')">
          </div>
          <div>
            <label for="tariffRate">{{ $t('itemDetails.tariffRatePerKilometer') }}</label>
            <input class="form-control" type="number" id="tariffRate" v-model="tariffRate" @input="calculateTariff" :placeholder="$t('itemDetails.enterTariffRate')">
          </div>
          <div v-if="directions">
            <h4>{{ $t('itemDetails.directions') }}</h4>
            <p><strong>{{ $t('itemDetails.distance') }}:</strong> {{ (directions.distance / 1000).toFixed(2) }} {{ $t('itemDetails.kilometers') }}</p>
            <p><strong>{{ $t('itemDetails.duration') }}:</strong> {{ formatDuration(directions.duration) }}</p>
            <p><strong>{{ $t('itemDetails.tariff') }}:</strong> {{ tariff.toFixed(2) }}</p>
          </div>
        </div>
      </div>
      <div class="col-md-6" v-if="isAuthenticated">
        <div id="map" class="map"></div>
      </div>
    </div>
    <div v-if="isAuthenticated && item.uuid">
      <div v-if="isOwner">
        <OwnerChatSwitcher :itemId="item.uuid" :ownerId="currentUserId" />
      </div>
      <div v-else>
        <ItemChat :itemId="item.uuid" :userId="currentUserId" :otherUserId="otherUserId"/>
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
    console.log("Current User:", currUser);
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
      // If User authenticated then send request to Mapbox 
      if (this.isAuthenticated) { 
        this.$nextTick(() => {this.initializeMap();})
      }
    } catch (error) {
      console.error('Error fetching item details:', error);
    }
  },
  methods: {
    checkAuthentication() {
      const token = localStorage.getItem('access_token');
      this.isAuthenticated = !!token;
    },
    initializeMap() {
      mapboxgl.accessToken = process.env.VUE_APP_MAPBOX_TOKEN;
      this.map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/standard',
        config: {
          basemap: {
            theme: 'monochrome',
          }
        },
        center: [this.item.longitude, this.item.latitude],
        zoom: 5,
      });

      this.marker = new mapboxgl.Marker()
        .setLngLat([this.item.longitude, this.item.latitude])
        .addTo(this.map);

      const geocoder = new MapboxGeocoder({
        accessToken: mapboxgl.accessToken,
        mapboxgl: mapboxgl,
      });

      this.map.addControl(geocoder);

      geocoder.on('result', (e) => {
        const { center } = e.result;
        this.searchLocation = `${center[1]},${center[0]}`;
        this.calculateDirections(center);
      });
    },
    async geocodeLocation() {
      try {
        const response = await axios.get(`https://api.mapbox.com/geocoding/v5/mapbox.places/${this.searchLocation}.json?access_token=${process.env.VUE_APP_MAPBOX_TOKEN}`);
        const coordinates = response.data.features[0].geometry.coordinates;
        this.calculateDirections(coordinates);
      } catch (error) {
        console.error('Error geocoding location:', error);
      }
    },
    async calculateDirections(coordinates) {
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
              'line-color': '#3887be',
              'line-width': 5,
              'line-opacity': 0.75,
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
      return `${hours} hours ${minutes} minutes`;
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
      return `https://maps.google.com/maps/@${this.item.latitude},${this.item.longitude},14z`;
    }
  },
};
</script>

<style>
.item-details {
  border: 1px solid #ccc;
  padding: 20px;
  border-radius: 5px;
}

.map {
  border: 1px solid #ccc;
  padding: 20px;
  border-radius: 5px;
  width: 100%;
  height: 500px;
}

</style>
