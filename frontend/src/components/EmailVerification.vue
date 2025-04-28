<template>
  <div class="email-verification-container">
    <div class="card">
      <div class="card-header">
        <h2>Подтверждение электронной почты</h2>
      </div>
      <div class="card-body">
        <div v-if="verified" class="success-message">
          <h3>Email успешно подтвержден!</h3>
          <p>Вы будете перенаправлены на главную страницу через {{ countdownSeconds }} секунд...</p>
        </div>
        <div v-else>
          <p class="info-text">
            Для завершения регистрации необходимо подтвердить вашу электронную почту.
            <br>На адрес <strong>{{ email }}</strong> был отправлен 6-значный код подтверждения.
          </p>
          
          <div class="verification-code-input">
            <div class="code-digits">
              <input 
                v-for="(digit, index) in codeDigits" 
                :key="index" 
                type="text" 
                maxlength="1" 
                class="code-digit" 
                :class="{ 'input-error': hasError }"
                v-model="codeDigits[index]"
                @input="onDigitInput(index)"
                @keydown="onDigitKeydown($event, index)"
                ref="digitInputs"
                :disabled="isVerifying || isLoading"
              />
            </div>
            <div v-if="errorMessage" class="error-message">
              {{ errorMessage }}
            </div>
          </div>

          <div class="actions">
            <!-- Кнопка подтверждения кода -->
            <button class="submit-button" @click="verifyCode" :disabled="isVerifying || !isCodeComplete || isLoading">
              <span v-if="isVerifying">
                <span class="spinner-small"></span> Проверка...
              </span>
              <span v-else>Подтвердить</span>
            </button>
            
            <!-- Кнопка назад теперь перемещена под кнопку подтвердить -->
            <div class="back-button-container">
              <button @click="goBack" class="back-button" :disabled="isVerifying || isResending || isLoading">
                Назад
              </button>
            </div>
            
            <!-- Раздел для повторной отправки кода -->
            <div class="resend-container">
              <p>Не получили код?</p>
              <button class="resend-button" @click="resendCode" :disabled="resendCountdown > 0 || isResending || isLoading">
                <span v-if="resendCountdown > 0">
                  Отправить повторно ({{ resendCountdown }}с)
                </span>
                <span v-else-if="isResending">
                  <span class="spinner-small"></span> Отправка...
                </span>
                <span v-else>
                  Отправить повторно
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Глобальный индикатор загрузки -->
      <div v-if="isLoading" class="loading-overlay">
        <div class="spinner"></div>
        <div class="loading-message">Пожалуйста, подождите...</div>
      </div>
    </div>
    
    <!-- Модальное окно с ошибкой Rate Limit -->
    <div v-if="showRateLimitModal" class="rate-limit-modal">
      <div class="rate-limit-content">
        <h3>Слишком много запросов</h3>
        <p>Пожалуйста, попробуйте позже.</p>
        <button @click="closeRateLimitModal" class="modal-button">Понятно</button>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from '../services/api';

