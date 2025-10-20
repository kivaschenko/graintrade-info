<template>
  <div class="container my-5">
    <h1 class="text-center mb-4 graintrade-title">{{ $t('create_form.form_title') }}</h1>

    <div class="row">
      <!-- Preview Map (Static/Read-only) - Only for Paid Plans -->
      <div class="col-lg-5 mb-4" v-if="hasMapAccess && !isLoadingSubscription">
        <div class="card h-100 graintrade-card">
          <div class="card-header text-center">
            <h2 class="mb-0">{{ $t('create_form.map_preview') || 'Location Preview' }}</h2>
          </div>
          <div class="card-body">
            <div id="map" class="map mb-3"></div>
            <p class="text-muted small text-center">
              <i class="fas fa-info-circle me-1"></i>
              {{ $t('create_form.map_preview_hint') || 'Location will be shown after entering address' }}
            </p>
          </div>
        </div>
      </div>
      
      <!-- Info Card for Free Plan Users -->
      <div class="col-lg-5 mb-4" v-if="!hasMapAccess && !isLoadingSubscription">
        <div class="card h-100 graintrade-card">
          <div class="card-header text-center bg-graintrade-primary text-white">
            <h2 class="mb-0 text-white">
              <i class="fas fa-map-marked-alt me-2"></i>
              {{ $t('create_form.upgrade_for_map') || 'Map Preview' }}
            </h2>
          </div>
          <div class="card-body d-flex flex-column justify-content-center align-items-center text-center">
            <i class="fas fa-lock fa-3x text-muted mb-3"></i>
            <h5 class="mb-3">{{ $t('create_form.map_preview_locked') || 'Map Preview Unavailable' }}</h5>
            <p class="text-muted mb-3">
              {{ $t('create_form.map_preview_locked_description') || 'Upgrade to a paid plan to view location previews on an interactive map.' }}
            </p>
            <p class="text-muted small mb-3">
              <i class="fas fa-check-circle text-success me-1"></i>
              {{ $t('create_form.geocoding_still_works') || 'Location geocoding still works - your address will be converted to coordinates automatically.' }}
            </p>
            <router-link to="/tariffs" class="btn btn-primary">
              <i class="fas fa-crown me-2"></i>
              {{ $t('create_form.view_plans') || 'View Tariff Plans' }}
            </router-link>
          </div>
        </div>
      </div>

      <!-- Form -->
      <div :class="['mb-4', hasMapAccess || isLoadingSubscription ? 'col-lg-7' : 'col-lg-12']">
        <div class="card h-100 graintrade-card">
          <div class="card-header text-center">
            <h2 class="mb-0">{{ $t('create_form.form_title') }}</h2>
          </div>
          <div class="card-body">
            <form @submit.prevent="createItem">
              <div class="mb-3">
                <label for="offer_type" class="form-label">{{ $t('create_form.offer_type') }}</label>
                <select class="form-select" id="offer_type" v-model="offer_type" required>
                  <option value="sell">{{ $t('create_form.sell') }}</option>
                  <option value="buy">{{ $t('create_form.buy') }}</option>
                </select>
              </div>

              <div class="mb-3">
                <label for="category_search" class="form-label">{{ $t('create_form.category') }}</label>
                <div class="autocomplete-container">
                  <input
                    type="text"
                    class="form-control"
                    id="category_search"
                    v-model="categorySearch"
                    @input="handleCategorySearch"
                    @blur="handleCategoryBlur"
                    @keydown="handleKeyDown"
                    :placeholder="$t('create_form.category_placeholder') || 'Type at least 3 characters to search categories...'"
                    autocomplete="off"
                    required
                  />
                  <div 
                    v-if="showCategorySuggestions && filteredCategories.length > 0" 
                    class="autocomplete-suggestions"
                  >
                    <div
                      v-for="(category, index) in filteredCategories"
                      :key="category.id"
                      :class="['autocomplete-item', { 'autocomplete-item-active': index === selectedSuggestionIndex }]"
                      @mousedown="selectCategory(category)"
                      @mouseover="selectedSuggestionIndex = index"
                    >
                      {{ getCategoryName(category) }}
                    </div>
                  </div>
                  <div 
                    v-if="showCategorySuggestions && categorySearch.length >= 3 && filteredCategories.length === 0"
                    class="autocomplete-no-results"
                  >
                    {{ $t('create_form.no_categories_found') || 'No categories found' }}
                  </div>
                </div>
              </div>

              <div class="mb-3">
                <label for="title" class="form-label">{{ $t('common_text.title') }}</label>
                <input type="text" class="form-control" id="title" v-model="title" readonly required>
              </div>

              <div class="mb-3">
                <label for="description" class="form-label">{{ $t('common_text.description') }}</label>
                <textarea
                  type="text"
                  maxlength="300"
                  rows="4"
                  class="form-control"
                  id="description"
                  v-model="description"
                  :placeholder="$t('create_form.description_placeholder')"
                  @input="validateDescription"
                ></textarea>
                <div v-if="descriptionError" class="text-danger mt-1">{{descriptionError}}</div>
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

              <!-- NEW: Address Input (replaces interactive map) -->
              <div class="mb-3">
                <label for="address" class="form-label">
                  <i class="fas fa-map-marker-alt me-1"></i>
                  {{ $t('create_form.address') || 'Address' }}
                  <span v-if="isGeocodingAddress" class="ms-2">
                    <span class="spinner-border spinner-border-sm text-primary" role="status" aria-hidden="true"></span>
                    <small class="text-muted ms-1">{{ $t('create_form.geocoding') || 'Finding location...' }}</small>
                  </span>
                </label>
                <input
                  type="text"
                  class="form-control"
                  id="address"
                  v-model="address"
                  @input="handleAddressInput"
                  :placeholder="$t('create_form.address_placeholder') || 'e.g., Kyiv, Ukraine or вулиця Хрещатик, Київ'"
                  required
                  :disabled="isGeocodingAddress"
                />
                <small class="form-text text-muted">
                  {{ $t('create_form.address_hint') || 'Enter city, region, or full address. Coordinates will be determined automatically.' }}
                </small>
              </div>

              <div class="row mb-3">
                <div class="col-md-6">
                  <label for="country" class="form-label">
                    {{ $t('create_form.country') }}
                    <small v-if="country" class="text-success ms-1">✓</small>
                  </label>
                  <input
                    type="text"
                    class="form-control"
                    id="country"
                    v-model="country"
                    :placeholder="$t('create_form.country_placeholder')"
                    required
                  />
                  <small v-if="country" class="text-muted">
                    <i class="fas fa-info-circle me-1"></i>
                    {{ $t('create_form.auto_filled') || 'Auto-filled from address' }}
                  </small>
                </div>
                <div class="col-md-6">
                  <label for="region" class="form-label">
                    {{ $t('create_form.region') }}
                    <small v-if="region" class="text-success ms-1">✓</small>
                  </label>
                  <input
                    type="text"
                    class="form-control"
                    id="region"
                    v-model="region"
                    :placeholder="$t('create_form.region_placeholder') || 'Optional region'"
                  />
                  <small v-if="region" class="text-muted">
                    <i class="fas fa-info-circle me-1"></i>
                    {{ $t('create_form.auto_filled') || 'Auto-filled from address' }}
                  </small>
                </div>
              </div>

              <!-- Coordinates (hidden/readonly - will be filled by backend) -->
              <div class="row mb-4" v-if="latitude && longitude">
                <div class="col-12">
                  <small class="text-muted">
                    <i class="fas fa-check-circle text-success me-1"></i>
                    {{ $t('create_form.coordinates_found') || 'Coordinates' }}: {{ latitude }}, {{ longitude }}
                  </small>
                </div>
              </div>

              <div class="d-grid gap-2 mb-4">
                <button type="submit" class="btn btn-primary btn-lg graintrade-btn-primary" :disabled="isSubmitting">
                  <span v-if="isSubmitting" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  {{ isSubmitting ? ($t('create_form.submitting') || 'Creating...') : $t('create_form.submit') }}
                </button>
              </div>

              <div v-if="successMessage" class="alert alert-success graintrade-alert-success" role="alert">
                <i class="fas fa-check-circle me-2"></i>{{ successMessage }}
              </div>
              <div v-if="errorMessage" class="alert alert-danger graintrade-alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>{{ errorMessage }}
              </div>

            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import axios from 'axios';
