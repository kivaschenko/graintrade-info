<template>
  <div class="container py-4" ref="termsContainer">
    <div class="row align-items-center mb-4">
      <div class="col">
        <div class="brand fw-bold fs-3">{{ t('brand') }}</div>
        <div class="stamp text-muted">
          <span>{{ t('updated') }}</span>:
          <span id="updated-date">2025-08-19</span>
        </div>
      </div>
      <div class="col-auto">
        <div class="toolbar card p-2 d-flex gap-2">
          <button class="btn btn-outline-secondary btn-sm" @click="print">{{ t('print') }}</button>
          <a class="btn btn-success btn-sm" :href="downloadUrl" :download="`${t('brand')}.html`">{{ t('download') }}</a>
        </div>
      </div>
    </div>
    <section id="requisites" class="card p-3">
      <h1 class="fs-4 mb-2">{{ t('requisites_title') }}</h1>
      <p class="text-muted">{{ t('requisites_intro') }}</p>
      <h2 class="fs-5 mt-3">{{ t('fop_details_title') }}</h2>
      <ul>
        <li><strong>{{ t('fio') }}:</strong> {{ t('full_name') }}</li>
        <li><strong>{{ t('tax_id') }}:</strong> 2706813416</li>
        <li><strong>{{ t('address') }}:</strong> {{ t('address_registration') }}</li>
      </ul>
      <h2 class="fs-5 mt-3">{{ t('bank_details_title') }}</h2>
      <ul>
        <li><strong>{{ t('account') }}:</strong> UA 66 300528 0000026002000011282</li>
        <li><strong>{{ t('bank') }}:</strong> {{ t('bank_full_name') }}</li>
        <li><strong>{{ t('mfo') }}:</strong> 300528</li>
      </ul>
      <h2 class="fs-5 mt-3">{{ t('contact_details_title') }}</h2>
      <ul>
        <li><strong>Email:</strong> <a id="contact-email" href="mailto:support@graintrade.info">support@graintrade.info</a></li>
        <li><strong>{{ t('phone') }}:</strong> +380 66 2760451</li>
      </ul>
    </section>
  </div>
</template>

<script>
import { mapState } from 'vuex';

export default {
  name: "ContactsRequisites",
  computed: {
    ...mapState(['currentLocale']),
    lang() {
      return this.currentLocale || 'en';
    }
  },
  data() {
    return {
      I18N: {
        en: {
          brand: "Graintrade.Info - Contacts and Requisites",
          updated: "Last updated",
          print: "Print",
          download: "Download",
          requisites_title: "Contacts and Requisites",
          requisites_intro: "Below are the contact details and business requisites.",
          fop_details_title: "Sole Proprietor Details",
          fio: "Full Name",
          full_name: "KOSTIANTYN M. IVASHCHENKO",
          tax_id: "Tax ID",
          address: "Address",
          address_registration: "Atamanovskogo lane, 44/2, Cherkasy, Cherkas`ka oblast, Ukraine, 18000",
          bank_details_title: "Bank Details",
          account: "Account/IBAN",
          bank: "Bank Name",
          mfo: "MFO",
          bank_full_name: "JOINT-STOCK COMPANY OTP BANK (OTP BANK JSC) 43 Zhylyanska str., Kyiv, Ukraine, 01033",
          contact_details_title: "Contact Information",
          phone: "Phone",
        },
        ua: {
          brand: "GrainTrade.Info — Контакти та реквізити",
          updated: "Оновлено",
          print: "Надрукувати",
          download: "Завантажити",
          requisites_title: "Контакти та реквізити",
          requisites_intro: "Нижче наведено контактні дані та реквізити.",
          fop_details_title: "Реквізити ФОП",
          fio: "ПІБ",
          full_name: "ІВАЩЕНКО КОСТЯНТИН МИКОЛАЙОВИЧ",
          tax_id: "РНОКПП",
          address: "Адреса",
          address_registration: "провул. Атамановськогоб 44/2, м. Черкаси, Черкаська область, Україна, 18000",
          bank_details_title: "Банківські реквізити",
          account: "Рахунок/IBAN",
          bank: "Банк",
          mfo: "МФО",
          bank_full_name: "АТ ОТП Банк вулиця Жилянська, 43, м. Київ, Україна, 01033",
          contact_details_title: "Контактна інформація",
          phone: "Телефон",
        }
      },
      downloadUrl: "#"
    };
  },
  watch: {
    lang: {
      handler() {
        document.documentElement.lang = this.lang === "ua" ? "uk" : "en";
        this.prepareDownload();
      },
      immediate: true
    }
  },
  methods: {
    t(key) {
      const val = this.I18N[this.lang][key];
      if (Array.isArray(val)) return val;
      return val || this.I18N.en[key] || key;
    },
    print() {
      window.print();
    },
    prepareDownload() {
      if (!this.$refs.termsContainer) return;
      const container = this.$refs.termsContainer;
      const html = `
        <html lang="${this.lang === "ua" ? "uk" : "en"}">
          <head>
            <meta charset="utf-8" />
            <title>${this.t('brand')}</title>
          </head>
          <body>
            ${container.outerHTML}
          </body>
        </html>
      `;
      const blob = new Blob([html], { type: "text/html" });
      this.downloadUrl = URL.createObjectURL(blob);
    }
  },
  mounted() {
    this.prepareDownload();
  },
}
</script>

<style scoped>
.brand {
  font-weight: bold;
  font-size: 1.5rem;
}
.stamp {
  font-size: 0.875rem;
}
.note {
  font-size: 0.875rem;
  margin-top: 20px;
}
.toolbar {
  display: flex;
  gap: 10px;
}
.card {
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
}
.card p {
  margin-bottom: 0.5rem;
}
.card ul {
  padding-left: 1.5rem;
}
.card ul li {
  margin-bottom: 0.5rem;
}
#contact-email {
  font-weight: bold;
  color: #007bff;
  text-decoration: none;
}
#contact-email:hover {
  text-decoration: underline;
}
#updated-date {
  font-weight: bold;
}
</style>