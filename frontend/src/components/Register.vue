<template>
  <div class="auth-container">
    <img alt="Лого" src="../assets/logo.png" class="logo">
    <h1>Регистрация</h1>
    
    <form @submit.prevent="register">
      <div class="form-group">
        <input 
          type="text" 
          v-model="registerData.login" 
          placeholder="Логин"
          required
        />
      </div>
      
      <div class="form-group">
        <input 
          type="email" 
          v-model="registerData.email" 
          placeholder="Почта"
          required
        />
      </div>
      
      <div class="form-group">
        <input 
          :type="showPassword ? 'text' : 'password'" 
          v-model="registerData.password" 
          placeholder="Пароль"
          required
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
          v-model="registerData.confirmPassword" 
          placeholder="Подтвердите пароль"
          required
        />
        <span class="password-toggle" @click="toggleConfirmPassword">
          <svg v-if="showConfirmPassword" class="eye-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path d="M12 4C7 4 2.73 7.11 1 12C2.73 16.89 7 20 12 20C17 20 21.27 16.89 23 12C21.27 7.11 17 4 12 4ZM12 16C9.79 16 8 14.21 8 12C8 9.79 9.79 8 12 8C14.21 8 16 9.79 16 12C16 14.21 14.21 16 12 16Z"/>
          </svg>
          <svg v-else class="eye-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path d="M12 4C7 4 2.73 7.11 1 12C2.73 16.89 7 20 12 20C17 20 21.27 16.89 23 12C21.27 7.11 17 4 12 4ZM12 16C9.79 16 8 14.21 8 12C8 9.79 9.79 8 12 8C14.21 8 16 9.79 16 12C16 14.21 14.21 16 12 16Z"/>
          </svg>
        </span>
      </div>
      
      <button type="submit" class="btn btn-primary">Зарегистрироваться</button>
    </form>
    
    <div class="auth-footer">
      <button @click="goBack" class="btn btn-secondary">Назад</button>
    </div>

    <div v-if="error" class="error-message">
      {{ error }}
    </div>
    
    <div v-if="isLoading" class="loading-spinner">
      <div class="spinner"></div>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import authService from '../services/auth.js';

