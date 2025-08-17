<template>
  <div class="container py-4" ref="termsContainer">
    <div class="row align-items-center mb-4">
      <div class="col">
        <div class="brand fw-bold fs-3">{{ t('brand') }}</div>
        <div class="stamp text-muted">
          <span>{{ t('updated') }}</span>:
          <span id="updated-date">2025-08-16</span>
        </div>
      </div>
      <!-- Remove local language switcher, use global locale from Vuex/i18n -->
      <div class="col-auto">
        <div class="toolbar card p-2 d-flex gap-2">
          <button class="btn btn-outline-secondary btn-sm" @click="print">{{ t('print') }}</button>
          <a class="btn btn-success btn-sm" :href="downloadUrl" download="terms.html">{{ t('download') }}</a>
        </div>
      </div>
    </div>

    <section id="terms" class="card p-3">
      <h1 class="fs-4 mb-2">{{ t('terms_title') }}</h1>
      <p class="text-muted">{{ t('terms_intro') }}</p>

      <h2 class="fs-5 mt-3">{{ t('terms_service_title') }}</h2>
      <ul>
        <li v-for="(item, idx) in t('terms_service_list')" :key="'service-'+idx">{{ item }}</li>
      </ul>

      <h2 class="fs-5 mt-3">{{ t('terms_payments_title') }}</h2>
      <ul>
        <li v-for="(item, idx) in t('terms_payments_list')" :key="'payments-'+idx">{{ item }}</li>
      </ul>

      <h2 class="fs-5 mt-3">{{ t('terms_subs_title') }}</h2>
      <ul>
        <li v-for="(item, idx) in t('terms_subs_list')" :key="'subs-'+idx">{{ item }}</li>
      </ul>

      <h2 class="fs-5 mt-3">{{ t('terms_resp_title') }}</h2>
      <ul>
        <li v-for="(item, idx) in t('terms_resp_list')" :key="'resp-'+idx">{{ item }}</li>
      </ul>

      <h2 class="fs-5 mt-3">{{ t('terms_contact_title') }}</h2>
      <p>
        {{ t('terms_contact_text') }}
        <span class="badge bg-light text-dark ms-1" id="contact-email">support@graintrade.info</span>
      </p>

      <h2 class="fs-5 mt-3">{{ t('terms_changes_title') }}</h2>
      <ul>
        <li v-for="(item, idx) in t('terms_changes_list')" :key="'changes-'+idx">{{ item }}</li>
      </ul>
    </section>
    <!-- <p class="note text-muted mt-4">{{ t('footnote') }}</p> -->
  </div>
</template>

<script>
import { mapState } from 'vuex';

