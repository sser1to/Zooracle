<template>
  <div id="app">
    <!-- Прогрессбар для отображения процесса загрузки -->
    <div class="progress-container">
      <div class="progress-bar" :style="{ width: loadingProgress + '%', opacity: isLoading ? 1 : 0 }"></div>
    </div>
    <router-view v-slot="{ Component }">
      <!-- Используем transition и keep-alive для плавных переходов между страницами -->
      <transition name="fade" mode="out-in">
        <keep-alive>
          <component :is="Component" />
        </keep-alive>
      </transition>
    </router-view>
  </div>
</template>

<script>
/**
 * Корневой компонент приложения
 * @description Содержит основную структуру приложения и отвечает за отображение текущего маршрута
 */
export default {
  name: 'App',
  
  data() {
    return {
      loadingProgress: 0,
      isLoading: false,
      loadingTimer: null
    }
  },

  created() {
    // Регистрация обработчиков событий для навигации
    this.$router.beforeEach(this.startLoading);
    this.$router.afterEach(this.completeLoading);
  },

  methods: {
    /**
     * Запускает анимацию загрузки
     * @description Метод вызывается перед каждой навигацией
     */
    startLoading() {
      // Сбрасываем предыдущие таймеры, если они есть
      clearInterval(this.loadingTimer);
      this.loadingProgress = 0;
      this.isLoading = true;

      // Имитируем прогресс загрузки
      this.loadingTimer = setInterval(() => {
        if (this.loadingProgress < 90) {
          // Постепенно увеличиваем прогресс, но не доходим до 100%
          // Последние 10% будут добавлены при завершении загрузки
          this.loadingProgress += (90 - this.loadingProgress) / 10;
        }
      }, 100);
    },

    /**
     * Завершает анимацию загрузки
     * @description Метод вызывается после завершения навигации
     */
    completeLoading() {
      // Завершаем прогресс загрузки
      this.loadingProgress = 100;
      
      // Скрываем прогрессбар через небольшую задержку
      setTimeout(() => {
        clearInterval(this.loadingTimer);
        this.isLoading = false;
      }, 300);
    }
  },
  
  mounted() {
    // Логирование для отладки, чтобы убедиться, что компонент корректно монтируется
    console.log('App.vue смонтирован');
    console.log('Текущий путь:', this.$route.path);
    console.log('Параметры URL:', this.$route.query);
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 20px; /* Уменьшаем верхний отступ с 60px до 20px */
  /* Добавляем масштабирование для всего приложения */
  transform: scale(1.2);
  transform-origin: top center;
  width: 83.33%; /* 100/1.5 чтобы компенсировать увеличение масштаба */
  margin-left: auto;
  margin-right: auto;
}

/* Стили для прогрессбара */
.progress-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 5px;
  z-index: 9999;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(to right, #4caf50, #8bc34a);
  transition: width 0.2s, opacity 0.6s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

/* Анимация перехода между страницами */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Глобальные стили для улучшения пользовательского опыта */
body {
  margin: 0;
  padding: 0;
  background-color: #f5f5f5;
  /* Добавляем стили для обработки масштабированного контента */
  overflow-x: hidden;
}

/* Базовые стили для всплывающих сообщений */
.message {
  padding: 10px;
  margin: 10px 0;
  border-radius: 4px;
}

.error-message {
  background-color: #ffebee;
  color: #d32f2f;
  border: 1px solid #ffcdd2;
}

.success-message {
  background-color: #e8f5e9;
  color: #388e3c;
  border: 1px solid #c8e6c9;
}

/* Медиа-запрос для адаптации в зависимости от размера экрана */
@media screen and (max-width: 768px) {
  #app {
    transform: scale(1.0);
    width: 100%;
  }
}

@media screen and (max-width: 480px) {
  #app {
    transform: scale(1.0);
    width: 100%;
  }
}
</style>