import { mapState } from 'vuex';

export default {
  data() {
    return {
      category_id: null,
      categories: [],
      categorySearch: '',
      filteredCategories: [],
      showCategorySuggestions: false,
      selectedSuggestionIndex: -1,
      title: '',
      description: '',
      price: 0,
      currency: 'UAH',
      amount: 0,
      measure: 'metric ton',
      terms_delivery: 'EXW',
      offer_type: 'sell',
      address: '',  // NEW: User enters address here
      country: '',
      region: '',
      latitude: null,  // Will be set by backend geocoding
      longitude: null,  // Will be set by backend geocoding
      map: null,
      marker: null,
      successMessage: '',
      errorMessage: '',
      descriptionError: '',
      isSubmitting: false,
      addressInputTimeout: null,  // For debouncing address input
      isGeocodingAddress: false,  // Loading state for address geocoding
      userSubscription: null,  // Store user's subscription info
      hasMapAccess: false,  // Whether user has access to Mapbox map
      isLoadingSubscription: true,  // Loading state for subscription check
    };
  },
  computed: {
    ...mapState(['user', 'currentLocale']),
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
    currentLocale() {
      this.title = this.computedTitle;
    },
  },
  async mounted() {
    // Check authentication (should be guaranteed by route guard, but double-check)
    if (!this.$store.state.isAuthenticated || !this.user) {
      this.$router.push('/login');
      return;
    }

    // Fetch user's subscription to determine map access
    await this.fetchUserSubscription();

    // Initialize map only for paid plans
    if (this.hasMapAccess) {
      mapboxgl.accessToken = process.env.VUE_APP_MAPBOX_TOKEN;
      this.map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/streets-v12',
        center: [31.946946, 49.305825], // Ukraine center
        zoom: 5,
        interactive: false, // Static map - no interaction
      });

      window.addEventListener('resize', () => {
        this.map.resize();
      });
    }

    // Fetch categories from the backend
    try {
      const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/categories`);
      this.categories = response.data;
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  },
  methods: {
    async fetchUserSubscription() {
      try {
        this.isLoadingSubscription = true;
        const response = await axios.get(
          `${process.env.VUE_APP_BACKEND_URL}/subscriptions/user/${this.user.id}`,
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('access_token')}`,
            },
          }
        );
        this.userSubscription = response.data;
        
        // Check if user has map access (paid plan)
        // Free plan typically has tarif_id = 1, paid plans have tarif_id > 1
        // Or check by tariff scope/name
        if (this.userSubscription && this.userSubscription.tarif) {
          const tariffScope = this.userSubscription.tarif.scope || '';
          // Only free plan users don't have map access
          // basic, premium, business, etc. all have map access
          this.hasMapAccess = tariffScope !== 'free';
          
          console.log('📊 User subscription:', {
            tariff: this.userSubscription.tarif.name,
            scope: tariffScope,
            hasMapAccess: this.hasMapAccess
          });
        } else {
          // No subscription = free user
          this.hasMapAccess = false;
        }
      } catch (error) {
        console.error('Error fetching subscription:', error);
        // Default to no map access on error
        this.hasMapAccess = false;
      } finally {
        this.isLoadingSubscription = false;
      }
    },

    // Category Autocomplete Methods
    handleCategorySearch() {
      if (this.categorySearch.length >= 3) {
        this.filterCategories();
        this.showCategorySuggestions = true;
        this.selectedSuggestionIndex = -1;
      } else {
        this.showCategorySuggestions = false;
        this.filteredCategories = [];
        this.category_id = null;
      }
    },
    
    filterCategories() {
      const searchTerm = this.categorySearch.toLowerCase();
      this.filteredCategories = this.categories.filter(category => {
        const categoryName = this.getCategoryName(category).toLowerCase();
        return categoryName.includes(searchTerm);
      }).slice(0, 10);
    },
    
    selectCategory(category) {
      this.category_id = category.id;
      this.categorySearch = this.getCategoryName(category);
      this.showCategorySuggestions = false;
      this.selectedSuggestionIndex = -1;
    },
    
    handleCategoryBlur() {
      setTimeout(() => {
        this.showCategorySuggestions = false;
      }, 200);
    },
    
    handleKeyDown(event) {
      if (!this.showCategorySuggestions || this.filteredCategories.length === 0) return;
      
      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          this.selectedSuggestionIndex = Math.min(
            this.selectedSuggestionIndex + 1, 
            this.filteredCategories.length - 1
          );
          break;
        case 'ArrowUp':
          event.preventDefault();
          this.selectedSuggestionIndex = Math.max(this.selectedSuggestionIndex - 1, -1);
          break;
        case 'Enter':
          event.preventDefault();
          if (this.selectedSuggestionIndex >= 0) {
            this.selectCategory(this.filteredCategories[this.selectedSuggestionIndex]);
          }
          break;
        case 'Escape':
          this.showCategorySuggestions = false;
          this.selectedSuggestionIndex = -1;
          break;
      }
    },
    
    handleAddressInput() {
      // Debounce address input to avoid too many API calls
      clearTimeout(this.addressInputTimeout);
      
      // Optional: Show location on map as preview (using free Nominatim)
      // This is optional and only for preview - real geocoding happens on backend
      if (this.address.length > 5) {
        this.addressInputTimeout = setTimeout(() => {
          this.updateMapPreview();
        }, 1000); // Wait 1 second after user stops typing
      } else {
        // Clear fields if address is too short
        this.country = '';
        this.region = '';
        this.latitude = null;
        this.longitude = null;
        
        // Remove marker from map
        if (this.marker) {
          this.marker.remove();
          this.marker = null;
        }
        
        // Reset map to default view
        this.map.flyTo({ center: [31.946946, 49.305825], zoom: 5 });
      }
    },

    async updateMapPreview() {
      // Use free Nominatim for geocoding (for all users)
      // Map display is only for paid users
      this.isGeocodingAddress = true;
      
      try {
        const response = await axios.get(
          `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(this.address)}&format=json&addressdetails=1&limit=1`,
          {
            headers: {
              'User-Agent': 'GrainTrade.info'
            }
          }
        );
        
        if (response.data && response.data.length > 0) {
          const result = response.data[0];
          const { lat, lon, address } = result;
          
          // Update coordinates
          this.latitude = parseFloat(lat);
          this.longitude = parseFloat(lon);
          
          // Extract country and region from address details
          if (address) {
            // Country - always available
            this.country = address.country || '';
            
            // Region - try multiple fields (Nominatim provides different fields for different places)
            this.region = address.state || 
                         address.region || 
                         address.province || 
                         address.county ||
                         address.city ||
                         address.town ||
                         address.village ||
                         '';
            
            console.log('📍 Location found:', {
              country: this.country,
              region: this.region,
              lat: this.latitude,
              lon: this.longitude,
              display_name: result.display_name
            });
          }
          
          // Update map preview ONLY for paid users with map access
          if (this.hasMapAccess && this.map) {
            if (this.marker) {
              this.marker.setLngLat([lon, lat]);
            } else {
              this.marker = new mapboxgl.Marker()
                .setLngLat([lon, lat])
                .addTo(this.map);
            }
            
            this.map.flyTo({ center: [lon, lat], zoom: 7 });
          }
        }
      } catch (error) {
        console.log('Preview geocoding failed (not critical):', error);
        // Clear fields on error
        this.country = '';
        this.region = '';
        this.latitude = null;
        this.longitude = null;
      } finally {
        this.isGeocodingAddress = false;
      }
    },
    
    validateDescription() {
      const scriptPattern = /<script\b[^>]*>(.*?)<\/script>|<img\b[^>]*onerror\b[^>]*>/i;
      if (scriptPattern.test(this.description)) {
        this.descriptionError = this.$t('create_form.validation_xss_description');
      } else { 
        this.descriptionError = '';
      }
    },

    getCategoryName(category) {
      return this.$store.state.currentLocale === 'ua' ? category.ua_name : category.name;
    },

    async createItem() {
      this.successMessage = '';
      this.errorMessage = '';
      this.isSubmitting = true;

      if (this.descriptionError) {
        this.errorMessage = this.$t('create_form.error_validation_failed');
        this.isSubmitting = false;
        return;
      }

      if (!this.$store.state.isAuthenticated) {
        this.errorMessage = this.$t('create_form.error_not_authenticated');
        this.isSubmitting = false;
        return;
      }

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
          address: this.address,  // Send address - backend will geocode
          country: this.country,
          region: this.region,
          latitude: this.latitude,  // Optional - backend will fill if null
          longitude: this.longitude,  // Optional - backend will fill if null
        }, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });

        console.log('Item created:', response.status);
        this.successMessage = this.$t('create_form.success_message') || 'Offer created successfully!';
        
        // Reset form
        setTimeout(() => {
          this.$router.push('/');
        }, 2000);

      } catch (error) {
        console.error(error.response?.status, "<- response.status");
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
        }
        console.error('Error creating offer:', error);
      } finally {
        this.isSubmitting = false;
      }
    }
  },
};
</script>

