<template>
  <div class="auth-container">
    <img alt="Лого" src="../assets/logo.png" class="logo">
    <h1>Новый пароль</h1>
    
    <div v-if="isTokenChecking" class="loading-container">
      <div class="spinner"></div>
      <p>Проверка ссылки...</p>
    </div>
    
    <div v-else-if="!isTokenValid" class="invalid-token-container">
      <div class="error-icon">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="error-svg">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
        </svg>
      </div>
      <h2>Недействительная ссылка</h2>
      <p>{{ tokenErrorMessage }}</p>
      <button @click="goToLogin" class="btn-primary">Вернуться на страницу входа</button>
    </div>
    
    <template v-else>
      <form @submit.prevent="resetPassword">
        <div class="form-group">
          <input 
            :type="showPassword ? 'text' : 'password'" 
            v-model="passwordData.password" 
            placeholder="Введите новый пароль"
            required
            minlength="6"
          />
          <span class="password-toggle" @click="togglePassword">
            <svg v-if="showPassword" class="eye-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
              <path d="M12 4C7 4 2.73 7.11 1 12C2.73 16.89 7 20 12 20C17 20 21.27 16.89 23 12C21.27 7.11 17 4 12 4ZM12 16C9.79 16 8 14.21 8 12C8 9.79 9.79 8 12 8C14.21 8 16 9.79 16 12C16 14.21 14.21 16 12 16ZM12 10C10.9 10 10 10.9 10 12C10 13.1 10.9 14 12 14C13.1 14 14 13.1 14 12C14 10.9 13.1 10 12 10Z"/>
            </svg>
            <svg v-else class="eye-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
              <path d="M12 4C7 4 2.73 7.11 1 12C2.73 16.89 7 20 12 20C17 20 21.27 16.89 23 12C21.27 7.11 17 4 12 4ZM12 16C9.79 16 8 14.21 8 12C8 9.79 9.79 8 12 8C14.21 8 16 9.79 16 12C16 14.21 14.21 16 12 16Z"/>
            </svg>
          </span>
        </div>
        
        <div class="form-group">
          <input 
            :type="showConfirmPassword ? 'text' : 'password'" 
            v-model="passwordData.confirm_password" 
            placeholder="Подтвердите новый пароль"
            required
            minlength="6"
          />
          <span class="password-toggle" @click="toggleConfirmPassword">
            <svg v-if="showConfirmPassword" class="eye-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
              <path d="M12 4C7 4 2.73 7.11 1 12C2.73 16.89 7 20 12 20C17 20 21.27 16.89 23 12C21.27 7.11 17 4 12 4ZM12 16C9.79 16 8 14.21 8 12C8 9.79 9.79 8 12 8C14.21 8 16 9.79 16 12C16 14.21 14.21 16 12 16ZM12 10C10.9 10 10 10.9 10 12C10 13.1 10.9 14 12 14C13.1 14 14 13.1 14 12C14 10.9 13.1 10 12 10Z"/>
            </svg>
            <svg v-else class="eye-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
              <path d="M12 4C7 4 2.73 7.11 1 12C2.73 16.89 7 20 12 20C17 20 21.27 16.89 23 12C21.27 7.11 17 4 12 4ZM12 16C9.79 16 8 14.21 8 12C8 9.79 9.79 8 12 8C14.21 8 16 9.79 16 12C16 14.21 14.21 16 12 16Z"/>
            </svg>
          </span>
        </div>
        
        <button type="submit" class="btn-primary" :disabled="isLoading">
          {{ isLoading ? 'Сохранение...' : 'Сохранить новый пароль' }}
        </button>
      </form>
      
      <div class="auth-footer">
        <button @click="goToLogin" class="btn-secondary">Вернуться на страницу входа</button>
      </div>

      <div v-if="message" class="message" :class="{ 'error-message': isError }">
        {{ message }}
      </div>
    </template>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onBeforeMount } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import axios from 'axios';

