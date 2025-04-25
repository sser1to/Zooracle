<template>
  <div class="auth-container">
    <img alt="Лого" src="../assets/logo.png" class="logo">
    <h1>Восстановление пароля</h1>
    
    <form @submit.prevent="sendResetEmail">
      <div class="form-group">
        <input 
          type="email" 
          v-model="email" 
          placeholder="Введите ваш email"
          required
        />
      </div>
      
      <button type="submit" class="btn-primary" :disabled="isLoading">
        {{ isLoading ? 'Отправка...' : 'Отправить' }}
      </button>
    </form>
    
    <div class="auth-footer">
      <button @click="goBack" class="btn-secondary">Назад</button>
    </div>

    <div v-if="message" class="message" :class="{ 'error-message': isError }">
      {{ message }}
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

/**
 * Компонент для запроса восстановления пароля
 * @description Позволяет пользователю запросить восстановление пароля через email
 */
export default {
  name: 'ResetPasswordForm',
  setup() {
    const router = useRouter();
    const email = ref('');
    const message = ref('');
    const isError = ref(false);
    const isLoading = ref(false);

    /**
     * Отправляет запрос на сброс пароля
     * @async
     * @returns {Promise<void>}
     */
    const sendResetEmail = async () => {
      try {
        isLoading.value = true;
        isError.value = false;
        message.value = '';
        
        // Проверка формата email
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email.value)) {
          isError.value = true;
          message.value = 'Пожалуйста, введите корректный email-адрес';
          return;
        }
        
        console.log('Отправка запроса на восстановление пароля:', email.value);
        
        // Отправляем запрос на API для сброса пароля
        await axios.post('/api/auth/reset-password/request', { 
          email: email.value 
        });
        
        // Успешная отправка
        message.value = 'Инструкции по восстановлению пароля отправлены на вашу почту';
      } catch (err) {
        isError.value = true;
        
        if (err.response && err.response.data) {
          message.value = err.response.data.detail || 'Ошибка при отправке запроса на восстановление пароля';
        } else {
          message.value = 'Произошла ошибка при отправке запроса. Проверьте подключение к сети.';
        }
        
        console.error('Ошибка при отправке запроса на восстановление пароля:', err);
      } finally {
        isLoading.value = false;
      }
    };

    /**
     * Возврат на предыдущую страницу
     * @returns {void}
     */
    const goBack = () => {
      router.push('/login');
    };

    return {
      email,
      message,
      isError,
      isLoading,
      sendResetEmail,
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