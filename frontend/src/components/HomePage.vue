<template>
  <div>
    <ItemTable :items="items" />
    <CategoryCards />
    <FilterItemsForm />
  </div>
</template>

<script>
import publicApi from '@/services/publicApi';
import CategoryCards from './CategoryCards.vue';
import ItemTable from './ItemTable.vue';
// import FilterItemsForm from './FilterItemsForm.vue';

export default {
  name: 'HomePage',
  components: {
    CategoryCards,
    ItemTable,
    // FilterItemsForm,
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
        const response = await publicApi.get('/items', {
          params: {
            offset: 0,
            limit: 10,
          }
        });
        const newItems = response.data;
        console.log(newItems);
        const currentUUIDs = this.items.map((i) => i.uuid);
        const newUUIDs = newItems.map((i) => i.uuid);

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
    this.timer = setInterval(this.fetchItems, 60000);
  },
  beforeUnmount() {
    clearInterval(this.timer);
  },
};
</script>
