<template>
  <div class="container py-4" ref="policyContainer">
    <div class="row align-items-center mb-4">
      <div class="col">
        <div class="brand fw-bold fs-3">{{ t('brand') }}</div>
        <div class="stamp text-muted">
          <span>{{ t('updated') }}</span>:
          <span id="updated-date">2025-08-15</span>
        </div>
      </div>
      <div class="col-auto">
        <div class="toolbar card p-2 d-flex gap-2">
          <button class="btn btn-outline-secondary btn-sm" @click="print">{{ t('print') }}</button>
          <a class="btn btn-success btn-sm" :href="downloadUrl" download="privacy.html">{{ t('download') }}</a>
        </div>
      </div>
    </div>

    <section id="privacy" class="card p-3">
      <h1 class="fs-4 mb-2">{{ t('privacy_title') }}</h1>
      <p class="text-muted">{{ t('privacy_intro') }}</p>

      <h2 class="fs-5 mt-3">{{ t('privacy_what_title') }}</h2>
      <ul>
        <li v-for="(item, idx) in t('privacy_what_list')" :key="'what-'+idx">{{ item }}</li>
      </ul>

      <h2 class="fs-5 mt-3">{{ t('privacy_why_title') }}</h2>
      <ul>
        <li v-for="(item, idx) in t('privacy_why_list')" :key="'why-'+idx">{{ item }}</li>
      </ul>

      <h2 class="fs-5 mt-3">{{ t('privacy_store_title') }}</h2>
      <ul>
        <li v-for="(item, idx) in t('privacy_store_list')" :key="'store-'+idx">{{ item }}</li>
      </ul>

      <h2 class="fs-5 mt-3">{{ t('privacy_cookies_title') }}</h2>
      <p>{{ t('privacy_cookies_text') }}</p>

      <h2 class="fs-5 mt-3">{{ t('privacy_rights_title') }}</h2>
      <ul>
        <li v-for="(item, idx) in t('privacy_rights_list')" :key="'rights-'+idx">
          <template v-if="idx === t('privacy_rights_list').length - 1">
            {{ item }}
            <span class="badge bg-light text-dark ms-1" id="contact-email">support@graintrade.info</span>
          </template>
          <template v-else>
            {{ item }}
          </template>
        </li>
      </ul>
    </section>

    <section id="crypto" class="card p-3 mt-4">
      <h1 class="fs-4 mb-2">{{ t('crypto_title') }}</h1>
      <ul>
        <li v-for="(item, idx) in t('crypto_list')" :key="'crypto-'+idx">{{ item }}</li>
      </ul>
    </section>

    <!-- <p class="note text-muted mt-4">{{ t('footnote') }}</p> -->  
  </div>
</template>

<script>
import { mapState } from 'vuex';

export default {
  name: "PrivacyPolicy",
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
          brand: "GrainTrade.Info — Legal",
          updated: "Last updated",
          print: "Print",
          download: "Download",
          privacy_title: "Privacy Policy",
          privacy_intro: "We respect your privacy and keep your data safe.",
          privacy_what_title: "1. Data we collect",
          privacy_what_list: [
            "Email, full name, and phone number during registration and payment.",
            "Payment info (transaction ID, amount, blockchain address).",
            "We use official payment gateways such as LiqPay for card payments and crypto providers for cryptocurrency payments.",
            "Additional minimal info required for payment processing (such as payment method, status, and confirmation).",
            "IP address (server logs)."
          ],
          privacy_why_title: "2. Why we collect it",
          privacy_why_list: [
            "To process subscriptions and payments.",
            "To provide support.",
            "To keep the service secure and prevent fraud."
          ],
          privacy_store_title: "3. Storage & protection",
          privacy_store_list: [
            "Data is stored on secure servers.",
            "We do not sell or share personal data.",
            "Payments are processed via official gateways (LiqPay, crypto providers); we do not store private keys or card data."
          ],
          privacy_cookies_title: "4. Cookies",
          privacy_cookies_text: "We do not use cookies or tracking tools. If we add analytics later, we will request consent.",
          privacy_rights_title: "5. Your rights (GDPR)",
          privacy_rights_list: [
            "Access, correction, deletion of your personal data.",
            "Objection to processing (unsubscribe).",
            "Contact us: "
          ],
          crypto_title: "Crypto Payments Disclaimer",
          crypto_list: [
            "Send funds only to the exact address and correct network shown at checkout.",
            "Transactions sent to the wrong address/network cannot be recovered.",
            "No refunds for completed blockchain transactions.",
            "Prices may change due to crypto volatility.",
            "We are not a financial institution. All transactions are final."
          ],
          footnote: "This page is a simplified legal template. Consult a lawyer for specific requirements.",
        },
        ua: {
          brand: "GrainTrade.Info — Правові документи",
          updated: "Оновлено",
          print: "Надрукувати",
          download: "Завантажити",
          privacy_title: "Політика конфіденційності",
          privacy_intro: "Ми поважаємо вашу приватність та дбаємо про безпеку даних.",
          privacy_what_title: "1. Які дані ми збираємо",
          privacy_what_list: [
            "Електронна пошта, ПІБ та телефон під час реєстрації та оплати.",
            "Платіжна інформація (ID транзакції, сума, блокчейн-адреса).",
            "Ми використовуємо офіційні платіжні шлюзи, такі як LiqPay для карткових оплат та криптопровайдерів для криптовалют.",
            "Додаткова мінімальна інформація, необхідна для обробки платежу (метод оплати, статус, підтвердження).",
            "IP-адреса (журнали сервера)."
          ],
          privacy_why_title: "2. Навіщо це потрібно",
          privacy_why_list: [
            "Щоб обробляти підписки та платежі.",
            "Щоб надавати підтримку.",
            "Щоб забезпечувати безпеку та запобігати шахрайству."
          ],
          privacy_store_title: "3. Зберігання та захист",
          privacy_store_list: [
            "Дані зберігаються на захищених серверах.",
            "Ми не продаємо та не передаємо персональні дані третім сторонам.",
            "Платежі обробляються через офіційні шлюзи (LiqPay, криптопровайдери); ми не зберігаємо приватні ключі чи дані карток."
          ],
          privacy_cookies_title: "4. Cookies",
          privacy_cookies_text: "Ми не використовуємо cookies або інструменти відстеження. Якщо додамо аналітику — попросимо згоду.",
          privacy_rights_title: "5. Ваші права (GDPR)",
          privacy_rights_list: [
            "Доступ, виправлення, видалення ваших даних.",
            "Заперечення проти обробки (відписка).",
            "Зв'яжіться з нами: "
          ],
          crypto_title: "Дисклеймер щодо криптоплатежів",
          crypto_list: [
            "Надсилайте кошти лише на точну адресу та у правильній мережі, вказаній при оплаті.",
            "Транзакції, надіслані на неправильну адресу/мережу, неможливо відновити.",
            "Повернення коштів за завершені блокчейн-транзакції не здійснюється.",
            "Ціни можуть змінюватись через волатильність криптовалют.",
            "Ми не є фінансовою установою. Усі транзакції остаточні."
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
      if (!this.$refs.policyContainer) return;
      const container = this.$refs.policyContainer;
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