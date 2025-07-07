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
                <div class="mb-4 p-3 border rounded bg-light">
                  <h5 class="text-primary mb-3">{{ $t('itemDetails.yourUsage') }}</h5>
                  <p v-if="userLimits.map_views_limit !== -1">
                    <strong>{{ $t('itemDetails.mapViews') }}:</strong> {{ userUsage.map_views || 0 }} / {{ userLimits.map_views_limit }}
                    <span v-if="userUsage.map_views >= userLimits.map_views_limit" class="text-danger ms-2">{{ $t('itemDetails.limitReached') }}</span>
                  </p>
                  <p v-if="userLimits.geo_search_limit !== -1">
                    <strong>{{ $t('itemDetails.geoSearches') }}:</strong> {{ userUsage.geo_search_count || 0 }} / {{ userLimits.geo_search_limit }}
                    <span v-if="userUsage.geo_search_count >= userLimits.geo_search_limit" class="text-danger ms-2">{{ $t('itemDetails.limitReached') }}</span>
                  </p>
                  <p v-if="userLimits.navigation_limit !== -1">
                    <strong>{{ $t('itemDetails.directionRequests') }}:</strong> {{ userUsage.navigation_count || 0 }} / {{ userLimits.navigation_limit }}
                    <span v-if="userUsage.navigation_count >= userLimits.navigation_limit" class="text-danger ms-2">{{ $t('itemDetails.limitReached') }}</span>
                  </p>
                  <p v-else class="text-muted">{{ $t('itemDetails.noUsageLimits') }}</p>
                </div>

                <div class="mb-3">
                  <label for="searchLocation" class="form-label">{{ $t('itemDetails.enterLocation') }}</label>
                  <input class="form-control" type="text" id="searchLocation" v-model="searchLocation" @change="geocodeLocation" :placeholder="$t('itemDetails.enterAddressOrCoordinates')" :disabled="!canPerformGeoSearch">
                  <small v-if="!canPerformGeoSearch" class="text-danger">{{ $t('itemDetails.geoSearchLimitReached') }}</small>
                </div>
                <div class="mb-3">
                  <label for="tariffRate" class="form-label">{{ $t('itemDetails.tariffRatePerKilometer') }}</label>
                  <input class="form-control" type="number" id="tariffRate" v-model="tariffRate" @input="calculateTariff" :placeholder="$t('itemDetails.enterTariffRate')">
                </div>
                <div v-if="directions" class="directions-info p-3 mt-4 rounded">
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

      <div class="col-md-6" v-if="isAuthenticated">
        <div class="card map-card">
          <div class="card-body p-0">
            <div id="map" class="map-instance" :class="{ 'disabled-map': !canViewMap }"></div>
             <div v-if="!canViewMap" class="map-overlay">
                <div class="alert alert-warning text-center">
                    <i class="bi bi-info-circle me-2"></i>{{ $t('itemDetails.mapViewLimitReached') }}
                </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="isAuthenticated && item.uuid" class="mt-5">
      <div class="card chat-card">
        <div class="card-body">
          <div v-if="isOwner">
            <OwnerChatSwitcher :itemId="item.uuid" :ownerId="currentUserId" />
          </div>
          <div v-else>
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
      userUsage: { // To store current usage counts
        map_views: 0,
        geo_search_count: 0,
        navigation_count: 0,
      },
      userLimits: { // To store tariff limits
        map_views_limit: -1, // -1 means unlimited
        geo_search_limit: -1,
        navigation_limit: -1,
      },
    };
  },
  watch: {
    tariffRate() {
      this.calculateTariff();
    },
  },
  async created() {
    this.checkAuthentication();
    if (this.isAuthenticated) {
      await this.fetchUserMapUsage(); // Fetch user usage and limits
    }

    try {
      const itemId = this.$route.params.id;
      const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/items/${itemId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      this.item = response.data;
      this.ownerId = response.data["owner_id"];

      if (this.isAuthenticated && this.canViewMap) { // Only initialize map if authenticated and within limits
        this.$nextTick(() => {this.initializeMap();})
      }
    } catch (error) {
      console.error('Error fetching item details:', error);
      // Handle 403 Forbidden or other errors related to limits
      if (error.response && error.response.status === 403) {
        alert(this.$t('itemDetails.mapViewLimitReachedAlert'));
      }
    }
  },
  methods: {
    checkAuthentication() {
      const token = localStorage.getItem('access_token');
      this.isAuthenticated = !!token;
    },
    async fetchUserMapUsage() {
      try {
        const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/user/map_usage`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
        this.userUsage = response.data.usage;
        this.userLimits = response.data.limits;
      } catch (error) {
        console.error('Error fetching user map usage:', error);
        // Handle error, maybe set default limits or show an error message
      }
    },
    async initializeMap() {
      if (this.map || !this.canViewMap) { // Prevent re-initialization or if limit reached
        return;
      }
      // This call should go through your backend to increment map_views
      try {
        const response = await axios.post(`${process.env.VUE_APP_BACKEND_URL}/mapbox/map-view`, {}, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
        // Update local usage counter after successful backend increment
        this.userUsage.map_views = response.data.map_views;

        mapboxgl.accessToken = process.env.VUE_APP_MAPBOX_TOKEN; // This token might be fetched from backend for security
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

        // Geocoder should also use your backend for counting
        const geocoder = new MapboxGeocoder({
          accessToken: mapboxgl.accessToken, // Still use the token for client-side functionality, but actual search goes to backend
          mapboxgl: mapboxgl,
          localGeocoder: async (query) => {
            // This local geocoder will call your backend for geo search
            try {
              const geoSearchResponse = await axios.post(`${process.env.VUE_APP_BACKEND_URL}/mapbox/geo-search`, { query: query }, {
                headers: {
                  Authorization: `Bearer ${localStorage.getItem('access_token')}`,
                },
              });
              this.userUsage.geo_search_count = geoSearchResponse.data.geo_search_count; // Update local counter
              return geoSearchResponse.data.results; // Return results from your backend
            } catch (error) {
              console.error('Error with backend geo search:', error);
              if (error.response && error.response.status === 403) {
                 alert(this.$t('itemDetails.geoSearchLimitReachedAlert'));
              }
              return []; // Return empty array on error
            }
          }
        });

        this.map.addControl(geocoder, 'top-left');

        geocoder.on('result', (e) => {
          const { center } = e.result;
          this.searchLocation = `${center[1]},${center[0]}`;
          this.calculateDirections(center);
        });
      } catch (error) {
        console.error('Error initializing map or incrementing map view:', error);
        if (error.response && error.response.status === 403) {
          alert(this.$t('itemDetails.mapViewLimitReachedAlert'));
          // Optionally disable map features or show a message
        }
      }
    },
    async geocodeLocation() {
      if (!this.canPerformGeoSearch) {
        alert(this.$t('itemDetails.geoSearchLimitReachedAlert'));
        return;
      }
      try {
        // Route geocoding through your backend proxy
        const response = await axios.post(`${process.env.VUE_APP_BACKEND_URL}/mapbox/geo-search`, { query: this.searchLocation }, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
        const coordinates = response.data.features[0].geometry.coordinates;
        this.userUsage.geo_search_count = response.data.geo_search_count; // Update local counter
        this.calculateDirections(coordinates);
      } catch (error) {
        console.error('Error geocoding location via backend:', error);
        if (error.response && error.response.status === 403) {
          alert(this.$t('itemDetails.geoSearchLimitReachedAlert'));
        }
      }
    },
    async calculateDirections(coordinates) {
      if (!this.canPerformNavigation) {
        alert(this.$t('itemDetails.directionLimitReachedAlert'));
        return;
      }
      try {
        // Route directions through your backend proxy
        const response = await axios.post(`${process.env.VUE_APP_BACKEND_URL}/mapbox/directions`, {
          origin: coordinates,
          destination: [this.item.longitude, this.item.latitude]
        }, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
        const route = response.data.route;
        this.directions = {
          distance: route.distance,
          duration: route.duration,
        };
        this.userUsage.navigation_count = response.data.navigation_count; // Update local counter

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
              'line-color': '#007bff',
              'line-width': 6,
              'line-opacity': 0.8,
            },
          });
        }
      } catch (error) {
        console.error('Error calculating directions via backend:', error);
        if (error.response && error.response.status === 403) {
          alert(this.$t('itemDetails.directionLimitReachedAlert'));
        }
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
      return `https://www.google.com/maps/search/?api=1&query=${this.item.latitude},${this.item.longitude}`;
    },
    canViewMap() {
        return this.userLimits.map_views_limit === -1 || (this.userUsage.map_views < this.userLimits.map_views_limit);
    },
    canPerformGeoSearch() {
        return this.userLimits.geo_search_limit === -1 || (this.userUsage.geo_search_count < this.userLimits.geo_search_limit);
    },
    canPerformNavigation() {
        return this.userLimits.navigation_limit === -1 || (this.userUsage.navigation_count < this.userLimits.navigation_limit);
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
/* Existing styles... */

/* New styles for disabled map overlay */
.map-instance.disabled-map {
  filter: grayscale(100%);
  pointer-events: none; /* Disable interactions */
}

.map-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(255, 255, 255, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10;
    border-radius: 0.75rem; /* Match card radius */
}
</style>

<i18n>
{
  "en": {
    "itemDetails": {
      "yourUsage": "Your Map Usage",
      "mapViews": "Map Views",
      "geoSearches": "Geo Searches",
      "directionRequests": "Direction Requests",
      "limitReached": "Limit Reached!",
      "noUsageLimits": "No usage limits applied.",
      "mapViewLimitReached": "You have reached your map view limit.",
      "geoSearchLimitReached": "You have reached your geo search limit.",
      "directionLimitReached": "You have reached your direction request limit.",
      "mapViewLimitReachedAlert": "You have reached your map view limit for this period. Please check your subscription.",
      "geoSearchLimitReachedAlert": "You have reached your geo search limit for this period. Please check your subscription.",
      "directionLimitReachedAlert": "You have reached your direction request limit for this period. Please check your subscription."
    }
  },
  "uk": {
    "itemDetails": {
      "yourUsage": "Ваше використання карти",
      "mapViews": "Перегляди карти",
      "geoSearches": "Геопошуки",
      "directionRequests": "Запити маршрутів",
      "limitReached": "Ліміт досягнуто!",
      "noUsageLimits": "Обмеження використання не застосовуються.",
      "mapViewLimitReached": "Ви досягли ліміту переглядів карти.",
      "geoSearchLimitReached": "Ви досягли ліміту геопошуків.",
      "directionLimitReached": "Ви досягли ліміту запитів маршрутів.",
      "mapViewLimitReachedAlert": "Ви досягли ліміту переглядів карти на цей період. Будь ласка, перевірте свою підписку.",
      "geoSearchLimitReachedAlert": "Ви досягли ліміту геопошуку на цей період. Будь ласка, перевірте свою підписку.",
      "directionLimitReachedAlert": "Ви досягли ліміту запитів маршрутів на цей період. Будь ласка, перевірте свою підписку."
    }
  }
}
</i18n>


### Explanation of Changes:

1.  **`data()` properties:**
    * `userUsage`: An object to store the current counts (`map_views`, `geo_search_count`, `navigation_count`) fetched from your backend.
    * `userLimits`: An object to store the limits (`map_views_limit`, `geo_search_limit`, `navigation_limit`) for the user's current tariff plan, also fetched from the backend. Default `-1` signifies unlimited.
2.  **`fetchUserMapUsage()` method:**
    * This new method makes an API call to your backend (e.g., `/user/map_usage`) to retrieve the current usage statistics and limits for the authenticated user.
    * It's called in the `created()` lifecycle hook, so usage information is available when the component loads.
3.  **Modified Mapbox Interaction Methods:**
    * `initializeMap()`: Instead of directly initializing the map, it first makes a `POST` request to `/mapbox/map-view` on your backend. Your backend will increment the `map_views` counter for the user and then respond. The Mapbox map is only initialized if the backend call is successful and within limits.
    * `geocodeLocation()`: Now sends the `searchLocation` query to your backend's `/mapbox/geo-search` endpoint via a `POST` request. Your backend will perform the actual Mapbox Geocoding API call, increment `geo_search_count`, and return the results.
    * `calculateDirections()`: Sends the origin and destination coordinates to your backend's `/mapbox/directions` endpoint via a `POST` request. Your backend will call the Mapbox Directions API, increment `navigation_count`, and return the route.
    * **Error Handling:** Each of these methods now includes `try-catch` blocks to handle potential 403 Forbidden responses from your backend, which would indicate that the user has hit a limit.
4.  **`computed` properties (`canViewMap`, `canPerformGeoSearch`, `canPerformNavigation`):**
    * These new computed properties check if the user is allowed to perform the respective actions based on their current usage and limits. They will return `true` if unlimited or if the current usage is below the limit.
5.  **Template Updates:**
    * A new `div` displays the `userUsage` and `userLimits` in a user-friendly format, indicating if a limit has been reached.
    * Input fields and the map container are conditionally disabled or visually altered (`disabled-map` class with an overlay) if the corresponding usage limit is reached.
6.  **I18n (Internationalization):** Added new translation keys for usage-related messages.

## 2. Conceptual FastAPI Backend Endpoints

Your FastAPI application will serve as a proxy for Mapbox API calls and will manage the usage tracking in your PostgreSQL database.

**Assumptions for Backend:**
* You have a way to authenticate users and extract their `user_id`.
* You have database models (e.g., using SQLAlchemy or raw `psycopg2`) for `Tarif` and `Subscription` corresponding to your provided schemas.
* The `current_user` object contains necessary information, including the user's subscription details.

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import httpx # For making external HTTP requests to Mapbox
from typing import Dict, Any, Optional

# --- Dummy Database Operations (Replace with your actual database logic) ---
# In a real app, these would interact with your PostgreSQL database
class TarifDB:
    def get_tarif_by_id(self, tarif_id: int):
        # Simulate fetching a tarif from DB
        # items_limit, map_views_limit, geo_search_limit, navigation_limit
        tarifs_data = {
            1: {"map_views_limit": 100, "geo_search_limit": 50, "navigation_limit": 20},
            2: {"map_views_limit": -1, "geo_search_limit": -1, "navigation_limit": -1}, # Unlimited
            3: {"map_views_limit": 5, "geo_search_limit": 2, "navigation_limit": 1},
        }
        return tarifs_data.get(tarif_id, {"map_views_limit": 10, "geo_search_limit": 5, "navigation_limit": 3})

class SubscriptionDB:
    def get_subscription_by_user_id(self, user_id: int):
        # Simulate fetching subscription from DB
        # For demo, let's assume user 1 has tarif 1, user 2 has tarif 2
        # user_id, tarif_id, map_views, geo_search_count, navigation_count
        subscriptions_data = {
            1: {"tarif_id": 1, "map_views": 80, "geo_search_count": 40, "navigation_count": 15},
            2: {"tarif_id": 2, "map_views": 10, "geo_search_count": 5, "navigation_count": 3},
            3: {"tarif_id": 3, "map_views": 5, "geo_search_count": 2, "navigation_count": 1}, # Reached limits for this user
        }
        return subscriptions_data.get(user_id)

    def update_subscription_counts(self, user_id: int, map_views: Optional[int] = None, geo_search_count: Optional[int] = None, navigation_count: Optional[int] = None):
        # Simulate updating counts in DB
        sub = self.get_subscription_by_user_id(user_id) # In real app, fetch from DB again
        if sub:
            if map_views is not None: sub["map_views"] = map_views
            if geo_search_count is not None: sub["geo_search_count"] = geo_search_count
            if navigation_count is not None: sub["navigation_count"] = navigation_count
        return sub # Return updated subscription


tarif_db = TarifDB()
subscription_db = SubscriptionDB()

# --- Authentication (Simplified for example) ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # In a real app, decode JWT token and fetch user from DB
    # For this example, let's just return a dummy user ID
    # Assume user ID 1 for any valid token
    # Or, if token contains user ID:
    # user_id = decode_token(token)
    # user = fetch_user_from_db(user_id)
    # return user
    # For demo purposes, map token to a user_id:
    if token == "user1_token":
        return {"id": 1, "username": "testuser1"}
    elif token == "user2_token":
        return {"id": 2, "username": "testuser2"}
    elif token == "user3_token":
        return {"id": 3, "username": "testuser3"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

# --- FastAPI App ---
app = FastAPI()

MAPBOX_TOKEN = "YOUR_MAPBOX_SECRET_TOKEN" # Store this securely, e.g., in environment variables
MAPBOX_API_BASE_URL = "[https://api.mapbox.com](https://api.mapbox.com)"

# --- Request Models ---
class GeoSearchRequest(BaseModel):
    query: str

class DirectionsRequest(BaseModel):
    origin: list[float] # [longitude, latitude]
    destination: list[float] # [longitude, latitude]

# --- Helper to check and increment usage ---
async def check_and_increment_usage(
    user_id: int,
    usage_type: str # 'map_views', 'geo_search_count', 'navigation_count'
):
    subscription = subscription_db.get_subscription_by_user_id(user_id)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    tarif = tarif_db.get_tarif_by_id(subscription["tarif_id"])
    if not tarif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tariff plan not found")

    current_usage = subscription.get(usage_type, 0)
    limit = tarif.get(f"{usage_type}_limit", -1)

    if limit != -1 and current_usage >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Limit for {usage_type.replace('_', ' ')} reached for your current tariff plan."
        )

    # Increment usage
    new_count = current_usage + 1
    updated_subscription = subscription_db.update_subscription_counts(user_id, **{usage_type: new_count})
    return updated_subscription

# --- API Endpoints ---

@app.get("/user/map_usage")
async def get_user_map_usage(current_user: Dict = Depends(get_current_user)):
    """
    Returns the current map-related usage and limits for the authenticated user.
    """
    user_id = current_user["id"]
    subscription = subscription_db.get_subscription_by_user_id(user_id)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    tarif = tarif_db.get_tarif_by_id(subscription["tarif_id"])
    if not tarif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tariff plan not found")

    return {
        "usage": {
            "map_views": subscription.get("map_views", 0),
            "geo_search_count": subscription.get("geo_search_count", 0),
            "navigation_count": subscription.get("navigation_count", 0),
        },
        "limits": {
            "map_views_limit": tarif.get("map_views_limit", -1),
            "geo_search_limit": tarif.get("geo_search_limit", -1),
            "navigation_limit": tarif.get("navigation_limit", -1),
        }
    }

@app.post("/mapbox/map-view")
async def increment_map_view(current_user: Dict = Depends(get_current_user)):
    """
    Increments map_views count for the user.
    """
    user_id = current_user["id"]
    updated_sub = await check_and_increment_usage(user_id, "map_views")
    return {"message": "Map view counted", "map_views": updated_sub["map_views"]}

@app.post("/mapbox/geo-search")
async def proxy_geo_search(request: GeoSearchRequest, current_user: Dict = Depends(get_current_user)):
    """
    Proxies Mapbox Geocoding API and increments geo_search_count.
    """
    user_id = current_user["id"]
    updated_sub = await check_and_increment_usage(user_id, "geo_search_count")

    async with httpx.AsyncClient() as client:
        mapbox_url = f"{MAPBOX_API_BASE_URL}/geocoding/v5/mapbox.places/{request.query}.json"
        params = {"access_token": MAPBOX_TOKEN}
        response = await client.get(mapbox_url, params=params)
        response.raise_for_status() # Raise an exception for HTTP errors
        mapbox_results = response.json()

    return {
        "message": "Geo search successful",
        "geo_search_count": updated_sub["geo_search_count"],
        "features": mapbox_results.get("features", []) # Return Mapbox results
    }

@app.post("/mapbox/directions")
async def proxy_directions(request: DirectionsRequest, current_user: Dict = Depends(get_current_user)):
    """
    Proxies Mapbox Directions API and increments navigation_count.
    """
    user_id = current_user["id"]
    updated_sub = await check_and_increment_usage(user_id, "navigation_count")

    async with httpx.AsyncClient() as client:
        coordinates_str = f"{request.origin[0]},{request.origin[1]};{request.destination[0]},{request.destination[1]}"
        mapbox_url = f"{MAPBOX_API_BASE_URL}/directions/v5/mapbox/driving/{coordinates_str}"
        params = {
            "alternatives": "true",
            "geometries": "geojson",
            "language": "en",
            "overview": "full",
            "steps": "true",
            "access_token": MAPBOX_TOKEN
        }
        response = await client.get(mapbox_url, params=params)
        response.raise_for_status()
        mapbox_results = response.json()

    # Assuming you want to return the first route found
    route = mapbox_results["routes"][0] if mapbox_results and "routes" in mapbox_results else None

    return {
        "message": "Directions successful",
        "navigation_count": updated_sub["navigation_count"],
        "route": route
    }