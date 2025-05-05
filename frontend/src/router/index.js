import { createRouter, createWebHistory } from 'vue-router';
import Login from '../components/UserLogin.vue';
import ItemForm from '@/components/ItemForm.vue';
import HomePage from '@/components/HomePage.vue';
import ItemListByCategory from '@/components/ItemListByCategory.vue';
import ItemDetails from '@/components/ItemDetails.vue';
import RegistrationForm from '@/components/RegistrationForm.vue';


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
  ];

const router = createRouter({
    history: createWebHistory(),
    routes,
    });

export default router;