export default {
  name: 'EmailVerification',
  props: {
    email: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      codeDigits: ['', '', '', '', '', ''],
      isVerifying: false,     // Флаг процесса проверки кода
      isResending: false,     // Флаг процесса повторной отправки кода
      isLoading: false,       // Глобальный флаг загрузки для блокировки интерфейса
      hasError: false,        // Флаг ошибки ввода
      errorMessage: '',       // Сообщение об ошибке
      verified: false,        // Флаг успешной верификации
      countdownSeconds: 5,    // Обратный отсчёт для редиректа после верификации
      resendCountdown: 0,     // Обратный отсчёт для кнопки повторной отправки
      resendTimer: null,      // Таймер повторной отправки
      countdownTimer: null,   // Таймер обратного отсчёта
      lastCodeSendTime: null, // Время последней отправки кода
      showRateLimitModal: false, // Флаг отображения модального окна с ошибкой Rate Limit
      cooldownPeriod: 60 * 1000, // Период ожидания между запросами отправки кода (60 секунд в миллисекундах)
      lastVerifyAttemptTime: null, // Время последней попытки проверки кода
      verifyAttempts: 0,      // Количество попыток проверки кода
      maxVerifyAttempts: 5,   // Максимальное количество попыток проверки
    };
  },
  computed: {
    /**
     * Проверяет, заполнен ли код полностью (все 6 цифр)
     * @returns {boolean} true если код полностью заполнен
     */
    isCodeComplete() {
      return this.codeDigits.every(digit => digit !== '');
    },
    
    /**
     * Объединяет массив цифр в одну строку кода
     * @returns {string} полный код подтверждения
     */
    fullCode() {
      return this.codeDigits.join('');
    },
    
    /**
     * Проверяет, прошло ли достаточно времени с последней отправки кода
     * @returns {boolean} true если можно отправить новый запрос на код
     */
    canResendCode() {
      if (!this.lastCodeSendTime) return true;
      
      const now = Date.now();
      const timeSinceLastSend = now - this.lastCodeSendTime;
      return timeSinceLastSend >= this.cooldownPeriod;
    }
  },
  methods: {
    /**
     * Обрабатывает ввод цифры в поле кода
     * @param {number} index - индекс текущего поля
     */
    onDigitInput(index) {
      // Сбрасываем сообщение об ошибке при вводе нового значения
      this.errorMessage = '';
      this.hasError = false;
      
      // Проверяем, что введен только числовой символ
      const value = this.codeDigits[index];
      if (value && !/^\d$/.test(value)) {
        this.codeDigits[index] = '';
        return;
      }
      
      // Если введена цифра и это не последнее поле, переходим к следующему полю
      if (value !== '' && index < this.codeDigits.length - 1) {
        this.$nextTick(() => {
          if (this.$refs.digitInputs[index + 1]) {
            this.$refs.digitInputs[index + 1].focus();
          }
        });
      }
      
      // Если заполнены все поля, автоматически проверяем код
      if (this.isCodeComplete) {
        // Добавляем задержку перед автоматической проверкой для лучшего UX
        setTimeout(() => this.verifyCode(), 300);
      }
    },

    /**
     * Обрабатывает нажатие клавиш при вводе кода
     * @param {Event} event - событие клавиатуры
     * @param {number} index - индекс текущего поля
     */
    onDigitKeydown(event, index) {
      // Если нажат Backspace и поле пустое, фокусируемся на предыдущем поле
      if (event.key === 'Backspace' && this.codeDigits[index] === '' && index > 0) {
        this.$refs.digitInputs[index - 1].focus();
      }
    },
    
    /**
     * Отправляет запрос на проверку кода подтверждения
     * Проверка кода не имеет ограничения по частоте запросов
     */
    async verifyCode() {
      // Проверяем блокировки UI и заполненность кода
      if (!this.isCodeComplete || this.isVerifying || this.isLoading) {
        return;
      }
      
      // Проверяем, не превышено ли количество попыток
      if (this.verifyAttempts >= this.maxVerifyAttempts) {
        this.hasError = true;
        this.errorMessage = 'Превышено количество попыток ввода. Пожалуйста, запросите новый код.';
        return;
      }
      
      // Инкрементируем счетчик попыток
      this.verifyAttempts++;
      
      this.isVerifying = true;
      this.hasError = false;
      this.errorMessage = '';
      
      try {
        console.log(`Отправка кода: ${this.fullCode} для email: ${this.email}`);
        
        const response = await api.post('/auth/verify-email/confirm', {
          email: this.email,
          code: this.fullCode
        });
        
        // Если успешно подтвержден, обновляем состояние и сохраняем токен
        if (response.data && response.data.access_token) {
          this.verified = true;
          
          // Сохраняем токен и информацию о пользователе
          localStorage.setItem('token', response.data.access_token);
          localStorage.setItem('user_id', response.data.user_id);
          localStorage.setItem('login', response.data.login);
          localStorage.setItem('email', response.data.email);
          localStorage.setItem('is_admin', response.data.is_admin);
          
          // Запускаем обратный отсчет для редиректа
          this.startRedirectCountdown();
        }
      } catch (error) {
        // Отображаем ошибку от сервера
        this.hasError = true;
        
        console.error('Ошибка при проверке кода:', error);
        
        // Проверяем тип ошибки для специальной обработки
        if (error.response) {
          // Есть ответ от сервера
          if (error.response.status === 429) {
            // HTTP 429 Too Many Requests
            this.showRateLimitError();
          } else if (error.response.data && error.response.data.detail) {
            // Отображаем конкретную ошибку от сервера
            this.errorMessage = error.response.data.detail;
            
            // Если ошибка связана с истекшим кодом, предлагаем отправить новый код
            if (error.response.data.detail.includes('истек')) {
              this.errorMessage = 'Срок действия кода истек. Пожалуйста, запросите новый код.';
              this.resendCountdown = 0; // Разрешаем сразу запросить новый код
            } else if (error.response.data.detail.includes('верн')) {
              this.errorMessage = 'Неверный код подтверждения. Пожалуйста, проверьте и попробуйте снова.';
            } else if (error.response.data.detail.includes('данные') || error.response.data.detail.includes('найден')) {
              this.errorMessage = 'Данные для регистрации не найдены или срок их действия истек. Пожалуйста, пройдите регистрацию повторно.';
            }
          } else {
            // Общая ошибка с сервера
            this.errorMessage = 'Ошибка при проверке кода. Пожалуйста, попробуйте еще раз.';
          }
        } else if (error.request) {
          // Запрос был сделан, но ответ не получен (ошибка сети)
          this.errorMessage = 'Не удалось связаться с сервером. Пожалуйста, проверьте ваше соединение с интернетом.';
        } else {
          // Что-то пошло не так при настройке запроса
          this.errorMessage = 'Произошла ошибка при отправке запроса. Пожалуйста, попробуйте снова.';
        }
        
        // Очищаем поля ввода только при неверном коде
        if (this.errorMessage.includes('Неверный код')) {
          this.codeDigits = ['', '', '', '', '', ''];
          
          // Фокусируемся на первом поле
          this.$nextTick(() => {
            if (this.$refs.digitInputs && this.$refs.digitInputs[0]) {
              this.$refs.digitInputs[0].focus();
            }
          });
        }
      } finally {
        this.isVerifying = false;
      }
    },
    
    /**
     * Отправляет запрос на повторную отправку кода подтверждения
     * Имеет ограничение в 60 секунд между запросами
     */
    async resendCode() {
      // Проверка блокировок интерфейса
      if (this.isResending || this.isLoading) {
        return;
      }
      
      // Проверка таймера ожидания
      if (this.resendCountdown > 0) {
        return;
      }
      
      // Проверяем, не превышен ли лимит запросов
      if (!this.canResendCode) {
        this.showRateLimitError();
        return;
      }
      
      this.isResending = true;
      this.hasError = false;
      this.errorMessage = '';
      
      try {
        // Устанавливаем время последней отправки запроса
        this.lastCodeSendTime = Date.now();
        
        await api.post('/auth/verify-email/request', {
          email: this.email
        });
        
        // Сбрасываем поля ввода
        this.codeDigits = ['', '', '', '', '', ''];
        
        // Сбрасываем счетчик попыток при получении нового кода
        this.verifyAttempts = 0;
        
        // Устанавливаем таймер для повторной отправки (60 секунд)
        this.resendCountdown = 60;
        this.startResendCountdown();
        
        // Фокусируемся на первом поле
        this.$nextTick(() => {
          if (this.$refs.digitInputs && this.$refs.digitInputs[0]) {
            this.$refs.digitInputs[0].focus();
          }
        });
      } catch (error) {
        this.hasError = true;
        
        // Проверяем тип ошибки для специальной обработки
        if (error.response && error.response.status === 429) {
          // HTTP 429 Too Many Requests
          this.showRateLimitError();
        } else if (error.response && error.response.data && error.response.data.detail) {
          this.errorMessage = error.response.data.detail;
        } else {
          this.errorMessage = 'Ошибка при повторной отправке кода. Пожалуйста, попробуйте позже.';
        }
      } finally {
        this.isResending = false;
      }
    },
    
    /**
     * Показывает модальное окно с ошибкой превышения лимита запросов
     */
    showRateLimitError() {
      this.showRateLimitModal = true;
    },
    
    /**
     * Закрывает модальное окно с ошибкой превышения лимита запросов
     */
    closeRateLimitModal() {
      this.showRateLimitModal = false;
    },
    
    /**
     * Запускает обратный отсчет для кнопки повторной отправки
     */
    startResendCountdown() {
      // Очищаем предыдущий таймер, если он был
      if (this.resendTimer) {
        clearInterval(this.resendTimer);
      }
      
      // Создаем новый таймер
      this.resendTimer = setInterval(() => {
        if (this.resendCountdown > 0) {
          this.resendCountdown--;
        } else {
          // Останавливаем таймер, когда достигнем нуля
          clearInterval(this.resendTimer);
        }
      }, 1000);
    },
    
    /**
     * Запускает обратный отсчет для редиректа после успешной верификации
     */
    startRedirectCountdown() {
      // Создаем новый таймер
      this.countdownTimer = setInterval(() => {
        if (this.countdownSeconds > 0) {
          this.countdownSeconds--;
        } else {
          // Останавливаем таймер и делаем редирект
          clearInterval(this.countdownTimer);
          this.$router.push('/');
        }
      }, 1000);
    },
    
    /**
     * Обрабатывает нажатие на кнопку "Назад"
     */
    goBack() {
      // Если идёт верификация или отправка кода, отключаем кнопку
      if (this.isVerifying || this.isResending || this.isLoading) {
        return;
      }
      
      // Показываем индикатор загрузки
      this.isLoading = true;
      
      // Перенаправляем на страницу регистрации
      this.$router.push('/register');
    }
  },
  
  /**
   * Очищаем таймеры перед удалением компонента
   * Используем beforeUnmount вместо устаревшего beforeDestroy (Vue 3 совместимость)
   */
  beforeUnmount() {
    if (this.resendTimer) {
      clearInterval(this.resendTimer);
    }
    
    if (this.countdownTimer) {
      clearInterval(this.countdownTimer);
    }
  },
  
  /**
   * Когда компонент монтируется, фокусируемся на первом поле
   * и устанавливаем начальное время для ограничения запросов на код
   */
  mounted() {
    // Устанавливаем начальное время запроса для отсчета ограничения
    this.lastCodeSendTime = Date.now();
    
    // Начинаем обратный отсчет для повторной отправки
    this.resendCountdown = 60;
    this.startResendCountdown();
    
    // Фокусируемся на первом поле ввода
    this.$nextTick(() => {
      if (this.$refs.digitInputs && this.$refs.digitInputs[0]) {
        this.$refs.digitInputs[0].focus();
      }
    });
  }
};
</script>

