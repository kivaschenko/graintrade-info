<template>
  <div class="map-page-container">
    <h1 class="map-page-title">{{ $t('map.filteredItemsMapTitle') }}</h1>
    
    <!-- Button to go back to the table -->
    <div class="text-center mb-4">
      <button @click="goBackToTable" class="btn btn-secondary btn-lg">
        &lt; {{ $t('common_text.backToTable') }}
      </button>
    </div>

    <div class="map-container-full">
      <div class="map-full" id="allItemsMapContainer" ref="allItemsMapContainer"></div>
      <div class="map-legend-full" v-if="mapLoaded">
        <h6>{{ $t('map.clusterSizes') }}</h6>
        <div class="legend-item">
          <span class="circle small"></span> 1-1000 {{ $t('map.tonn') }}
        </div>
        <div class="legend-item">
          <span class="circle medium"></span> 1000 - 10000 {{ $t('map.tonn') }}
        </div>
        <div class="legend-item">
          <span class="circle large"></span> 10000+ {{ $t('map.tonn') }}
        </div>
        <p class="legend-note">{{ $t('map.clusterAmountNote') }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { mapState } from 'vuex';

export default {
  name: 'AllItemsMap',
  data() {
    return {
      map: null,
      popup: null,
      mapLoaded: false,
      markers: {},
      markersOnScreen: {},
      geoJsonData: null,
      loadingMapData: false, // New loading indicator for map data
    };
  },
  computed: {
    ...mapState(['currentLocale']),
    // Get filter parameters from route query
    filterParams() {
      // Ensure params are treated as numbers where expected
      const query = { ...this.$route.query };
      if (query.min_price) query.min_price = parseFloat(query.min_price);
      if (query.max_price) query.max_price = parseFloat(query.max_price);
      if (query.category_id) query.category_id = parseInt(query.category_id);
      return query;
    }
  },
  async mounted() {
    // Fetch initial data based on route filters (before map init)
    await this.fetchAllItemsGeoJson(); 
    await this.initializeMap();
    window.addEventListener('resize', this.resizeMap);
  },
  beforeUnmount() {
    if (this.map) {
      this.map.off('click', 'unclustered-point');
      this.map.off('idle', this.updateMarkers);
      this.map.off('mouseenter', 'unclustered-point');
      this.map.off('mouseleave', 'unclustered-point');

      for (const id in this.markers) {
        this.markers[id].remove();
      }
      this.markers = {};
      this.markersOnScreen = {};

      this.map.remove();
      this.map = null;
    }
    window.removeEventListener('resize', this.resizeMap);
  },
  watch: {
    // Watch for changes in filterParams (from route query) and re-fetch/update map
    filterParams: {
      handler(newParams, oldParams) {
        // Only re-fetch if filter parameters actually changed in a meaningful way
        // JSON.stringify can be used for deep comparison, but might be overkill.
        // Simple checks for common cases like category_id change are sufficient.
        if (JSON.stringify(newParams) !== JSON.stringify(oldParams)) {
             this.fetchAllItemsGeoJson();
        }
      },
      deep: true, // Watch for nested changes in query object
    },
  },
  methods: {
    resizeMap() {
      if (this.map) {
        this.map.resize();
      }
    },
    async fetchAllItemsGeoJson() {
      this.loadingMapData = true; // Set loading to true
      try {
        const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/items-geojson`, {
          params: this.filterParams, // Pass route query params directly
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
        let geoJsonData;
        if (response.data && response.data.type === 'FeatureCollection' && Array.isArray(response.data.features)) {
          geoJsonData = response.data;
        } else if (response.data && response.data.items && response.data.items.type === 'FeatureCollection' && Array.isArray(response.data.items.features)) {
          geoJsonData = response.data.items;
        } else {
          console.error('Unexpected GeoJSON data structure:', response.data);
          geoJsonData = { type: 'FeatureCollection', features: [] };
        }
        geoJsonData.features = geoJsonData.features.map(feature => {
            if (typeof feature.geometry === 'string') {
                try {
                    feature.geometry = JSON.parse(feature.geometry);
                } catch (e) {
                    console.error('Error parsing geometry string:', e, feature.geometry);
                    feature.geometry = null;
                }
            }
            if (feature.properties && typeof feature.properties.amount !== 'number') {
                feature.properties.amount = parseFloat(feature.properties.amount) || 0;
            }
            if (feature.geometry && feature.geometry.coordinates) {
                feature.geometry.coordinates[0] = parseFloat(feature.geometry.coordinates[0]);
                feature.geometry.coordinates[1] = parseFloat(feature.geometry.coordinates[1]);
            }
            return feature;
        }).filter(feature => feature.geometry !== null && feature.geometry.coordinates && !isNaN(feature.geometry.coordinates[0]) && !isNaN(feature.geometry.coordinates[1]));
        this.geoJsonData = geoJsonData;
        // Update map source if it's already initialized
        if (this.map && this.map.getSource('items')) {
            this.map.getSource('items').setData(this.geoJsonData);
            this.updateMarkers(); // Update custom markers
            this.fitMapToBounds(); // Refit map to new filtered data
        }
        return true; 
      } catch (error) {
        console.error('Error fetching all items GeoJSON:', error);
        this.geoJsonData = {
          type: 'FeatureCollection',
          features: []
        };
        if (this.map && this.map.getSource('items')) {
            this.map.getSource('items').setData(this.geoJsonData);
            this.updateMarkers();
        }
        return false;
      } finally {
        this.loadingMapData = false; // Set loading to false
      }
    },
    async initializeMap() {
      if (!this.$refs.allItemsMapContainer) {
        console.error('Map container not found');
        return;
      }
      if (this.map) {
        this.map.remove();
        this.map = null;
      }
      try {
        mapboxgl.accessToken = process.env.VUE_APP_MAPBOX_TOKEN;
        this.map = new mapboxgl.Map({
          container: this.$refs.allItemsMapContainer,
          style: 'mapbox://styles/mapbox/light-v11',
          center: [31.946946, 49.305825],
          zoom: 3.5,
          maxZoom: 10,
          minZoom: 2,
        });
        this.map.addControl(new mapboxgl.NavigationControl(), 'top-right');
        this.map.addControl(new mapboxgl.FullscreenControl(), 'top-right');
        this.map.on('load', () => {
          this.mapLoaded = true;
          if (this.geoJsonData && this.geoJsonData.features.length > 0) {
            this.addMapSources();
            this.addMapLayers();
            this.addMapInteractions();
            this.fitMapToBounds();
            this.map.on('idle', this.updateMarkers);
          } else {
            console.warn('No initial GeoJSON features to display. Map will be empty until data is loaded/filtered.');
            this.addMapSources(); 
            this.addMapLayers();
            this.map.on('idle', this.updateMarkers);
          }
        });
      } catch (error) {
        console.error('Error initializing map:', error);
      }
    },
    addMapSources() {
      if (!this.map) return;
      if (this.map.getSource('items')) {
        return;
      }
      this.map.addSource('items', {
        type: 'geojson',
        data: this.geoJsonData || { type: 'FeatureCollection', features: [] },
        cluster: true,
        clusterMaxZoom: 14,
        clusterRadius: 100,
        clusterProperties: {
          'sum_amount': ['+', ['get', 'amount']]
        }
      });
      this.map.getSource('items').on('data', (e) => {
        if (e.dataType === 'source' && e.sourceId === 'items' && e.isSourceLoaded) { 
          this.updateMarkers(); 
        }
      });
    },
    addMapLayers() {
      if (!this.map) return;
      if (!this.map.getLayer('unclustered-point')) { // Prevent adding multiple times
        this.map.addLayer({
          id: 'unclustered-point',
          type: 'circle',
          source: 'items',
          filter: ['!', ['has', 'point_count']],
          paint: {
            'circle-color': '#11b4da',
            'circle-radius': 6,
            'circle-stroke-width': 1,
            'circle-stroke-color': '#fff'
          }
        },); // Place above road labels
        console.log('Unclustered point layer added.');
      } else {
          console.log('Unclustered point layer already exists.');
      }
    },
    addMapInteractions() {
      if (!this.map) return;
      this.map.off('mouseenter', 'unclustered-point'); 
      this.map.on('mouseenter', 'unclustered-point', () => {
        this.map.getCanvas().style.cursor = 'pointer';
      });
      this.map.off('mouseleave', 'unclustered-point'); 
      this.map.on('mouseleave', 'unclustered-point', () => {
        this.map.getCanvas().style.cursor = '';
      });
      this.map.off('click', 'unclustered-point'); 
      this.map.on('click', 'unclustered-point', (e) => {
        if (!e.features || e.features.length === 0) {
            console.warn('No features found on click.');
            return;
        }
        const coordinates = e.features[0].geometry.coordinates.slice();
        const item = JSON.parse(JSON.stringify(e.features[0].properties));
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
            console.log('Popup button found. Adding click listener.');
          } else {
            console.log('Popup button NOT found.');
          }
        });
        this.popup.on('close', () => {
          this.popup = null;
        });
      });
    },
    updateMarkers() {
      if (!this.map || !this.mapLoaded || !this.map.getSource('items')) {
          return;
      }
      const newMarkers = {};
      const features = this.map.querySourceFeatures('items', {
        filter: ['has', 'point_count']
      });
      for (const feature of features) {
        const clusterId = feature.properties.cluster_id;
        const coordinates = feature.geometry.coordinates;
        const sumAmount = feature.properties.sum_amount; 
        let marker = this.markers[clusterId];
        if (!marker) {
          const el = document.createElement('div');
          el.className = 'cluster-marker';
          const size = Math.min(60, 20 + Math.log10(sumAmount + 1) * 10); 
          el.style.width = `${size}px`;
          el.style.height = `${size}px`;
          el.style.lineHeight = `${size}px`; 
          el.style.backgroundColor = this.getClusterColor(sumAmount); 
          el.style.borderRadius = '50%';
          el.style.display = 'flex';
          el.style.justifyContent = 'center';
          el.style.alignItems = 'center';
          el.style.color = '#fff';
          el.style.fontWeight = 'bold';
          el.style.fontSize = `${Math.min(14, size / 2.5)}px`; 
          el.style.boxShadow = '0 0 5px rgba(0,0,0,0.3)';
          el.style.cursor = 'pointer';
          el.textContent = this.formatAmount(sumAmount); 
          el.addEventListener('click', () => {
            this.map.getSource('items').getClusterExpansionZoom(clusterId, (err, zoom) => {
              if (err) return;
              this.map.easeTo({
                center: coordinates,
                zoom: zoom
              });
            });
          });
          marker = new mapboxgl.Marker({ element: el }).setLngLat(coordinates);
          this.markers[clusterId] = marker;
        }
        if (!this.markersOnScreen[clusterId]) {
          marker.addTo(this.map);
          this.markersOnScreen[clusterId] = true;
        }
        newMarkers[clusterId] = true;
      }
      for (const id in this.markersOnScreen) {
        if (!newMarkers[id]) {
          this.markers[id].remove();
          delete this.markers[id];
          delete this.markersOnScreen[id];
        }
      }
    },
    getClusterColor(amount) {
      if (amount < 1000) return '#51bbd6'; 
      if (amount < 10000) return '#f1f075'; 
      return '#f28cb1'; 
    },
    formatAmount(amount) {
      if (amount >= 1000000) return (amount / 1000000).toFixed(1) + 'M';
      if (amount >= 1000) return (amount / 1000).toFixed(1) + 'K';
      return Math.round(amount).toString(); 
    },
    getPopupHTML(item) {
      let popupContent = `
        <div class="popup-content">
          <h5><span class="badge bg-info text-dark">${item.offer_type ? item.offer_type.toUpperCase() : ''}</span> ${item.title || ''}</h5>
          <p>${item.description || ''}</p>
          <p><strong>${this.$t('common_text.price')}:</strong> ${item.price || 0} ${item.currency || ''}</p>
          <p><strong>${this.$t('common_text.amount')}:</strong> ${item.amount || 0} ${item.measure || ''}</p>
          <p><strong>${this.$t('common_text.incoterms')}:</strong> ${item.terms_delivery || ''}</p>
          <p><strong>${this.$t('common_text.country')}:</strong> ${item.country || ''}</p>
          <p><strong>${this.$t('common_text.region')}:</strong> ${item.region || ''}</p>
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
    fitMapToBounds() {
        if (!this.map || !this.geoJsonData || !this.geoJsonData.features || this.geoJsonData.features.length === 0) {
            console.warn('Cannot fit map to bounds: No GeoJSON data or map not ready.');
            // If no data, set a default center/zoom to ensure map is visible
            this.map.easeTo({
                center: [31.946946, 49.305825], // Default center Ukraine
                zoom: 3.5
            });
            return;
        }
        const bounds = new mapboxgl.LngLatBounds();
        for (const feature of this.geoJsonData.features) {
            if (feature.geometry && feature.geometry.coordinates && 
                !isNaN(feature.geometry.coordinates[0]) && !isNaN(feature.geometry.coordinates[1])) {
                bounds.extend(feature.geometry.coordinates);
            } else {
                console.warn('Skipping feature with invalid coordinates (for bounds):', feature);
            }
        }
        if (!bounds.isEmpty()) {
            this.map.fitBounds(bounds, {
                padding: 50,
                maxZoom: 10 
            });
        } else {
            console.warn('Bounds are empty (no valid features found), cannot fit map to features. Setting default view.');
            this.map.easeTo({
                center: [31.946946, 49.305825],
                zoom: 3.5
            });
        }
    },
    goBackToTable() {
      // Navigate back to ItemListByCategory page, preserving current category
      // Use this.$route.query.category_id directly as it's what we received
      this.$router.push({
        name: 'ItemListByCategory', 
        params: { id: this.$route.query.category_id || '' }, 
      });
    }
  },
};
</script>

<style>
/* Base map container styles */
.map-page-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 20px;
  box-sizing: border-box;
  font-family: 'Inter', sans-serif;
  background-color: #f8f9fa;
}

.map-page-title {
  text-align: center;
  margin-bottom: 20px;
  color: #343a40;
  font-size: 2.2em;
  font-weight: 700;
  letter-spacing: -0.5px;
}

/* Back Button styling */
.btn-secondary {
  background-color: #6c757d;
  color: #fff;
  border: 1px solid #6c757d;
  border-radius: 8px;
  padding: 10px 20px;
  font-weight: 600;
  transition: all 0.2s ease-in-out;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.btn-secondary:hover {
  background-color: #5a6268;
  border-color: #545b62;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}


/* Map container styles (unchanged mostly) */
.map-container-full {
  position: relative;
  flex-grow: 1;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 6px 20px rgba(0,0,0,0.15);
  background-color: #e0e0e0; /* Fallback for map loading */
}

.map-full {
  width: 100%;
  height: 100%;
}

.mapboxgl-canvas {
  width: 100% !important;
  height: 100% !important;
}

.map-legend-full {
  position: absolute;
  bottom: 25px;
  right: 25px;
  background: rgba(255, 255, 255, 0.95);
  padding: 18px;
  border-radius: 10px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.15);
  font-family: 'Inter', sans-serif;
  color: #343a40;
  z-index: 10;
  border: 1px solid #e0e0e0;
  width: 200px;
}

.map-legend-full h6 {
  margin-top: 0;
  margin-bottom: 12px;
  font-weight: 700;
  font-size: 1.15em;
  color: #212529;
}

.legend-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  font-size: 0.95em;
}

.legend-item .circle {
  width: 20px;
  height: 20px;
  min-width: 20px;
  border-radius: 50%;
  margin-right: 15px;
  border: 1px solid rgba(0,0,0,0.1);
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  display: inline-block;
  vertical-align: middle;
}

.circle.small { background-color: #51bbd6; }
.circle.medium { background-color: #f1f075; }
.circle.large { background-color: #f28cb1; }

.legend-note {
  font-size: 0.8em;
  color: #6c757d;
  margin-top: 18px;
  border-top: 1px solid #e9ecef;
  padding-top: 12px;
  line-height: 1.4;
}

/* Custom cluster markers (unchanged mostly) */
.cluster-marker {
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 50%;
  color: #fff;
  font-weight: bold;
  box-shadow: 0 0 8px rgba(0,0,0,0.4);
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  border: 2px solid rgba(255,255,255,0.7);
}

.cluster-marker:hover {
  transform: scale(1.1);
  box-shadow: 0 0 15px rgba(0,0,0,0.6);
}

/* Mapbox GL JS popup overrides */
.mapboxgl-popup {
  max-width: 320px;
  font-family: 'Inter', sans-serif;
}

.mapboxgl-popup-content {
  padding: 15px;
  border-radius: 10px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.15);
  border: none;
}

.mapboxgl-popup-close-button {
  right: 8px;
  top: 8px;
  font-size: 1.5em;
  color: #6c757d;
  transition: color 0.2s;
}
.mapboxgl-popup-close-button:hover {
    color: #343a40;
}

/* Popup content styles */
.popup-content {
  padding: 0;
  flex: 1;
  color: #343a40;
}

.popup-content h5 {
  margin-bottom: 10px;
  font-weight: 700;
  font-size: 1.2em;
  display: flex;
  align-items: center;
  color: #212529;
}

.popup-content .badge {
    margin-right: 10px;
    padding: 5px 10px;
    border-radius: 5px;
    font-size: 0.85em;
    font-weight: 600;
}

.popup-content p {
  margin: 6px 0;
  font-size: 0.95em;
  color: #495057;
  line-height: 1.5;
}

.popup-content p strong {
    color: #343a40;
    font-weight: 600;
}

.popup-content .btn {
  margin-top: 20px;
  display: block;
  width: 100%;
  text-align: center;
  padding: 12px;
  font-size: 1.05em;
  border-radius: 8px;
  font-weight: 600;
  background-color: #007bff;
  color: #fff;
  border: none;
  box-shadow: 0 3px 10px rgba(0, 123, 255, 0.2);
  transition: background-color 0.2s, transform 0.2s, box-shadow 0.2s;
}

.popup-content .btn:hover {
  background-color: #0056b3;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 123, 255, 0.3);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .map-page-container {
    padding: 10px;
  }

  .map-page-title {
    font-size: 1.8em;
    margin-bottom: 15px;
  }

  .map-legend-full {
    bottom: 15px;
    right: 15px;
    padding: 15px;
    font-size: 0.9em;
  }

  .map-legend-full h6 {
    font-size: 1em;
    margin-bottom: 8px;
  }

  .legend-item {
    font-size: 0.85em;
    margin-bottom: 8px;
  }

  .legend-item .circle {
    width: 16px;
    height: 16px;
    min-width: 16px;
    margin-right: 10px;
  }

  .legend-note {
    font-size: 0.75em;
    padding-top: 8px;
  }
}
</style>
