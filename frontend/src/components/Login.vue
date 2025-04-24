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
          <!-- Здесь будет иконка показа/скрытия пароля -->
        </span>
      </div>
      
      <div class="forgot-password">
        <router-link to="/reset-password">Забыли пароль?</router-link>
      </div>
      
      <button type="submit" class="btn-primary">Войти</button>
    </form>
    
    <div class="auth-footer">
      <router-link to="/register" class="btn-secondary">Зарегистрироваться</router-link>
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
          router.push('/');
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

.forgot-password {
  text-align: right;
  margin: 10px 0 20px;
}

.forgot-password a {
  color: #4CAF50;
  text-decoration: none;
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