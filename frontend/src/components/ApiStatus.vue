<template>
  <div class="api-status">
    <h3>Статус API</h3>
    <div :class="['status-indicator', statusClass]">
      {{ apiStatus.message }}
    </div>
  </div>
</template>

<script>
import apiService from '../services/api';

export default {
  name: 'ApiStatus',
  data() {
    return {
      apiStatus: {
        status: 'pending',
        message: 'Проверка статуса API...'
      }
    };
  },
  computed: {
    statusClass() {
      return {
        'status-success': this.apiStatus.status === 'success',
        'status-error': this.apiStatus.status === 'error',
        'status-pending': this.apiStatus.status === 'pending'
      };
    }
  },
  async mounted() {
    try {
      // Проверяем статус API при монтировании компонента
      this.apiStatus = await apiService.checkHealth();
    } catch (error) {
      console.error('Error in ApiStatus component:', error);
      this.apiStatus = {
        status: 'error',
        message: 'Ошибка при проверке статуса API'
      };
    }
  }
};
</script>

<style scoped>
.api-status {
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
  background-color: #ffebee;
  color: #dc3545;
  border: 1px solid #f5c2c7;
}

.status-pending {
  background-color: #fff8e1;
  color: #ffc107;
  border: 1px solid #ffe69c;
}
</style>