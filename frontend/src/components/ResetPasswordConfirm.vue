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
          <i :class="showPassword ? 'eye-slash' : 'eye'"></i>
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
          <i :class="showConfirmPassword ? 'eye-slash' : 'eye'"></i>
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
import { ref, reactive, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import axios from 'axios';

/**
 * Компонент для подтверждения сброса пароля по токену из email
 */
export default {
  name: 'ResetPasswordConfirm',
  setup() {
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
     * При загрузке компонента извлекаем токен из URL
     */
    onMounted(() => {
      token.value = route.query.token;
      
      if (!token.value) {
        isError.value = true;
        message.value = 'Недействительная ссылка для сброса пароля. Отсутствует токен.';
      }
    });

    /**
     * Отправка запроса на сброс пароля
     */
    const resetPassword = async () => {
      try {
        isLoading.value = true;
        isError.value = false;
        message.value = '';
        
        // Проверка наличия токена
        if (!token.value) {
          isError.value = true;
          message.value = 'Недействительная ссылка для сброса пароля. Отсутствует токен.';
          return;
        }
        
        // Проверка совпадения паролей на стороне клиента
        if (passwordData.password !== passwordData.confirm_password) {
          isError.value = true;
          message.value = 'Пароли не совпадают';
          return;
        }
        
        // Проверка длины пароля
        if (passwordData.password.length < 6) {
          isError.value = true;
          message.value = 'Пароль должен быть не менее 6 символов';
          return;
        }
        
        // Отправка запроса на API для сброса пароля
        await axios.post('/api/auth/reset-password/confirm', {
          token: token.value,
          password: passwordData.password,
          confirm_password: passwordData.confirm_password
        });
        
        // Успешный сброс пароля
        message.value = 'Пароль успешно изменен! Перенаправление на страницу входа...';
        
        // Добавляем задержку перед переадресацией
        setTimeout(() => {
          router.push('/login');
        }, 3000);
        
      } catch (err) {
        isError.value = true;
        
        if (err.response && err.response.data) {
          message.value = err.response.data.detail || 'Произошла ошибка при сбросе пароля';
        } else {
          message.value = 'Произошла ошибка при сбросе пароля. Проверьте подключение к сети.';
        }
        
        console.error('Ошибка при сбросе пароля:', err);
      } finally {
        isLoading.value = false;
      }
    };

    /**
     * Переключение видимости пароля
     */
    const togglePassword = () => {
      showPassword.value = !showPassword.value;
    };

    /**
     * Переключение видимости подтверждения пароля
     */
    const toggleConfirmPassword = () => {
      showConfirmPassword.value = !showConfirmPassword.value;
    };

    /**
     * Переход на страницу входа
     */
    const goToLogin = () => {
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

.eye, .eye-slash {
  display: inline-block;
  width: 20px;
  height: 20px;
  background-color: #ccc;
  border-radius: 50%;
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
}

.error-message {
  color: red;
  margin-top: 15px;
}

.message {
  color: green;
  margin-top: 15px;
}
</style>