/**
 * Компонент для подтверждения сброса пароля по токену из email
 * @description Позволяет пользователю установить новый пароль после восстановления
 */
export default {
  name: 'ResetPasswordConfirm',
  
  // Принимаем токен через пропсы (альтернативный способ получения)
  props: {
    token: {
      type: String,
      default: ''
    }
  },

  setup(props) {
    const router = useRouter();
    const route = useRoute();
    
    // Состояния для паролей и их отображения
    const showPassword = ref(false);
    const showConfirmPassword = ref(false);
    const message = ref('');
    const isError = ref(false);
    const isLoading = ref(false);
    const token = ref('');

    // Новые состояния для проверки токена
    const isTokenValid = ref(true); // Предполагаем, что токен действителен изначально
    const isTokenChecking = ref(true); // Флаг проверки токена
    const tokenErrorMessage = ref('Недействительная ссылка для сброса пароля');
    
    // Данные формы
    const passwordData = reactive({
      password: '',
      confirm_password: ''
    });

    /**
     * Переводит код причины невалидности токена в понятное сообщение
     * @param {String} reason - Код причины невалидности токена
     * @returns {String} - Сообщение для пользователя
     */
    const getErrorMessageByReason = (reason) => {
      const errorMessages = {
        'token_not_found': 'Ссылка для сброса пароля не найдена',
        'token_used': 'Эта ссылка уже была использована для смены пароля',
        'token_expired': 'Срок действия ссылки для сброса пароля истек',
        'token_invalid': 'Ссылка для сброса пароля недействительна',
        'user_not_found': 'Пользователь не найден',
        'email_changed': 'Email пользователя изменился после запроса сброса пароля',
        'default': 'Недействительная ссылка для сброса пароля'
      };
      
      return errorMessages[reason] || errorMessages.default;
    };

    /**
     * Проверка валидности токена на сервере
     * @async
     * @returns {Promise<void>}
     */
    const validateToken = async () => {
      if (!token.value) {
        console.error('Попытка проверки токена без токена');
        isTokenValid.value = false;
        tokenErrorMessage.value = 'Отсутствует токен для сброса пароля';
        isTokenChecking.value = false;
        return;
      }

      try {
        console.log('Проверка валидности токена на сервере');
        const apiUrl = `${axios.defaults.baseURL}/api/auth/reset-password/validate-token/${token.value}`;
        console.log(`Используется URL API: ${apiUrl}`);
        
        const response = await axios.get(apiUrl);
        const data = response.data;
        
        console.log('Результат проверки токена:', data);
        
        if (data.valid) {
          console.log('Токен действителен');
          isTokenValid.value = true;
        } else {
          console.warn(`Токен недействителен. Причина: ${data.reason}`);
          isTokenValid.value = false;
          tokenErrorMessage.value = getErrorMessageByReason(data.reason);
        }
      } catch (err) {
        console.error('Ошибка при проверке токена:', err);
        isTokenValid.value = false;
        tokenErrorMessage.value = 'Ошибка при проверке ссылки для сброса пароля';
      } finally {
        isTokenChecking.value = false;
      }
    };

    /**
     * Получение токена перед монтированием компонента для избежания проблем с рендерингом
     * @returns {void}
     */
    onBeforeMount(() => {
      // Логирование для отладки
      console.log('ResetPasswordConfirm: onBeforeMount вызван');
      console.log('Токен из props:', props.token);
      console.log('URL параметры:', route.query);
      
      // Получаем токен из разных возможных источников
      if (props.token) {
        // 1. Из пропсов (если передан напрямую)
        token.value = props.token;
        console.log('Токен получен из пропсов:', token.value);
      } else if (route.query && route.query.token) {
        // 2. Из параметров URL (стандартный способ)
        token.value = route.query.token;
        console.log('Токен получен из URL параметров:', token.value);
      } else {
        // 3. Попытка извлечь токен из последнего сегмента URL (альтернативный формат)
        const urlSegments = window.location.pathname.split('/');
        const lastSegment = urlSegments[urlSegments.length - 1];
        if (lastSegment && lastSegment !== 'confirm') {
          token.value = lastSegment;
          console.log('Токен извлечен из последнего сегмента URL:', token.value);
        } else {
          console.warn('Токен не найден ни в одном из источников');
        }
      }

      // Если токен найден, выводим только первые и последние 5 символов для безопасности
      if (token.value) {
        const tokenLength = token.value.length;
        const maskedToken = tokenLength > 10 
          ? `${token.value.substring(0, 5)}...${token.value.substring(tokenLength - 5)}`
          : token.value;
        console.log(`Найденный токен (маскированный): ${maskedToken}`);
      }
    });

    /**
     * При загрузке компонента проверяем наличие токена и отображаем ошибку при необходимости
     * @returns {void}
     */
    onMounted(() => {
      console.log('ResetPasswordConfirm: onMounted вызван');
      
      // Если токен всё ещё не получен, отображаем ошибку
      if (!token.value) {
        isError.value = true;
        message.value = 'Недействительная ссылка для сброса пароля. Отсутствует токен.';
        isTokenValid.value = false;
        isTokenChecking.value = false;
        console.error('Токен не был получен при монтировании компонента');
      } else {
        console.log('Компонент успешно смонтирован с токеном');
        // Проверяем валидность токена на сервере
        validateToken();
      }

      // Добавляем проверку на правильность загрузки ресурсов
      document.addEventListener('DOMContentLoaded', () => {
        const stylesheets = document.styleSheets;
        let loadedStyles = 0;
        
        for (let i = 0; i < stylesheets.length; i++) {
          try {
            if (stylesheets[i].cssRules) {
              loadedStyles++;
            }
          } catch (e) {
            console.error('Ошибка при проверке стилей:', e);
          }
        }
        
        console.log(`Загружено ${loadedStyles} из ${stylesheets.length} таблиц стилей`);
        
        if (loadedStyles === 0) {
          console.warn('Не загружены таблицы стилей. Возможны проблемы с отображением.');
        }
      });
    });

    /**
     * Отправка запроса на сброс пароля
     * @async
     * @returns {Promise<void>}
     */
    const resetPassword = async () => {
      try {
        console.log('Начинается процесс сброса пароля');
        isLoading.value = true;
        isError.value = false;
        message.value = '';
        
        // Проверка наличия токена
        if (!token.value) {
          console.error('Попытка сброса пароля без токена');
          isError.value = true;
          message.value = 'Недействительная ссылка для сброса пароля. Отсутствует токен.';
          return;
        }
        
        // Проверка совпадения паролей на стороне клиента
        if (passwordData.password !== passwordData.confirm_password) {
          console.warn('Пароли не совпадают');
          isError.value = true;
          message.value = 'Пароли не совпадают';
          return;
        }
        
        // Проверка длины пароля
        if (passwordData.password.length < 6) {
          console.warn('Пароль слишком короткий');
          isError.value = true;
          message.value = 'Пароль должен быть не менее 6 символов';
          return;
        }
        
        console.log('Отправка запроса на сервер для сброса пароля');
        // Отправка запроса на API для сброса пароля с использованием абсолютного пути
        const apiUrl = `${axios.defaults.baseURL}/api/auth/reset-password/confirm`;
        console.log(`Используется URL API: ${apiUrl}`);
        
        await axios.post(apiUrl, {
          token: token.value,
          password: passwordData.password,
          confirm_password: passwordData.confirm_password
        });
        
        // Успешный сброс пароля
        console.log('Пароль успешно сброшен');
        message.value = 'Пароль успешно изменен! Перенаправление на страницу входа...';
        
        // Добавляем задержку перед переадресацией
        setTimeout(() => {
          console.log('Перенаправление на страницу входа');
          router.push('/login');
        }, 3000);
        
      } catch (err) {
        isError.value = true;
        
        if (err.response && err.response.data) {
          console.error('Ошибка ответа от сервера:', err.response.data);
          
          // Проверяем сообщение об ошибке от сервера
          const errorDetail = err.response.data.detail || '';
          
          // Если токен недействителен или истек, отмечаем это и показываем соответствующее сообщение
          if (errorDetail.includes('Недействительная или истекшая ссылка')) {
            isTokenValid.value = false;
            tokenErrorMessage.value = errorDetail;
          } else {
            // Другие ошибки
            message.value = errorDetail || 'Произошла ошибка при сбросе пароля';
          }
        } else {
          console.error('Общая ошибка:', err);
          message.value = 'Произошла ошибка при сбросе пароля. Проверьте подключение к сети.';
        }
      } finally {
        isLoading.value = false;
      }
    };

    /**
     * Переключение видимости пароля
     * @returns {void}
     */
    const togglePassword = () => {
      showPassword.value = !showPassword.value;
      console.log('Видимость пароля переключена:', showPassword.value);
    };

    /**
     * Переключение видимости подтверждения пароля
     * @returns {void}
     */
    const toggleConfirmPassword = () => {
      showConfirmPassword.value = !showConfirmPassword.value;
      console.log('Видимость подтверждения пароля переключена:', showConfirmPassword.value);
    };

    /**
     * Переход на страницу входа
     * @returns {void}
     */
    const goToLogin = () => {
      console.log('Переход на страницу входа');
      router.push('/login');
    };

    return {
      passwordData,
      message,
      isError,
      isLoading,
      showPassword,
      showConfirmPassword,
      resetPassword,
      togglePassword,
      toggleConfirmPassword,
      goToLogin,
      isTokenValid,
      isTokenChecking,
      tokenErrorMessage
    };
  }
}
</script>

