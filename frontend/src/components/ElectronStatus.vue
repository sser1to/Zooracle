<template>
  <div class="electron-status">
    <h3>Статус Electron</h3>
    <div :class="['status-indicator', isElectron ? 'status-success' : 'status-error']">
      {{ statusMessage }}
    </div>
    <div v-if="isElectron && appVersion" class="version-info">
      Версия: {{ appVersion }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'ElectronStatus',
  data() {
    return {
      isElectron: false,
      appVersion: null
    };
  },
  computed: {
    statusMessage() {
      return this.isElectron 
        ? 'Приложение работает в режиме Electron' 
        : 'Приложение работает в браузере';
    }
  },
  async mounted() {
    // Проверяем, запущено ли приложение в Electron
    this.isElectron = window.electronAPI !== undefined;
    
    // Если приложение запущено в Electron, получаем версию
    if (this.isElectron) {
      try {
        this.appVersion = await window.electronAPI.getAppVersion();
      } catch (error) {
        console.error('Ошибка при получении версии:', error);
      }
    }
  }
};
</script>

<style scoped>
.electron-status {
  margin: 20px;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.status-indicator {
  padding: 10px;
  border-radius: 4px;
  margin-top: 10px;
  font-weight: bold;
}

.status-success {
  background-color: #e6ffec;
  color: #1a8754;
  border: 1px solid #a3e9b7;
}

.status-error {
  background-color: #ffe6e6;
  color: #dc3545;
  border: 1px solid #e9a3a3;
}

.version-info {
  margin-top: 10px;
  font-size: 0.9em;
  color: #6c757d;
}
</style>