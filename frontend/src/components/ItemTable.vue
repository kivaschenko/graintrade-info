<template>
  <div class="container mt-5">
    <div class="card shadow-graintrade">
      <div class="card-header bg-graintrade-primary text-white">
        <h1 class="mb-0 text-white h4">
          <i class="bi bi-list-ul me-2"></i>
          {{ $t('common_text.offers') }}
        </h1>
      </div>
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-hover mb-0">
            <thead class="table-light">
              <tr>
                <th scope="col" class="fw-semibold">
                  <i class="bi bi-card-text me-1"></i>
                  {{ $t('common_text.title') }}
                </th>
                <th scope="col" class="fw-semibold">
                  <i class="bi bi-tags me-1"></i>
                  {{ $t('create_form.category') }}
                </th>
                <th scope="col" class="fw-semibold">
                  <i class="bi bi-arrow-left-right me-1"></i>
                  {{ $t('common_text.type') }}
                </th>
                <th scope="col" class="text-end fw-semibold">
                  <i class="bi bi-currency-dollar me-1"></i>
                  {{ $t('common_text.price') }}
                </th>
                <th scope="col" class="text-start fw-semibold">{{ $t('common_text.currency') }}</th>
                <th scope="col" class="text-end fw-semibold">
                  <i class="bi bi-box me-1"></i>
                  {{ $t('common_text.amount') }}
                </th>
                <th scope="col" class="text-start fw-semibold">{{ $t('create_form.measure') }}</th>
                <th scope="col" class="text-end fw-semibold">
                  <i class="bi bi-geo-alt me-1"></i>
                  {{ $t('common_text.incoterms') }}
                </th>
                <th scope="col" class="text-end fw-semibold">
                  <i class="bi bi-calendar me-1"></i>
                  {{ $t('common_text.createdAt') }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.id" class="item-row">
                <td class="text-start">
                  <router-link 
                    :to="{ name: 'ItemDetails', params: { id: item.id } }"
                    class="item-title-link fw-semibold"
                  >
                    {{ item.title }}
                  </router-link>
                </td>
                <td class="text-start">
                  <span class="badge bg-light text-dark">
                    {{ $i18n.locale === 'en' ? item.category_name : item.category_ua_name }}
                  </span>
                </td>
                <td>
                  <span class="badge" :class="getOfferTypeBadgeClass(item.offer_type)">
                    {{ $t(`offer_type.${item.offer_type}`) }}
                  </span>
                </td>
                <td class="text-end">
                  <span class="fw-bold text-graintrade-primary">{{ item.price }}</span>
                </td>
                <td class="text-start">
                  <small class="text-muted">{{ $t(`currency.${item.currency}`) }}</small>
                </td>
                <td class="text-end">
                  <span class="fw-semibold">{{ item.amount }}</span>
                </td>
                <td class="text-start">
                  <small class="text-muted">{{ item.measure }}</small>
                </td>
                <td class="text-end">
                  <small>
                    {{ item.terms_delivery }}<br>
                    <span class="text-muted">({{ item.country }} {{ item.region }})</span>
                  </small>
                </td>
                <td class="text-end">
                  <small class="text-muted">
                    {{ new Date(item.created_at).toLocaleDateString() }}
                  </small>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
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
  methods: {
    getOfferTypeBadgeClass(offerType) {
      const classes = {
        'sell': 'bg-success',
        'buy': 'bg-primary',
        'transport': 'bg-info',
        'service': 'bg-warning'
      };
      return classes[offerType] || 'bg-secondary';
    }
  }
};
</script>

<style scoped>
.item-row {
  transition: var(--graintrade-transition);
}

.item-row:hover {
  background-color: rgba(39, 174, 96, 0.05) !important;
}

.item-title-link {
  color: var(--graintrade-primary);
  text-decoration: none;
  font-weight: 600;
  transition: var(--graintrade-transition);
}

.item-title-link:hover {
  color: var(--graintrade-primary-dark);
  text-decoration: underline;
}

.table th {
  background-color: var(--graintrade-bg-alt);
  border-bottom: 2px solid var(--graintrade-border);
  color: var(--graintrade-secondary);
  font-weight: 600;
  padding: 1rem 0.75rem;
}

.table td {
  padding: 1rem 0.75rem;
  vertical-align: middle;
  border-bottom: 1px solid var(--graintrade-border);
}

.badge {
  font-size: 0.75rem;
  padding: 0.4rem 0.6rem;
  border-radius: var(--graintrade-border-radius);
}

.card {
  border: none;
  overflow: hidden;
}

.card-header {
  border-bottom: none;
  padding: 1.5rem;
}

.table-responsive {
  border-radius: 0 0 var(--graintrade-border-radius-large) var(--graintrade-border-radius-large);
}

/* Responsive adjustments */
@media (max-width: 992px) {
  .table th,
  .table td {
    padding: 0.75rem 0.5rem;
    font-size: 0.9rem;
  }
  
  .card-header h1 {
    font-size: 1.25rem;
  }
}

@media (max-width: 768px) {
  .table th,
  .table td {
    padding: 0.5rem 0.25rem;
    font-size: 0.8rem;
  }
  
  .badge {
    font-size: 0.7rem;
    padding: 0.3rem 0.5rem;
  }
  
  .item-title-link {
    font-size: 0.9rem;
  }
  
  .card-header {
    padding: 1rem;
  }
  
  .card-header h1 {
    font-size: 1.1rem;
  }
}

/* Table striping override */
.table-striped > tbody > tr:nth-of-type(odd) > td {
  background-color: rgba(248, 249, 250, 0.8);
}
</style>