<style scoped>
.email-verification-container {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: 100vh;
  padding: 20px;
  background-color: #f5f5f5;
}

.card {
  width: 100%;
  max-width: 500px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  position: relative; /* Для корректного позиционирования индикатора загрузки */
}

.card-header {
  background-color: #4caf50;
  color: white;
  padding: 20px;
  text-align: center;
}

.card-header h2 {
  margin: 0;
  font-size: 1.8rem;
}

.card-body {
  padding: 30px;
}

.info-text {
  margin-bottom: 25px;
  text-align: center;
  color: #555;
  line-height: 1.6;
}

.verification-code-input {
  margin-bottom: 30px;
}

.code-digits {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-bottom: 15px;
}

.code-digit {
  width: 45px;
  height: 50px;
  font-size: 24px;
  text-align: center;
  border: 2px solid #ddd;
  border-radius: 5px;
  transition: border-color 0.2s;
}

.code-digit:focus {
  outline: none;
  border-color: #4caf50;
}

.input-error {
  border-color: #f44336;
}

.error-message {
  color: #f44336;
  text-align: center;
  margin-top: 10px;
  font-size: 14px;
}

.actions {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.submit-button {
  width: 100%;
  padding: 12px;
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 5px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  justify-content: center;
  align-items: center;
}

.submit-button:hover:not(:disabled) {
  background-color: #3d8b40;
}

.submit-button:disabled {
  background-color: #a5d6a7;
  cursor: not-allowed;
}

/* Стили для кнопки "Назад" */
.back-button-container {
  margin-top: 15px;
  width: 100%;
}

.back-button {
  width: 100%;
  padding: 12px;
  background-color: white;
  color: #4caf50;
  border: 1px solid #4caf50;
  border-radius: 5px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
}

.back-button:hover:not(:disabled) {
  background-color: #f1f8e9;
}

.back-button:disabled {
  border-color: #a5d6a7;
  color: #a5d6a7;
  cursor: not-allowed;
}

.resend-container {
  margin-top: 25px;
  text-align: center;
  width: 100%;
}

.resend-container p {
  margin-bottom: 5px;
  color: #666;
  text-align: center;
}

.resend-button {
  background: none;
  border: none;
  color: #4caf50;
  font-size: 14px;
  cursor: pointer;
  padding: 5px 0;
  text-decoration: underline;
  transition: color 0.2s;
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 0 auto; /* Центрирование кнопки */
  width: fit-content; /* Размер по содержимому */
}

.resend-button:hover:not(:disabled) {
  color: #3d8b40;
}

.resend-button:disabled {
  color: #a5d6a7;
  cursor: not-allowed;
  text-decoration: none;
}

.success-message {
  text-align: center;
  padding: 20px;
}

.success-message h3 {
  color: #4caf50;
  margin-bottom: 15px;
}

/* Стили для индикатора загрузки */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 10;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 5px solid #f3f3f3;
  border-top: 5px solid #4caf50;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner-small {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 5px;
}

.loading-message {
  margin-top: 10px;
  color: #4caf50;
  font-weight: bold;
}

/* Стили для модального окна с ошибкой Rate Limit */
.rate-limit-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 20;
}

.rate-limit-content {
  background-color: white;
  padding: 30px;
  border-radius: 8px;
  max-width: 400px;
  width: 80%;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.rate-limit-content h3 {
  color: #f44336;
  margin-top: 0;
}

.modal-button {
  padding: 10px 20px;
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  margin-top: 15px;
  transition: background-color 0.2s;
}

.modal-button:hover {
  background-color: #3d8b40;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>