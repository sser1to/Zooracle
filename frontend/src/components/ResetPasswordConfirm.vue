<template>
  <div class="auth-container">
    <img alt="Лого" src="../assets/logo.png" class="logo">
    <h1>Новый пароль</h1>
    
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
          <!-- Заменяем i-элементы на SVG иконки -->
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
          <!-- Заменяем i-элементы на SVG иконки -->
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
    
    // Данные формы
    const passwordData = reactive({
      password: '',
      confirm_password: ''
    });

    /**
     * Получение токена перед монтированием компонента для избежания проблем с рендерингом
     * @returns {void}
     */
    onBeforeMount(() => {
      // Логирование для отладки
      console.log('ResetPasswordConfirm: onBeforeMount вызван');
      console.log('Токен из props:', props.token);
      console.log('URL параметры:', route.query);

      // Получаем токен из пропсов или из URL
      if (props.token) {
        token.value = props.token;
        console.log('Токен получен из пропсов:', token.value);
      } else if (route.query && route.query.token) {
        token.value = route.query.token;
        console.log('Токен получен из URL:', token.value);
      } else {
        console.warn('Токен не найден ни в пропсах, ни в URL');
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
        console.error('Токен не был получен при монтировании компонента');
      } else {
        console.log('Компонент успешно смонтирован с токеном');
      }
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
        // Отправка запроса на API для сброса пароля
        await axios.post('/api/auth/reset-password/confirm', {
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
          message.value = err.response.data.detail || 'Произошла ошибка при сбросе пароля';
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
      goToLogin
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