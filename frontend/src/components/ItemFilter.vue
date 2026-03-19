<template>
  <div class="filters-container">
    <div class="filter-group">
      <label for="category-filter">{{ $t('common_text.category') }}:</label>
      <select id="category-filter" v-model="currentSelectedCategory" @change="applyFilters">
        <option value="">{{ $t('common_text.allCategories') }}</option>
        <option v-for="cat in categories" :key="cat.id" :value="cat.id">
          {{ currentLocale === 'ua' ? cat.ua_name : cat.name }}
        </option>
      </select>
    </div>

    <div class="filter-group offer-type-group">
      <label>{{ $t('common_text.offerType') }}:</label>
      <div>
        <button
          @click="setOfferType('all')"
          :class="{ 'active-filter': currentSelectedOfferType === 'all' }"
        >
          {{ $t('common_text.all') }}
        </button>
        <button
          @click="setOfferType('buy')"
          :class="{ 'active-filter': currentSelectedOfferType === 'buy' }"
        >
          {{ $t('common_text.buy') }}
        </button>
        <button
          @click="setOfferType('sell')"
          :class="{ 'active-filter': currentSelectedOfferType === 'sell' }"
        >
          {{ $t('common_text.sell') }}
        </button>
      </div>
    </div>

    <!-- Price range filter -->
    <div class="filter-group price-group">
      <label>{{ $t('common_text.price') }}:</label>
      <div>
        <input type="number" v-model.number="currentMinPrice" :placeholder="$t('common_text.from')" @input="debounceApplyFilters">
        <span class="price-separator">-</span>
        <input type="number" v-model.number="currentMaxPrice" :placeholder="$t('common_text.to')" @input="debounceApplyFilters">
      </div>
    </div>

    <!-- Currency filter -->
    <div class="filter-group offer-type-group">
      <label>{{ $t('common_text.currency') }}:</label>
      <div>
        <button
          @click="setCurrency('all')"
          :class="{ 'active-filter': currentSelectedCurrency === 'all' }"
        >
          {{ $t('common_text.all') }}
        </button>
        <button
          @click="setCurrency('uah')"
          :class="{ 'active-filter': currentSelectedCurrency === 'uah' }"
        >
          UAH
        </button>
        <button
          @click="setCurrency('usd')"
          :class="{ 'active-filter': currentSelectedCurrency === 'usd' }"
        >
          USD
        </button>
        <button
          @click="setCurrency('eur')"
          :class="{ 'active-filter': currentSelectedCurrency === 'eur' }"
        >
          EUR
        </button>
      </div>
    </div>

    <!-- Country filter -->
    <div class="filter-group country-group">
      <label for="country-filter">{{ $t('common_text.country') }}:</label>
      <select id="country-filter" v-model="currentSelectedCountry" @change="applyFilters">
        <option value="all">{{ $t('common_text.allCountries') }}</option>
        <option
          v-for="country in countriesList"
          :key="country.value"
          :value="country.value"
        >
          {{ currentLocale === 'ua' ? country.ua_name : country.name }}
        </option>
      </select>
    </div>

    <!-- Amount filter -->
    <div class="filter-group price-group">
      <label>{{ $t('common_text.amount') }}:</label>
      <div>
        <input type="number" v-model.number="currentMinAmount" :placeholder="$t('common_text.from')" @input="debounceApplyFilters">
        <span class="price-separator">-</span>
        <input type="number" v-model.number="currentMaxAmount" :placeholder="$t('common_text.to')" @input="debounceApplyFilters">
      </div>
    </div>

    <!-- Measure filter -->
    <div class="filter-group offer-type-group">
      <label>{{ $t('create_form.measure') }}:</label>
      <div>
        <button
          @click="setMeasure('all')"
          :class="{ 'active-filter': currentSelectedMeasure === 'all' }"
        >
          {{ $t('common_text.all') }}
        </button>
        <button
          @click="setMeasure('kg')"
          :class="{ 'active-filter': currentSelectedMeasure === 'kg' }"
        >
          {{ $t('create_form.kg') }}
        </button>
        <button
          @click="setMeasure('liter')"
          :class="{ 'active-filter': currentSelectedMeasure === 'l' }"
        >
          {{ $t('create_form.liter') }}
        </button>
        <button
          @click="setMeasure('metric ton')"
          :class="{ 'active-filter': currentSelectedMeasure === 'metric ton' }"
        >
          {{ $t('create_form.metric_ton') }}
        </button>
      </div>
    </div>

    <!-- Incoterms filter -->
    <div class="filter-group incoterms-group">
      <label for="incoterms-filter">{{ $t('common_text.incoterms') }}:</label>
      <select id="incoterms-filter" v-model="currentSelectedIncoterm" @change="applyFilters">
        <option value="">{{ $t('common_text.allIncoterms') }}</option>
        <option v-for="incoterm in incoterms" :key="incoterm.abbreviation" :value="incoterm.abbreviation">
          {{ incoterm.abbreviation }} - {{ incoterm.description }}
        </option>
      </select>
    </div>

    <div>
    <button class="btn-apply-filters" @click="applyFilters" :disabled="loadingCategories">
      <span v-if="loadingCategories">{{ $t('common_text.loading') }}...</span>
      <span v-else>{{ $t('common_text.applyFilters') }}</span>
    </button>
    <button class="btn-clear-filters" @click="clearFilters">{{ $t('common_text.clearFilters') }}</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { mapState } from 'vuex';

