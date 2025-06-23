<template>
  <div class="container mt-5">
    <h1 class="mb-4">{{ $t( 'common_text.offers' ) }}</h1>
    <table class="table table-striped table-hover">
      <thead>
        <tr>
          <th scope="col">{{ $t( 'common_text.title' ) }}</th>
          <th scope="col">{{ $t( 'common_text.type' ) }}</th>
          <th scope="col" class="text-end">{{ $t( 'common_text.price' ) }}</th>
          <th scope="col" class="text-end">{{ $t( 'common_text.amount' ) }}</th>
          <th scope="col" class="text-end">{{ $t( 'common_text.incoterms' ) }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <th class="text-start">
            <router-link :to="{ name: 'ItemDetails', params: { id: item.id } }">
              {{ item.title }}
            </router-link>
          </th>
          <td>{{ $t(`offer_type.${item.offer_type}`) }}</td>
          <td class="text-end">{{ item.price }} {{ $t(`currency.${item.currency}`) }}</td>
          <td class="text-end">{{ item.amount }} {{ item.measure }}</td>
          <td class="text-end">{{ item.terms_delivery }} ({{ item.country }} {{ item.region }})</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  name: 'ItemTable',
  props: {
    items: {
      type: Array,
      required: true,
    },
  },
};
</script>