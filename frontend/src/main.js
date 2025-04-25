import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'
import authService from './services/auth'

/**
 * Настройка базового URL для Axios
 * Это обеспечивает корректную работу API запросов независимо от текущего маршрута
 */
axios.defaults.baseURL = window.location.origin;

// Настройка перехватчика запросов для добавления токена авторизации
axios.interceptors.request.use(
  (config) => {
    const token = authService.getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Добавляем отладочную информацию
    console.log(`API запрос: ${config.method.toUpperCase()} ${config.url}`);
    
    return config;
  },
  (error) => {
    console.error('Ошибка при формировании запроса:', error);
    return Promise.reject(error);
  }
);

// Обработка ответов с ошибками авторизации
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      console.log('Получен статус 401 - перенаправление на страницу входа');
      authService.logout();
      router.push('/login');
    }
    return Promise.reject(error);
  }
);

// Создаем и монтируем основное приложение
const app = createApp(App);

// Добавляем глобальное свойство $axios для доступа во всех компонентах
app.config.globalProperties.$axios = axios;

// Подключаем роутер и монтируем приложение
app.use(router).mount('#app')