export default {
  name: 'ItemFilter',
  props: {
    // Initial category ID passed from the parent (e.g., ItemListByCategory route param)
    initialCategoryId: {
      type: [String, Number],
      default: ''
    }
  },
  data() {
    return {
      categories: [],
      currentSelectedCategory: this.initialCategoryId,
      currentSelectedOfferType: 'all',
      currentMinPrice: null,
      currentMaxPrice: null,
      currentSelectedCountry: 'all', // Default to 'all' for country filter
      currentSelectedCurrency: 'all', // Default to 'all' for currency filter
      currentSelectedIncoterm: '', // Default to no incoterm selected
      currentMinAmount: null,
      currentMaxAmount: null,
      currentSelectedMeasure: 'all', // Default to 'all' for measure filter
      loadingCategories: false,
      debounceTimeout: null,
    };
  },
  computed: {
    ...mapState(['currentLocale']),
    // Get current filter parameters as a computed property
    currentFilterParams() {
      const params = {};
      if (this.currentSelectedCategory) {
        params.category_id = this.currentSelectedCategory;
      }
      if (this.currentSelectedOfferType !== 'all') {
        params.offer_type = this.currentSelectedOfferType;
      }
      if (this.currentMinPrice !== null && this.currentMinPrice !== '') {
        params.min_price = this.currentMinPrice;
      }
      if (this.currentMaxPrice !== null && this.currentMaxPrice !== '') {
        params.max_price = this.currentMaxPrice;
      }
      if (this.currentSelectedCountry) {
        params.country = this.currentSelectedCountry;
      }
      if (this.currentSelectedCurrency !== 'all') {
        params.currency = this.currentSelectedCurrency;
      }
      if (this.currentSelectedIncoterm) {
        params.incoterm = this.currentSelectedIncoterm;
      }
      if (this.currentMinAmount !== null && this.currentMinAmount !== '') {
        params.min_amount = this.currentMinAmount;
      }
      if (this.currentMaxAmount !== null && this.currentMaxAmount !== '') {
        params.max_amount = this.currentMaxAmount;
      }
      if (this.currentSelectedMeasure !== 'all') {
        params.measure = this.currentSelectedMeasure;
      }
      return params;
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
    countriesList() {
      // Full country list, English and Ukrainian names, value for filter
      return [
        // Major grain exporters/importers and countries with key sea ports
        { name: 'Ukraine', ua_name: 'Україна', value: 'Ukraine' },
        { name: 'United States', ua_name: 'Сполучені Штати', value: 'United States' },
        { name: 'Canada', ua_name: 'Канада', value: 'Canada' },
        { name: 'Brazil', ua_name: 'Бразилія', value: 'Brazil' },
        { name: 'Argentina', ua_name: 'Аргентина', value: 'Argentina' },
        { name: 'France', ua_name: 'Франція', value: 'France' },
        { name: 'Germany', ua_name: 'Німеччина', value: 'Germany' },
        { name: 'Poland', ua_name: 'Польща', value: 'Poland' },
        { name: 'Romania', ua_name: 'Румунія', value: 'Romania' },
        { name: 'Bulgaria', ua_name: 'Болгарія', value: 'Bulgaria' },
        { name: 'Hungary', ua_name: 'Угорщина', value: 'Hungary' },
        { name: 'Turkey', ua_name: 'Туреччина', value: 'Turkey' },
        { name: 'Egypt', ua_name: 'Єгипет', value: 'Egypt' },
        { name: 'China', ua_name: 'Китай', value: 'China' },
        { name: 'India', ua_name: 'Індія', value: 'India' },
        { name: 'Italy', ua_name: 'Італія', value: 'Italy' },
        { name: 'Spain', ua_name: 'Іспанія', value: 'Spain' },
        { name: 'United Kingdom', ua_name: 'Велика Британія', value: 'United Kingdom' },
        { name: 'Netherlands', ua_name: 'Нідерланди', value: 'Netherlands' },
        { name: 'Belgium', ua_name: 'Бельгія', value: 'Belgium' },
        { name: 'Austria', ua_name: 'Австрія', value: 'Austria' },
        { name: 'Switzerland', ua_name: 'Швейцарія', value: 'Switzerland' },
        { name: 'Sweden', ua_name: 'Швеція', value: 'Sweden' },
        { name: 'Norway', ua_name: 'Норвегія', value: 'Norway' },
        { name: 'Denmark', ua_name: 'Данія', value: 'Denmark' },
        { name: 'Finland', ua_name: 'Фінляндія', value: 'Finland' },
        { name: 'Czech Republic', ua_name: 'Чехія', value: 'Czech Republic' },
        { name: 'Slovakia', ua_name: 'Словаччина', value: 'Slovakia' },
        { name: 'Greece', ua_name: 'Греція', value: 'Greece' },
        { name: 'Moldova', ua_name: 'Молдова', value: 'Moldova' },
        { name: 'Lithuania', ua_name: 'Литва', value: 'Lithuania' },
        { name: 'Latvia', ua_name: 'Латвія', value: 'Latvia' },
        { name: 'Estonia', ua_name: 'Естонія', value: 'Estonia' },
        { name: 'Portugal', ua_name: 'Португалія', value: 'Portugal' },
        { name: 'Ireland', ua_name: 'Ірландія', value: 'Ireland' },
        { name: 'Croatia', ua_name: 'Хорватія', value: 'Croatia' },
        { name: 'Serbia', ua_name: 'Сербія', value: 'Serbia' },
        { name: 'Slovenia', ua_name: 'Словенія', value: 'Slovenia' },
        { name: 'Montenegro', ua_name: 'Чорногорія', value: 'Montenegro' },
        { name: 'Bosnia and Herzegovina', ua_name: 'Боснія і Герцеговина', value: 'Bosnia and Herzegovina' },
        { name: 'North Macedonia', ua_name: 'Північна Македонія', value: 'North Macedonia' },
        { name: 'Albania', ua_name: 'Албанія', value: 'Albania' },
        { name: 'Georgia', ua_name: 'Грузія', value: 'Georgia' },
        { name: 'Armenia', ua_name: 'Вірменія', value: 'Armenia' },
        { name: 'Azerbaijan', ua_name: 'Азербайджан', value: 'Azerbaijan' },
        // Major sea port cities (as countries for filter, you may want to add a separate port filter)
        { name: 'Singapore', ua_name: 'Сінгапур', value: 'Singapore' },
        { name: 'United Arab Emirates', ua_name: 'Об\'єднані Арабські Емірати', value: 'United Arab Emirates' },
        { name: 'Saudi Arabia', ua_name: 'Саудівська Аравія', value: 'Saudi Arabia' },
        { name: 'Morocco', ua_name: 'Марокко', value: 'Morocco' },
        { name: 'South Africa', ua_name: 'Південна Африка', value: 'South Africa' },
        { name: 'Australia', ua_name: 'Австралія', value: 'Australia' },
        { name: 'Japan', ua_name: 'Японія', value: 'Japan' },
        { name: 'South Korea', ua_name: 'Південна Корея', value: 'South Korea' },
        // Add more as needed for your market
      ];
    },
  },
  watch: {
    // Watch for changes in initialCategoryId prop to update the internal state
    initialCategoryId(newVal) {
      this.currentSelectedCategory = newVal;
    },
    // Watch for changes in route query parameters and update filters (for map page)
    '$route.query': {
      immediate: true, // Run on component creation
      handler(newQuery) {
        // Only apply if the current page is the map page or if we need to sync filters
        // This is primarily for the AllItemsMap component, which will read query params
        // For ItemListByCategory, the filters are driven by user interaction here.
        if (this.$route.name === 'FilteredItemsMap' || this.$route.name === 'ItemListByCategory' || this.$route.name === 'AllItems') {
          this.currentSelectedCategory = newQuery.category_id || this.$route.params.id || '';
          this.currentSelectedOfferType = newQuery.offer_type || 'all';
          this.currentMinPrice = newQuery.min_price ? parseFloat(newQuery.min_price) : null;
          this.currentMaxPrice = newQuery.max_price ? parseFloat(newQuery.max_price) : null;
          this.currentSelectedCountry = newQuery.country || 'all'; // Set default if not in query
          this.currentSelectedCurrency = newQuery.currency || 'all';
          this.currentMinAmount = newQuery.min_amount ? parseFloat(newQuery.min_amount) : null;
          this.currentMaxAmount = newQuery.max_amount ? parseFloat(newQuery.max_amount) : null;
          this.currentSelectedMeasure = newQuery.measure || 'all'; // Default to 'all' if not specified
          // Handle incoterm filter
          // If incoterm is not in query, default to empty string
          this.currentSelectedIncoterm = newQuery.incoterm || '';
          // Emit the updated filters to the parent component
          this.applyFilters();
        }
      }
    },
    // Watch for route param changes (specifically for category ID in path)
    '$route.params.id': {
      immediate: true,
      handler(newId) {
        if (this.$route.name === 'ItemListByCategory') {
          this.currentSelectedCategory = newId || '';
        }
      }
    }
  },
  async created() {
    await this.fetchCategories();
  },
  methods: {
    async fetchCategories() {
      this.loadingCategories = true;
      try {
        const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/categories`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
        this.categories = response.data;
      } catch (error) {
        console.error('Error fetching categories in ItemFilter:', error);
      } finally {
        this.loadingCategories = false;
      }
    },
    setOfferType(type) {
      this.currentSelectedOfferType = type;
      this.applyFilters();
    },
    setCurrency(currency) {
      this.currentSelectedCurrency = currency;
      this.applyFilters();
    },
    setIncoterm(incoterm) {
      this.currentSelectedIncoterm = incoterm;
      this.applyFilters();
    },
    setMeasure(measure) {
      this.currentSelectedMeasure = measure;
      this.applyFilters();
    },

    // Debounce the applyFilters method to prevent excessive calls
    debounceApplyFilters() {
      clearTimeout(this.debounceTimeout);
      this.debounceTimeout = setTimeout(() => {
        this.applyFilters();
      }, 500); // Debounce for 500ms
    },
    applyFilters() {
      // Emit the current filter parameters to the parent component
      this.$emit('filters-changed', this.currentFilterParams);

      const currentRouteName = this.$route.name;
      const currentRouteParams = { ...this.$route.params }; // Clone existing params
      const currentRouteQuery = { ...this.$route.query }; // Clone existing query

      // Build the base query parameters for the new route
      let newQuery = {
        // Explicitly set filter-related query parameters, using undefined to remove them if "all" or null
        offer_type: this.currentSelectedOfferType === 'all' ? undefined : this.currentSelectedOfferType,
        min_price: this.currentMinPrice === null ? undefined : this.currentMinPrice,
        max_price: this.currentMaxPrice === null ? undefined : this.currentMaxPrice,
        country: this.currentSelectedCountry === '' ? undefined : this.currentSelectedCountry,
        currency: this.currentSelectedCurrency === 'all' ? undefined : this.currentSelectedCurrency,
        min_amount: this.currentMinAmount === null ? undefined : this.currentMinAmount,
        max_amount: this.currentMaxAmount === null ? undefined : this.currentMaxAmount,
        measure: this.currentSelectedMeasure === 'all' ? undefined : this.currentSelectedMeasure,
        incoterm: this.currentSelectedIncoterm === '' ? undefined : this.currentSelectedIncoterm,
      };

      let targetRoute = {};

      // Scenario 1: Current route is category-specific (e.g., /categories/:id/items)
      if (currentRouteName === 'ItemListByCategory') {
        const routeCategoryId = currentRouteParams.id;
        const selectedCategoryId = this.currentSelectedCategory;

        if (selectedCategoryId && String(selectedCategoryId) !== String(routeCategoryId)) {
          // Category changed to a specific one: navigate to new category path
          targetRoute = {
            name: 'ItemListByCategory',
            params: { id: selectedCategoryId },
            query: newQuery // Other filters go into query
          };
        } else if (!selectedCategoryId && routeCategoryId) {
          // Category changed to 'All Categories' from a specific category page
          // Navigate to a general items list. Assuming 'AllItems' route for '/items'.
          // If 'AllItems' doesn't exist, change to 'FilteredItemsMap' or your main items page.
          targetRoute = {
            name: 'AllItems', // Or 'FilteredItemsMap' or your main items page name
            params: {}, // Clear category param
            query: newQuery // Other filters go into query
          };
        } else {
          // Category selected is the same as the route param, or both are 'All'
          // Just update query parameters for the existing route
          targetRoute = {
            name: currentRouteName,
            params: currentRouteParams,
            query: newQuery
          };
        }
      }
      // Scenario 2: Current route is general (e.g., /items or /map)
      else if (currentRouteName === 'AllItems' || currentRouteName === 'FilteredItemsMap') {
        const selectedCategoryId = this.currentSelectedCategory;

        if (selectedCategoryId) {
          // A specific category is selected: navigate to category-specific page
          targetRoute = {
            name: 'ItemListByCategory',
            params: { id: selectedCategoryId },
            query: newQuery
          };
        } else {
          // No specific category selected: remain on general page, update query
          targetRoute = {
            name: currentRouteName,
            query: newQuery
          };
        }
      }
      // Fallback for other routes (e.g., if filter is used on an unrelated page)
      else {
          targetRoute = {
              name: currentRouteName,
              params: currentRouteParams,
              query: { ...currentRouteQuery, ...newQuery } // Merge with existing query
          };
          if (!this.currentSelectedCategory) {
            delete targetRoute.query.category_id; // Remove if 'all'
          }
      }

      // Ensure category_id is not in query if it's already in params (for ItemListByCategory)
      if (targetRoute.name === 'ItemListByCategory' && targetRoute.params.id) {
          delete targetRoute.query.category_id;
      }

      // Clean up undefined values from the query object before pushing
      Object.keys(targetRoute.query).forEach(key => {
        if (targetRoute.query[key] === undefined) {
          delete targetRoute.query[key];
        }
      });

      this.$router.push(targetRoute).catch(err => {
        if (err.name !== 'NavigationDuplicated') {
          console.error("Router push error:", err);
        }
      });
    },
    clearFilters() {
      // Reset all filter data properties to their initial/default values
      this.currentSelectedCategory = this.initialCategoryId;
      this.currentSelectedOfferType = 'all';
      this.currentMinPrice = null;
      this.currentMaxPrice = null;
      this.currentSelectedCountry = 'Ukraine';
      this.currentSelectedCurrency = 'all';
      this.currentMinAmount = null;
      this.currentMaxAmount = null;
      this.currentSelectedMeasure = 'all';
      // Reset incoterm filter
      this.currentSelectedIncoterm = '';
      // Call applyFilters to update the route and emit cleared filters
      this.applyFilters();
    },
  },
};
</script>

<style scoped>
/* GrainTrade ItemFilter Styles */
.filters-container {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  justify-content: center;
  align-items: flex-end;
  width: 100%;
  gap: 1.5rem;
  margin-bottom: 2rem;
  padding: 2rem;
  background: var(--graintrade-bg);
  border-radius: var(--graintrade-border-radius-large);
  box-shadow: var(--graintrade-shadow);
  border: 1px solid var(--graintrade-border);
  transition: var(--graintrade-transition);
}

.filters-container:hover {
  box-shadow: var(--graintrade-shadow-hover);
}

/* Filter Group Styling */
.filter-group {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-width: 140px;
}

.filter-group label {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--graintrade-secondary);
  margin-bottom: 0.5rem;
  font-family: var(--graintrade-font-family);
}

/* Form Controls */
.filters-container select,
.filters-container input[type="number"] {
  padding: 0.75rem 1rem;
  border: 1px solid var(--graintrade-border);
  border-radius: var(--graintrade-border-radius);
  font-size: 0.95rem;
  color: var(--graintrade-text);
  background-color: var(--graintrade-bg-light);
  font-family: var(--graintrade-font-family);
  transition: var(--graintrade-transition);
  min-width: 140px;
}

.filters-container select:focus,
.filters-container input[type="number"]:focus {
  border-color: var(--graintrade-primary);
  box-shadow: 0 0 0 0.2rem rgba(39, 174, 96, 0.25);
  outline: none;
  background-color: var(--graintrade-bg);
}

.filters-container select:hover,
.filters-container input[type="number"]:hover {
  border-color: var(--graintrade-primary);
}

/* Button Groups */
.offer-type-group,
.incoterms-group {
  flex-direction: column;
  align-items: flex-start;
}

.offer-type-group button {
  padding: 0.625rem 1rem;
  border: 1px solid var(--graintrade-border);
  background-color: var(--graintrade-bg);
  color: var(--graintrade-text);
  border-radius: var(--graintrade-border-radius);
  cursor: pointer;
  transition: var(--graintrade-transition);
  font-weight: 500;
  font-size: 0.9rem;
  margin-right: 0.5rem;
  margin-bottom: 0.25rem;
  font-family: var(--graintrade-font-family);
  min-width: 80px;
}

.offer-type-group button:last-child {
  margin-right: 0;
}

.offer-type-group button.active-filter {
  background-color: var(--graintrade-primary);
  color: white;
  border-color: var(--graintrade-primary);
  box-shadow: 0 2px 8px rgba(39, 174, 96, 0.25);
}

.offer-type-group button:hover:not(.active-filter) {
  background-color: rgba(39, 174, 96, 0.1);
  border-color: var(--graintrade-primary);
  color: var(--graintrade-primary);
}

.offer-type-group button.active-filter:hover {
  background-color: var(--graintrade-primary-dark);
  border-color: var(--graintrade-primary-dark);
}

/* Price and Amount Groups */
.price-group {
  flex-direction: column;
  align-items: flex-start;
  gap: 0.5rem;
}

.price-group > div {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.price-group input {
  width: 100px;
  min-width: 100px;
}

.price-separator {
  font-size: 1.1rem;
  color: var(--graintrade-text-muted);
  font-weight: 500;
  padding: 0 0.25rem;
}

/* Country and Category Groups */
.country-group,
.category-group {
  min-width: 180px;
}

.country-group select,
.category-group select,
.incoterms-group select {
  min-width: 180px;
}

/* Action Buttons */
.btn-apply-filters,
.btn-clear-filters {
  padding: 0.75rem 1.5rem;
  border-radius: var(--graintrade-border-radius);
  cursor: pointer;
  font-weight: 600;
  font-size: 0.95rem;
  transition: var(--graintrade-transition);
  min-width: 140px;
  align-self: center;
  margin: 0.25rem;
  font-family: var(--graintrade-font-family);
  border: none;
}

.btn-apply-filters {
  background: var(--graintrade-primary);
  color: white;
  box-shadow: 0 4px 8px rgba(39, 174, 96, 0.2);
}

.btn-apply-filters:hover:not(:disabled) {
  background: var(--graintrade-primary-dark);
  transform: translateY(-1px);
  box-shadow: 0 6px 12px rgba(39, 174, 96, 0.3);
}

.btn-apply-filters:disabled {
  background: rgba(39, 174, 96, 0.6);
  cursor: not-allowed;
  opacity: 0.8;
  transform: none;
  box-shadow: none;
}

.btn-clear-filters {
  background: var(--graintrade-accent);
  color: white;
  box-shadow: 0 4px 8px rgba(231, 76, 60, 0.2);
}

.btn-clear-filters:hover {
  background: #c0392b;
  transform: translateY(-1px);
  box-shadow: 0 6px 12px rgba(231, 76, 60, 0.3);
}

/* Responsive Design */
@media (max-width: 1200px) {
  .filters-container {
    gap: 1rem;
    padding: 1.5rem;
  }
}

@media (max-width: 768px) {
  .filters-container {
    flex-direction: column;
    align-items: stretch;
    padding: 1.5rem;
    gap: 1rem;
  }

  .filter-group {
    width: 100%;
    min-width: unset;
  }

  .filters-container select,
  .filters-container input[type="number"] {
    width: 100%;
    min-width: unset;
  }

  .offer-type-group {
    width: 100%;
  }

  .offer-type-group > div {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    width: 100%;
  }

  .offer-type-group button {
    flex: 1;
    margin-right: 0;
    margin-bottom: 0;
    min-width: unset;
  }

  .price-group {
    width: 100%;
  }

  .price-group > div {
    width: 100%;
    justify-content: space-between;
  }

  .price-group input {
    flex: 1;
    width: auto;
    min-width: 80px;
  }

  .btn-apply-filters,
  .btn-clear-filters {
    width: 100%;
    min-width: unset;
    margin: 0.25rem 0;
  }
}

@media (max-width: 576px) {
  .filters-container {
    padding: 1rem;
    margin-bottom: 1.5rem;
  }

  .filter-group label {
    font-size: 0.9rem;
  }

  .filters-container select,
  .filters-container input[type="number"],
  .offer-type-group button {
    padding: 0.625rem 0.75rem;
    font-size: 0.9rem;
  }

  .btn-apply-filters,
  .btn-clear-filters {
    padding: 0.75rem 1rem;
    font-size: 0.9rem;
  }
}

/* Loading State */
.filters-container[data-loading="true"] {
  opacity: 0.7;
  pointer-events: none;
}

/* Focus Styles for Accessibility */
.filters-container select:focus-visible,
.filters-container input[type="number"]:focus-visible,
.offer-type-group button:focus-visible,
.btn-apply-filters:focus-visible,
.btn-clear-filters:focus-visible {
  outline: 2px solid var(--graintrade-primary);
  outline-offset: 2px;
}

/* Enhanced Visual Hierarchy */
.filter-group:first-child {
  margin-left: 0;
}

.filter-group:last-child {
  margin-right: 0;
}

/* Improved Button Group Layout */
.offer-type-group > div {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

/* Price Range Styling */
.price-group > div {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
}
</style>
