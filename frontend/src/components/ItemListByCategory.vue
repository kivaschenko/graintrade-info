<template>
  <div>
    <div class="container mt-5">
      <div class="card" style="width: auto;">
        <div class="card-body">
          <h1 class="card-title">{{ getCategoryName(category) }}</h1>
          <p class="card-text">{{ getCategoryDescription(category) }}</p>
        </div>
      </div>
    </div>
    <ItemTable :items="items" />
    <div class="container mt-5">
      <div class="map mt-5" id="map" ref="map"></div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { mapState } from 'vuex';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import ItemTable from './ItemTable.vue';

export default {
  name: 'ItemListByCategory',
  components: {
    ItemTable,
  },
  data() {
    return {
      items: [],
      category: {},
      map: null,
      markers: [],
    };
  },
  computed: {
    ...mapState(['currentLocale']),
  },
  async created() {
    try {
      const category_id = this.$route.params.id;
      const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/categories/${category_id}/items`, {
        params: {
          offset: 0,
          limit: 10,
        },
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      this.items = response.data.items;
      this.category = {
        name: response.data.name,
        description: response.data.description,
        ua_name: response.data.ua_name,
        ua_description: response.data.ua_description,
      };
      this.initializeMap();
    } catch (error) {
      console.error('Error fetching items:', error);
    }
  },
  methods: {
    initializeMap() {
      console.log('Initializing map with items:', this.items);
      mapboxgl.accessToken = process.env.VUE_APP_MAPBOX_TOKEN;
      this.map = new mapboxgl.Map({
        container: this.$refs.map,
        style: 'mapbox://styles/mapbox/streets-v12',
        center: [31.946946, 49.305825],
        zoom: 5,
      });

      this.addMarkers(this.items);
    },
    addMarkers(items) {
      console.log('Adding markers for items:', items);
      this.clearMarkers();

      items.forEach(item => {
        console.log('Adding marker for item:', item);
        const marker = new mapboxgl.Marker()
          .setLngLat([item.longitude, item.latitude])
          .addTo(this.map);

        const popup = new mapboxgl.Popup({ offset: 25 })
          .setHTML(`
            <h5>${item.title}</h5>
            <p>${item.description}</p>
            <p>Price: ${item.price} ${item.currency}</p>
            <p>Amount: ${item.amount} ${item.measure}</p>
            <p>Incoterms: ${item.terms_delivery} (${item.country} ${item.region})</p>
          `);

        marker.setPopup(popup);
        this.markers.push(marker);
      });
    },
    clearMarkers() {
      this.markers.forEach(marker => marker.remove());
      this.markers = [];
    },
    // Translate Category
    getCategoryName(category) {
      const currentLocale = this.$store.state.currentLocale;
      console.log('currentLocale', currentLocale);
      return currentLocale === 'ua' ? category.ua_name : category.name;
    },
    getCategoryDescription(category) {
      const currentLocale = this.$store.state.currentLocale;
      return currentLocale === 'ua' ? category.ua_description : category.description;
    },
  },
};
</script>

<style>
.map {
  width: 100%;
  height: 400px;
}
</style>