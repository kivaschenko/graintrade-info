<template>
  <div class="container py-4" ref="policyContainer">
    <div class="row align-items-center mb-4">
      <div class="col">
        <div class="brand fw-bold fs-3" data-i18n="brand">{{ t('brand') }}</div>
        <div class="stamp text-muted">
          <span data-i18n="updated">{{ t('updated') }}</span>:
          <span id="updated-date">2025-08-15</span>
        </div>
      </div>
      <div class="col-auto">
        <div class="toolbar card p-2 d-flex gap-2">
          <select v-model="lang" class="form-select form-select-sm" aria-label="Language">
            <option value="en">English</option>
            <option value="ua">Українська</option>
          </select>
          <button class="btn btn-outline-secondary btn-sm" @click="print" data-i18n="print">{{ t('print') }}</button>
          <a class="btn btn-success btn-sm" :href="downloadUrl" download="policies.html" data-i18n="download">{{ t('download') }}</a>
        </div>
      </div>
    </div>

    <ul class="nav nav-tabs mb-3">
      <li class="nav-item" v-for="tab in tabs" :key="tab.key">
        <button
          class="nav-link"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
          :data-tab="tab.key"
          :data-i18n="tab.i18n"
        >
          {{ t(tab.i18n) }}
        </button>
      </li>
    </ul>

    <div class="row g-4">
      <div class="col-12 col-md-6">
        <section v-show="activeTab === 'privacy'" id="privacy" class="card p-3">
          <h1 class="fs-4 mb-2" data-i18n="privacy_title">{{ t('privacy_title') }}</h1>
          <p class="text-muted" data-i18n="privacy_intro">{{ t('privacy_intro') }}</p>

          <h2 class="fs-5 mt-3" data-i18n="privacy_what_title">{{ t('privacy_what_title') }}</h2>
          <ul>
            <li data-i18n="privacy_what_1">{{ t('privacy_what_1') }}</li>
            <li data-i18n="privacy_what_2">{{ t('privacy_what_2') }}</li>
            <li data-i18n="privacy_what_3">{{ t('privacy_what_3') }}</li>
          </ul>

          <h2 class="fs-5 mt-3" data-i18n="privacy_why_title">{{ t('privacy_why_title') }}</h2>
          <ul>
            <li data-i18n="privacy_why_1">{{ t('privacy_why_1') }}</li>
            <li data-i18n="privacy_why_2">{{ t('privacy_why_2') }}</li>
            <li data-i18n="privacy_why_3">{{ t('privacy_why_3') }}</li>
          </ul>

          <h2 class="fs-5 mt-3" data-i18n="privacy_store_title">{{ t('privacy_store_title') }}</h2>
          <ul>
            <li data-i18n="privacy_store_1">{{ t('privacy_store_1') }}</li>
            <li data-i18n="privacy_store_2">{{ t('privacy_store_2') }}</li>
            <li data-i18n="privacy_store_3">{{ t('privacy_store_3') }}</li>
          </ul>

          <h2 class="fs-5 mt-3" data-i18n="privacy_cookies_title">{{ t('privacy_cookies_title') }}</h2>
          <p data-i18n="privacy_cookies_text">{{ t('privacy_cookies_text') }}</p>

          <h2 class="fs-5 mt-3" data-i18n="privacy_rights_title">{{ t('privacy_rights_title') }}</h2>
          <ul>
            <li data-i18n="privacy_rights_1">{{ t('privacy_rights_1') }}</li>
            <li data-i18n="privacy_rights_2">{{ t('privacy_rights_2') }}</li>
            <li data-i18n="privacy_rights_3">
              {{ t('privacy_rights_3') }}
              <span class="badge bg-light text-dark ms-1" id="contact-email">support@graintrade.info</span>
            </li>
          </ul>
        </section>
      </div>

      <div class="col-12 col-md-6" v-if="activeTab === 'terms'">
        <section id="terms" class="card p-3">
          <h1 class="fs-4 mb-2" data-i18n="terms_title">{{ t('terms_title') }}</h1>
          <p class="text-muted" data-i18n="terms_intro">{{ t('terms_intro') }}</p>

          <h2 class="fs-5 mt-3" data-i18n="terms_service_title">{{ t('terms_service_title') }}</h2>
          <p data-i18n="terms_service_text">{{ t('terms_service_text') }}</p>

          <h2 class="fs-5 mt-3" data-i18n="terms_payments_title">{{ t('terms_payments_title') }}</h2>
          <ul>
            <li data-i18n="terms_payments_1">{{ t('terms_payments_1') }}</li>
            <li data-i18n="terms_payments_2">{{ t('terms_payments_2') }}</li>
            <li data-i18n="terms_payments_3">{{ t('terms_payments_3') }}</li>
          </ul>

          <h2 class="fs-5 mt-3" data-i18n="terms_subs_title">{{ t('terms_subs_title') }}</h2>
          <ul>
            <li data-i18n="terms_subs_1">{{ t('terms_subs_1') }}</li>
            <li data-i18n="terms_subs_2">{{ t('terms_subs_2') }}</li>
            <li data-i18n="terms_subs_3">{{ t('terms_subs_3') }}</li>
          </ul>

          <h2 class="fs-5 mt-3" data-i18n="terms_resp_title">{{ t('terms_resp_title') }}</h2>
          <ul>
            <li data-i18n="terms_resp_1">{{ t('terms_resp_1') }}</li>
            <li data-i18n="terms_resp_2">{{ t('terms_resp_2') }}</li>
            <li data-i18n="terms_resp_3">{{ t('terms_resp_3') }}</li>
          </ul>

          <h2 class="fs-5 mt-3" data-i18n="terms_contact_title">{{ t('terms_contact_title') }}</h2>
          <p data-i18n="terms_contact_text">
            {{ t('terms_contact_text') }}
            <span class="badge bg-light text-dark ms-1" id="contact-email-2">support@graintrade.info</span>
          </p>
        </section>
      </div>

      <div class="col-12 col-md-6" v-if="activeTab === 'crypto'">
        <section id="crypto" class="card p-3">
          <h1 class="fs-4 mb-2" data-i18n="crypto_title">{{ t('crypto_title') }}</h1>
          <ul>
            <li data-i18n="crypto_1">{{ t('crypto_1') }}</li>
            <li data-i18n="crypto_2">{{ t('crypto_2') }}</li>
            <li data-i18n="crypto_3">{{ t('crypto_3') }}</li>
            <li data-i18n="crypto_4">{{ t('crypto_4') }}</li>
            <li data-i18n="crypto_5">{{ t('crypto_5') }}</li>
          </ul>
        </section>
      </div>
    </div>

    <p class="note text-muted mt-4" data-i18n="footnote">{{ t('footnote') }}</p>
  </div>
