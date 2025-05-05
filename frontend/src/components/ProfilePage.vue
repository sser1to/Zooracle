<template>
  <div class="profile-container">
    <img alt="Лого" src="../assets/logo.png" class="logo">
    <h1>Личный кабинет</h1>
    
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Загрузка данных...</p>
    </div>
    
    <div v-else-if="error" class="error-container">
      <div class="error-icon">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="error-svg">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
        </svg>
      </div>
      <p class="error-message">{{ error }}</p>
      <button @click="loadUserData" class="btn-primary">Повторить</button>
    </div>
    
    <template v-else>
      <!-- Секция данных пользователя -->
      <div class="profile-section">
        <h2>Основные данные</h2>
        
        <!-- Форма редактирования логина -->
        <div class="form-group">
          <label for="login">Логин:</label>
          <div class="input-with-button">
            <input 
              type="text" 
              id="login" 
              v-model="userData.login" 
              :disabled="!isEditingLogin" 
              :class="{ 'input-error': loginError }"
            />
            <button 
              v-if="!isEditingLogin" 
              @click="startEditingLogin" 
              class="edit-button"
              title="Изменить логин"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="edit-icon">
                <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
              </svg>
            </button>
            <div v-else class="action-buttons">
              <button 
                @click="saveLogin" 
                class="save-button"
                title="Сохранить"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="save-icon">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                </svg>
              </button>
              <button 
                @click="cancelEditingLogin" 
                class="cancel-button"
                title="Отмена"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="cancel-icon">
                  <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
                </svg>
              </button>
            </div>
          </div>
          <p v-if="loginError" class="error-text">{{ loginError }}</p>
        </div>
        
        <!-- Email пользователя (только для чтения) -->
        <div class="form-group">
          <label for="email">Email:</label>
          <input 
            type="email" 
            id="email" 
            v-model="userData.email" 
            disabled 
            class="readonly-input"
          />
          <p class="info-text">Email используется для восстановления пароля и не может быть изменен.</p>
        </div>
        
        <!-- Раздел для смены пароля -->
        <div class="form-group password-section">
          <label>Пароль:</label>
          <div class="password-display">
            <span class="password-dots">••••••••</span>
            <button 
              @click="requestPasswordReset" 
              class="btn-secondary"
              :disabled="passwordResetRequested"
            >
              {{ passwordResetRequested ? 'Письмо отправлено' : 'Сменить пароль' }}
            </button>
          </div>
          <p v-if="passwordResetRequested" class="info-text success-text">
            На ваш email отправлена ссылка для смены пароля. 
            Проверьте почту и следуйте инструкциям в письме.
          </p>
        </div>
        
        <!-- Дополнительная информация о пользователе -->
        <div class="info-block" v-if="userData.is_admin">
          <div class="admin-badge">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="admin-icon">
              <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/>
            </svg>
            <span>Администратор</span>
          </div>
        </div>
      </div>
      
      <!-- Секция статистики с условным отображением для админов -->
      <div class="profile-section">
        <h2>Статистика</h2>
        <div class="stats-grid" :class="{ 'admin-stats-grid': userData.is_admin }">
          <div class="stat-card">
            <div class="stat-value">{{ userStats.testsCompleted || 0 }}</div>
            <div class="stat-label">Пройдено тестов</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ userStats.averageScore || '0%' }}</div>
            <div class="stat-label">Средний результат</div>
          </div>
          <!-- Блок "В избранном" отображается только для обычных пользователей -->
          <div v-if="!userData.is_admin" class="stat-card">
            <div class="stat-value">{{ userStats.favoritesCount || 0 }}</div>
            <div class="stat-label">В избранном</div>
          </div>
        </div>
      </div>
      
      <!-- Секция пройденных тестов -->
      <div class="profile-section">
        <h2>Пройденные тесты</h2>
        
        <!-- Индикатор загрузки -->
        <div v-if="loadingTestScores" class="loading-tests">
          <div class="spinner spinner-small"></div>
          <p>Загрузка тестов...</p>
        </div>
        
        <!-- Сообщение, если тестов нет -->
        <div v-else-if="testScores.length === 0 && !loadingTestScores" class="no-tests-message">
          У вас пока нет пройденных тестов
        </div>
        
        <!-- Список тестов -->
        <div v-if="testScores.length > 0" class="test-scores-list">
          <div class="test-scores-header">
            <div class="test-name-header">Название теста</div>
            <div class="test-score-header">Результат</div>
            <div class="test-date-header">Дата</div>
          </div>
          
          <div class="test-scores-scroll-container">
            <div 
              v-for="(test, index) in testScores" 
              :key="index" 
              class="test-score-item"
            >
              <div class="test-name">{{ test.testName }}</div>
              <div class="test-score">
                <div class="score-badge" :class="getScoreClass(test.percentScore)">
                  {{ test.percentScore }}%
                </div>
                <div class="score-detail">{{ test.score }}</div>
              </div>
              <div class="test-date">{{ test.formattedDate }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Кнопка выхода из аккаунта -->
      <div class="actions-bar">
        <router-link to="/" class="btn-back">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="back-icon">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
          </svg>
          Вернуться в каталог
        </router-link>
        <router-link to="/logout" class="btn-logout">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="logout-icon">
            <path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/>
          </svg>
          Выйти из аккаунта
        </router-link>
      </div>
    </template>
    
    <!-- Глобальное сообщение о состоянии операции -->
    <div v-if="statusMessage" class="status-message" :class="{ 'error-message': isStatusError }">
      {{ statusMessage }}
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onBeforeUnmount, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import axios from 'axios';
import authService from '../services/auth';

/**
 * Компонент личного кабинета пользователя
 * @description Позволяет пользователю просматривать и редактировать свои данные
 */
export default {
  name: 'ProfilePage',
  
  setup() {
    // Основные состояния
    const router = useRouter();
    const route = useRoute(); // Добавляем доступ к текущему маршруту
    const loading = ref(true);
    const error = ref(false);
    
    // Данные пользователя
    const userData = reactive({
      id: null,
      login: '',
      email: '',
      is_admin: false
    });
    
    // Статистика пользователя
    const userStats = reactive({
      testsCompleted: 0,
      averageScore: '0%',
      favoritesCount: 0
    });
    
    // Список пройденных тестов
    const testScores = ref([]);
    const loadingTestScores = ref(false);
    
    // Состояния для редактирования логина
    const isEditingLogin = ref(false);
    const originalLogin = ref('');
    const loginError = ref('');
    
    // Состояния для смены пароля
    const passwordResetRequested = ref(false);
    
    // Состояние сообщений
    const statusMessage = ref('');
    const isStatusError = ref(false);
    
    // Константы для API
    const BACKEND_PORT = process.env.BACKEND_PORT;
    const SITE_IP = process.env.SITE_IP;
    const apiBase = process.env.NODE_ENV === 'production' 
      ? '/api'
      : `${SITE_IP}:${BACKEND_PORT}/api`;
    
    /**
     * Очистка данных пользователя
     * Предотвращает отображение данных предыдущего пользователя при смене аккаунта
     */
    const clearUserData = () => {
      // Сбрасываем данные пользователя
      userData.id = null;
      userData.login = '';
      userData.email = '';
      userData.is_admin = false;
      
      // Сбрасываем статистику
      userStats.testsCompleted = 0;
      userStats.averageScore = '0%';
      userStats.favoritesCount = 0;
      
      // Сбрасываем состояния UI
      isEditingLogin.value = false;
      originalLogin.value = '';
      loginError.value = '';
      passwordResetRequested.value = false;
      
      // Устанавливаем флаг загрузки
      loading.value = true;
      error.value = '';
      
      // Логируем операцию для отладки
      console.log('Данные пользователя очищены');
    };
    
    /**
     * Загрузка данных пользователя
     * @async
     */
    const loadUserData = async () => {
      try {
        // Сначала очищаем данные для предотвращения отображения старой информации
        clearUserData();
        loading.value = true;
        error.value = '';
        
        console.log('Загрузка данных пользователя...');
        
        // Проверяем, авторизован ли пользователь
        if (!authService.isAuthenticated()) {
          console.error('Пользователь не авторизован');
          router.push('/login');
          return;
        }
        
        // Получаем свежие данные текущего пользователя из localStorage
        const currentUser = authService.getCurrentUser();
        
        if (!currentUser) {
          error.value = 'Не удалось получить данные пользователя';
          return;
        }
        
        // Логируем загрузку данных конкретного пользователя
        console.log(`Загружены данные пользователя: ${currentUser.login}`);
        
        // Заполняем данные пользователя
        userData.id = currentUser.user_id;
        userData.login = currentUser.login;
        userData.email = currentUser.email;
        userData.is_admin = currentUser.is_admin;
        
        // Сохраняем оригинальный логин для отмены изменений
        originalLogin.value = userData.login;
        
        // Загружаем статистику пользователя
        await loadUserStats();
        
        // Автоматически загружаем историю тестов
        loadTestScores();
        
      } catch (err) {
        console.error('Ошибка при загрузке данных пользователя:', err);
        error.value = 'Не удалось загрузить данные пользователя';
      } finally {
        loading.value = false;
      }
    };
    
    /**
     * Обработчик события изменения авторизации
     * Вызывается при входе/выходе пользователя
     */
    const handleAuthChange = () => {
      console.log('Обнаружено изменение авторизации');
      // Перезагружаем данные пользователя, только если мы находимся на странице профиля
      if (route.path === '/profile') {
        console.log('Обновление данных профиля после изменения авторизации');
        loadUserData();
      }
    };
    
    /**
     * Загрузка статистики пользователя
     * @async
     */
    const loadUserStats = async () => {
      try {
        // Загружаем количество пройденных тестов
        // Используем корректный эндпоинт API для получения результатов тестов
        const testsResponse = await axios.get(`${apiBase}/test-scores/`);
        if (testsResponse.data) {
          userStats.testsCompleted = testsResponse.data.length;
          
          // Вычисляем средний балл
          if (userStats.testsCompleted > 0) {
            let totalPercent = 0;
            
            testsResponse.data.forEach(test => {
              const [correct, total] = test.score.split('/');
              const percent = (parseInt(correct) / parseInt(total)) * 100;
              totalPercent += percent;
            });
            
            userStats.averageScore = `${Math.round(totalPercent / userStats.testsCompleted)}%`;
          }
        }
        
        // Загружаем количество избранных животных
        const favoritesResponse = await axios.get(`${apiBase}/animals/favorites/`);
        if (favoritesResponse.data) {
          userStats.favoritesCount = favoritesResponse.data.length;
        }
        
      } catch (err) {
        console.error('Ошибка при загрузке статистики:', err);
        // Не показываем ошибку пользователю, т.к. это не критичная информация
      }
    };
    
    /**
     * Загрузка подробной информации о пройденных тестах
     * @async
     */
    const loadTestScores = async () => {
      loadingTestScores.value = true;
      testScores.value = []; // Очистка предыдущих данных
      
      try {
        // Получаем список всех пройденных тестов
        const testsResponse = await axios.get(`${apiBase}/test-scores/`);
        if (testsResponse.data && testsResponse.data.length > 0) {
          // Сохраняем базовую информацию о тестах
          const testScoresData = testsResponse.data;
          
          // Загружаем информацию о каждом тесте для получения названия
          const testDetails = await Promise.all(
            testScoresData.map(async (score) => {
              try {
                // Получаем информацию о тесте
                const testResponse = await axios.get(`${apiBase}/tests/${score.test_id}`);
                const testName = testResponse.data.name;
                
                // Формируем объект с полной информацией о результате теста
                return {
                  ...score,
                  testName,
                  // Расчет процента правильных ответов
                  percentScore: (() => {
                    const [correct, total] = score.score.split('/');
                    return Math.round((parseInt(correct) / parseInt(total)) * 100);
                  })(),
                  // Форматирование даты (только дата без времени)
                  formattedDate: new Date(score.date).toLocaleString('ru-RU', { 
                    day: '2-digit', 
                    month: '2-digit', 
                    year: 'numeric'
                  })
                };
              } catch (err) {
                console.error(`Ошибка при загрузке информации о тесте ID ${score.test_id}:`, err);
                return {
                  ...score,
                  testName: 'Неизвестный тест',
                  percentScore: 0,
                  formattedDate: new Date(score.date).toLocaleString('ru-RU')
                };
              }
            })
          );
          
          // Сортируем результаты по дате (сначала самые новые)
          testScores.value = testDetails.sort((a, b) => 
            new Date(b.date).getTime() - new Date(a.date).getTime()
          );
          
          console.log('Загружены результаты тестов:', testScores.value);
        }
      } catch (err) {
        console.error('Ошибка при загрузке результатов тестов:', err);
      } finally {
        loadingTestScores.value = false;
      }
    };
    
    /**
     * Начинает редактирование логина
     */
    const startEditingLogin = () => {
      isEditingLogin.value = true;
      originalLogin.value = userData.login;
      loginError.value = '';
    };
    
    /**
     * Отменяет редактирование логина и восстанавливает оригинальное значение
     */
    const cancelEditingLogin = () => {
      userData.login = originalLogin.value;
      isEditingLogin.value = false;
      loginError.value = '';
    };
    
    /**
     * Сохраняет новый логин пользователя
     * @async
     */
    const saveLogin = async () => {
      try {
        loginError.value = '';
        
        // Проверка на пустое значение
        if (!userData.login || userData.login.trim() === '') {
          loginError.value = 'Логин не может быть пустым';
          return;
        }
        
        // Проверка на минимальную длину
        if (userData.login.length < 3) {
          loginError.value = 'Логин должен содержать не менее 3 символов';
          return;
        }
        
        // Если логин не изменился, просто закрываем режим редактирования
        if (userData.login === originalLogin.value) {
          isEditingLogin.value = false;
          return;
        }
        
        // Отправляем запрос на обновление логина
        await axios.put(`${apiBase}/users/update-login`, {
          login: userData.login
        });
        
        // Обновляем данные в localStorage
        const currentUser = authService.getCurrentUser();
        currentUser.login = userData.login;
        localStorage.setItem('user', JSON.stringify(currentUser));
        
        // Выходим из режима редактирования
        isEditingLogin.value = false;
        
        // Показываем уведомление об успехе
        showStatusMessage('Логин успешно обновлен', false);
        
      } catch (err) {
        console.error('Ошибка при обновлении логина:', err);
        
        if (err.response && err.response.status === 409) {
          loginError.value = 'Этот логин уже занят. Пожалуйста, выберите другой.';
        } else {
          loginError.value = 'Не удалось обновить логин';
        }
      }
    };
    
    /**
     * Отправляет запрос на сброс пароля
     * @async
     */
    const requestPasswordReset = async () => {
      try {
        // Отправляем запрос на сброс пароля
        await authService.resetPassword(userData.email);
        
        // Показываем уведомление об успехе
        passwordResetRequested.value = true;
        showStatusMessage('Письмо для смены пароля отправлено на вашу почту', false);
        
      } catch (err) {
        console.error('Ошибка при запросе сброса пароля:', err);
        showStatusMessage('Не удалось отправить письмо для сброса пароля', true);
      }
    };
    
    /**
     * Показывает временное сообщение о состоянии операции
     * @param {string} message - Текст сообщения
     * @param {boolean} isError - true, если это сообщение об ошибке
     */
    const showStatusMessage = (message, isError = false) => {
      statusMessage.value = message;
      isStatusError.value = isError;
      
      // Автоматически убираем сообщение через 5 секунд
      setTimeout(() => {
        statusMessage.value = '';
      }, 5000);
    };
    
    /**
     * Определяет класс для отображения результата теста
     * @param {number} score - Процентная оценка результата теста
     * @returns {string} - Класс для отображения (low, medium, high)
     */
    const getScoreClass = (score) => {
      if (score < 50) return 'low';
      if (score < 75) return 'medium';
      return 'high';
    };
    
    // Запускаем загрузку данных при монтировании компонента
    onMounted(() => {
      // Настраиваем axios для работы с токенами
      axios.interceptors.request.use(config => {
        const token = authService.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      });
      
      // Загружаем данные пользователя
      loadUserData();
      
      // Добавляем слушатель события изменения авторизации
      window.addEventListener('localAuthChange', handleAuthChange);
    });
    
    // Наблюдаем за изменениями маршрута для перезагрузки данных при возвращении на страницу
    watch(
      () => route.path,
      (newPath) => {
        if (newPath === '/profile') {
          console.log('Обнаружен возврат на страницу профиля, обновление данных...');
          loadUserData();
        }
      }
    );
    
    // Убираем слушатель события при размонтировании компонента
    onBeforeUnmount(() => {
      window.removeEventListener('localAuthChange', handleAuthChange);
    });
    
    return {
      userData,
      userStats,
      testScores,
      loadingTestScores,
      loading,
      error,
      isEditingLogin,
      loginError,
      passwordResetRequested,
      statusMessage,
      isStatusError,
      
      loadUserData,
      startEditingLogin,
      cancelEditingLogin,
      saveLogin,
      requestPasswordReset,
      loadTestScores,
      getScoreClass
    };
  }
}
</script>

<style scoped>
.profile-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  position: relative;
}

