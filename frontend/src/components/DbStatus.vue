<template>
  <div class="db-status">
    <h3>Статус подключения к базе данных</h3>
    <div :class="['status-indicator', statusClass]">
      {{ dbStatus.message }}
    </div>
  </div>
</template>

<script>
import apiService from '../services/api';

export default {
  name: 'DbStatus',
  data() {
    return {
      dbStatus: {
        status: 'pending',
        message: 'Проверка подключения к базе данных...'
      }
    };
  },
  computed: {
    statusClass() {
      return {
        'status-success': this.dbStatus.status === 'success',
        'status-error': this.dbStatus.status === 'error',
        'status-pending': this.dbStatus.status === 'pending'
      };
    }
  },
  async mounted() {
    try {
      // Проверяем статус подключения к БД при монтировании компонента
      this.dbStatus = await apiService.checkDbStatus();
    } catch (error) {
      console.error('Error in DbStatus component:', error);
      this.dbStatus = {
        status: 'error',
        message: 'Ошибка при проверке подключения к базе данных'
      };
    }
  }
};
</script>

<style scoped>
.db-status {
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