</template>

<script>
export default {
  name: "PrivacyPolicy",
  data() {
    return {
      lang: "en",
      activeTab: "privacy",
      tabs: [
        { key: "privacy", i18n: "tab_privacy" },
        { key: "terms", i18n: "tab_terms" },
        { key: "crypto", i18n: "tab_crypto" },
      ],
      I18N: {
        en: {
          brand: "GrainTrade — Legal",
          updated: "Last updated",
          print: "Print",
          download: "Download",
          tab_privacy: "Privacy Policy",
          tab_terms: "Terms of Service",
          tab_crypto: "Crypto Disclaimer",
          privacy_title: "Privacy Policy",
          privacy_intro: "We respect your privacy and keep your data safe.",
          privacy_what_title: "1. Data we collect",
          privacy_what_1: "Email (if you contact us or register)",
          privacy_what_2: "IP address (server logs)",
          privacy_what_3: "Payment info (transaction ID, amount, blockchain address)",
          privacy_why_title: "2. Why we collect it",
          privacy_why_1: "To process subscriptions and payments",
          privacy_why_2: "To provide support",
          privacy_why_3: "To keep the service secure and prevent fraud",
          privacy_store_title: "3. Storage & protection",
          privacy_store_1: "Data is stored on secure servers",
          privacy_store_2: "We do not sell or share personal data",
          privacy_store_3: "Payments are processed via blockchain / provider; we do not store private keys or card data",
          privacy_cookies_title: "4. Cookies",
          privacy_cookies_text: "We do not use cookies or tracking tools. If we add analytics later, we will request consent.",
          privacy_rights_title: "5. Your rights (GDPR)",
          privacy_rights_1: "Access, correction, deletion of your personal data",
          privacy_rights_2: "Objection to processing (unsubscribe)",
          privacy_rights_3: "Contact us: ",
          terms_title: "Terms of Service (Public Offer)",
          terms_intro: "By using our service, you agree to these terms.",
          terms_service_title: "1. Service",
          terms_service_text: "We provide an online marketplace for grain trade. Paid subscription grants access to premium features.",
          terms_payments_title: "2. Payments",
          terms_payments_1: "We accept crypto via our payment provider",
          terms_payments_2: "Prices are shown in UAH or converted at payment time",
          terms_payments_3: "Payments are final and non-refundable",
          terms_subs_title: "3. Subscription & Renewal",
          terms_subs_1: "Subscription is valid for the selected period",
          terms_subs_2: "You can cancel anytime; unused days are not refunded",
          terms_subs_3: "For crypto, renewal reminders are sent before period end",
          terms_resp_title: "4. Responsibility",
          terms_resp_1: "We are not responsible for wrong addresses or wrong networks chosen by the user",
          terms_resp_2: "We are not responsible for cryptocurrency volatility",
          terms_resp_3: "We are not responsible for blockchain confirmation delays",
          terms_contact_title: "5. Contact",
          terms_contact_text: "Questions? Email ",
          crypto_title: "Crypto Payments Disclaimer",
          crypto_1: "Send funds only to the exact address and correct network shown at checkout.",
          crypto_2: "Transactions sent to the wrong address/network cannot be recovered.",
          crypto_3: "No refunds for completed blockchain transactions.",
          crypto_4: "Prices may change due to crypto volatility.",
          crypto_5: "We are not a financial institution. All transactions are final.",
          footnote: "This page is a simplified legal template. Consult a lawyer for specific requirements.",
        },
        ua: {
          brand: "GrainTrade — Правові документи",
          updated: "Оновлено",
          print: "Надрукувати",
          download: "Завантажити",
          tab_privacy: "Політика конфіденційності",
          tab_terms: "Публічна оферта",
          tab_crypto: "Дисклеймер щодо криптоплатежів",
          privacy_title: "Політика конфіденційності",
          privacy_intro: "Ми поважаємо вашу приватність та дбаємо про безпеку даних.",
          privacy_what_title: "1. Які дані ми збираємо",
          privacy_what_1: "Електронна пошта (якщо ви звертаєтесь до нас або реєструєтесь)",
          privacy_what_2: "IP-адреса (журнали сервера)",
          privacy_what_3: "Платіжна інформація (ID транзакції, сума, блокчейн-адреса)",
          privacy_why_title: "2. Навіщо це потрібно",
          privacy_why_1: "Щоб обробляти підписки та платежі",
          privacy_why_2: "Щоб надавати підтримку",
          privacy_why_3: "Щоб забезпечувати безпеку та запобігати шахрайству",
          privacy_store_title: "3. Зберігання та захист",
          privacy_store_1: "Дані зберігаються на захищених серверах",
          privacy_store_2: "Ми не продаємо та не передаємо персональні дані третім сторонам",
          privacy_store_3: "Платежі обробляються через блокчейн/провайдера; ми не зберігаємо приватні ключі чи дані карток",
          privacy_cookies_title: "4. Cookies",
          privacy_cookies_text: "Ми не використовуємо cookies або інструменти відстеження. Якщо додамо аналітику — попросимо згоду.",
          privacy_rights_title: "5. Ваші права (GDPR)",
          privacy_rights_1: "Доступ, виправлення, видалення ваших даних",
          privacy_rights_2: "Заперечення проти обробки (відписка)",
          privacy_rights_3: "Зв'яжіться з нами: ",
          terms_title: "Публічна оферта (Правила користування)",
          terms_intro: "Користуючись сервісом, ви погоджуєтесь із цими умовами.",
          terms_service_title: "1. Сервіс",
          terms_service_text: "Ми надаємо онлайн-платформу для торгівлі зерном. Платна підписка відкриває доступ до преміум-функцій.",
          terms_payments_title: "2. Платежі",
          terms_payments_1: "Ми приймаємо криптовалюту через платіжного провайдера",
          terms_payments_2: "Ціни відображаються у грн або конвертуються під час оплати",
          terms_payments_3: "Оплати остаточні та не повертаються",
          terms_subs_title: "3. Підписка та продовження",
          terms_subs_1: "Підписка діє протягом обраного періоду",
          terms_subs_2: "Ви можете скасувати у будь-який час; невикористані дні не компенсуються",
          terms_subs_3: "Для крипти надсилаємо нагадування перед закінченням періоду",
          terms_resp_title: "4. Відповідальність",
          terms_resp_1: "Ми не несемо відповідальності за неправильні адреси чи мережі, обрані користувачем",
          terms_resp_2: "Ми не відповідаємо за волатильність криптовалют",
          terms_resp_3: "Ми не відповідаємо за затримки підтверджень у блокчейні",
          terms_contact_title: "5. Контакти",
          terms_contact_text: "Питання? Напишіть на ",
          crypto_title: "Дисклеймер щодо криптоплатежів",
          crypto_1: "Надсилайте кошти лише на точну адресу та у правильній мережі, вказаній при оплаті.",
          crypto_2: "Транзакції, надіслані на неправильну адресу/мережу, неможливо відновити.",
          crypto_3: "Повернення коштів за завершені блокчейн-транзакції не здійснюється.",
          crypto_4: "Ціни можуть змінюватись через волатильність криптовалют.",
          crypto_5: "Ми не є фінансовою установою. Усі транзакції остаточні.",
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
    },
    activeTab() {
      this.prepareDownload(); // Update download content when tab changes
    }
  },
  methods: {
    t(key) {
      return this.I18N[this.lang][key] || this.I18N.en[key] || key;
    },
    print() {
      window.print();
    },
    prepareDownload() {
      // Only run if ref exists and component is mounted
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
.nav-tabs .nav-link {
  cursor: pointer;
}
.nav-tabs .nav-link.active {
  font-weight: bold;
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
#contact-email, #contact-email-2 {
  font-weight: bold;
  color: #007bff;
  text-decoration: none;
}
#contact-email:hover, #contact-email-2:hover {
  text-decoration: underline;
}
#updated-date {
  font-weight: bold;
}
.nav-tabs {
  margin-bottom: 1rem;
}
.nav-tabs .nav-item {
  margin-right: 0.5rem;
}
.nav-tabs .nav-link {
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
}
.nav-tabs .nav-link.active {
  background-color: #007bff;
  color: white;
}
.nav-tabs .nav-link:hover {
  background-color: #0056b3;
  color: white;
}
#privacy, #terms, #crypto {
  margin-bottom: 1rem;
}
</style>