<style scoped>
/* Existing styles remain the same */
.container {
  max-width: 1200px;
}

.map {
  width: 100%;
  height: 400px;
  border-radius: var(--graintrade-border-radius);
  border: 1px solid var(--graintrade-border);
  overflow: hidden;
  opacity: 0.8; /* Slightly faded to indicate it's preview only */
}

.graintrade-title {
  color: var(--graintrade-secondary);
  font-weight: 700;
  font-size: 2.5rem;
  margin-bottom: 2rem;
}

.graintrade-card {
  border-radius: var(--graintrade-border-radius-large);
  border: none;
  box-shadow: var(--graintrade-shadow);
  transition: var(--graintrade-transition);
  background: var(--graintrade-bg);
}

.graintrade-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--graintrade-shadow-hover);
}

.graintrade-card .card-header {
  background: var(--graintrade-bg-alt);
  border-bottom: 1px solid var(--graintrade-border);
  border-radius: var(--graintrade-border-radius-large) var(--graintrade-border-radius-large) 0 0 !important;
  font-weight: 600;
  color: var(--graintrade-secondary);
  padding: 1.25rem 1.5rem;
}

.graintrade-card .card-body {
  padding: 2rem;
}

.form-label {
  font-weight: 600;
  color: var(--graintrade-secondary);
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
}

