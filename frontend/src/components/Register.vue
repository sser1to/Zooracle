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
          <!-- Здесь будет иконка показа/скрытия пароля -->
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
          <!-- Здесь будет иконка показа/скрытия пароля -->
        </span>
      </div>
      
      <button type="submit" class="btn-primary">Зарегистрироваться</button>
    </form>
    
    <div class="auth-footer">
      <button @click="goBack" class="btn-secondary">Назад</button>
    </div>

    <div v-if="error" class="error-message">
      {{ error }}
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
    const registerData = reactive({
      login: '',
      email: '',
      password: '',
      confirmPassword: ''
    });

    const register = async () => {
      try {
        error.value = '';
        
        // Более строгие проверки на стороне клиента
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
        
        // Информируем пользователя о начале процесса
        error.value = 'Выполняется регистрация...';
        
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
          // При успешной регистрации даем положительное сообщение перед переходом
          error.value = 'Регистрация успешна! Перенаправление на страницу входа...';
          error.value = ''; // Очищаем сообщение об ошибке
          
          // Добавляем небольшую задержку, чтобы пользователь увидел сообщение об успехе
          setTimeout(() => {
            router.push('/login');
          }, 1000);
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
      }
    };

    const togglePassword = () => {
      showPassword.value = !showPassword.value;
    };

    const toggleConfirmPassword = () => {
      showConfirmPassword.value = !showConfirmPassword.value;
    };

    const goBack = () => {
      router.push('/login');
    };

    return {
      registerData,
      error,
      register,
      showPassword,
      showConfirmPassword,
      togglePassword,
      toggleConfirmPassword,
      goBack
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
}

.error-message {
  color: red;
  margin-top: 15px;
}
</style>