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
      
      <button type="submit" class="btn-primary">Отправить</button>
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

export default {
  name: 'ResetPasswordForm',
  setup() {
    const router = useRouter();
    const email = ref('');
    const message = ref('');
    const isError = ref(false);

    const sendResetEmail = async () => {
      try {
        isError.value = false;
        message.value = '';
        
        // В реальном проекте здесь будет API-запрос на отправку инструкций по восстановлению
        // Сейчас просто имитируем успешную отправку
        // await authService.resetPassword(email.value);
        
        message.value = 'Инструкции по восстановлению пароля отправлены на вашу почту';
      } catch (err) {
        isError.value = true;
        message.value = err.response?.data?.detail || 'Ошибка при отправке инструкций по восстановлению';
      }
    };

    const goBack = () => {
      router.push('/login');
    };

    return {
      email,
      message,
      isError,
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