import { createRouter, createWebHistory } from 'vue-router';
import Login from '../components/UserLogin.vue';
import ItemForm from '@/components/ItemForm.vue';
import HomePage from '@/components/HomePage.vue';
import ItemListByCategory from '@/components/ItemListByCategory.vue';
import ItemDetails from '@/components/ItemDetails.vue';
import RegistrationForm from '@/components/RegistrationForm.vue';
import UserProfile from '@/components/UserProfile.vue';
import TariffPlans from '@/components/TariffPlans.vue';
import PasswordRecovery from '@/components/PasswordRecovery.vue';
import AllItemsMap from '../components/AllItemsMap.vue';
import PublicProfile from '@/components/PublicProfile.vue';
import ContactsRequisites from '@/components/ContactsRequisites.vue';
import CryptoCheckout from '@/components/CryptoCheckout.vue';
import AboutUs from '@/components/AboutUs.vue';
import SubscriptionCheckout from '@/components/SubscriptionCheckout.vue';

const routes = [
  {
    path: '/',
    name: 'HomePage',
    component: HomePage,
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
  },
  {
    path: '/register',
    name: 'Register',
    component: RegistrationForm,
  },
  {
    path: '/items/new',
    name: 'ItemForm',
    component: ItemForm,
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: '/categories/:id/items',
    name: 'ItemListByCategory',
    component: ItemListByCategory,
  },
  {
    path: '/items/:id',
    name: 'ItemDetails',
    component: ItemDetails,
  },
  {
    path: '/profile',
    name: 'UserProfile',
    component: UserProfile,
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: '/tariffs',
    name: 'TariffPlans',
    component: TariffPlans,
  },
  {
    path: '/reset-password',
    name: 'PasswordRecovery',
    component: PasswordRecovery,
  },
  {
    path: '/map/all-items',
    name: 'AllItemsMap',
    component: AllItemsMap,
    meta: { requiresAuth: true, scope: 'view:map' }
  },
  {
    path: '/map/filtered-items',
    name: 'FilteredItemsMap',
    component: AllItemsMap, // Reusing AllItemsMap for filtered items
    meta: { requiresAuth: true, scope: 'view:map' },
    props: (route) => ({ // Дозволяє передавати query params як пропси
      category_id: route.query.category_id,
      offer_type: route.query.offer_type,
      min_price: route.query.min_price,
      max_price: route.query.max_price,
      currency: route.query.currency,
      country: route.query.country,
      incoterms: route.query.incoterms,
    })
  },
  {
    path: '/public-profile/:id',
    name: 'PublicProfile',
    component: PublicProfile,
    meta: { requiresAuth: true },
  },
  {
    path: '/privacy-policy',
    name: 'PrivacyPolicy',
    component: () => import('@/components/PrivacyPolicy.vue'), // Lazy loading
  },
  {
    path: '/terms-of-service',
    name: 'TermsOfService',
    component: () => import('@/components/TermsOfService.vue'), // Lazy loading
  },
  {
    path: '/contacts-requisites',
    name: 'ContactsRequisites',
    component: ContactsRequisites,
  },
  {
    path: '/crypto-checkout',
    name: 'CryptoCheckout',
    component: CryptoCheckout,
  },
  {
    path: '/about-us',
    name: 'AboutUs',
    component: AboutUs,
  },
  {
    path: '/subscription-checkout',
    name: 'SubscriptionCheckout',
    component: SubscriptionCheckout,
  }
];
const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Navigation guard to check authentication
router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('access_token');

  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!isAuthenticated) {
      // Redirect to login page with the intended destination
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      });
    } else {
      next();
    }
  } else {
    next();
  }
});

export default router;
