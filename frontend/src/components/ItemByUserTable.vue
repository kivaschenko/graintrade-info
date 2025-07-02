<template>
  <div class="container mt-5">
    <h1 class="mb-4">{{ $t( 'common_text.offers' ) }}</h1>
    <table class="table table-striped table-hover">
      <thead>
        <tr>
          <th scope="col" class="text-start">ID</th>
          <th scope="col">{{ $t( 'common_text.title' ) }}</th>
          <th scope="col">{{ $t( 'common_text.type' ) }}</th>
          <th scope="col" class="text-end">{{ $t( 'common_text.price' ) }}</th>
          <th scope="col" class="text-start">{{ $t( 'common_text.currency' ) }}</th>
          <th scope="col" class="text-end">{{ $t( 'common_text.amount' ) }}</th>
          <th scope="col" class="text-start">{{ $t( 'create_form.measure' ) }}</th>
          <th scope="col" class="text-end">{{ $t( 'common_text.incoterms' ) }}</th>
          <th scope="col" class="text-end">{{ $t( 'common_text.createdAt') }}</th>
          <th scope="col" class="text-end">{{ $t( 'common_text.action' ) }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td class="text-start">{{ item.uuid }}</td>
          <th class="text-start">
            <router-link :to="{ name: 'ItemDetails', params: { id: item.id } }">
              {{ item.title }}
            </router-link>
          </th>
          <td>{{ $t(`offer_type.${item.offer_type}`) }}</td>
          <td class="text-end">{{ item.price }} </td>
          <td class="text-start">{{ $t(`currency.${item.currency}`) }}</td>
          <td class="text-end">{{ item.amount }}</td>
          <td class="text-start">{{ item.measure }}</td>
          <td class="text-end">{{ item.terms_delivery }} ({{ item.country }} {{ item.region }})</td>
          <td class="text-end">{{ new Date(item.created_at).toLocaleDateString() }}</td>
          <td class="text-end">
            <!-- <router-link :to="{ name: 'EditItem', params: { id: item.id } }" class="btn btn-primary btn-sm">
              {{ $t( 'common_text.edit' ) }} -->
            <!-- </router-link> -->
            <button class="btn btn-danger btn-sm" @click="deleteItem(item.id)">
              {{ $t( 'common_text.delete' ) }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import axios from 'axios';
export default {
  name: 'ItemTable',
  props: {
    items: {
      type: Array,
      required: true,
    },
  },
  emits: ['delete-item'],
  methods: {
    deleteItem(itemId) {
      if (confirm(this.$t('common_text.confirmDelete'))) {
        axios.delete(`${process.env.VUE_APP_BACKEND_URL}/items/${itemId}`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },  
          })
          .then(() => {
            this.$emit('delete-item', itemId);
            // this.$toast.success(this.$t('common_text.itemDeleted'));
          })
          .catch(error => {
            console.error('Error deleting item:', error);
            // this.$toast.error(this.$t('common_text.itemDeleteError'));
          });
      }
    },
  },
};
</script>
