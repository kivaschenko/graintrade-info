// PreferencesForm.vue
<template>
	<div class="max-w-md p-4 bg-white shadow rounded">
		<h2 class="text-xl font-bold mb-4">Notification Preferences</h2>

		<label class="block mb-2">
			<input type="checkbox" v-model="notify_new_messages" />
			Notify me about new messages
		</label>

		<label class="block mb-2">
			<input type="checkbox" v-model="notify_new_items" />
			Notify me about new items in categories
		</label>

		<label for="category_idx" class="block mb-2">Interested Categories</label>
		<select
			id="category_idx"
			v-model="selectedCategories"
			class="w-full p-2 border rounded mb-4"
			multiple
			size="5"
		>
		<option v-for="category in categories" :key="category.id" :value="category.name">
			{{ getCategoryName(category) }}
		</option>
	</select>

		<button
			@click="updatePreferences"
			class="bg-blue-600 text-white px-4 py-2 rounded"
		>
			Save
		</button>

		<div v-if="message" class="mt-3 text-green-600">
			{{ message }}
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
		...mapState(['currentLocale']), // Removed 'user' as it's not directly used here anymore
		form() {
			return {
				notify_new_messages: this.notify_new_messages,
				notify_new_items: this.notify_new_items,
				interested_categories: this.selectedCategories,
			};
		},
		extractedCategories() {
			return this.selectedCategories.map(category => {
				const foundCategory = this.categories.find(c => c.name === category);
				return foundCategory ? foundCategory.id : null;
			})
		},
	},
	watch: {
		initialPreferences: {
			handler(newVal) {
				this.notify_new_messages = newVal.notify_new_messages;
				this.notify_new_items = newVal.notify_new_items;
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
				this.$emit('updated'); // Emit an event to notify the parent component
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