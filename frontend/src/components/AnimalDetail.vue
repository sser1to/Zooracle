<template>
  <div class="animal-detail-container">
    <!-- Основное содержимое страницы разделено на 2 колонки -->
    <div v-if="loading" class="loading-message">
      <div class="spinner"></div>
      <p>Загрузка данных...</p>
    </div>

    <div v-else-if="error" class="error-message">
      <p>{{ error }}</p>
      <button @click="loadAnimalData" class="retry-button">Повторить</button>
    </div>

    <div v-else-if="animal" class="animal-content">
      <!-- Левая колонка с основной информацией и видео -->
      <div class="left-column">
        <!-- Заголовок и основная информация -->
        <h1 class="animal-title">{{ animal.name }}</h1>
        
        <!-- Основная информация -->
        <div class="info-block">
          <div class="info-row">
            <div class="class-label">Класс:</div>
            <div class="info-value">{{ animal.animal_type?.name || 'Не указан' }}</div>
          </div>
          
          <div class="info-row">
            <div class="habitat-label">Ареал обитания:</div>
            <div class="info-value">{{ animal.habitat?.name || 'Не указан' }}</div>
          </div>
        </div>
        
        <!-- Описание -->
        <div class="description-block">
          <h3>Описание:</h3>
          <p class="description-text">{{ animal.description }}</p>
        </div>
        
        <!-- Секция с видео, если оно есть -->
        <div v-if="animal.video_id" class="video-block">
          <div class="video-container">
            <video controls class="animal-video">
              <source :src="getVideoUrl(animal.video_id)" type="video/mp4">
              Ваш браузер не поддерживает видео.
            </video>
            <div class="play-button" @click="playVideo">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#ffffff" width="48px" height="48px">
                <path d="M8 5v14l11-7z"/>
              </svg>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Правая колонка с изображениями и тестом -->
      <div class="right-column">
        <!-- Основное изображение -->
        <div class="main-image-container">
          <img 
            :src="getImageUrl(currentImageId)" 
            :alt="animal.name" 
            @error="handleImageError"
            class="main-image"
          />
        </div>
        
        <!-- Галерея миниатюр -->
        <div v-if="animal.photos && animal.photos.length > 0" class="thumbnails-container">
          <div 
            v-for="(photo, index) in displayPhotos" 
            :key="photo.id" 
            class="thumbnail-item"
            @click="setMainImage(photo.photo_id)"
            :class="{ 'active': photo.photo_id === currentImageId }"
          >
            <img 
              :src="getImageUrl(photo.photo_id)" 
              :alt="`${animal.name} - изображение ${index + 1}`" 
              @error="handleImageError"
              class="thumbnail-image"
            />
          </div>
        </div>
        
        <!-- Кнопка для теста -->
        <div v-if="animal.test_id" class="test-button-container">
          <button class="test-button" @click="goToTest">
            Пройти тест на знание вида
          </button>
        </div>
      </div>
    </div>

    <!-- Кнопка "На главную" (всегда внизу страницы) -->
    <div class="navigation-footer">
      <router-link to="/" class="home-button">
        <span class="arrow-icon">←</span> На главную
      </router-link>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';

/**
 * Компонент для отображения детальной информации о животном
 * @component
 * @description Отображает подробную информацию о животном в двухколоночном макете согласно дизайну
 * @author Zooracle Team
 */