.form-control,
.form-select {
  border-radius: var(--graintrade-border-radius);
  border: 1px solid var(--graintrade-border);
  font-family: var(--graintrade-font-family);
  transition: var(--graintrade-transition);
  background-color: var(--graintrade-bg-light);
  padding: 0.75rem 1rem;
  font-size: 0.95rem;
}

.form-control:focus,
.form-select:focus {
  border-color: var(--graintrade-primary);
  box-shadow: 0 0 0 0.2rem rgba(39, 174, 96, 0.25);
  outline: none;
}

.form-control:read-only {
  background-color: var(--graintrade-bg-alt);
  color: var(--graintrade-text-muted);
}

/* Autocomplete Styling */
.autocomplete-container {
  position: relative;
}

.autocomplete-suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--graintrade-bg);
  border: 1px solid var(--graintrade-border);
  border-top: none;
  border-radius: 0 0 var(--graintrade-border-radius) var(--graintrade-border-radius);
  box-shadow: var(--graintrade-shadow);
  z-index: 1000;
  max-height: 250px;
  overflow-y: auto;
}

.autocomplete-item {
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: var(--graintrade-transition);
  border-bottom: 1px solid var(--graintrade-bg-alt);
  font-size: 0.95rem;
}

.autocomplete-item:hover,
.autocomplete-item-active {
  background-color: var(--graintrade-bg-alt);
  color: var(--graintrade-primary);
}

