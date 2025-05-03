import axios from 'axios';
import AuthService from './auth';

/**
 * Определение базового URL для API в зависимости от окружения
 * В Docker-окружении используем относительные пути, которые обрабатывает Nginx
 * В режиме разработки обращаемся напрямую к бэкенду
 */
const BACKEND_PORT = process.env.FRONTEND_PORT;
const SITE_IP = process.env.SITE_IP;

const API_URL = process.env.NODE_ENV === 'production' 
  ? '/api' // В продакшне используем относительные URL через nginx
  : `${SITE_IP}:${BACKEND_PORT}/api`; // Для локальной разработки

/**
 * Создаем настроенный экземпляр axios с базовым URL и заголовками
 */
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Добавляем перехватчик запросов для включения токена авторизации,
 * если пользователь авторизован
 */
apiClient.interceptors.request.use(
  config => {
    const token = AuthService.getToken();
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Добавляем перехватчик для логирования ошибок
apiClient.interceptors.response.use(
  response => response,
  error => {
    console.error('Ошибка API:', error.message);
    
    // Если сервер вернул 401 (неавторизован) и пользователь был авторизован,
    // то сессия истекла, нужно разлогинить пользователя
    if (error.response && error.response.status === 401 && AuthService.isAuthenticated()) {
      console.warn('Сессия истекла, выполняется выход');
      AuthService.logout();
      window.location.reload();
    }
    
    return Promise.reject(error);
  }
);

// Экспортируем настроенный экземпляр для прямого использования HTTP методов
export const api = apiClient;

// Экспортируем объект с дополнительными вспомогательными методами
export default {
  /**
   * Метод для проверки статуса подключения к БД
   * @returns {Promise<Object>} Статус подключения
   */
  async checkDbStatus() {
    try {
      const response = await apiClient.get('/db-status');
      return response.data;
    } catch (error) {
      console.error('Ошибка при проверке статуса БД:', error);
      return {
        status: 'error',
        message: 'Не удалось получить статус подключения к базе данных'
      };
    }
  },
  
  /**
   * Проверка доступности API бэкенда
   * @returns {Promise<Object>} Статус API
   */
  async checkHealth() {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      console.error('Ошибка при проверке здоровья API:', error);
      return {
        status: 'error',
        message: 'Не удалось получить статус API'
      };
    }
  },

  /**
   * Метод для отправки HTTP POST запросов
   * @param {string} url - URL эндпоинта
   * @param {Object} data - Данные для отправки
   * @returns {Promise<Object>} Ответ от сервера
   */
  post(url, data) {
    return apiClient.post(url, data);
  },

  /**
   * Метод для отправки HTTP GET запросов
   * @param {string} url - URL эндпоинта
   * @param {Object} params - Параметры запроса
   * @returns {Promise<Object>} Ответ от сервера
   */
  get(url, params) {
    return apiClient.get(url, { params });
  },

  /**
   * Метод для отправки HTTP PUT запросов
   * @param {string} url - URL эндпоинта
   * @param {Object} data - Данные для отправки
   * @returns {Promise<Object>} Ответ от сервера
   */
  put(url, data) {
    return apiClient.put(url, data);
  },

  /**
   * Метод для отправки HTTP DELETE запросов
   * @param {string} url - URL эндпоинта
   * @returns {Promise<Object>} Ответ от сервера
   */
  delete(url) {
    return apiClient.delete(url);
  }
};