export default {
  name: 'RegisterForm',
  setup() {
    const router = useRouter();
    const error = ref('');
    const showPassword = ref(false);
    const showConfirmPassword = ref(false);
    const isLoading = ref(false);
    const registerData = reactive({
      login: '',
      email: '',
      password: '',
      confirmPassword: ''
    });

    /**
     * Сбрасывает форму к начальному состоянию
     * Очищает все поля ввода и возвращает индикаторы видимости паролей в исходное состояние
     */
    const resetForm = () => {
      // Очищаем все поля формы
      registerData.login = '';
      registerData.email = '';
      registerData.password = '';
      registerData.confirmPassword = '';
      
      // Сбрасываем видимость паролей
      showPassword.value = false;
      showConfirmPassword.value = false;
      
      // Очищаем сообщение об ошибке
      error.value = '';
    };

    const register = async () => {
      try {
        error.value = '';
        
        // Проверка логина
        if (!registerData.login.trim()) {
          error.value = 'Логин не может быть пустым';
          return;
        }

        if (registerData.login.length < 3) {
          error.value = 'Логин должен содержать не менее 3 символов';
          return;
        }
        
        // Проверка совпадения паролей
        if (registerData.password !== registerData.confirmPassword) {
          error.value = 'Пароли не совпадают';
          return;
        }
        
        // Проверка длины пароля
        if (registerData.password.length < 6) {
          error.value = 'Пароль должен быть не менее 6 символов';
          return;
        }
        
        // Проверка формата email с использованием регулярного выражения
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(registerData.email)) {
          error.value = 'Введите корректный адрес электронной почты';
          return;
        }
        
        // Показываем индикатор загрузки
        isLoading.value = true;
        
        console.log('Отправка запроса на регистрацию:', { 
          login: registerData.login, 
          email: registerData.email 
        });
        
        const result = await authService.register(
          registerData.login, 
          registerData.email, 
          registerData.password
        );
        
        console.log('Ответ от сервера:', result);
        
        if (result) {
          // Сбрасываем форму к начальному состоянию
          resetForm();
          
          // После успешной регистрации перенаправляем на страницу верификации email
          router.push({
            name: 'verify-email',
            params: { email: result.email || registerData.email }
          });
        }
      } catch (err) {
        console.error('Ошибка при регистрации:', err);
        
        // Улучшенная обработка ошибок
        if (err.response) {
          console.error('Данные ответа:', err.response.data);
          console.error('Статус:', err.response.status);
          
          // Обработка ошибок по коду статуса
          switch (err.response.status) {
            case 400:
              // Обработка ошибок валидации и бизнес-логики
              error.value = err.response.data?.detail || 'Ошибка валидации данных';
              break;
              
            case 422:
              // Обработка ошибок валидации Pydantic
              try {
                const validationErrors = err.response.data.detail;
                if (Array.isArray(validationErrors)) {
                  // Формируем читаемое сообщение из ошибок валидации
                  const errMessages = validationErrors.map(err => {
                    const field = err.loc[err.loc.length - 1];
                    const msg = err.msg;
                    return `${field}: ${msg}`;
                  });
                  error.value = `Ошибка валидации: ${errMessages.join('; ')}`;
                } else if (typeof validationErrors === 'object') {
                  error.value = `Ошибка валидации: ${JSON.stringify(validationErrors)}`;
                } else {
                  error.value = `Ошибка валидации: ${validationErrors || 'Неизвестная ошибка'}`;
                }
              } catch (e) {
                error.value = `Ошибка валидации данных. Проверьте правильность заполнения полей.`;
              }
              break;
              
            case 401:
              error.value = 'Ошибка авторизации. Проверьте правильность учетных данных.';
              break;
              
            case 403:
              error.value = 'Доступ запрещен. У вас нет прав для выполнения этой операции.';
              break;
              
            case 404:
              error.value = 'Ресурс не найден. Возможно, страница была перемещена или удалена.';
              break;
              
            case 500:
              // Для ошибок сервера показываем более дружественное сообщение
              error.value = 'Внутренняя ошибка сервера. Пожалуйста, попробуйте позже или обратитесь к администратору.';
              
              // Для отладки смотрим детали в консоли
              if (err.response.data?.detail) {
                console.error('Детали ошибки 500:', err.response.data.detail);
              }
              break;
              
            default:
              error.value = `Ошибка ${err.response.status}: ${err.response.data?.detail || JSON.stringify(err.response.data)}`;
          }
        } else if (err.request) {
          console.error('Нет ответа от сервера:', err.request);
          error.value = 'Сервер не отвечает. Проверьте соединение с сервером.';
        } else {
          console.error('Ошибка запроса:', err.message);
          error.value = `Ошибка запроса: ${err.message}`;
        }
      } finally {
        isLoading.value = false;
      }
    };

    const togglePassword = () => {
      showPassword.value = !showPassword.value;
    };

    const toggleConfirmPassword = () => {
      showConfirmPassword.value = !showConfirmPassword.value;
    };

    const goBack = () => {
      // Сбрасываем форму перед возвратом на страницу логина
      resetForm();
      router.push('/login');
    };

    return {
      registerData,
      error,
      register,
      showPassword,
      showConfirmPassword,
      isLoading,
      togglePassword,
      toggleConfirmPassword,
      goBack,
      resetForm
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
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  position: relative;
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

.btn, .btn-primary {
  width: 100%;
  padding: 12px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  margin-bottom: 10px;
  transition: background-color 0.3s;
}

.btn-primary:hover, .btn.btn-primary:hover {
  background-color: #45a049;
}

.btn-secondary, .btn.btn-secondary {
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

.btn-secondary:hover, .btn.btn-secondary:hover {
  background-color: #f1f8e9;
}

.error-message {
  color: #e53935;
  margin-top: 15px;
  font-weight: 500;
}

.auth-footer {
  margin-top: 5px;
}

/* Стили для индикатора загрузки */
.loading-spinner {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: rgba(255, 255, 255, 0.8);
  border-radius: 8px;
  z-index: 10;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 5px solid #f3f3f3;
  border-top: 5px solid #4CAF50;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>