export default {
  name: "TermsOfService",
  computed: {
    ...mapState(['currentLocale']),
    lang() {
      // Use global locale from Vuex
      return this.currentLocale || 'en';
    }
  },
  data() {
    return {
      I18N: {
        en: {
          brand: "GrainTrade.Info — Terms of Service",
          updated: "Last updated",
          print: "Print",
          download: "Download",
          terms_title: "Terms of Service (Public Offer)",
          terms_intro: "By using our service, you agree to these terms.",
          terms_service_title: "1. Service",
          terms_service_list: [
            "We provide an online platform for posting grain, fertilizer, and fuel offers.",
            "Users can create, view, and interact with listings.",
            "The platform is not a party to transactions between users.",
            "The platform is not a trading venue, but a communication tool.",
            "User communication is via private messages or contact info in listings.",
            "We are not responsible for the content of user listings.",
            "We do not guarantee fulfillment of deals between users.",
            "We are not liable for any losses from using the platform or deals between users.",
            "Paid subscription grants access to premium features. Subscription prices are listed on the site."
          ],
          terms_payments_title: "2. Payments",
          terms_payments_list: [
            "We accept payments via provider for cards and bank transfers.",
            "We accept crypto via provider for cryptocurrencies.",
            "Prices are shown in USD or converted at payment time depending on method.",
            "Payments are final and non-refundable except as required by law."
          ],
          terms_subs_title: "3. Subscription & Renewal",
          terms_subs_list: [
            "Subscription is valid for the selected period (month, quarter, year).",
            "You can cancel anytime; unused days are not refunded.",
            "For crypto, renewal reminders are sent before subscription period ends."
          ],
          terms_resp_title: "4. Responsibility",
          terms_resp_list: [
            "We are not responsible for wrong addresses or networks chosen by the user.",
            "We are not responsible for cryptocurrency volatility.",
            "We are not responsible for blockchain confirmation delays."
          ],
          terms_contact_title: "5. Contact",
          terms_contact_text: "Questions? Email ",
          terms_changes_title: "6. Changes",
          terms_changes_list: [
            "We may change these terms. Changes take effect when published on the site.",
            "Using the service after changes means you accept the new terms."
          ],
          footnote: "This page is a simplified legal template. Consult a lawyer for specific requirements.",
        },
        ua: {
          brand: "GrainTrade.Info — Публічна оферта (Правила користування)",
          updated: "Оновлено",
          print: "Надрукувати",
          download: "Завантажити",
          terms_title: "Публічна оферта (Правила користування)",
          terms_intro: "Користуючись сервісом, ви погоджуєтесь із цими умовами.",
          terms_service_title: "1. Сервіс",
          terms_service_list: [
            "Ми надаємо онлайн-платформу для розміщення пропозицій по торгівлі зерном, добривами, паливом.",
            "Платформа дозволяє користувачам створювати, переглядати та взаємодіяти з оголошеннями.",
            "Платформа не є стороною угод між користувачами.",
            "Платформа не є торговим майданчиком, а лише інструментом для зв'язку між користувачами.",
            "Звязок між користувачами здійснюється через особисті повідомлення або контактні дані, вказані в оголошеннях.",
            "Платформа не несе відповідальності за зміст оголошень, які розміщують користувачі.",
            "Платформа не є гарантом виконання угод між користувачами.",
            "Платформа не несе відповідальності за будь-які збитки, які можуть виникнути внаслідок використання платформи або укладення угод між користувачами.",
            "Платна підписка відкриває доступ до преміум-функцій. Вартість підписки вказана на сайті."
          ],
          terms_payments_title: "2. Платежі",
          terms_payments_list: [
            "Ми приймаємо платежі через платіжного провайдера для карток та банківських переказів.",
            "Ми приймаємо криптовалюту через платіжного провайдера для криптовалют.",
            "Ціни відображаються у доларах або конвертуються під час оплати залежно від обраного методу.",
            "Оплати остаточні та не повертаються за винятком випадків, передбачених законодавством."
          ],
          terms_subs_title: "3. Підписка та продовження",
          terms_subs_list: [
            "Підписка діє протягом обраного періоду (місяць, квартал, рік).",
            "Ви можете скасувати у будь-який час; невикористані дні не компенсуються.",
            "Для крипти надсилаємо нагадування перед закінченням періоду підписки."
          ],
          terms_resp_title: "4. Відповідальність",
          terms_resp_list: [
            "Ми не несемо відповідальності за неправильні адреси чи мережі, обрані користувачем.",
            "Ми не відповідаємо за волатильність криптовалют.",
            "Ми не відповідаємо за затримки підтверджень у блокчейні."
          ],
          terms_contact_title: "5. Контакти",
          terms_contact_text: "Питання? Напишіть на ",
          terms_changes_title: "6. Зміни",
          terms_changes_list: [
            "Ми можемо змінювати ці умови. Зміни набирають чинності з моменту публікації на сайті.",
            "Використання сервісу після змін означає вашу згоду з новими умовами."
          ],
          footnote: "Ця сторінка — спрощений юридичний шаблон. За потреби зверніться до юриста.",
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
};
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