.logo {
  width: 80px;
  margin-bottom: 20px;
}

h1 {
  font-size: 24px;
  color: #333;
  margin-bottom: 30px;
  text-align: center;
}

h2 {
  font-size: 18px;
  color: #4CAF50;
  margin-bottom: 20px;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 10px;
}

/* Стили для секций профиля */
.profile-section {
  margin-bottom: 40px;
}

/* Стили для формы */
.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #555;
}

.form-group input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 16px;
  box-sizing: border-box;
}

.form-group input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.readonly-input {
  background-color: #f5f5f5 !important;
  cursor: not-allowed;
}

.input-with-button {
  display: flex;
  align-items: center;
}

.input-with-button input {
  flex-grow: 1;
  margin-right: 10px;
}

.input-error {
  border-color: #e53935 !important;
}

.error-text {
  color: #e53935;
  font-size: 14px;
  margin-top: 5px;
}

.info-text {
  color: #757575;
  font-size: 14px;
  margin-top: 5px;
}

.success-text {
  color: #4CAF50;
}

/* Стили для блока пароля */
.password-section {
  margin-top: 30px;
}

.password-display {
  display: flex;
  align-items: center;
}

.password-dots {
  flex-grow: 1;
  padding: 12px;
  background-color: #f5f5f5;
  border: 1px solid #ccc;
  border-radius: 4px;
  margin-right: 10px;
  color: #333;
  font-family: monospace;
  letter-spacing: 3px;
}

