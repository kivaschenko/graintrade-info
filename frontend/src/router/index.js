import { createRouter, createWebHistory } from 'vue-router';
import Login from '../components/UserLogin.vue';
import ItemForm from '@/components/ItemForm.vue';
import HomePage from '@/components/HomePage.vue';
import ItemListByCategory from '@/components/ItemListByCategory.vue';
import ItemDetails from '@/components/ItemDetails.vue';
import RegistrationForm from '@/components/RegistrationForm.vue';
import UserProfile from '@/components/UserProfile.vue';


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
      path: '/categories/:id',
      name: 'Category',
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
      name: 'Tariffs',
      component: () => import('@/components/TariffPlans.vue'),
      meta: {
        requiresAuth: true,
      },
    },
    {

    }
  ];

const router = createRouter({
    history: createWebHistory(),
    routes,
    });

export default router;