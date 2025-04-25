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