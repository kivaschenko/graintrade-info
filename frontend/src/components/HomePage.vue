<template>
  <div>
    <ItemTable :items="items" />
    <CategoryCards />
   </div>
</template>

<script>
import axios from 'axios';
import CategoryCards from './CategoryCards.vue';
import ItemTable from './ItemTable.vue';

export default {
  name: 'HomePage',
  components: {
    CategoryCards,
    ItemTable,
  },
  data() {
    return {
      items: [],
    };
  },
  async created() {
    try {
      const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/items`, {
        params: {
          offset: 0,
          limit: 10,
        },
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      this.items = response.data;
    } catch (error) {
      console.log('Error fetching items', error);
    }
  },
};
</script>