.autocomplete-item:last-child {
  border-bottom: none;
}

.autocomplete-no-results {
  padding: 0.75rem 1rem;
  color: var(--graintrade-text-muted);
  font-style: italic;
  text-align: center;
  background-color: var(--graintrade-bg-alt);
  border-radius: 0 0 var(--graintrade-border-radius) var(--graintrade-border-radius);
}

.autocomplete-container .form-control:focus {
  border-radius: var(--graintrade-border-radius) var(--graintrade-border-radius) 0 0;
}

.graintrade-btn-primary {
  background: var(--graintrade-primary) !important;
  border-color: var(--graintrade-primary) !important;
  color: white !important;
  font-weight: 600;
  padding: 0.875rem 2rem;
  border-radius: var(--graintrade-border-radius);
  transition: var(--graintrade-transition);
  font-size: 1.1rem;
  box-shadow: 0 4px 8px rgba(39, 174, 96, 0.2);
}

.graintrade-btn-primary:hover:not(:disabled),
.graintrade-btn-primary:focus:not(:disabled),
.graintrade-btn-primary:active:not(:disabled) {
  background: var(--graintrade-primary-dark) !important;
  border-color: var(--graintrade-primary-dark) !important;
  color: white !important;
  transform: translateY(-1px);
  box-shadow: 0 6px 12px rgba(39, 174, 96, 0.3);
}

.graintrade-btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.graintrade-alert-success {
  border: none;
  background: linear-gradient(135deg, rgba(39, 174, 96, 0.1), rgba(39, 174, 96, 0.05));
  color: var(--graintrade-primary-dark);
  border-radius: var(--graintrade-border-radius);
  border-left: 4px solid var(--graintrade-primary);
  font-weight: 500;
}

.graintrade-alert-danger {
  border: none;
  background: linear-gradient(135deg, rgba(231, 76, 60, 0.1), rgba(231, 76, 60, 0.05));
  color: var(--graintrade-accent);
  border-radius: var(--graintrade-border-radius);
  border-left: 4px solid var(--graintrade-accent);
  font-weight: 500;
}

.text-danger {
  color: var(--graintrade-accent) !important;
  font-size: 0.875rem;
  font-weight: 500;
}

@media (max-width: 768px) {
  .graintrade-title {
    font-size: 2rem;
  }
  
  .graintrade-card .card-body {
    padding: 1.5rem;
  }
  
  .map {
    height: 300px;
  }
}

@media (max-width: 576px) {
  .graintrade-title {
    font-size: 1.75rem;
  }
  
  .graintrade-card .card-body {
    padding: 1rem;
  }
  
  .graintrade-btn-primary {
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
  }
}
</style>
