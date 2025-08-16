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
    },
    {
      path: '/categories/:id/items',
      name: 'ItemListByCategory',
      component: ItemListByCategory,
    },
    { path: '/items/:id',
      name: 'ItemDetails',
      component: ItemDetails,
    },
    { path: '/profile',
      name: 'UserProfile',
      component: UserProfile,
      meta: {
        requiresAuth: true,
      },
    },
    { path: '/tariffs',
      name: 'TariffPlans',
      component: TariffPlans,
      meta: {
        requiresAuth: true,
      },
    },
    { path: '/reset-password',
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
    },
    {
      path: '/privacy-policy',
      name: 'PrivacyPolicy',
      component: () => import('@/components/PrivacyPolicy.vue'), // Lazy loading
    }
  ];
const router = createRouter({
    history: createWebHistory(),
    routes,
    });

export default router;