export default {
  name: 'AnimalDetail',
  setup() {
    /**
     * Реактивные переменные состояния компонента
     */
    const animal = ref(null);
    const loading = ref(true);
    const error = ref('');
    const currentImageId = ref(null);
    const route = useRoute();
    const apiBase = 'http://localhost:8000/api';
    
    /**
     * Вычисляемое свойство для получения фотографий для отображения в галерее
     * @returns {Array} Массив фотографий для отображения (включая основную, если она есть)
     */
    const displayPhotos = computed(() => {
      if (!animal.value) return [];
      
      const photos = [...(animal.value.photos || [])];
      
      // Если есть основное изображение и оно не дублируется в фотографиях
      if (animal.value.preview_id && !photos.some(p => p.photo_id === animal.value.preview_id)) {
        // Добавляем основное изображение в начало списка
        photos.unshift({
          id: 'preview',
          photo_id: animal.value.preview_id
        });
      }
      
      return photos;
    });
    
    /**
     * Загружает данные о животном из API
     * @async
     * @function loadAnimalData
     */
    const loadAnimalData = async () => {
      const animalId = route.params.id;
      if (!animalId) {
        error.value = 'Идентификатор животного не указан';
        loading.value = false;
        return;
      }
      
      try {
        loading.value = true;
        error.value = '';
        
        const response = await axios.get(`${apiBase}/animals/${animalId}`);
        animal.value = response.data;
        
        // Устанавливаем основное изображение
        if (animal.value.preview_id) {
          currentImageId.value = animal.value.preview_id;
        } else if (animal.value.photos && animal.value.photos.length > 0) {
          currentImageId.value = animal.value.photos[0].photo_id;
        }
        
        // Устанавливаем заголовок страницы
        document.title = `${animal.value.name} - Zooracle`;
        
      } catch (err) {
        console.error('Ошибка при загрузке данных о животном:', err);
        error.value = 'Не удалось загрузить информацию о животном';
      } finally {
        loading.value = false;
      }
    };
    
    /**
     * Возвращает URL изображения по его ID
     * @param {string} imageId - ID изображения
     * @returns {string} URL изображения
     */
    const getImageUrl = (imageId) => {
      if (!imageId) {
        return '/placeholder.jpg'; // Заглушка, если нет изображения
      }
      return `${apiBase}/media/${imageId}`;
    };
    
    /**
     * Возвращает URL видео по его ID
     * @param {string} videoId - ID видео
     * @returns {string} URL видео
     */
    const getVideoUrl = (videoId) => {
      if (!videoId) {
        return ''; 
      }
      return `${apiBase}/media/${videoId}`;
    };
    
    /**
     * Обработчик ошибок при загрузке изображений
     * @param {Event} e - Событие ошибки
     */
    const handleImageError = (e) => {
      e.target.src = '/placeholder.jpg'; // Заменяем на заглушку
    };
    
    /**
     * Устанавливает выбранное изображение как основное
     * @param {string} photoId - ID изображения
     */
    const setMainImage = (photoId) => {
      currentImageId.value = photoId;
    };
    
    /**
     * Воспроизводит видео и скрывает кнопку воспроизведения
     */
    const playVideo = () => {
      const video = document.querySelector('.animal-video');
      if (video) {
        video.play();
        // Скрываем кнопку воспроизведения после начала проигрывания
        const playButton = document.querySelector('.play-button');
        if (playButton) {
          playButton.style.display = 'none';
        }
      }
    };
    
    /**
     * Обработчик перехода на страницу теста
     */
    const goToTest = () => {
      if (animal.value && animal.value.test_id) {
        // Здесь будет переход на страницу теста (функционал будет добавлен позже)
        alert('Функционал тестирования находится в разработке');
      }
    };
    
    // Отслеживаем изменения параметра ID в URL для перезагрузки данных при необходимости
    watch(
      () => route.params.id,
      (newId, oldId) => {
        if (newId !== oldId) {
          loadAnimalData();
        }
      }
    );
    
    // Загружаем данные при монтировании компонента
    onMounted(() => {
      // Настраиваем axios для работы с токенами
      axios.interceptors.request.use(config => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      });
      
      // Загружаем данные о животном
      loadAnimalData();
    });
    
    return {
      animal,
      loading,
      error,
      currentImageId,
      displayPhotos,
      loadAnimalData,
      getImageUrl,
      getVideoUrl,
      handleImageError,
      setMainImage,
      playVideo,
      goToTest
    };
  }
}
</script>

