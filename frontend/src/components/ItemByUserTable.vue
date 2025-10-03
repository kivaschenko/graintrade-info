<template>
  <div class="container mt-5">
    <div class="card shadow-graintrade">
      <div class="card-header bg-graintrade-secondary text-white">
        <h2 class="mb-0 text-white h4">
          <i class="bi bi-person-circle me-2"></i>
          {{ $t('common_text.myOffers') || 'My Offers' }}
        </h2>
      </div>
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-hover mb-0">
            <thead class="table-light">
              <tr>
                <th scope="col" class="text-start fw-semibold">ID</th>
                <th scope="col" class="fw-semibold">
                  <i class="bi bi-card-text me-1"></i>
                  {{ $t('common_text.title') }}
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
                <th scope="col" class="text-end fw-semibold">
                  <i class="bi bi-chat-dots me-1"></i>
                  {{ $t('common_text.messagesCounter') }}
                </th>
                <th scope="col" class="text-end fw-semibold">
                  <i class="bi bi-gear me-1"></i>
                  {{ $t('common_text.action') }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.id" class="item-row">
                <td class="text-start">
                  <span class="badge bg-graintrade-primary text-white">#{{ item.id }}</span>
                </td>
                <td class="text-start">
                  <router-link 
                    :to="{ name: 'ItemDetails', params: { id: item.id } }"
                    class="item-title-link fw-semibold"
                  >
                    {{ item.title }}
                  </router-link>
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
                <td class="text-end">
                  <span class="badge bg-light text-dark">
                    <i class="bi bi-chat-dots me-1"></i>
                    {{ item.messages_counter }}
                  </span>
                </td>
                <td class="text-end">
                  <button 
                    class="btn btn-sm btn-outline-secondary" 
                    @click="deleteItem(item.id)"
                    :title="$t('common_text.delete')"
                  >
                    <i class="bi bi-trash me-1"></i>
                    {{ $t('common_text.delete') }}
                  </button>
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
import axios from 'axios';
export default {
  name: 'ItemByUserTable',
  props: {
    items: {
      type: Array,
      required: true,
    },
  },
  emits: ['delete-item'],
  methods: {
    getOfferTypeBadgeClass(offerType) {
      const classes = {
        'sell': 'bg-success',
        'buy': 'bg-primary',
        'transport': 'bg-info',
        'service': 'bg-warning'
      };
      return classes[offerType] || 'bg-secondary';
    },
    deleteItem(itemId) {
      if (confirm(this.$t('common_text.confirmDelete'))) {
        axios.delete(`${process.env.VUE_APP_BACKEND_URL}/items/${itemId}`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },  
          })
          .then(() => {
            this.$emit('delete-item', itemId);
          })
          .catch(error => {
            console.error('Error deleting item:', error);
          });
      }
    },
  },
};
</script>

<style scoped>
.item-row {
  transition: var(--graintrade-transition);
}

.item-row:hover {
  background-color: rgba(44, 62, 80, 0.05) !important;
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

.btn-danger {
  font-size: 0.8rem;
  padding: 0.375rem 0.75rem;
  border-radius: var(--graintrade-border-radius);
}

.btn-danger:hover {
  transform: translateY(-2px);
  box-shadow: var(--graintrade-shadow);
}

/* Responsive adjustments */
@media (max-width: 1200px) {
  .table th,
  .table td {
    padding: 0.75rem 0.5rem;
    font-size: 0.9rem;
  }
  
  .btn-danger {
    font-size: 0.75rem;
    padding: 0.3rem 0.6rem;
  }
}

@media (max-width: 992px) {
  .table th,
  .table td {
    padding: 0.6rem 0.4rem;
    font-size: 0.85rem;
  }
  
  .card-header h2 {
    font-size: 1.25rem;
  }
  
  .badge {
    font-size: 0.7rem;
    padding: 0.3rem 0.5rem;
  }
}

@media (max-width: 768px) {
  .table th,
  .table td {
    padding: 0.5rem 0.25rem;
    font-size: 0.8rem;
  }
  
  .item-title-link {
    font-size: 0.9rem;
  }
  
  .card-header {
    padding: 1rem;
  }
  
  .card-header h2 {
    font-size: 1.1rem;
  }
  
  .btn-danger {
    font-size: 0.7rem;
    padding: 0.25rem 0.5rem;
  }
  
  .btn-danger .bi {
    display: none;
  }
}

/* Table striping override */
.table-striped > tbody > tr:nth-of-type(odd) > td {
  background-color: rgba(248, 249, 250, 0.8);
}

/* Special styling for user's own table */
.card-header.bg-graintrade-secondary {
  background: linear-gradient(135deg, var(--graintrade-secondary), #34495e) !important;
}
</style>
