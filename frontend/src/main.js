import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'
import authService from './services/auth'

// Настройка перехватчика запросов для добавления токена авторизации
axios.interceptors.request.use(
  (config) => {
    const token = authService.getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Обработка ответов с ошибками авторизации
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      authService.logout();
      router.push('/login');
    }
    return Promise.reject(error);
  }
);

createApp(App)
  .use(router)
  .mount('#app')