<style scoped>
/* Основной контейнер с фиксированной шириной */
.animal-detail-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  box-sizing: border-box;
  position: relative;
  min-height: calc(100vh - 40px);
  display: flex;
  flex-direction: column;
}

/* Основное содержимое со сдвоенными колонками */
.animal-content {
  display: flex;
  gap: 30px;
  flex: 1;
}

/* Левая колонка с информацией и видео */
.left-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

/* Правая колонка с изображением и галереей */
.right-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

/* Стили для заголовка */
.animal-title {
  font-size: 32px;
  font-weight: bold;
  margin: 0 0 10px 0;
  color: #333;
  text-align: left;
}

/* Блок с информацией */
.info-block {
  background-color: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 15px;
}

.info-row {
  display: flex;
  margin-bottom: 8px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.class-label {
  min-width: 60px;
  font-weight: bold;
  color: #333;
  text-align: left;
}

.habitat-label {
  min-width: 140px;
  font-weight: bold;
  color: #333;
  text-align: left;
}

.info-value {
  flex: 1;
  color: #333;
  text-align: left;
}

/* Блок с описанием */
.description-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.description-block h3 {
  font-size: 18px;
  font-weight: bold;
  margin: 0;
  color: #333;
  text-align: left;
}

.description-text {
  margin: 0;
  line-height: 1.5;
  color: #333;
  text-align: left;
  white-space: pre-line; /* Сохраняем переносы строк из текста */
  overflow-wrap: break-word; /* Разрешаем перенос длинных слов */
}

/* Блок с видео */
.video-block {
  margin-top: 15px;
}

.video-container {
  position: relative;
  width: 100%;
  padding-bottom: 56.25%; /* Соотношение 16:9 */
  background-color: #000;
  border-radius: 4px;
  overflow: hidden;
}

.animal-video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.play-button {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 60px;
  height: 60px;
  background-color: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 2;
}

/* Основное изображение */
.main-image-container {
  width: 100%;
  aspect-ratio: 1 / 1; /* Квадратное соотношение как на макете */
  border: 1px solid #8BC34A; /* Зеленая рамка как на макете */
  border-radius: 4px;
  overflow: hidden;
}

.main-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Контейнер с миниатюрами */
.thumbnails-container {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.thumbnail-item {
  aspect-ratio: 1 / 1;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
}

.thumbnail-item.active {
  border-color: #8BC34A; /* Зеленая рамка для активной миниатюры */
  border-width: 2px;
}

.thumbnail-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Кнопка для теста */
.test-button-container {
  margin-top: auto;
}

.test-button {
  width: 100%;
  padding: 12px;
  background-color: #8BC34A;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.3s;
}

.test-button:hover {
  background-color: #7CB342;
}

/* Нижняя навигационная панель */
.navigation-footer {
  margin-top: 20px;
  text-align: left; /* Выравнивание содержимого по левому краю */
  width: 100%; /* Занимаем всю ширину */
}

.home-button {
  display: inline-flex;
  align-items: center;
  text-decoration: none;
  color: #8BC34A;
  font-weight: bold;
  border: 2px solid #8BC34A;
  border-radius: 4px;
  padding: 8px 16px;
  transition: color 0.3s, border-color 0.3s;
}

.home-button:hover {
  color: #7CB342;
  border-color: #7CB342;
}

.arrow-icon {
  margin-right: 5px;
}

/* Сообщения о загрузке и ошибках */
.loading-message,
.error-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  text-align: center;
}

.spinner {
  border: 3px solid rgba(0, 0, 0, 0.1);
  border-top: 3px solid #8BC34A;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.retry-button {
  padding: 8px 16px;
  background-color: #8BC34A;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  margin-top: 10px;
}

/* Медиа-запросы для адаптивности */
@media (max-width: 768px) {
  .animal-content {
    flex-direction: column;
  }
  
  .main-image-container {
    aspect-ratio: 16 / 9; /* Изменяем соотношение для мобильных */
  }
  
  .thumbnails-container {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>