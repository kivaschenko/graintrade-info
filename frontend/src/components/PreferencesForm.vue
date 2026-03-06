<template>
	<div class="graintrade-preferences">
		<!-- Toggle button for preferences form -->
		<button
			id="togglePreferencesForm"
			class="graintrade-toggle-btn"
			@click="showForm = !showForm"
		>
			<i class="fas fa-cog me-2"></i>
			{{ showForm ? $t('preferences.hidePreferencesForm') : $t('preferences.showPreferencesForm') }}
		</button>

		<div v-if="showForm" class="graintrade-preferences-card">
			<div class="preferences-header">
				<h4 class="preferences-title">
					<i class="fas fa-bell me-2"></i>
					{{ $t('preferences.notificationPreferencesEdit') }}
				</h4>
			</div>

			<div class="preferences-body">
				
				<!-- Notification Preferences Section -->
				<div class="preferences-section">
					<h5 class="section-title">
						<i class="fas fa-envelope me-2"></i>
						{{ $t('preferences.notificationSettings') || 'Notification Settings' }}
					</h5>
					
					<div class="notification-options">
						<div class="graintrade-checkbox-item">
							<input type="checkbox" class="graintrade-checkbox" id="notifyMessages" v-model="notify_new_messages" />
							<label class="graintrade-checkbox-label" for="notifyMessages">
								<span class="checkbox-custom"></span>
								<span class="checkbox-text">{{ $t('preferences.notifyMeAboutNewMessages') }}</span>
							</label>
						</div>

						<div class="graintrade-checkbox-item">
							<input type="checkbox" class="graintrade-checkbox" id="notifyItems" v-model="notify_new_items" />
							<label class="graintrade-checkbox-label" for="notifyItems">
								<span class="checkbox-custom"></span>
								<span class="checkbox-text">{{ $t('preferences.notifyMeAboutNewItems') }}</span>
							</label>
						</div>
					</div>
				</div>

				<!-- Categories Selection Section -->
				<div class="preferences-section">
					<h5 class="section-title">
						<i class="fas fa-tags me-2"></i>
						{{ $t('preferences.interestedCategories') }}
					</h5>
					<p class="section-description">{{ $t('preferences.helpText') }}</p>
					
					<div class="categories-container">
						<div v-for="(group, parentCategory) in groupedCategories" :key="parentCategory" class="category-group">
							<div class="parent-category-header" @click="toggleParentCategory(parentCategory)">
								<i class="bi bi-grid-3x3-gap me-2"></i>
								<span class="parent-category-name">{{ getParentCategoryName(parentCategory) }}</span>
								<i :class="['fas', 'toggle-icon', expandedParents.includes(parentCategory) ? 'fa-chevron-up' : 'fa-chevron-down']"></i>
							</div>
							
							<div v-show="expandedParents.includes(parentCategory)" class="category-group-content">
								<div class="category-checkboxes">
									<div v-for="category in group" :key="category.id" class="graintrade-checkbox-item">
										<input 
											type="checkbox" 
											class="graintrade-checkbox" 
											:id="`category-${category.id}`" 
											:value="category.name"
											v-model="selectedCategories" 
										/>
										<label class="graintrade-checkbox-label" :for="`category-${category.id}`">
											<span class="checkbox-custom"></span>
											<span class="checkbox-text">{{ getCategoryName(category) }}</span>
										</label>
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- Country Selection Section -->
				<div class="preferences-section">
					<h5 class="section-title">
						<i class="fas fa-globe me-2"></i>
						{{ $t('common_text.country') }}
					</h5>
					<p class="section-description">{{ $t('preferences.selectCountry') }}</p>
					
					<div class="autocomplete-container">
						<input
							type="text"
							class="graintrade-input"
							id="country_search"
							v-model="countrySearch"
							@input="handleCountrySearch"
							@blur="handleCountryBlur"
							@keydown="handleKeyDown"
							:placeholder="$t('preferences.country_placeholder') || 'Type at least 3 characters to search countries...'"
							autocomplete="off"
						/>
						<div 
							v-if="showCountrySuggestions && filteredCountries.length > 0" 
							class="autocomplete-suggestions"
						>
							<div
								v-for="(country, index) in filteredCountries"
								:key="country.value"
								:class="['autocomplete-item', { 'autocomplete-item-active': index === selectedSuggestionIndex }]"
								@mousedown="selectCountry(country)"
								@mouseover="selectedSuggestionIndex = index"
							>
								{{ currentLocale === 'ua' ? country.ua_name : country.name }}
							</div>
						</div>
						<div 
							v-if="showCountrySuggestions && countrySearch.length >= 3 && filteredCountries.length === 0"
							class="autocomplete-no-results"
						>
							{{ $t('preferences.no_countries_found') || 'No countries found' }}
						</div>
					</div>
				</div>

				<!-- Language Selection Section -->
				<div class="preferences-section">
					<h5 class="section-title">
						<i class="fas fa-language me-2"></i>
						{{ $t('preferences.notificationLanguage') }}
					</h5>
					<p class="section-description">{{ $t('preferences.selectNotificationLanguage') }}</p>
					
					<div class="language-toggle">
						<div class="language-option">
							<input
								class="language-radio"
								type="radio"
								id="langEn"
								value="en"
								v-model="notificationLanguage"
							/>
							<label class="language-label" for="langEn">
								<span class="flag-icon">🇺🇸</span>
								<span class="language-text">English</span>
							</label>
						</div>
						<div class="language-option">
							<input
								class="language-radio"
								type="radio"
								id="langUa"
								value="ua"
								v-model="notificationLanguage"
							/>
							<label class="language-label" for="langUa">
								<span class="flag-icon">🇺🇦</span>
								<span class="language-text">Українська</span>
							</label>
						</div>
					</div>
				</div>

				<!-- Action Buttons -->
				<div class="preferences-actions">
					<button
						@click="updatePreferences"
						class="graintrade-btn-primary"
						:disabled="isLoading"
					>
						<i v-if="isLoading" class="fas fa-spinner fa-spin me-2"></i>
						<i v-else class="fas fa-save me-2"></i>
						{{ $t('preferences.savePreferences') }}
					</button>
				</div>

				<!-- Messages -->
				<div v-if="message" :class="['preferences-message', message.includes('successfully') ? 'message-success' : 'message-error']">
					<i :class="['fas', 'me-2', message.includes('successfully') ? 'fa-check-circle' : 'fa-exclamation-triangle']"></i>
					{{ message }}
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import axios from 'axios';
import { mapState } from 'vuex';

