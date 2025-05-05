<template>
  <div class="animal-detail-container">
    <!-- Кнопка "На главную" (перемещена в верх страницы) -->
    <div class="back-link-container">
      <router-link to="/" class="back-link">
        <span class="back-arrow">←</span> На главную
      </router-link>
    </div>

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
        <!-- Заголовок с кнопками действий -->
        <div class="title-container">
          <h1 class="animal-title">{{ animal.name }}</h1>
          
          <!-- Кнопка редактирования для администраторов -->
          <router-link 
            v-if="isAdmin" 
            :to="`/edit-animal/${animal.id}`" 
            class="action-button edit-button"
            title="Редактировать"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="edit-icon">
              <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
            </svg>
          </router-link>
          
          <!-- Кнопка избранного для обычных пользователей -->
          <button 
            v-if="!isAdmin"
            class="action-button favorite-button" 
            @click="toggleFavorite"
            :class="{ 'is-favorite': isFavorite }"
            :title="isFavorite ? 'Удалить из избранного' : 'Добавить в избранное'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="heart-icon">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
          </button>
        </div>
        
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
            <video controls class="animal-video" @play="isVideoPlaying = true" @pause="isVideoPlaying = false">
              <source :src="getVideoUrl(animal.video_id)" type="video/mp4">
              Ваш браузер не поддерживает видео.
            </video>
            <div v-if="!isVideoPlaying" class="play-button" @click="playVideo">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#ffffff" width="48px" height="48px">
                <path d="M8 5v14l11-7z"/>
              </svg>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Правая колонка с изображениями и тестом -->
      <div class="right-column">
        <!-- Основное изображение с индикатором загрузки -->
        <div class="main-image-container">
          <!-- Индикатор загрузки изображения -->
          <div v-if="imageLoading" class="image-loading-overlay">
            <div class="spinner"></div>
          </div>
          <img 
            :src="getImageUrl(currentImageId)" 
            :alt="animal.name" 
            @error="handleImageError"
            @load="handleImageLoaded"
            class="main-image"
          />
        </div>
        
        <!-- Галерея миниатюр -->
        <div v-if="animal.photos && animal.photos.length > 0" class="thumbnails-container">
          <div 
            v-for="photo in displayPhotos" 
            :key="photo.id" 
            class="thumbnail-item"
            @click="setMainImage(photo.photo_id)"
            :class="{ 'active': photo.photo_id === currentImageId }"
          >
            <!-- Индикатор загрузки миниатюры -->
            <div v-if="!thumbnailsLoaded[photo.photo_id]" class="thumbnail-loading">
              <div class="thumbnail-spinner"></div>
            </div>
            <img 
              :src="getImageUrl(photo.photo_id)" 
              :alt="animal.name"
              @error="handleImageError"
              @load="() => handleThumbnailLoaded(photo.photo_id)"
              class="thumbnail-image"
            />
          </div>
        </div>
        
        <!-- Блок с тестом -->
        <div v-if="animal.test_id" class="test-button-container">
          <button 
            @click="goToTest" 
            class="test-button"
          >
            Пройти тест
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, reactive, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

