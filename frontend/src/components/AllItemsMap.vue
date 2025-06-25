<template>
  <div class="map-page-container">
    <h1 class="map-page-title">{{ $t('map.allItemsMapTitle') }}</h1>
    <div class="map-container-full">
      <div class="map-full" id="allItemsMapContainer" ref="allItemsMapContainer"></div>
      <div class="map-legend-full" v-if="mapLoaded">
        <h6>{{ $t('map.clusterSizes') }}</h6>
        <div class="legend-item">
          <span class="circle small"></span> 1-10 {{ $t('map.items') }}
        </div>
        <div class="legend-item">
          <span class="circle medium"></span> 11-50 {{ $t('map.items') }}
        </div>
        <div class="legend-item">
          <span class="circle large"></span> 50+ {{ $t('map.items') }}
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
import { mapState } from 'vuex'; // Import mapState to access currentLocale

export default {
  name: 'AllItemsMap',
  data() {
    return {
      map: null,
      popup: null,
      mapLoaded: false,
      markers: {}, // Stores Mapbox GL JS Marker instances for clusters
      markersOnScreen: {} // Tracks markers currently on screen
    };
  },
  computed: {
    ...mapState(['currentLocale']), // Access currentLocale from Vuex store
  },
  async mounted() {
    await this.fetchAndInitializeMap();
    window.addEventListener('resize', this.resizeMap); // Listen for window resize
  },
  beforeUnmount() {
    if (this.map) {
      // Remove event listeners added to the map instance
      this.map.off('click', 'unclustered-point');
      this.map.off('render', this.updateMarkers);
      this.map.off('idle', this.updateMarkers);
      this.map.off('mouseenter', 'unclustered-point');
      this.map.off('mouseleave', 'unclustered-point');

      // Remove all custom markers from the map
      for (const id in this.markers) {
        this.markers[id].remove();
      }
      this.markers = {};
      this.markersOnScreen = {};

      // Remove the map instance
      this.map.remove();
      this.map = null;
    }
    window.removeEventListener('resize', this.resizeMap); // Remove window resize listener
  },
  methods: {
    resizeMap() {
      // Resize the map when the window size changes
      if (this.map) {
        this.map.resize();
      }
    },
    async fetchAllItemsGeoJson() {
      try {
        // Fetch all items' GeoJSON data without pagination
        const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/items-geojson`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
        // Assuming your backend endpoint /items-geojson returns a GeoJSON FeatureCollection
        // with 'items' property containing the actual GeoJSON data.
        console.log('Fetched all items GeoJSON:', response.data.items);
        return response.data.items;
      } catch (error) {
        console.error('Error fetching all items GeoJSON:', error);
        return {
          type: 'FeatureCollection',
          features: []
        }; // Return empty GeoJSON on error
      }
    },
    async fetchAndInitializeMap() {
      if (!this.$refs.allItemsMapContainer) {
        console.error('Map container not found');
        return;
      }
      if (this.map) { // Prevent re-initializing if already initialized
        this.map.remove();
        this.map = null;
      }

      try {
        mapboxgl.accessToken = process.env.VUE_APP_MAPBOX_TOKEN;
        this.map = new mapboxgl.Map({
          container: this.$refs.allItemsMapContainer,
          style: 'mapbox://styles/mapbox/standard',
          config: {
            basemap: {
              theme: 'monochrome',
            }
          },
          center: [31.946946, 49.305825], // Centered on Ukraine
          zoom: 4.5, // Initial zoom level
          maxZoom: 14, // Maximum zoom level for clusters
          minZoom: 3, // Minimum zoom level
        });

        this.map.addControl(new mapboxgl.NavigationControl(), 'top-right');
        this.map.addControl(new mapboxgl.FullscreenControl(), 'top-right');

        this.map.on('load', async () => {
          this.mapLoaded = true;
          const geoJsonData = await this.fetchAllItemsGeoJson();
          console.log('Fetched GeoJSON for all items:', geoJsonData);
          this.addMapSources(geoJsonData);
          this.addMapLayers();
          this.addMapInteractions();

          // Add render/idle listeners for dynamic marker updates
          this.map.on('render', this.updateMarkers);
          this.map.on('idle', this.updateMarkers);
        });

      } catch (error) {
        console.error('Error initializing map:', error);
      }
    },
    addMapSources(geoJsonData) {
      if (!this.map) return;
      this.map.addSource('items', {
        type: 'geojson',
        data: geoJsonData,
        cluster: true,
        clusterMaxZoom: 14, // Max zoom to cluster points on
        clusterRadius: 50,
        clusterProperties: {
          'sum_amount': ['+', ['get', 'amount']] // Aggregate sum of 'amount'
        }
      });
    },
    addMapLayers() {
      if (!this.map) return;
      
      // Add unclustered points layer
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
      }, 
    //   'road-label'
    ); // Place above road labels
    },
    addMapInteractions() {
      if (!this.map) return;

      // Add pointer cursor for unclustered points
      this.map.on('mouseenter', 'unclustered-point', () => {
        this.map.getCanvas().style.cursor = 'pointer';
      });
      this.map.on('mouseleave', 'unclustered-point', () => {
        this.map.getCanvas().style.cursor = '';
      });

      // Handle unclustered point clicks
      this.map.on('click', 'unclustered-point', (e) => {
        console.log('Unclustered point clicked:', e);
        if (!e.features || e.features.length === 0) return;
        const coordinates = e.features[0].geometry.coordinates.slice();
        const item = JSON.parse(JSON.stringify(e.features[0].properties));
        console.log('Clicked item (after deep copy):', item);

        if (this.popup) {
          this.popup.remove();
          this.popup = null;
        }

        const popupContent = this.getPopupHTML(item);
        console.log('Popup content:', popupContent);

        this.popup = new mapboxgl.Popup({ closeOnClick: false })
          .setLngLat(coordinates)
          .setHTML(popupContent)
          .addTo(this.map);
        console.log('Popup added to map.');

        this.popup.on('open', () => {
          console.log('Popup opened event fired.');
          const popupButton = document.getElementById(`popup-view-details-${item.id}`);
          if (popupButton) {
            console.log('Popup button found. Adding click listener.');
            // No explicit click listener needed here if href is used for navigation
          } else {
            console.log('Popup button NOT found.');
          }
        });

        this.popup.on('close', () => {
          console.log('Popup closed.');
          this.popup = null;
        });
      });
    },
    updateMarkers() {
      if (!this.map || !this.mapLoaded || !this.map.getSource('items')) return;

      const newMarkers = {};
      // Query for all features that are clusters
      const features = this.map.querySourceFeatures('items', {
        filter: ['has', 'point_count']
      });

      // For every cluster feature, update its marker or create a new one
      for (const feature of features) {
        const clusterId = feature.properties.cluster_id;
        const coordinates = feature.geometry.coordinates;
        // const pointCount = feature.properties.point_count;
        const sumAmount = feature.properties.sum_amount; // Get the aggregated sum_amount

        let marker = this.markers[clusterId];

        if (!marker) {
          // Create a new marker if it doesn't exist
          const el = document.createElement('div');
          el.className = 'cluster-marker';
          // Dynamically adjust size based on sum_amount
          // Example logic: min size 20px, max size 60px, scale based on log of amount
          const size = Math.min(60, 20 + Math.log10(sumAmount + 1) * 10); 
          el.style.width = `${size}px`;
          el.style.height = `${size}px`;
          el.style.lineHeight = `${size}px`; // Center text vertically
          el.style.backgroundColor = this.getClusterColor(sumAmount); // Color based on sum_amount
          el.style.borderRadius = '50%';
          el.style.display = 'flex';
          el.style.justifyContent = 'center';
          el.style.alignItems = 'center';
          el.style.color = '#fff';
          el.style.fontWeight = 'bold';
          el.style.fontSize = `${Math.min(14, size / 2.5)}px`; // Adjust font size based on marker size
          el.style.boxShadow = '0 0 5px rgba(0,0,0,0.3)';
          el.style.cursor = 'pointer';

          el.textContent = this.formatAmount(sumAmount); // Display formatted sum_amount

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

      // Remove markers that are no longer on screen
      for (const id in this.markersOnScreen) {
        if (!newMarkers[id]) {
          this.markers[id].remove();
          delete this.markers[id];
          delete this.markersOnScreen[id];
        }
      }
    },
    // Helper function to determine cluster color based on aggregated amount
    getClusterColor(amount) {
      if (amount < 1000) return '#51bbd6'; // Small amount
      if (amount < 10000) return '#f1f075'; // Medium amount
      return '#f28cb1'; // Large amount
    },
    // Helper function to format amount for display
    formatAmount(amount) {
      if (amount >= 1000000) return (amount / 1000000).toFixed(1) + 'M';
      if (amount >= 1000) return (amount / 1000).toFixed(1) + 'K';
      return Math.round(amount).toString(); // Round to whole number for display
    },
    getPopupHTML(item) {
      console.log('Generating popup HTML for item:', item);
      let popupContent = `
        <div class="popup-content">
          <h5><span class="badge bg-info text-dark">${item.offer_type ? item.offer_type.toUpperCase() : ''}</span> ${item.title || ''}</h5>
          <p>${item.description || ''}</p>
          <p><strong>${this.$t('common.price')}:</strong> ${item.price || 0} ${item.currency || ''}</p>
          <p><strong>${this.$t('common.amount')}:</strong> ${item.amount || 0} ${item.measure || ''}</p>
          <p><strong>${this.$t('common.incoterms')}:</strong> ${item.terms_delivery || ''}</p>
          <p><strong>${this.$t('common.country')}:</strong> ${item.country || ''}</p>
          <p><strong>${this.$t('common.region')}:</strong> ${item.region || ''}</p>
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
  },
};
</script>

<style>
.map-page-container {
  display: flex;
  flex-direction: column;
  height: 100vh; /* Full viewport height */
  padding: 20px;
  box-sizing: border-box;
}

.map-page-title {
  text-align: center;
  margin-bottom: 20px;
  color: #333;
}

.map-container-full {
  position: relative;
  flex-grow: 1; /* Allow map to take available space */
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.map-full {
  width: 100%;
  height: 100%; /* Fill parent container */
}

.mapboxgl-canvas {
  width: 100% !important;
  height: 100% !important;
}

.map-legend-full {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background: rgba(255, 255, 255, 0.9);
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 0 15px rgba(0,0,0,0.2);
  font-family: 'Inter', sans-serif;
  color: #333;
  z-index: 10;
}

.map-legend-full h6 {
  margin-top: 0;
  margin-bottom: 10px;
  font-weight: bold;
  font-size: 1.1em;
}

.legend-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-bottom: 8px;
}

.legend-item .circle {
  width: 18px;
  height: 18px;
  min-width: 18px;
  border-radius: 50%;
  margin-right: 14px;
  border: 1px solid rgba(0,0,0,0.2);
  display: inline-block;
  vertical-align: middle;
}

.circle.small { background-color: #51bbd6; }
.circle.medium { background-color: #f1f075; }
.circle.large { background-color: #f28cb1; }

.legend-note {
  font-size: 0.85em;
  color: #666;
  margin-top: 15px;
  border-top: 1px solid #eee;
  padding-top: 10px;
}

/* Styles for custom cluster markers */
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
  border: 2px solid rgba(255,255,255,0.7); /* White border for contrast */
}

.cluster-marker:hover {
  transform: scale(1.1);
  box-shadow: 0 0 15px rgba(0,0,0,0.6);
}

/* Default Mapbox GL JS popup styles (if overriding is needed for consistency) */
.mapboxgl-popup {
  max-width: 300px;
  font-family: 'Inter', sans-serif;
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
  padding: 5px;
  flex: 1;
}

.popup-content h5 {
  margin-bottom: 8px;
  font-weight: bold;
  color: #333;
  font-size: 1.1em;
  display: flex;
  align-items: center;
}

.popup-content .badge {
    margin-right: 8px;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.8em;
}

.popup-content p {
  margin: 5px 0;
  font-size: 0.9em;
  color: #666;
}

.popup-content p strong {
    color: #444;
}

.popup-content .btn {
  margin-top: 15px;
  display: block;
  width: 100%;
  text-align: center;
  padding: 10px;
  font-size: 1em;
  border-radius: 6px;
}
</style>
