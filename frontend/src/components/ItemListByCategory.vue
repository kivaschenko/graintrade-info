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
    <!-- ItemFilter component -->
    <ItemFilter :initialCategoryId="selectedCategory" @filters-changed="handleFiltersChanged" ref="ItemFilter" class="mt-4 mb-4" />
    <!-- ItemTable component -->
    <ItemTable :items="items" />
    <div class="pagination-controls" v-if="totalItems > pageSize">
      <button
        :disabled="page === 1"
        @click="handlePageChange(page -1)"
        class="btn btn-outline-secondary btn-sm"
      >&lt; Prev</button>
      <span> {{ page }} / {{ Math.ceil(totalItems /pageSize) }}</span>
      <button
        :disabled="page * pageSize >= totalItems"
        @click="handlePageChange(page + 1)"
        class="btn btn-outline-secondary btn-sm"
      >Next &gt;</button>
    </div>
    <!-- Map section with access control -->
    <div class="container mt-5">
      <div v-if="!hasMapAccess" class="alert alert-info">
        {{ $t('map.registerToView') }}
        <router-link to="/register" class="btn btn-primary ml-3">{{ $t('navbar.register') }}</router-link>
      </div>
      <div v-else>
        <div class="map-container">
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
  </div>
</template>

<script>
import axios from 'axios';
import { mapState } from 'vuex';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import ItemTable from './ItemTable.vue';
import ItemFilter from './ItemFilter.vue';