export default {
	props: {
		initialPreferences: {
			type: Object,
			default: () => ({
				notify_new_messages: false,
				notify_new_items: false,
				interested_categories: [],
				country: '',
				notification_language: 'en',
			})
		}
	},
	data() {
		return {
			showForm: false,
			notify_new_messages: this.initialPreferences.notify_new_messages,
			notify_new_items: this.initialPreferences.notify_new_items,
			selectedCategories: this.initialPreferences.interested_categories,
			categories: [],
			message: '',
			selectedCountry: this.initialPreferences.country,
			notificationLanguage: this.initialPreferences.notification_language || 'en',
			ua_categories: [],
			isLoading: false,
			expandedParents: [], // Track which parent categories are expanded
			
			// Country autocomplete data
			countrySearch: '',
			filteredCountries: [],
			showCountrySuggestions: false,
			selectedSuggestionIndex: -1,
		};
	},
	computed: {
		...mapState(['currentLocale']),
		form() {
			return {
				notify_new_messages: this.notify_new_messages,
				notify_new_items: this.notify_new_items,
				interested_categories: this.selectedCategories,
				country: this.selectedCountry,
				notificationLanguage: this.notificationLanguage,
			};
		},
		extractedCategories() {
			// Map selected category names back to their IDs for the backend
			return this.selectedCategories.map(categoryName => {
				const foundCategory = this.categories.find(c => c.name === categoryName);
				return foundCategory ? foundCategory.id : null;
			}).filter(id => id !== null); // Filter out any nulls if a category name wasn't found
		},
		groupedCategories() {
			return this.categories.reduce((groups, category) => {
				const parent = category.parent_category || 'Other';
				if (!groups[parent]) {
					groups[parent] = [];
				}
				groups[parent].push(category);
				return groups;
			}, {});
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
		];
		},
	},
	watch: {
		initialPreferences: {
			handler(newVal) {
				this.notify_new_messages = newVal.notify_new_messages;
				this.notify_new_items = newVal.notify_new_items;
				// Ensure selectedCategories are names, as the select component uses names
				this.selectedCategories = newVal.interested_categories;
				this.selectedCountry = newVal.country;
				this.notificationLanguage = newVal.notification_language || 'en';
				this.ua_categories = newVal.ua_interested_categories || [];
			},
			deep: true,
			immediate: true // Run the handler immediately when the component is mounted
		}
	},
	async mounted() {
		// Fetch categories from the backend.
		try {
			const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/categories`);
			this.categories = response.data;
			// Initialize all parent categories as expanded by default
			this.expandedParents = Object.keys(this.groupedCategories);
		} catch (error) {
			console.error('Error fetching categories:', error);
		}
		
		// Initialize country search with selected country
		if (this.selectedCountry) {
			const country = this.countriesList.find(c => c.value === this.selectedCountry);
			if (country) {
				this.countrySearch = this.currentLocale === 'ua' ? country.ua_name : country.name;
			}
		}
	},
	methods: {
		// Country Autocomplete Methods
		handleCountrySearch() {
			if (this.countrySearch.length >= 3) {
				this.filterCountries();
				this.showCountrySuggestions = true;
				this.selectedSuggestionIndex = -1;
			} else {
				this.showCountrySuggestions = false;
				this.filteredCountries = [];
				this.selectedCountry = '';
			}
		},
		
		filterCountries() {
			const searchTerm = this.countrySearch.toLowerCase();
			this.filteredCountries = this.countriesList.filter(country => {
				const countryName = (this.currentLocale === 'ua' ? country.ua_name : country.name).toLowerCase();
				return countryName.includes(searchTerm);
			}).slice(0, 10); // Limit to 10 suggestions
		},
		
		selectCountry(country) {
			this.selectedCountry = country.value;
			this.countrySearch = this.currentLocale === 'ua' ? country.ua_name : country.name;
			this.showCountrySuggestions = false;
			this.selectedSuggestionIndex = -1;
		},
		
		handleCountryBlur() {
			// Delay hiding suggestions to allow for click events
			setTimeout(() => {
				this.showCountrySuggestions = false;
			}, 200);
		},
		
		handleKeyDown(event) {
			if (!this.showCountrySuggestions || this.filteredCountries.length === 0) return;
			
			switch (event.key) {
				case 'ArrowDown':
					event.preventDefault();
					this.selectedSuggestionIndex = Math.min(
						this.selectedSuggestionIndex + 1, 
						this.filteredCountries.length - 1
					);
					break;
				case 'ArrowUp':
					event.preventDefault();
					this.selectedSuggestionIndex = Math.max(this.selectedSuggestionIndex - 1, -1);
					break;
				case 'Enter':
					event.preventDefault();
					if (this.selectedSuggestionIndex >= 0) {
						this.selectCountry(this.filteredCountries[this.selectedSuggestionIndex]);
					}
					break;
				case 'Escape':
					this.showCountrySuggestions = false;
					this.selectedSuggestionIndex = -1;
					break;
			}
		},
		
		// Category Methods
		toggleParentCategory(parentCategory) {
			const index = this.expandedParents.indexOf(parentCategory);
			if (index > -1) {
				this.expandedParents.splice(index, 1);
			} else {
				this.expandedParents.push(parentCategory);
			}
		},
		
		getParentCategoryName(parentCategory) {
			// Translation logic matching exact database parent_category names
			const parentNames = {
				'Grains': this.currentLocale === 'ua' ? 'Зернові' : 'Grains',
				'Oilseeds': this.currentLocale === 'ua' ? 'Олійні' : 'Oilseeds',
				'Oils': this.currentLocale === 'ua' ? 'Олії' : 'Oils',
				'Pulses': this.currentLocale === 'ua' ? 'Бобові' : 'Pulses',
				'Processed products': this.currentLocale === 'ua' ? 'Перероблені продукти' : 'Processed products',
				'Industrial products': this.currentLocale === 'ua' ? 'Промислові продукти' : 'Industrial products',
				'Feed products': this.currentLocale === 'ua' ? 'Кормові продукти' : 'Feed products',
				'Other': this.currentLocale === 'ua' ? 'Інше' : 'Other',
				'Uncategorized': this.currentLocale === 'ua' ? 'Без категорії' : 'Uncategorized',
			};
			return parentNames[parentCategory] || parentCategory;
		},

		async updatePreferences() {
			this.isLoading = true;
			this.message = '';
			
			try {
				const response = await axios.put(
					`${process.env.VUE_APP_BACKEND_URL}/preferences`,
					{
						notify_new_messages: this.notify_new_messages,
						notify_new_items: this.notify_new_items,
						interested_categories: this.selectedCategories,
						country: this.selectedCountry,
						language: this.notificationLanguage,
					},
					{
						headers: {
							Authorization: `Bearer ${localStorage.getItem('access_token')}`,
						},
					}
				);
				console.log("Update response:", response.status);
				this.message = 'Preferences updated successfully!';
				this.$emit('updated'); // Emit an event to notify the parent component to re-fetch preferences
			} catch (error) {
				console.error('Error updating preferences:', error);
				this.message = 'Failed to update preferences.';
			} finally {
				this.isLoading = false;
			}
		},
		getCategoryName(category) {
			return this.$store.state.currentLocale === 'ua' ? category.ua_name : category.name;
		},
	},
}
</script>

<style scoped>
/* GrainTrade PreferencesForm Styles */

.graintrade-preferences {
  margin-top: 2rem;
  margin-bottom: 2rem;
}

/* Toggle Button */
.graintrade-toggle-btn {
  background: var(--graintrade-bg);
  color: var(--graintrade-primary);
  border: 2px solid var(--graintrade-primary);
  padding: 0.75rem 1.5rem;
  border-radius: var(--graintrade-border-radius);
  cursor: pointer;
  transition: var(--graintrade-transition);
  font-weight: 600;
  font-family: var(--graintrade-font-family);
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 200px;
  margin-bottom: 1.5rem;
}

.graintrade-toggle-btn:hover {
  background: var(--graintrade-primary);
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(39, 174, 96, 0.2);
}

/* Main Card */
.graintrade-preferences-card {
  background: var(--graintrade-bg);
  border-radius: var(--graintrade-border-radius-large);
  box-shadow: var(--graintrade-shadow);
  border: 1px solid var(--graintrade-border);
  overflow: hidden;
  transition: var(--graintrade-transition);
  animation: slideInFromTop 0.6s ease-out;
}

.graintrade-preferences-card:hover {
  box-shadow: var(--graintrade-shadow-hover);
}

/* Header */
.preferences-header {
  background: linear-gradient(135deg, var(--graintrade-primary), var(--graintrade-primary-dark));
  color: white;
  padding: 1.5rem 2rem;
}

.preferences-title {
  margin: 0;
  font-weight: 700;
  font-size: 1.5rem;
  font-family: var(--graintrade-font-family);
  display: flex;
  align-items: center;
}

/* Body */
.preferences-body {
  padding: 2rem;
}

/* Sections */
.preferences-section {
  margin-bottom: 2.5rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid var(--graintrade-border);
}

.preferences-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.section-title {
  color: var(--graintrade-secondary);
  font-weight: 600;
  font-size: 1.25rem;
  margin-bottom: 0.75rem;
  font-family: var(--graintrade-font-family);
  display: flex;
  align-items: center;
}

.section-description {
  color: var(--graintrade-text-light);
  font-size: 0.95rem;
  margin-bottom: 1.5rem;
  line-height: 1.5;
}

/* Notification Options */
.notification-options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Custom Checkboxes */
.graintrade-checkbox-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.graintrade-checkbox {
  display: none;
}

.graintrade-checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  font-family: var(--graintrade-font-family);
  font-weight: 500;
  color: var(--graintrade-text);
  transition: var(--graintrade-transition);
  line-height: 1.5;
}

.checkbox-custom {
  width: 20px;
  height: 20px;
  border: 2px solid var(--graintrade-border);
  border-radius: 4px;
  background: var(--graintrade-bg);
  transition: var(--graintrade-transition);
  position: relative;
  flex-shrink: 0;
}

.graintrade-checkbox:checked + .graintrade-checkbox-label .checkbox-custom {
  background: var(--graintrade-primary);
  border-color: var(--graintrade-primary);
}

.graintrade-checkbox:checked + .graintrade-checkbox-label .checkbox-custom::after {
  content: '✓';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-weight: bold;
  font-size: 12px;
}

.graintrade-checkbox-label:hover .checkbox-custom {
  border-color: var(--graintrade-primary);
  box-shadow: 0 0 0 2px rgba(39, 174, 96, 0.1);
}

/* Categories Container */
.categories-container {
  background: var(--graintrade-bg-alt);
  border-radius: var(--graintrade-border-radius);
  border: 1px solid var(--graintrade-border);
  overflow: hidden;
}

.category-group {
  border-bottom: 1px solid var(--graintrade-border);
}

.category-group:last-child {
  border-bottom: none;
}

.parent-category-header {
  background: var(--graintrade-bg);
  padding: 1rem 1.5rem;
  cursor: pointer;
  transition: var(--graintrade-transition);
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: var(--graintrade-secondary);
  font-family: var(--graintrade-font-family);
}

.parent-category-header:hover {
  background: rgba(39, 174, 96, 0.05);
}

.parent-category-name {
  flex: 1;
  margin-left: 0.5rem;
}

.toggle-icon {
  transition: var(--graintrade-transition);
  color: var(--graintrade-primary);
}

.category-group-content {
  padding: 1.5rem;
  background: var(--graintrade-bg-alt);
}

.category-checkboxes {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

/* Country Autocomplete */
.autocomplete-container {
  position: relative;
}

.graintrade-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid var(--graintrade-border);
  border-radius: var(--graintrade-border-radius);
  font-size: 0.95rem;
  color: var(--graintrade-text);
  background-color: var(--graintrade-bg-light);
  font-family: var(--graintrade-font-family);
  transition: var(--graintrade-transition);
}

.graintrade-input:focus {
  border-color: var(--graintrade-primary);
  box-shadow: 0 0 0 0.2rem rgba(39, 174, 96, 0.25);
  outline: none;
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
}

/* Language Toggle */
.language-toggle {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.language-option {
  flex: 1;
  min-width: 150px;
}

.language-radio {
  display: none;
}

.language-label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border: 2px solid var(--graintrade-border);
  border-radius: var(--graintrade-border-radius);
  cursor: pointer;
  transition: var(--graintrade-transition);
  background: var(--graintrade-bg);
  font-family: var(--graintrade-font-family);
  font-weight: 500;
  justify-content: center;
}

.language-radio:checked + .language-label {
  border-color: var(--graintrade-primary);
  background: rgba(39, 174, 96, 0.1);
  color: var(--graintrade-primary);
}

.language-label:hover {
  border-color: var(--graintrade-primary);
  background: rgba(39, 174, 96, 0.05);
}

.flag-icon {
  font-size: 1.25rem;
}

.language-text {
  font-weight: 600;
}

/* Action Buttons */
.preferences-actions {
  margin-top: 2rem;
  display: flex;
  justify-content: center;
}

.graintrade-btn-primary {
  background: linear-gradient(135deg, var(--graintrade-primary), var(--graintrade-primary-dark));
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: var(--graintrade-border-radius);
  font-weight: 600;
  font-size: 1.1rem;
  font-family: var(--graintrade-font-family);
  cursor: pointer;
  transition: var(--graintrade-transition);
  box-shadow: 0 4px 12px rgba(39, 174, 96, 0.3);
  min-width: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.graintrade-btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--graintrade-primary-dark), #1e8449);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(39, 174, 96, 0.4);
}

.graintrade-btn-primary:disabled {
  background: linear-gradient(135deg, rgba(39, 174, 96, 0.6), rgba(39, 174, 96, 0.4));
  cursor: not-allowed;
  opacity: 0.7;
  transform: none;
  box-shadow: none;
}

/* Messages */
.preferences-message {
  margin-top: 1.5rem;
  padding: 1rem 1.5rem;
  border-radius: var(--graintrade-border-radius);
  font-weight: 500;
  font-family: var(--graintrade-font-family);
  display: flex;
  align-items: center;
}

.message-success {
  background: linear-gradient(135deg, rgba(39, 174, 96, 0.1), rgba(39, 174, 96, 0.05));
  color: var(--graintrade-primary-dark);
  border: 1px solid rgba(39, 174, 96, 0.3);
}

.message-error {
  background: linear-gradient(135deg, rgba(231, 76, 60, 0.1), rgba(231, 76, 60, 0.05));
  color: var(--graintrade-accent);
  border: 1px solid rgba(231, 76, 60, 0.3);
}

/* Responsive Design */
@media (max-width: 768px) {
  .preferences-header {
    padding: 1rem 1.5rem;
  }

  .preferences-title {
    font-size: 1.25rem;
  }

  .preferences-body {
    padding: 1.5rem;
  }

  .category-checkboxes {
    grid-template-columns: 1fr;
  }

  .language-toggle {
    flex-direction: column;
  }

  .language-option {
    min-width: unset;
  }

  .graintrade-btn-primary {
    width: 100%;
    min-width: unset;
  }
}

@media (max-width: 576px) {
  .graintrade-toggle-btn {
    width: 100%;
    min-width: unset;
  }

  .preferences-header {
    padding: 1rem;
  }

  .preferences-body {
    padding: 1rem;
  }

  .preferences-section {
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
  }

  .parent-category-header {
    padding: 0.75rem 1rem;
  }

  .category-group-content {
    padding: 1rem;
  }

  .section-title {
    font-size: 1.125rem;
  }
}

/* Animations */
@keyframes slideInFromTop {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.category-group-content {
  animation: fadeInDown 0.3s ease-out;
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Focus States for Accessibility */
.graintrade-toggle-btn:focus-visible,
.graintrade-checkbox:focus-visible + .graintrade-checkbox-label .checkbox-custom,
.graintrade-input:focus-visible,
.language-radio:focus-visible + .language-label,
.graintrade-btn-primary:focus-visible {
  outline: 2px solid var(--graintrade-primary);
  outline-offset: 2px;
}

/* High Contrast Mode Support */
@media (prefers-contrast: high) {
  .graintrade-preferences-card,
  .categories-container,
  .autocomplete-suggestions {
    border-width: 2px;
  }
  
  .graintrade-toggle-btn,
  .graintrade-btn-primary,
  .language-label {
    border-width: 2px;
  }
}
</style>