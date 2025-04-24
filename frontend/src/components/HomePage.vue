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
      timer: null,
    };
  },
  methods: {
    async fetchItems() {
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
        const newItems = response.data;
        const currentUUIDs = this.items.map((i) => i.uuid);
        const newUUIDs = newItems.map((i) => i.uuid);

        // Only update if something changed
        if (JSON.stringify(currentUUIDs) !== JSON.stringify(newUUIDs)) {
          this.items = newItems;
        }
      } catch (error) {
        console.error('Failed to fetch items:', error);
      }
    },
  },
  mounted() {
    this.fetchItems();
    this.timer = setInterval(this.fetchItems, 60000); // every 60s
  },
  beforeUnmount() {
    clearInterval(this.timer);
  },
  // async created() {
  //   try {
  //     const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/items`, {
  //       params: {
  //         offset: 0,
  //         limit: 10,
  //       },
  //       headers: {
  //         Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  //       },
  //     });
  //     this.items = response.data;
  //   } catch (error) {
  //     console.log('Error fetching items', error);
  //   }
  // },
};
</script>
