<template>
  <div>
    <ItemTable :items="items" />
    <div class="pagination-controls" v-if="totalItems > pageSize">
      <button
        :disabled="page === 1"
        @click="handlePageChange(page -1)"
        class="btn btn-outline-primary btn-sm me-2 rounded-pill"
      >&lt; {{ $t('pagination.prev') }}</button>
      <span> {{ page }} / {{ Math.ceil(totalItems /pageSize) }}</span>
      <button
        :disabled="page * pageSize >= totalItems"
        @click="handlePageChange(page + 1)"
        class="btn btn-outline-primary btn-sm ms-2 rounded-pill"
      >{{ $t('pagination.next') }} &gt;</button>
    </div>

    <div class="container mt-5">
      <div v-if="!hasMapAccess" class="alert alert-info">
        {{ $t('map.registerToView') }}
        <router-link to="/register" class="btn btn-primary ml-3">{{ $t('navbar.register') }}</router-link>
      </div>
      <div v-else>
        <div class="mb-3">
          <button v-if="!showMap" @click="toggleMap" class="btn btn-primary">
            <i class="bi bi-map me-2"></i>{{ $t('homePage.showMapWithMarkers') }}
          </button>
          <button v-else @click="toggleMap" class="btn btn-secondary">
            <i class="bi bi-eye-slash me-2"></i>{{ $t('homePage.hideMap') }}
          </button>
        </div>

        <div class="map-container" v-if="showMap">
          <div class="map mt-5" id="mapContainer" ref="mapContainer"></div>
          <div class="map-legend" v-if="mapLoaded">
            <h6>{{ $t('map.clusterSizes') }}</h6>
            <div class="legend-item">
              <span class="circle small"></span> 1-3 {{ $t('map.items') }}
            </div>
            <div class="legend-item">
              <span class="circle medium"></span> 4-6 {{ $t('map.items') }}
            </div>
            <div class="legend-item">
              <span class="circle large"></span> 6+ {{ $t('map.items') }}
            </div>
          </div>
        </div>
      </div>
    </div>
    <CategoryCards />
  </div>
</template>

<script>
import axios from 'axios';
import { mapState } from 'vuex';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import CategoryCards from './CategoryCards.vue';
import ItemTable from './ItemTable.vue';

