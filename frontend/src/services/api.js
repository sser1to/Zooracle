import axios from 'axios';

// Определение базового URL в зависимости от окружения
const API_URL = process.env.NODE_ENV === 'production' 
  ? '' // В продакшне используем относительные URL благодаря nginx
  : 'http://localhost:8000/api'; // Изменяем порт с 8080 на 8000

// Создаем экземпляр axios с базовым URL
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default {
  // Метод для проверки статуса подключения к БД
  async checkDbStatus() {
    try {
      const response = await apiClient.get('/db-status');
      return response.data;
    } catch (error) {
      console.error('Error checking DB status:', error);
      return {
        status: 'error',
        message: 'Не удалось получить статус подключения к базе данных'
      };
    }
  },
  
  // Проверка доступности API бэкенда
  async checkHealth() {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      console.error('Error checking API health:', error);
      return {
        status: 'error',
        message: 'Не удалось получить статус API'
      };
    }
  }
};