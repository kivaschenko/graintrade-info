<template>
	<div class="card shadow-sm border-0 custom-card-nested mt-4">
		<div class="card-body">
			<h4 class="card-title text-primary mb-3">{{ $t('preferences.notificationPreferencesEdit') }}</h4>
			
			<!-- Notification preferences -->
			<div class="mb-3 form-check">
				<input type="checkbox" class="form-check-input" id="notifyMessages" v-model="notify_new_messages" />
				<label class="form-check-label" for="notifyMessages">{{ $t('preferences.notifyMeAboutNewMessages') }}</label>
			</div>

			<!-- New items notification -->
			<div class="mb-3 form-check">
				<input type="checkbox" class="form-check-input" id="notifyItems" v-model="notify_new_items" />
				<label class="form-check-label" for="notifyItems">{{ $t('preferences.notifyMeAboutNewItems') }}</label>
			</div>

			<!-- Categories selection -->
			<div class="mb-3">
				<label for="category_idx" class="form-label">{{ $t('preferences.interestedCategories') }}</label>
				<select
					id="category_idx"
					v-model="selectedCategories"
					class="form-select"
					multiple
					size="6"
				>
					<option v-for="category in categories" :key="category.id" :value="category.name">
						{{ getCategoryName(category) }}
					</option>
				</select>
				<small class="form-text text-muted">{{ $t('preferences.helpText') }}</small>
			</div>

			<!-- Country selection -->
			<div class="mb-3">
				<label for="country" class="form-label">{{ $t('common_text.country') }}</label>
				<select
					id="country"
					v-model="selectedCountry"
					class="form-select"
				>
					<option v-for="country in countriesList" :key="country.value" :value="country.value">
						{{ currentLocale === 'ua' ? country.ua_name : country.name }}
					</option>
				</select>
				<small class="form-text text-muted">{{ $t('preferences.selectCountry') }}</small>
			</div>

			<!-- Save button -->
			<button
				@click="updatePreferences"
				class="btn btn-primary"
			>
				{{ $t('preferences.savePreferences') }}
			</button>

			<div v-if="message" :class="['mt-3', message.includes('successfully') ? 'alert alert-success' : 'alert alert-danger']" role="alert">
				{{ message }}
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
				country: ''
			})
		}
	},
	data() {
		return {
			notify_new_messages: this.initialPreferences.notify_new_messages,
			notify_new_items: this.initialPreferences.notify_new_items,
			selectedCategories: this.initialPreferences.interested_categories,
			categories: [],
			message: '',
			selectedCountry: this.initialPreferences.country,
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
			};
		},
		extractedCategories() {
			// Map selected category names back to their IDs for the backend
			return this.selectedCategories.map(categoryName => {
				const foundCategory = this.categories.find(c => c.name === categoryName);
				return foundCategory ? foundCategory.id : null;
			}).filter(id => id !== null); // Filter out any nulls if a category name wasn't found
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
		} catch (error) {
			console.error('Error fetching categories:', error);
		}
	},
	methods: {
		async updatePreferences() {
			try {
				const response = await axios.put(
					`${process.env.VUE_APP_BACKEND_URL}/preferences`,
					{
						notify_new_messages: this.notify_new_messages,
						notify_new_items: this.notify_new_items,
						interested_categories: this.selectedCategories,
						country: this.selectedCountry,
					},
					{
						headers: {
							Authorization: `Bearer ${localStorage.getItem('access_token')}`,
						},
					}
				);
				this.message = 'Preferences updated successfully!';
				this.$emit('updated'); // Emit an event to notify the parent component to re-fetch preferences
			} catch (error) {
				console.error('Error updating preferences:', error);
				this.message = 'Failed to update preferences.';
			}
		},
		getCategoryName(category) {
			return this.$store.state.currentLocale === 'ua' ? category.ua_name : category.name;
		},
	},
}
</script>

<style scoped>
/* Inherit custom-card-nested styling from UserProfile for consistency */
.custom-card-nested {
    background-color: #fcfdff;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
}

.custom-card-nested:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 15px rgba(0, 0, 0, 0.1);
}

.card-title {
  font-weight: 600;
  margin-bottom: 1.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  color: #007bff;
}

.form-check-input:checked {
    background-color: #007bff;
    border-color: #007bff;
}

.form-select:focus {
    border-color: #80bdff;
    box-shadow: 0 0 0 0.25rem rgba(0, 123, 255, 0.25);
}

.btn-primary {
    background-color: #007bff;
    border-color: #007bff;
    font-weight: 600;
}

.btn-primary:hover {
    background-color: #0056b3;
    border-color: #0056b3;
}

.alert-success {
    color: #155724;
    background-color: #d4edda;
    border-color: #c3e6cb;
}

.alert-danger {
    color: #721c24;
    background-color: #f8d7da;
    border-color: #f5c6cb;
}
</style>