/* Стили для кнопок */
.btn-primary,
.btn-secondary,
.btn-back,
.btn-logout {
  padding: 12px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  text-decoration: none;
  display: inline-block;
  text-align: center;
  transition: background-color 0.3s, color 0.3s;
}

.btn-primary {
  background-color: #4CAF50;
  color: white;
  border: none;
}

.btn-primary:hover {
  background-color: #45a049;
}

.btn-secondary {
  background-color: white;
  color: #4CAF50;
  border: 1px solid #4CAF50;
}

.btn-secondary:hover {
  background-color: #f1f8e9;
}

.btn-secondary:disabled {
  border-color: #a5d6a7;
  color: #a5d6a7;
  cursor: not-allowed;
}

/* Стили для кнопок действий */
.edit-button,
.save-button,
.cancel-button {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.3s;
}

.edit-button {
  background-color: #f5f5f5;
}

.edit-button:hover {
  background-color: #e0e0e0;
}

.save-button {
  background-color: #4CAF50;
  margin-right: 5px;
}

.save-button:hover {
  background-color: #45a049;
}

.cancel-button {
  background-color: #f44336;
}

.cancel-button:hover {
  background-color: #e53935;
}

.edit-icon,
.save-icon,
.cancel-icon {
  width: 20px;
  height: 20px;
}