/**
 * Компонент для отображения детальной информации о животном
 * @component
 * @description Отображает подробную информацию о животном в двухколоночном макете согласно дизайну
 * @author Zooracle Team
 * @date 2 мая 2023 г.
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
    const imageLoading = ref(false); // Состояние загрузки основного изображения
    const thumbnailsLoaded = reactive({}); // Хранит состояние загрузки каждой миниатюры
    const favorites = ref([]); // Массив ID животных в избранном
    const isAdmin = ref(false); // Статус администратора пользователя
    const isVideoPlaying = ref(false); // Состояние воспроизведения видео
    
    const route = useRoute();
    const router = useRouter();
    
    // Константы и настройки
    const BACKEND_PORT = process.env.BACKEND_PORT;
    const SITE_IP = process.env.SITE_IP;
    
    // Определяем базовый URL API в зависимости от окружения
    const apiBase = process.env.NODE_ENV === 'production' 
      ? '/api'
      : `${SITE_IP}:${BACKEND_PORT}/api`;
    
    /**
     * Проверяет, находится ли текущее животное в избранном
     * @type {import('vue').ComputedRef<boolean>}
     */
    const isFavorite = computed(() => {
      if (!animal.value) return false;
      return favorites.value.includes(animal.value.id);
    });
    
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
     * Проверяет статус администратора пользователя
     */
    const checkAdminStatus = () => {
      try {
        // Получаем данные пользователя из localStorage
        const userData = localStorage.getItem('user');
        if (!userData) return;
        
        const user = JSON.parse(userData);
        // Устанавливаем флаг администратора на основе данных пользователя
        isAdmin.value = user && user.is_admin === true;
        
        console.log('Статус администратора:', isAdmin.value);
      } catch (err) {
        console.error('Ошибка при проверке статуса администратора:', err);
        // Если произошла ошибка, сбрасываем флаг
        isAdmin.value = false;
      }
    };
    
    /**
     * Загружает избранные животные пользователя
     * @async
     */
    const loadFavorites = async () => {
      try {
        const response = await axios.get(`${apiBase}/animals/favorites/`);
        favorites.value = response.data.map(animal => animal.id);
      } catch (err) {
        console.error('Ошибка при загрузке избранных животных:', err);
        // Не показываем ошибку пользователю, т.к. это не критичная информация
      }
    };
    
    /**
     * Загружает данные о животном из API
     * @async
     * @function loadAnimalData
     */
    const loadAnimalData = async () => {
      const animalId = route.params.id;
      
      try {
        loading.value = true;
        error.value = '';
        imageLoading.value = true; // Начинаем загрузку изображений
        
        // Если ID не указан, просто показываем состояние загрузки
        if (!animalId) {
          return;
        }
        
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
        
        // Предварительно загружаем миниатюры
        preloadImages();
        
      } catch (err) {
        console.error('Ошибка при загрузке данных о животном:', err);
        error.value = 'Не удалось загрузить информацию о животном';
      } finally {
        loading.value = false;
      }
    };
    
    /**
     * Предварительно загружает все изображения для ускорения отображения
     */
    const preloadImages = () => {
      if (!animal.value) return;
      
      // Отмечаем все изображения как не загруженные
      thumbnailsLoaded.value = {};
      
      // Предварительно загружаем основное изображение
      if (animal.value.preview_id) {
        const img = new Image();
        img.src = getImageUrl(animal.value.preview_id);
      }
      
      // Предварительно загружаем все миниатюры
      if (animal.value.photos && animal.value.photos.length > 0) {
        animal.value.photos.forEach(photo => {
          thumbnailsLoaded[photo.photo_id] = false;
          const img = new Image();
          img.src = getImageUrl(photo.photo_id);
          img.onload = () => {
            thumbnailsLoaded[photo.photo_id] = true;
          };
          img.onerror = () => {
            thumbnailsLoaded[photo.photo_id] = true; // Помечаем как загруженное даже при ошибке
          };
        });
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
     * Обработчик успешной загрузки основного изображения
     */
    const handleImageLoaded = () => {
      imageLoading.value = false;
    };
    
    /**
     * Обработчик успешной загрузки миниатюры
     * @param {string} photoId - ID фото
     */
    const handleThumbnailLoaded = (photoId) => {
      thumbnailsLoaded[photoId] = true;
    };
    
    /**
     * Обработчик ошибок при загрузке изображений
     * @param {Event} e - Событие ошибки
     */
    const handleImageError = (e) => {
      e.target.src = '/placeholder.jpg'; // Заменяем на заглушку
      
      // Скрываем индикатор загрузки
      if (e.target.classList.contains('main-image')) {
        imageLoading.value = false;
      }
      
      // Если это миниатюра, помечаем её как загруженную
      const photoId = e.target.getAttribute('data-photo-id');
      if (photoId) {
        thumbnailsLoaded[photoId] = true;
      }
    };
    
    /**
     * Устанавливает выбранное изображение как основное
     * @param {string} photoId - ID изображения
     */
    const setMainImage = (photoId) => {
      if (currentImageId.value !== photoId) {
        imageLoading.value = true; // Показываем индикатор загрузки
        currentImageId.value = photoId;
      }
    };
    
    /**
     * Воспроизводит видео и скрывает кнопку воспроизведения
     */
    const playVideo = () => {
      const video = document.querySelector('.animal-video');
      if (video) {
        video.play();
      }
    };
    
    /**
     * Переключает статус избранного для текущего животного
     * @async
     */
    const toggleFavorite = async () => {
      if (!animal.value) return;
      
      try {
        const isFav = isFavorite.value;
        
        if (isFav) {
          // Удаляем из избранного
          await axios.delete(`${apiBase}/animals/favorites/${animal.value.id}`);
          favorites.value = favorites.value.filter(id => id !== animal.value.id);
        } else {
          // Добавляем в избранное
          await axios.post(`${apiBase}/animals/favorites/`, {
            animal_id: animal.value.id
          });
          favorites.value.push(animal.value.id);
        }
      } catch (err) {
        console.error('Ошибка при обновлении избранного:', err);
      }
    };
    
    /**
     * Обработчик перехода на страницу теста
     */
    const goToTest = () => {
      if (animal.value && animal.value.test_id) {
        // Очищаем предыдущие данные перед навигацией, используя force=true для принудительного обновления,
        // даже если маршрут остаётся тем же самым
        router.push({
          name: 'take-test',
          params: { 
            animalId: animal.value.id,
            testId: animal.value.test_id 
          },
          force: true // Принудительная навигация, даже если URL такой же
        });
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
      
      // Проверяем статус администратора
      checkAdminStatus();
      
      // Загружаем избранные животные
      loadFavorites();
      
      // Загружаем данные о животном
      loadAnimalData();
    });
    
    return {
      animal,
      loading,
      error,
      currentImageId,
      imageLoading,
      thumbnailsLoaded,
      displayPhotos,
      isAdmin,
      isFavorite,
      isVideoPlaying,
      loadAnimalData,
      getImageUrl,
      getVideoUrl,
      handleImageError,
      handleImageLoaded,
      handleThumbnailLoaded,
      setMainImage,
      playVideo,
      toggleFavorite,
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

/* Контейнер для кнопки "На главную" */
.back-link-container {
  margin-bottom: 20px;
  text-align: left;
}

.back-link {
  display: inline-flex;
  align-items: center;
  text-decoration: none;
  color: #8BC34A;
  font-weight: 500;
  transition: color 0.3s;
  padding: 8px 0;
}

.back-link:hover {
  color: #7CB342;
}

.back-arrow {
  font-size: 18px;
  margin-right: 8px;
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

/* Заголовок с кнопками действий */
.title-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* Стили для заголовка */
.animal-title {
  font-size: 32px;
  font-weight: bold;
  margin: 0;
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
  transition: background-color 0.3s;
  z-index: 3;
}

.play-button:hover {
  background-color: rgba(0, 0, 0, 0.7);
}

/* Основное изображение */
.main-image-container {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 1; /* Квадратное соотношение как на макете */
  border: 1px solid #8BC34A; /* Зеленая рамка как на макете */
  border-radius: 4px;
  overflow: hidden;
}

.image-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(245, 245, 245, 0.7);
  z-index: 5;
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
  position: relative;
  aspect-ratio: 1 / 1;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
}

.thumbnail-loading {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(245, 245, 245, 0.7);
  z-index: 3;
}

.thumbnail-spinner {
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-top: 2px solid #8BC34A;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  animation: spin 1s linear infinite;
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

/* Кнопки избранного и редактирования */
.action-button {
  background: rgba(255, 255, 255, 0.8);
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 8px;
  box-sizing: border-box;
  transition: background-color 0.3s;
  z-index: 10;
  text-decoration: none;
}

.action-button:hover {
  background-color: white;
}

.heart-icon {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: #ff4081;
  stroke-width: 2;
}

.favorite-button.is-favorite .heart-icon {
  fill: #ff4081;
}

.edit-icon {
  width: 20px;
  height: 20px;
  fill: #2196F3;
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
  
  .thumbnails-container {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>