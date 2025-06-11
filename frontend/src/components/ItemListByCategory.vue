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
    <!-- Map section with access control -->
    <div class="container mt-5">
      <div v-if="!hasMapAccess" class="alert alert-info">
        {{ $t('map.registerToView') }}
        <router-link to="/register" class="btn btn-primary ml-3">{{ $t('navbar.register') }}</router-link>
      </div>
      <div v-else>
        <div class="map-container">
          <div class="map mt-5" id="mapContainer" ref="mapContainer"></div>
          <div class="maplegend" v-if="mapLoaded">
            <h6>{{ $t('map.clusterSize') }}</h6>
            <div class="legend-item">
              <span class="circle small"></span> 1-10 {{ $t('map.items') }}
            </div>
            <div class="legend-item">
              <span class="circle medium"> 11-50 {{ $t('map.items') }}</span>
            </div>
            <div class="legend-item">
              <span class="circle large"> 50+ {{ $t('map.items') }}</span>
            </div>
          </div>
        </div>
      </div>
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
      mapLoaded: false,
      hasMapAccess: false,
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
          limit: 100,
        },
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      this.items = response.data.items;
      this.category = response.data.category;
      this.hasMapAccess = response.data.has_map_access;
      if (this.hasMapAccess) {
        this.$nextTick(() => {this.initializeMap();})
      }
    } catch (error) {
      console.error('Error fetching items:', error);
    }
  },
  methods: {
    initializeMap() {
      if (!this.$refs.mapContainer) {
        console.error('Map container not found');
        return;
      }
      try {
        console.log('Initializing map with items:', this.items);
        mapboxgl.accessToken = process.env.VUE_APP_MAPBOX_TOKEN;
        this.map = new mapboxgl.Map({
          container: this.$refs.mapContainer,
          style: 'mapbox://styles/mapbox/light-v11',
          center: [31.946946, 49.305825],
          zoom: 5,
        });
        // Wait for map to load before adding sources and layers
        this.map.on('load', () => {
          this.mapLoaded = true;
          this.addMapSources();
          this.addMapLayers();
          this.addMapInteractions();
        });

      } catch (error) {
        console.error('Error initializing map:', error);
      }
    },
    addMapSources() {
      if (!this.map) return;
      // Add a new source from our GeoJSON data
        this.map.addSource('items', {
          type: 'geojson',
          data: this.getGeoJsonFromItems(),
          cluster: true,
          clusterMaxZoom: 14,
          clasterRadius: 50
        });
    },
    addMapLayers() {
      if (!this.map) return;
      // Add cluster circles
      this.map.addLayer({
        id: 'clusters',
        type: 'circle',
        source: 'items',
        filter: ['has', 'point_count'],
        paint: {
          'circle-color': [
            'step',
            ['get', 'point_count'],
            '#51bbd6',  // 0-9 items
            10,
            '#f1f075',  // 10-49 items
            50,
            '#f28cb1',  // 50+ items
          ],
          'circle-radius': [
            'step',
            ['get', 'point_count'],
            20,  // 0-9 items
            10,
            30,  // 10-49 items
            50,
            40  // 50+ items
          ]
        }
      });
      // Add cluster count numbers
      this.map.addLayer({
        id: 'cluster-count',
        type: 'symbol',
        source: 'items',
        filter: ['has', 'point_count'],
        layout: {
          'text-field': '{point_count_abbreviated}',
          'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
          'text-size': 12
        }
      });
      // Add unclustered point circles
      this.map.addLayer({
        id: 'unclustered-point',
        type: 'circle',
        source: 'items',
        filter: ['!', ['has', 'point_count']],
        paint: {
          'circle-color': '#11b4da',
          'circle-radius': 8,
          'circle-stroke-width': 1,
          'circle-stroke-color': '#fff'
        }
      });
    },
    addMapInteractions() {
      if (!this.map) return;

      // Handle clicks on individual points
      this.map.on('click', 'unclustered-point', (e) => {
        if (!e.features || !e.features[0]) return;

        const coordinates = e.features[0].geometry.coordinates.slice();
        const item = e.features[0].properties;
        // Ensure coordinates are valid
        if (!coordinates || coordinates.length !== 2) return;

        // Fix for when the map is zoomed in a lot
        while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
          coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
        }
        // Create popup
        new mapboxgl.Popup()
          .setLngLat(coordinates)
          .setHTML(this.getPopupHTML(item))
          .addTo(this.map);
      });

      // Handle clicks on clusters
      this.map.on('click', 'clusters', (e) => {
        const features = this.map.queryRenderedFeatures(e.point, {
          layers: ['clusters']
        });
        const clusterId = features[0].properties.cluster_id;
        this.map.getSource('items').getClusterExpansionZoom(
          clusterId,
          (err, zoom) => {
            if (err) return;

            this.map.easeTo({
              center: features[0].geometry.coordinates,
              zoom: zoom
            });
          }
        );
      });

      // Add cursor style for unclustered points
      this.map.on('mouseenter', 'unclustered-point', () => {
        this.map.getCanvas().style.cursor = 'pointer';
      });

      this.map.on('mouseleave', 'unclustered-point', () => {
        this.map.getCanvas().style.cursor = '';
      });

      // Change cursor on hover
      this.map.on('mouseenter', 'clusters', () => {
        this.map.getCanvas().style.cursor = 'pointer';
      });
      this.map.on('mouseleave', 'clusters', () => {
        this.map.getCanvas().style.cursor = '';
      });
    },
    getGeoJsonFromItems() {
      return {
        type: 'FeatureCollection',
        features: this.items.map(item => ({
          type: 'Feature',
          properties: {
            id: item.id,
            title: item.title,
            description: item.description,
            price: item.price,
            currency: item.currency,
            amount: item.amount,
            measure: item.measure,
            terms_delivery: item.terms_delivery,
            country: item.country,
            region: item.region
          },
          geometry: {
            type: 'Point',
            coordinates: [item.longitude, item.latitude]
          }
        }))
      };
    },
    getPopupHTML(item) {
      // Get translations first to avoid undefined this.$t in template string
      const translations = {
        price: this.$t('common.price'),
        amount: this.$t('common.amount'),
        incoterms: this.$t('common.incoterms'),
        viewDetails: this.$t('common.viewDetails')
      };

      return `
        <div class="popup-content">
          <h5>${item.title || ''}</h5>
          <p>${item.description || ''}</p>
          <p>${translations.price}: ${item.price || 0} ${item.currency || ''}</p>
          <p>${translations.amount}: ${item.amount || 0} ${item.measure || ''}</p>
          <p>${translations.incoterms}: ${item.terms_delivery || ''}</p>
          <p>${item.country || ''} ${item.region || ''}</p>
          <a href="/items/${item.id}" class="btn btn-sm btn-primary">
            ${translations.viewDetails}
          </a>
        </div>
      `;
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
.map-container {
  position: relative;
}

.map {
  width: 100%;
  height: 400px;
}

.map-legend {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background: white;
  padding: 10px;
  border-radius: 4px;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

.legend-item {
  margin: 5px 0;
  display: flex;
  align-items: center;
}

.circle.small { background-color: #51bbd6; }
.circle.medium { background-color: #f1f075; }
.circle.large { background-color: #f28cb1; }

.mapboxgl-popup {
  max-width: 400px;
}

.mapboxgl-popup-content {
  padding: 15px;
}

.popup-content {
  padding: 10px;
  max-width: 300px;
}

.popup-content h5 {
  margin-bottom: 8px;
  font-weight: bold;
  color: #333;
}

.popup-content p {
  margin: 4px;
  font-size: 0.9em;
}
</style>