<template>
	<div class="card shadow-sm border-0 custom-card-nested mt-4">
		<div class="card-body">
			<h4 class="card-title text-primary mb-3">Notification Preferences Edit</h4>

			<div class="mb-3 form-check">
				<input type="checkbox" class="form-check-input" id="notifyMessages" v-model="notify_new_messages" />
				<label class="form-check-label" for="notifyMessages">Notify me about new messages</label>
			</div>

			<div class="mb-3 form-check">
				<input type="checkbox" class="form-check-input" id="notifyItems" v-model="notify_new_items" />
				<label class="form-check-label" for="notifyItems">Notify me about new items in categories</label>
			</div>

			<div class="mb-3">
				<label for="category_idx" class="form-label">Interested Categories</label>
				<select
					id="category_idx"
					v-model="selectedCategories"
					class="form-select"
					multiple
					size="6"
					aria-label="Select categories of interest"
					help-text="Select categories you are interested in for notifications with Ctrl/Cmd + Click"
				>
					<option v-for="category in categories" :key="category.id" :value="category.name">
						{{ getCategoryName(category) }}
					</option>
				</select>
			</div>

			<button
				@click="updatePreferences"
				class="btn btn-primary"
			>
				Save Preferences
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
				interested_categories: []
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
		};
	},
	computed: {
		...mapState(['currentLocale']),
		form() {
			return {
				notify_new_messages: this.notify_new_messages,
				notify_new_items: this.notify_new_items,
				interested_categories: this.selectedCategories,
			};
		},
		extractedCategories() {
			// Map selected category names back to their IDs for the backend
			return this.selectedCategories.map(categoryName => {
				const foundCategory = this.categories.find(c => c.name === categoryName);
				return foundCategory ? foundCategory.id : null;
			}).filter(id => id !== null); // Filter out any nulls if a category name wasn't found
		},
	},
	watch: {
		initialPreferences: {
			handler(newVal) {
				this.notify_new_messages = newVal.notify_new_messages;
				this.notify_new_items = newVal.notify_new_items;
				// Ensure selectedCategories are names, as the select component uses names
				this.selectedCategories = newVal.interested_categories;
			},
			deep: true,
			immediate: true // Run the handler immediately when the component is mounted
		}
	},
	async mounted() {
		// Fetch categories from the backend.
		try {
			const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/categories`);
			console.log("Categories response:", response);
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
					},
					{
						headers: {
							Authorization: `Bearer ${localStorage.getItem('access_token')}`,
						},
					}
				);
				console.log("Update response:", response.status, response.data);
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