.edit-icon {
  fill: #2196F3;
}

.save-icon {
  fill: white;
}

.cancel-icon {
  fill: white;
}

.action-buttons {
  display: flex;
}

/* Стили для блока статистики */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

/* Для админа - только две карточки статистики */
.admin-stats-grid {
  grid-template-columns: repeat(2, 1fr);
}

.stat-card {
  background-color: #f5f5f5;
  border-radius: 8px;
  padding: 15px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #4CAF50;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #757575;
}

/* Стили для блока пройденных тестов */
.test-scores-list {
  margin-top: 20px;
}

.test-scores-header {
  display: flex;
  padding: 0 10px;
  font-weight: bold;
  color: #555;
  margin-bottom: 10px;
}

.test-name-header {
  flex: 2;
  text-align: left;
}

.test-score-header,
.test-date-header {
  flex: 1;
  text-align: center;
}

.test-scores-scroll-container {
  /* Устанавливаем фиксированную высоту для отображения ровно 3 записей */
  height: 150px; /* Высота для 3 записей при высоте строки 50px */
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background-color: #f9f9f9;
}

.test-score-item {
  display: flex;
  padding: 12px 10px;
  border-bottom: 1px solid #e0e0e0;
  align-items: center;
  /* Устанавливаем фиксированную высоту для строки */
  height: 26px; /* 50px с учётом padding */
}

