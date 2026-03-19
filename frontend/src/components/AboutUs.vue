<template>
  <div class="container py-4">
    <div class="row align-items-center mb-4">
      <div class="col">
        <div class="brand fw-bold fs-3">{{ t('brand') }}</div>
        <div class="stamp text-muted">
          <span>{{ t('updated') }}</span>:
          <span id="updated-date">2025-08-20</span>
        </div>
      </div>
    </div>

    <section id="about" class="card p-3">
      <h1 class="fs-4 mb-2">{{ t('about_title') }}</h1>
      <p>{{ t('about_intro') }}</p>

      <h2 class="fs-5 mt-3">{{ t('about_goals_title') }}</h2>
      <ul>
        <li v-for="(item, idx) in t('about_goals_list')" :key="'goal-'+idx">{{ item }}</li>
      </ul>

      <h2 class="fs-5 mt-3">{{ t('about_principles_title') }}</h2>
      <ul>
        <li v-for="(item, idx) in t('about_principles_list')" :key="'principle-'+idx">{{ item }}</li>
      </ul>

      <h2 class="fs-5 mt-3">{{ t('about_future_title') }}</h2>
      <ul>
        <li v-for="(item, idx) in t('about_future_list')" :key="'future-'+idx">{{ item }}</li>
      </ul>

      <h2 class="fs-5 mt-3">{{ t('about_contact_title') }}</h2>
      <p>
        {{ t('about_contact_text') }}
        <span class="badge bg-light text-dark ms-1" id="contact-email">support@graintrade.info</span>
      </p>
    </section>
  </div>
</template>

<script>
import { mapState } from 'vuex';

export default {
  name: "AboutUs",
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
          brand: "GrainTrade.Info — About Us",
          updated: "Last updated",
          about_title: "About GrainTrade.Info",
          about_intro: "GrainTrade.Info is created to help farmers and traders in Ukraine connect and make deals. Our goal is to make grain trading more transparent and efficient by providing a platform for sharing offers and requests.",
          about_goals_title: "Our Goals",
          about_goals_list: [
            "Facilitate direct connections between farmers and traders.",
            "Increase transparency in the grain market.",
            "Provide up-to-date information about offers and requests.",
            "Support fair and efficient trading practices."
          ],
          about_principles_title: "Our Principles",
          about_principles_list: [
            "We are not intermediaries; all deals are made directly between users.",
            "We encourage honesty and ethical behavior in trading.",
            "Do not post misleading or false information.",
            "We reserve the right to remove any listings that violate our rules or Ukrainian law."
          ],
          about_future_title: "Future Plans",
          about_future_list: [
            "Expand site functionality with price monitoring, news, and analytics.",
            "Add options for posting offers and searching for partners in agribusiness.",
            "Continue improving the platform based on user feedback."
          ],
          about_contact_title: "Contact Us",
          about_contact_text: "Questions or suggestions? Email ",
        },
        ua: {
          brand: "GrainTrade.Info — Про нас",
          updated: "Оновлено",
          about_title: "Про GrainTrade.Info",
          about_intro: "GrainTrade.Info створено для допомоги фермерам та торговцям зерном в Україні знайти один одного та укласти угоди. Ми прагнемо зробити торгівлю зерном прозорішою та ефективнішою, забезпечуючи платформу для обміну пропозиціями та запитами.",
          about_goals_title: "Наші цілі",
          about_goals_list: [
            "Сприяти прямим контактам між фермерами та торговцями.",
            "Підвищувати прозорість ринку зерна.",
            "Надавати актуальну інформацію про пропозиції та запити.",
            "Підтримувати чесні та ефективні торгові практики."
          ],
          about_principles_title: "Наші принципи",
          about_principles_list: [
            "Ми не є посередниками; всі угоди укладаються напряму між користувачами.",
            "Ми закликаємо до чесності та етики у торгівлі.",
            "Не розміщуйте неправдиву або оманливу інформацію.",
            "Ми залишаємо за собою право видаляти оголошення, що порушують наші правила або законодавство України."
          ],
          about_future_title: "Плани на майбутнє",
          about_future_list: [
            "Розширення функціоналу сайту: моніторинг цін, новини, аналітика.",
            "Додавання можливостей для розміщення оголошень та пошуку партнерів у агробізнесі.",
            "Постійне вдосконалення платформи на основі відгуків користувачів."
          ],
          about_contact_title: "Зв'язок з нами",
          about_contact_text: "Питання чи пропозиції? Напишіть на ",
        }
      }
    };
  },
  methods: {
    t(key) {
      const val = this.I18N[this.lang][key];
      if (Array.isArray(val)) return val;
      return val || this.I18N.en[key] || key;
    }
  }
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
  color: #6c757d;
}
</style>