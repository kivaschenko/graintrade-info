<template>
  <div class="container mt-5">
    <h1 class="mb-4">{{ $t( 'common_text.offers' ) }}</h1>
    <table class="table table-striped table-hover">
      <thead>
        <tr>
          <th scope="col">{{ $t( 'common_text.title' ) }}</th>
          <th scope="col">{{ $t( 'common_text.type' ) }}</th>
          <th scope="col" class="text-end">{{ $t( 'common_text.price' ) }}</th>
          <th scope="col" class="text-start">{{ $t( 'common_text.currency' ) }}</th>
          <th scope="col" class="text-end">{{ $t( 'common_text.amount' ) }}</th>
          <th scope="col" class="text-start">{{ $t( 'create_form.measure' ) }}</th>
          <th scope="col" class="text-end">{{ $t( 'common_text.incoterms' ) }}</th>
          <th scope="col" class="text-end">{{ $t( 'common_text.createdAt') }}</th>
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
          <td class="text-end">{{ item.price }} </td>
          <td class="text-start">{{ $t(`currency.${item.currency}`) }}</td>
          <td class="text-end">{{ item.amount }}</td>
          <td class="text-start">{{ item.measure }}</td>
          <td class="text-end">{{ item.terms_delivery }} ({{ item.country }} {{ item.region }})</td>
          <td class="text-end">{{ new Date(item.created_at).toLocaleDateString() }}</td>
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