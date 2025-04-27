<template>
  <div id="app">
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
</style>
