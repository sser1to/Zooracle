<template>
  <div class="p-4">
    <h1 class="text-xl font-bold">Ответ от сервера:</h1>
    <p v-if="message" class="mt-2 text-green-600">{{ message }}</p>
    <p v-else class="text-gray-500">Загрузка...</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const message = ref(null)

onMounted(async () => {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/api/test/hello`)
    message.value = await response.text()
  } catch (err) {
    message.value = 'Ошибка при получении данных'
  }
})
</script>

<style scoped>
</style>
