import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  uz: {
    translation: {
      "welcome": "Xush kelibsiz",
      "cart": "Savatcha",
      "checkout": "Buyurtma berish"
    }
  },
  ru: {
    translation: {
      "welcome": "Добро пожаловать",
      "cart": "Корзина",
      "checkout": "Оформить заказ"
    }
  },
  en: {
    translation: {
      "welcome": "Welcome",
      "cart": "Cart",
      "checkout": "Checkout"
    }
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: "ru", // default language
    fallbackLng: "en",
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;
