<template>
  <div class="container">
		<footer class="py-3 my-4">
			<ul class="nav justify-content-center border-bottom pb-3 mb-3">
				<li class="nav-item"><a href="#" class="nav-link px-2 text-muted">{{ $t('footer.contact') }}</a></li>
				<li class="nav-item">
					<router-link class="nav-link px-2 text-muted" to="/privacy-policy">{{ $t('footer.privacyPolicy') }}</router-link>
				</li>
				<li class="nav-item">
					<router-link class="nav-link px-2 text-muted" to="/terms-of-service">{{ $t('footer.termsOfService') }}</router-link>
				</li>
				<li class="nav-item">
					<router-link class="nav-link px-2 text-muted" to="/tariffs">{{ $t('footer.pricing') }}</router-link>
				</li>
				<li class="nav-item"><a href="#" class="nav-link px-2 text-muted">{{ $t('footer.faqs') }}</a></li>
				<li class="nav-item"><a href="#" class="nav-link px-2 text-muted">{{ $t('footer.about') }}</a></li>
			</ul>
			<p class="text-center text-muted">&copy; 2025 Graintraide.Info</p>
		</footer>
	</div>
</template>

<script>
import { mapState } from 'vuex';

export default {
	name: 'FooterPage',
	data() {
		return {
			selectedLocale: this.$store.state.currentLocale, // Initialize with current locale
		};
	},
	computed: {
		...mapState(['isAuthenticated', 'currentLocale']),
	},
	methods: {
		changeLocale() {
			this.$store.commit('setLocale', this.selectedLocale); // Commit the new locale to the store
			this.$i18n.locale = this.selectedLocale; // Update i18n locale
		},
	},
};
</script>

<style scoped>
footer {
	background-color: #f8f9fa;
	color: #6c757d;
}
.nav-link {
	color: #6c757d;
}
.nav-link:hover {
	color: #495057;
}
</style>