export default {
  name: 'ItemListByCategory',
  components: {
    ItemTable,
    ItemFilter,
  },
  data() {
    return {
      items: [],
      category: {},
      map: null,
      popup: null, // Додано для відстеження поточного попапу
      mapLoaded: false,
      hasMapAccess: false,
      // Pagination state
      page: 1,
      pageSize: 10,
      totalItems: 0,
    };
  },
  computed: {
    ...mapState(['currentLocale']),
  },
  async created() {
    await this.fetchItems();
  },
  watch: {
    items() {
      if (this.map && this.map.getSource('items')) {
        const geoJsonData = this.getGeoJsonFromItems();
        this.map.getSource('items').setData(geoJsonData);
      }
    }
  },
  methods: {
    beforeUnmount() {
      if (this.map) {
        // Remove event listeners
        this.map.off('mouseenter', 'clusters');
        this.map.off('mouseleave', 'clusters');
        this.map.off('click', 'unclustered-point');
        this.map.off('click', 'clusters');
        
        // Remove the map
        this.map.remove();
        this.map = null;
      }
    },
    async fetchItems() {
      try {
        const category_id = this.$route.params.id;
        const offset = (this.page -1) * this.pageSize;
        const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/categories/${category_id}/items`, {
          params: {
            offset: offset,
            limit: this.pageSize,
          },
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
        this.items = response.data.items;
        this.category = response.data.category;
        this.hasMapAccess = response.data.has_map_access;
        // If backend returns total count, use it. Otherwise, estimate
        this.totalItems = response.data.total_items || (offset + this.items.length + (this.items.length === this.pageSize ? this.pageSize : 0));
        if (this.hasMapAccess) {
          this.$nextTick(() => {this.initializeMap();})
        }
      } catch (error) {
        console.error('Error fetching items:', error);
      }
    },
    
    async handlePageChange(newPage) {
      this.page = newPage;
      await this.fetchItems();
    },
      initializeMap() {
      if (!this.$refs.mapContainer) {
        console.error('Map container not found');
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
            }
          },
          center: [31.946946, 49.305825],
          zoom: 4,
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
      console.log('GeoJSON data:', geoJsonData);
      this.map.addSource('items', {
        type: 'geojson',
        data: geoJsonData,
        cluster: true,
        clusterMaxZoom: 14, // Max zoom to cluster points on
        clusterMinPoints: 2, // Minimum number of points to form a cluster
        clusterRadius: 60  // Fixed typo from clasterRadius
      });
    },
    addMapLayers() {
      if (!this.map) return;
      // Add clusters layer
      this.map.addLayer({
        id: 'clusters',
        type: 'circle',
        source: 'items',
        filter: ['has', 'point_count'],
        paint: {
          'circle-color': [
            'step',
            ['get', 'point_count'],
            '#51bbd6',  // 0-3 items
            4,
            '#f1f075',  // 4-8 items
            6,
            '#f28cb1'   // 8+ items
          ],
          'circle-radius': [
            'step',
            ['get', 'point_count'],
            30, 4, 40, 6, 60
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
          'text-field': ['get', 'point_count_abbreviated'],
          'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
          'text-size': 14
        }
      });
      // Add unclustered points - simplified from your current version
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
      // Add pointer cursor for both layers
      this.map.on('mouseenter', 'clusters', () => {
        this.map.getCanvas().style.cursor = 'pointer';
      });
      this.map.on('mouseleave', 'clusters', () => {
        this.map.getCanvas().style.cursor = '';
      });
      // Handle cluster clicks
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
      // Unclustered point interaction (works for both single and multiple points)
      this.map.on('mouseenter', 'unclustered-point', () => {
        this.map.getCanvas().style.cursor = 'pointer';
      });
      this.map.on('mouseleave', 'unclustered-point', () => {
        this.map.getCanvas().style.cursor = '';
      });
      // Handle unclustered point clicks
      this.map.on('click', 'unclustered-point', (e) => {
        const feature = e.features[0];
        const coordinates = feature.geometry.coordinates.slice();
        const item = feature.properties;
        // Ensure the popup is closed before opening a new one
        if (this.popup) { // Змінено з this.map.getPopup() на this.popup
          this.popup.remove();
          this.popup = null; // Очистити посилання після видалення
        }

        // Create and show the popup
        const popupContent = this.getPopupHTML(item);
        console.log('Popup content:', popupContent);

        this.popup = new mapboxgl.Popup({ closeOnClick: false })
          .setLngLat(coordinates)
          .setHTML(popupContent)
          .addTo(this.map);
        console.log('Popup added to map.'); // Додано лог

        // Add a 'open' event listener to the popup to ensure the button is in the DOM
        this.popup.on('open', () => {
          console.log('Popup opened event fired.'); // Додано лог
          const popupButton = document.getElementById(`popup-view-details-${item.id}`);
          if (popupButton) {
            console.log('Popup button found. Adding click listener.'); // Додано лог
            popupButton.addEventListener('click', (event) => {
              event.preventDefault(); // Prevent default anchor behavior
              this.$router.push(`/items/${item.id}`);
            });
          } else {
            console.log('Popup button NOT found.'); // Лог, якщо кнопка не знайдена
          }
        });

        this.popup.on('close', () => { // Додано обробник закриття для очищення
          console.log('Popup closed.');
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
    console.log('Generating popup HTML for item:', item);
      let popupContent = `
        <div class="popup-content">
          <h5><span class="badge bg-info text-dark">${item.offer_type.toUpperCase()}</span> ${item.title || ''}</h5>
          <p>${item.description || ''}</p>
          <p><strong>${this.$t('common.price')}:</strong> ${item.price || 0} ${item.currency || ''}</p>
          <p><strong>${this.$t('common.amount')}:</strong> ${item.amount || 0} ${item.measure || ''}</p>
          <p><strong>${this.$t('common.incoterms')}:</strong> ${item.terms_delivery || ''} ${item.country || ''} ${item.region || ''}</p>
          <a
            href="/items/${item.id}"
            id="popup-view-details-${item.id}"
            class="btn btn-sm btn-primary"
            style="display: block; text-align: center; padding: 8px; margin-top: 10px; background: #007bff; color: white; text-decoration: none; border-radius: 4px;"
          >
            ${this.$t('common.viewDetails')}
          </a>
        </div>
      `;
      console.log('Popup content:', popupContent);
      return popupContent;
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
.pagination-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin: 20px 0;
}

.pagination-controls button {
  min-width: 70px;
  margin: 0 4px;
  padding: 6px 16px;
  border-radius: 20px;
  border: 1px solid #ced4da;
  color:#333;
  transition: background 0.2s, color 0.2s, border 0.2s;
  font-weight: 500;
  cursor: pointer;
}

.pagination-controls button:disabled {
  background: #e9ecef;
  color: #aaa;
  border-color: #e9ecef;
  cursor: not-allowed;
}

.pagination-controls button:not(:disabled):hover {
  background: #007bff;
  color: #fff;
  border-color: #007bff;
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

