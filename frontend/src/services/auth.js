import axios from 'axios';

/**
 * Настройка базовых URL для API в зависимости от окружения
 * В Docker-окружении используем относительные пути через Nginx
 * В режиме разработки обращаемся напрямую к бэкенду
 */
const API_URL = process.env.NODE_ENV === 'production' 
  ? '/api' // Относительный путь в продакшне (обрабатывается Nginx)
  : 'http://localhost:8000/api'; // Для локальной разработки

/**
 * Перехватчик для подробного логирования ошибок
 * Помогает в отладке проблем с аутентификацией
 */
axios.interceptors.response.use(
  response => response,
  error => {
    console.error('Ошибка запроса:', error);
    
    if (error.response) {
      console.error('Данные ошибки:', error.response.data);
      console.error('Статус ошибки:', error.response.status);
      console.error('Заголовки ответа:', error.response.headers);
    } else if (error.request) {
      console.error('Запрос был отправлен, но ответ не получен:', error.request);
    } else {
      console.error('Ошибка при настройке запроса:', error.message);
    }
    
    return Promise.reject(error);
  }
);

/**
 * Сервис аутентификации для работы с API
 * Обеспечивает функции входа, регистрации, выхода и проверки статуса пользователя
 */
class AuthService {
  /**
   * Вход пользователя в систему
   * @param {string} username - Имя пользователя или email
   * @param {string} password - Пароль пользователя
   * @returns {Promise<Object>} - Данные пользователя и токен доступа
   */
  async login(username, password) {
    try {
      console.log('Отправка запроса на вход:', username);
      const response = await axios.post(`${API_URL}/auth/login`, {
        username,
        password
      });
      
      console.log('Успешный вход, получен токен');
      
      if (response.data.access_token) {
        localStorage.setItem('user', JSON.stringify(response.data));
      }
      
      return response.data;
    } catch (error) {
      console.error('Ошибка при входе:', error);
      throw error;
    }
  }

  /**
   * Регистрация нового пользователя
   * @param {string} login - Логин пользователя
   * @param {string} email - Email пользователя
   * @param {string} password - Пароль пользователя
   * @returns {Promise<Object>} - Результат регистрации
   */
  async register(login, email, password) {
    try {
      console.log('Отправка запроса на регистрацию:', { login, email });
      
      const response = await axios.post(`${API_URL}/auth/register`, {
        login,
        email,
        password
      });
      
      console.log('Успешная регистрация пользователя');
      return response.data;
    } catch (error) {
      console.error('Ошибка при регистрации:', error);
      
      // Анализ ошибок валидации
      if (error.response && error.response.status === 422) {
        console.error('Ошибки валидации:', JSON.stringify(error.response.data.detail, null, 2));
      }
      
      throw error;
    }
  }

  /**
   * Восстановление пароля пользователя
   * @param {string} email - Email для восстановления пароля
   * @returns {Promise<Object>} - Результат запроса на восстановление
   */
  async resetPassword(email) {
    try {
      const response = await axios.post(`${API_URL}/auth/reset-password`, { email });
      return response.data;
    } catch (error) {
      console.error('Ошибка при запросе восстановления пароля:', error);
      throw error;
    }
  }

  /**
   * Выход пользователя из системы
   */
  logout() {
    localStorage.removeItem('user');
  }

  /**
   * Получение данных текущего пользователя
   * @returns {Object|null} - Данные пользователя или null
   */
  getCurrentUser() {
    return JSON.parse(localStorage.getItem('user'));
  }

  /**
   * Проверка аутентификации пользователя
   * @returns {boolean} - true, если пользователь аутентифицирован
   */
  isAuthenticated() {
    const user = this.getCurrentUser();
    return !!user && !!user.access_token;
  }

  /**
   * Проверка прав администратора у пользователя
   * @returns {boolean} - true, если пользователь имеет права администратора
   */
  isAdmin() {
    const user = this.getCurrentUser();
    return !!user && user.is_admin;
  }

  /**
   * Получение токена доступа текущего пользователя
   * @returns {string|undefined} - Токен доступа
   */
  getToken() {
    const user = this.getCurrentUser();
    return user?.access_token;
  }
}

export default new AuthService();