export default {
  name: 'HomePage',
  components: {
    CategoryCards,
    ItemTable,
  },
  data() {
    return {
      items: [],
      timer: null,
      map: null,
      popup: null,
      mapLoaded: false,
      hasMapAccess: false,
      page: 1,
      pageSize: 10,
      totalItems: 0,
      showMap: false, // NEW: Control map visibility
      mapInitialized: false, // NEW: Track if map has been initialized
    };
  },
  computed: {
    ...mapState(['currentLocale']),
  },
  async created() {
    await this.fetchItems();
  },
  watch: {
    // Only update map source if map is already visible and initialized
    items() {
      if (this.map && this.map.getSource('items') && this.showMap) {
        const geoJsonData = this.getGeoJsonFromItems();
        this.map.getSource('items').setData(geoJsonData);
      }
    }
  },
  methods: {
    async fetchItems() {
      try {
        const offset = (this.page -1) * this.pageSize;
        const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/items`, {
          params: {
            offset: offset,
            limit: this.pageSize,
          },
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
        this.items = response.data.items;
        this.hasMapAccess = response.data.has_map_access;
        this.totalItems = response.data.total_items || (offset + this.items.length + (this.items.length === this.pageSize ? this.pageSize : 0));

        // NEW: Do NOT initialize map here. It's handled by toggleMap.
      } catch (error) {
        console.error('Failed to fetch items:', error);
      }
    },
    async handlePageChange(newPage) {
      this.page = newPage;
      await this.fetchItems();
      // If map is visible, re-center or refresh data after pagination
      if (this.showMap && this.mapInitialized) {
        // The watch handler for 'items' will update the source data automatically.
        // You might want to re-center the map if the new items are far from the current view.
        // For now, simply updating source data is sufficient.
      }
    },
    // NEW: Method to toggle map visibility and initialize
    async toggleMap() {
      this.showMap = !this.showMap;
      if (this.showMap && this.hasMapAccess && !this.mapInitialized) {
        // Ensure map container is rendered before initializing Mapbox
        await this.$nextTick();
        const isAllowed = await this.incrementCounter('map_views'); // Increment counter when map is first shown
        if (isAllowed) {
          this.initializeMap();
          this.mapInitialized = true; // Mark as initialized
        }
      } else if (!this.showMap && this.map) {
        // Optional: Remove map instance if hiding to free up resources
        this.map.remove();
        this.map = null;
        this.popup = null; // Clear popup reference
        this.mapInitialized = false; // Reset initialized state
        this.mapLoaded = false; // Reset mapLoaded state
      }
    },
    // NEW: Method to increment counters (copied from ItemDetails.vue)
    async incrementCounter(counterName) {
      try {
        const accessToken = localStorage.getItem('access_token');
        if (!accessToken) {
          console.error('No access token found. User not authenticated.');
          throw new Error('No access token');
        }

        const response = await axios.post(
          `${process.env.VUE_APP_BACKEND_URL}/mapbox/increment-counter?counter=${counterName}`,
          {}, // Empty request body
          {
            headers: {
              Authorization: `Bearer ${accessToken}`
            }
          }
        );

        if (response.data.status === 'success') {
          return true;
        } else if (response.data.status === 'denied') {
          alert(`${this.$t('profile.serviceLimitReached')}`)
          return false;
        }
      } catch (error) {
        console.error('Error sending signal to counters:', error.response ? error.response.data : error.message);
        if (error.response && error.response.status === 401) {
          alert('Your session has expired or you are not authorized. Please log in again.');
        } else if (error.response && error.response.status === 503) {
            alert(`Service unavailable: ${error.response.data.detail}`);
        }
      }
    },
    initializeMap() {
      if (!this.$refs.mapContainer) {
        console.error('Map container not found');
        return;
      }
      // If map already exists and is initialized, just update data if items changed.
      // The toggleMap logic should prevent this from being called if map is already running.
      if (this.map && this.mapInitialized) {
        const geoJsonData = this.getGeoJsonFromItems();
        this.map.getSource('items').setData(geoJsonData);
        return;
      }
      try {
        mapboxgl.accessToken = process.env.VUE_APP_MAPBOX_TOKEN;
        this.map = new mapboxgl.Map({
          container: this.$refs.mapContainer,
          style: 'mapbox://styles/mapbox/standard',
          config: {
            basemap: {
                theme: 'monochrome'
            },
          },
          center: [31.946946, 49.305825],
          zoom: 4,
          maxZoom: 12,
          minZoom: 2,
        });
        this.map.addControl(new mapboxgl.NavigationControl(), 'top-right');
        this.map.addControl(new mapboxgl.FullscreenControl(), 'top-right');
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
      const geoJsonData = this.getGeoJsonFromItems();
      this.map.addSource('items', {
        type: 'geojson',
        data: geoJsonData,
        cluster: true,
        clusterMaxZoom: 14, // Max zoom to cluster points on
        clusterMinPoints: 2, // Minimum number of points to form a cluster
        clusterRadius: 60
      });
    },
    addMapLayers() {
      if (!this.map) return;
      this.map.addLayer({
        id: 'clusters',
        type: 'circle',
        source: 'items',
        filter: ['has', 'point_count'],
        paint: {
          'circle-color': [
            'step',
            ['get', 'point_count'],
            '#51bbd6',
            4,
            '#f1f075',
            6,
            '#f28cb1'
          ],
          'circle-radius': [
            'step',
            ['get', 'point_count'],
            30, 4, 40, 6, 60
          ]
        }
      });
      this.map.addLayer({
        id: 'cluster-count',
        type: 'symbol',
        source: 'items',
        filter: ['has', 'point_count'],
        layout: {
          'text-field': ['get', 'point_count_abbreviated'],
          'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
          'text-size': 14
        }
      });
      this.map.addLayer({
        id: 'unclustered-point',
        type: 'circle',
        source: 'items',
        filter: ['!', ['has', 'point_count']],
        paint: {
          'circle-color': '#11b4da',
          'circle-radius': 8,
          'circle-stroke-width': 1,
          'circle-stroke-color': '#fff',
          'circle-emissive-strength': 0.5
        }
      });
    },
    addMapInteractions() {
      if (!this.map) return;
      this.map.on('mouseenter', 'clusters', () => {
        this.map.getCanvas().style.cursor = 'pointer';
      });
      this.map.on('mouseleave', 'clusters', () => {
        this.map.getCanvas().style.cursor = '';
      });
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
      this.map.on('mouseenter', 'unclustered-point', () => {
        this.map.getCanvas().style.cursor = 'pointer';
      });
      this.map.on('mouseleave', 'unclustered-point', () => {
        this.map.getCanvas().style.cursor = '';
      });
      this.map.on('click', 'unclustered-point', (e) => {
        const feature = e.features[0];
        const coordinates = feature.geometry.coordinates.slice();
        const item = feature.properties;
        if (this.popup) {
          this.popup.remove();
          this.popup = null;
        }
        const popupContent = this.getPopupHTML(item);
        this.popup = new mapboxgl.Popup({ closeOnClick: false })
          .setLngLat(coordinates)
          .setHTML(popupContent)
          .addTo(this.map);
        this.popup.on('open', () => {
          const popupButton = document.getElementById(`popup-view-details-${item.id}`);
          if (popupButton) {
            popupButton.addEventListener('click', (event) => {
              event.preventDefault();
              this.$router.push(`/items/${item.id}`);
            });
          } else {
            console.error('Popup button NOT found.');
          }
        });

        this.popup.on('close', () => {
          this.popup = null;
        });
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
            offer_type: item.offer_type,
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
            coordinates: [parseFloat(item.longitude), parseFloat(item.latitude)]
          }
        }))
      };
    },
    getPopupHTML(item) {
      let popupContent = `
        <div class="popup-content">
          <h5><span class="badge bg-info text-dark">${item.offer_type.toUpperCase()}</span> ${item.title || ''}</h5>
          <p>${item.description || ''}</p>
          <p><strong>${this.$t('common_text.price')}:</strong> ${item.price || 0} ${item.currency || ''}</p>
          <p><strong>${this.$t('common_text.amount')}:</strong> ${item.amount || 0} ${item.measure || ''}</p>
          <p><strong>${this.$t('common_text.incoterms')}:</strong> ${item.terms_delivery || ''} ${item.country || ''} ${item.region || ''}</p>
          <a
            href="/items/${item.id}"
            id="popup-view-details-${item.id}"
            class="btn btn-sm btn-primary"
            style="display: block; text-align: center; padding: 8px; margin-top: 10px; background: #007bff; color: white; text-decoration: none; border-radius: 4px;"
          >
            ${this.$t('common_text.viewDetails')}
          </a>
        </div>
      `;
      return popupContent;
    },
  },
  mounted() {
    this.fetchItems();
    this.timer = setInterval(this.fetchItems, 60000);
  },
  beforeUnmount() {
    clearInterval(this.timer);
    if (this.map) {
      this.map.off('mouseenter', 'clusters');
      this.map.off('mouseleave', 'clusters');
      this.map.off('click', 'unclustered-point');
      this.map.off('click', 'clusters');
      this.map.remove();
      this.map = null;
    }
  },
};
</script>

<style>
/* Pagination controls */
.pagination-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin: 20px 0;
}

.pagination-controls button {
  min-width: 80px;
  padding: 8px 18px;
  border-radius: var(--graintrade-border-radius-large);
  font-weight: 600;
  transition: var(--graintrade-transition);
}

.pagination-controls button:disabled {
  background: var(--graintrade-bg-alt);
  color: var(--graintrade-text-muted);
  border-color: var(--graintrade-border);
  cursor: not-allowed;
}

.pagination-controls button:not(:disabled):hover {
  transform: translateY(-1px);
}

.pagination-controls span {
  font-weight: 500;
  color: var(--graintrade-text-light);
}

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
  max-width: 300px;
  z-index: 1000;
}

.mapboxgl-popup-content {
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.mapboxgl-popup-close-button {
  right: 5px;
  top: 5px;
  font-size: 16px;
  color: #666;
}

.popup-content {
  padding: 2px;
flex: 1;
}

.popup-content h5 {
  margin-bottom: 5px;
  font-weight: bold;
  color: #333;
}

.popup-content p {
  margin: 6px 0;
  font-size: 0.9em;
  color: #666;
}

.popup-content .btn {
  margin-top: 12px;
  display: block;
  width: 100%;
  text-align: center;
}
</style>