<style scoped>
.auth-container {
  max-width: 400px;
  margin: 0 auto;
  padding: 20px;
  text-align: center;
  background-color: #fff; /* Явно указываем белый фон контейнера */
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); /* Добавляем тень для видимости на белом фоне */
}

/* Добавляем базовые стили для body на случай, если глобальные стили не загружаются */
:root {
  --background-color: #f5f5f5;
  --text-color: #333;
}

/* Стили для отображения состояния проверки токена */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: 30px 0;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-left-color: #4CAF50;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Стили для отображения ошибки токена */
.invalid-token-container {
  padding: 20px 0;
  text-align: center;
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

.invalid-token-container h2 {
  color: #e53935;
  margin-bottom: 15px;
}

.invalid-token-container p {
  margin-bottom: 20px;
  color: #666;
}

/* Остальные стили идентичны оригинальному компоненту */
.logo {
  width: 80px;
  margin-bottom: 20px;
}

.form-group {
  position: relative;
  margin-bottom: 15px;
}

input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 16px;
  box-sizing: border-box;
}

.password-toggle {
  position: absolute;
  right: 15px;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
}

/* Стили для SVG иконок */
.eye-icon {
  width: 20px;
  height: 20px;
  fill: #666;
}

.btn-primary {
  width: 100%;
  padding: 12px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  margin-bottom: 15px;
  transition: background-color 0.3s;
}

.btn-primary:hover {
  background-color: #45a049;
}

.btn-primary:disabled {
  background-color: #a5d6a7;
  cursor: not-allowed;
}

.btn-secondary {
  width: 100%;
  padding: 12px;
  background-color: white;
  color: #4CAF50;
  border: 1px solid #4CAF50;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  text-decoration: none;
  display: inline-block;
  transition: background-color 0.3s, color 0.3s;
}

.btn-secondary:hover {
  background-color: #f1f8e9;
}

.error-message {
  color: #e53935;
  margin-top: 15px;
  font-weight: 500;
}

.message {
  color: #43a047;
  margin-top: 15px;
  font-weight: 500;
}
</style>