.test-score-item:hover {
  background-color: #f0f0f0;
}

.test-score-item:last-child {
  border-bottom: none;
}

.test-name {
  flex: 2;
  text-align: left;
  font-weight: 500;
}

.test-score,
.test-date {
  flex: 1;
  text-align: center;
}

.score-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
  color: white;
}

.score-badge.low {
  background-color: #f44336;
}

.score-badge.medium {
  background-color: #ff9800;
}

.score-badge.high {
  background-color: #4CAF50;
}

.score-detail {
  font-size: 12px;
  color: #757575;
  margin-top: 3px;
}

.load-tests-button {
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 10px 15px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.3s;
  margin-top: 10px;
}

.load-tests-button:hover {
  background-color: #45a049;
}

.no-tests-message {
  padding: 15px;
  text-align: center;
  color: #757575;
  font-style: italic;
}

.loading-tests {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 15px;
}

.loading-tests p {
  margin-top: 10px;
  color: #757575;
}

/* Стили для блока действий */
.actions-bar {
  display: flex;
  justify-content: space-between;
  margin-top: 40px;
}

.btn-back,
.btn-logout {
  display: flex;
  align-items: center;
  font-weight: 500;
}

.btn-back {
  color: #757575;
}

.btn-back:hover {
  color: #4CAF50;
}

