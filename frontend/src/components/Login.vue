<template>
  <div class="auth-container">
    <img alt="Лого" src="../assets/logo.png" class="logo">
    <h1>Вход</h1>
    
    <form @submit.prevent="login">
      <div class="form-group">
        <input 
          type="text" 
          v-model="loginData.username" 
          placeholder="Логин/почта"
          required
        />
      </div>
      
      <div class="form-group">
        <input 
          :type="showPassword ? 'text' : 'password'" 
          v-model="loginData.password" 
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
      
      <div class="forgot-password">
        <router-link to="/reset-password">Забыли пароль?</router-link>
      </div>
      
      <button type="submit" class="btn btn-primary">Войти</button>
    </form>
    
    <div class="auth-footer">
      <router-link to="/register" class="btn btn-secondary register-btn">Зарегистрироваться</router-link>
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
  name: 'LoginForm',
  setup() {
    const router = useRouter();
    const error = ref('');
    const showPassword = ref(false);
    const loginData = reactive({
      username: '',
      password: ''
    });

    const login = async () => {
      try {
        error.value = '';
        const result = await authService.login(loginData.username, loginData.password);
        if (result) {
          // Создаем и диспетчеризируем специальное событие для уведомления других компонентов
          // о том, что произошла авторизация на этой же странице (без перезагрузки)
          window.dispatchEvent(new CustomEvent('localAuthChange', {
            detail: { action: 'login', user: result }
          }));
          
          console.log('Успешная авторизация, переадресация на главную страницу');
          
          // Короткая задержка для обеспечения обработки события
          setTimeout(() => {
            router.push('/');
          }, 100);
        }
      } catch (err) {
        error.value = err.response?.data?.detail || 'Ошибка при входе. Проверьте логин и пароль.';
      }
    };

    const togglePassword = () => {
      showPassword.value = !showPassword.value;
    };

    return {
      loginData,
      error,
      login,
      showPassword,
      togglePassword
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

.forgot-password {
  text-align: right;
  margin: 10px 0 20px;
}

.forgot-password a {
  color: #4CAF50;
  text-decoration: none;
}

.btn-primary, .btn {
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

/* Переопределяем ширину для кнопки регистрации, чтобы она соответствовала размеру формы */
.register-btn {
  width: 100%; /* Устанавливаем явную ширину на 100% от контейнера */
  box-sizing: border-box; /* Учитываем границы и отступы в рамках ширины */
  margin: 0 auto; /* Центрирование */
  display: block; /* Делаем блочным для контроля ширины */
  max-width: 100%; /* Ограничиваем максимальную ширину контейнером */
  overflow: hidden; /* Предотвращаем выход за границы */
  text-overflow: ellipsis; /* При необходимости обрезаем текст */
  white-space: nowrap; /* Предотвращаем перенос текста */
}

/* Дополнительно устанавливаем стили для всех кнопок в форме для единообразия */
.btn {
  width: 100%;
  box-sizing: border-box;
  margin-bottom: 15px;
}
</style>