.btn-logout {
  color: #f44336;
}

.btn-logout:hover {
  color: #e53935;
}

.back-icon,
.logout-icon {
  width: 20px;
  height: 20px;
  margin-right: 5px;
}

.back-icon {
  fill: currentColor;
}

.logout-icon {
  fill: currentColor;
}

/* Стили для блока с уведомлением администратора */
.info-block {
  margin-top: 20px;
}

.admin-badge {
  display: inline-flex;
  align-items: center;
  background-color: #ffecb3;
  padding: 8px 15px;
  border-radius: 20px;
  font-size: 14px;
  color: #ff9800;
  font-weight: 500;
}

.admin-icon {
  width: 20px;
  height: 20px;
  fill: #ff9800;
  margin-right: 5px;
}

/* Стили для состояний загрузки и ошибок */
.loading-container,
.error-container {
  text-align: center;
  padding: 30px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-left-color: #4CAF50;
  animation: spin 1s linear infinite;
  margin: 0 auto 15px;
}

.spinner-small {
  width: 20px;
  height: 20px;
  border-width: 2px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-icon {
  margin: 0 auto 20px;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background-color: #f8d7da;
  display: flex;
  align-items: center;
  justify-content: center;
}

.error-svg {
  width: 40px;
  height: 40px;
  fill: #e53935;
}

.error-message {
  color: #e53935;
}

/* Стили для всплывающего уведомления */
.status-message {
  position: fixed;
  bottom: 20px;
  right: 20px;
  padding: 15px 20px;
  background-color: #4CAF50;
  color: white;
  border-radius: 4px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  z-index: 1000;
  animation: fadeIn 0.3s, fadeOut 0.3s 4.7s;
}

.status-message.error-message {
  background-color: #f44336;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeOut {
  from { opacity: 1; transform: translateY(0); }
  to { opacity: 0; transform: translateY(20px); }
}

/* Медиа-запросы для адаптивности */
@media (max-width: 600px) {
  .profile-container {
    padding: 15px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  
  .actions-bar {
    flex-direction: column;
    gap: 15px;
  }
  
  .btn-back,
  .btn-logout {
    width: 100%;
    justify-content: center;
  }
}
</style>