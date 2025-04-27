<template>
  <div class="catalog-container">
    <div class="catalog-header">
      <h1>Каталог животных</h1>
      <!-- Кнопка добавления нового вида (только для администраторов) -->
      <router-link v-if="isAdmin" to="/add-animal" class="add-animal-button">
        <span class="plus-icon">+</span> Добавить
      </router-link>
    </div>
    
    <!-- Панель фильтров и поиска -->
    <div class="filters-panel">
      <div class="search-container">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="Введите название вида" 
          class="search-input"
          @input="debouncedSearch"
        />
        <span class="search-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#666" width="20px" height="20px">
            <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
          </svg>
        </span>
      </div>

      <div class="dropdown-filters">
        <div class="filter-group">
          <button 
            class="dropdown-toggle" 
            @click="toggleDropdown('sort')"
          >
            {{ getSortLabel() }} <span class="arrow">▼</span>
          </button>
          <div class="dropdown-menu" v-show="activeDropdown === 'sort'">
            <div 
              class="dropdown-item" 
              v-for="option in sortOptions" 
              :key="option.value"
              @click="selectSort(option.value)"
              :class="{ active: sortBy === option.value }"
            >
              {{ option.label }}
            </div>
          </div>
        </div>

        <div class="filter-group">
          <button 
            class="dropdown-toggle" 
            @click="toggleDropdown('class')"
          >
            {{ getClassLabel() }} <span class="arrow">▼</span>
          </button>
          <div class="dropdown-menu" v-show="activeDropdown === 'class'">
            <div 
              class="dropdown-item" 
              v-for="option in animalTypes" 
              :key="option.id"
              @click="selectClass(option.id)"
              :class="{ active: selectedClassId === option.id }"
            >
              {{ option.name }}
            </div>
          </div>
        </div>

        <div class="filter-group">
          <button 
            class="dropdown-toggle" 
            @click="toggleDropdown('habitat')"
          >
            {{ getHabitatLabel() }} <span class="arrow">▼</span>
          </button>
          <div class="dropdown-menu" v-show="activeDropdown === 'habitat'">
            <div 
              class="dropdown-item" 
              v-for="option in habitats" 
              :key="option.id"
              @click="selectHabitat(option.id)"
              :class="{ active: selectedHabitatId === option.id }"
            >
              {{ option.name }}
            </div>
          </div>
        </div>

        <div class="filter-group favorites-filter">
          <label class="favorite-toggle">
            <input 
              type="checkbox" 
              v-model="showFavorites"
              @change="loadAnimals"
            >
            <span class="favorite-label">Избранное</span>
          </label>
        </div>
      </div>
    </div>

    <!-- Сообщение о загрузке -->
    <div v-if="loading" class="loading-message">
      <div class="spinner"></div>
      <p>Загрузка данных...</p>
    </div>

    <!-- Сообщение об ошибке -->
    <div v-if="error" class="error-message">
      <p>{{ error }}</p>
      <button @click="loadAnimals" class="retry-button">Повторить</button>
    </div>

    <!-- Сообщение если нет животных -->
    <div v-if="!loading && !error && animals.length === 0" class="no-results">
      <p>Ничего не найдено. Попробуйте изменить параметры поиска.</p>
    </div>

    <!-- Каталог животных -->
    <div v-if="!loading && !error && animals.length > 0" class="animals-grid">
      <div v-for="animal in animals" :key="animal.id" class="animal-card">
        <div class="animal-image">
          <img 
            :src="getImageUrl(animal.preview_id)" 
            :alt="animal.name" 
            @error="handleImageError"
            class="animal-img"
          />
        </div>
        <div class="animal-info">
          <h3 class="animal-name">{{ animal.name }}</h3>
        </div>
        <button 
          class="favorite-button" 
          @click="toggleFavorite(animal)"
          :class="{ 'is-favorite': isFavorite(animal.id) }"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="heart-icon">
            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Пагинация -->
    <div v-if="!loading && !error && totalPages > 1" class="pagination">
      <button 
        @click="prevPage" 
        :disabled="currentPage === 1" 
        class="pagination-button"
      >
        &laquo; Назад
      </button>
      <span class="page-info">Страница {{ currentPage }} из {{ totalPages }}</span>
      <button 
        @click="nextPage" 
        :disabled="currentPage === totalPages" 
        class="pagination-button"
      >
        Вперед &raquo;
      </button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';

/**
 * Компонент каталога животных
 * @component
 * @description Отображает список всех видов животных с возможностью поиска, фильтрации и сортировки
 */
export default {
  name: 'AnimalCatalog',
  setup() {
    // Реактивное состояние
    const animals = ref([]);
    const favorites = ref([]);
    const animalTypes = ref([]);  // Классы животных
    const habitats = ref([]);     // Ареалы обитания
    const loading = ref(true);
    const error = ref('');
    const apiBase = 'http://localhost:8000/api';
    const isAdmin = ref(false);  // Статус администратора
    
    // Параметры фильтрации
    const searchQuery = ref('');
    const selectedClassId = ref(null);
    const selectedHabitatId = ref(null);
    const sortBy = ref('name');
    const sortOrder = ref('asc');
    const showFavorites = ref(false);
    
    // Пагинация
    const currentPage = ref(1);
    const pageSize = 10;  // Количество элементов на странице
    const totalItems = ref(0);
    
    // Состояние UI
    const activeDropdown = ref(null);
    
    // Опции для выпадающих списков
    const sortOptions = [
      { value: 'name_asc', label: 'По имени (А-Я)' },
      { value: 'name_desc', label: 'По имени (Я-А)' },
      { value: 'id_asc', label: 'Сначала старые' },
      { value: 'id_desc', label: 'Сначала новые' },
    ];
    
    /**
     * Вычисляемое свойство для общего количества страниц
     * @returns {number} Количество страниц
     */
    const totalPages = computed(() => {
      return Math.ceil(totalItems.value / pageSize);
    });
    
    /**
     * Проверяет, добавлено ли животное в избранное
     * @param {number} animalId - ID животного
     * @returns {boolean} true если животное в избранном
     */
    const isFavorite = (animalId) => {
      return favorites.value.includes(animalId);
    };
    
    /**
     * Возвращает URL изображения из ID изображения
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
     * Обработчик ошибок при загрузке изображений
     * @param {Event} e - Событие ошибки
     */
    const handleImageError = (e) => {
      e.target.src = '/placeholder.jpg'; // Заменяем на заглушку
    };
    
    /**
     * Загружает данные о животных с применением всех фильтров
     */
    const loadAnimals = async () => {
      try {
        loading.value = true;
        error.value = '';
        
        // Вычисляем параметры сортировки
        const [sortField, sortDirection] = sortBy.value.includes('_') 
          ? sortBy.value.split('_') 
          : [sortBy.value, sortOrder.value];
        
        // Вычисляем смещение для пагинации
        const skip = (currentPage.value - 1) * pageSize;
        
        // Формируем параметры запроса
        const params = {
          skip,
          limit: pageSize,
          sort_by: sortField,
          sort_order: sortDirection,
          favorites_only: showFavorites.value
        };
        
        // Добавляем опциональные параметры
        if (searchQuery.value) params.search = searchQuery.value;
        if (selectedClassId.value) params.animal_type_id = selectedClassId.value;
        if (selectedHabitatId.value) params.habitat_id = selectedHabitatId.value;
        
        // Запрашиваем данные с API
        const response = await axios.get(`${apiBase}/animals/`, { params });
        
        animals.value = response.data;
        totalItems.value = response.data.length; // В идеале API должен возвращать общее количество
        
      } catch (err) {
        console.error('Ошибка при загрузке животных:', err);
        error.value = 'Не удалось загрузить данные. Пожалуйста, попробуйте позже.';
      } finally {
        loading.value = false;
      }
    };
    
    /**
     * Загружает справочные данные (типы животных, ареалы обитания)
     */
    const loadReferenceData = async () => {
      try {
        // Загружаем типы/классы животных
        const typesResponse = await axios.get(`${apiBase}/animal-types/`);
        animalTypes.value = typesResponse.data;
        
        // Загружаем ареалы обитания
        const habitatsResponse = await axios.get(`${apiBase}/habitats/`);
        habitats.value = habitatsResponse.data;
        
      } catch (err) {
        console.error('Ошибка при загрузке справочных данных:', err);
        error.value = 'Не удалось загрузить справочные данные.';
      }
    };
    
    /**
     * Загружает избранные животные пользователя
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
     * Переключает статус избранного для животного
     * @param {Object} animal - Объект с данными о животном
     */
    const toggleFavorite = async (animal) => {
      try {
        const isFav = isFavorite(animal.id);
        
        if (isFav) {
          // Удаляем из избранного
          await axios.delete(`${apiBase}/animals/favorites/${animal.id}`);
          favorites.value = favorites.value.filter(id => id !== animal.id);
        } else {
          // Добавляем в избранное
          await axios.post(`${apiBase}/animals/favorites/`, {
            animal_id: animal.id
          });
          favorites.value.push(animal.id);
        }
      } catch (err) {
        console.error('Ошибка при обновлении избранного:', err);
      }
    };
    
    /**
     * Создает debounce-функцию для поиска
     */
    const debouncedSearch = (() => {
      let timeout = null;
      return () => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
          currentPage.value = 1; // Сбрасываем страницу на первую при поиске
          loadAnimals();
        }, 500); // Задержка 500 мс
      };
    })();
    
    /**
     * Переключает состояние выпадающего списка
     * @param {string} dropdown - Имя выпадающего списка
     */
    const toggleDropdown = (dropdown) => {
      activeDropdown.value = activeDropdown.value === dropdown ? null : dropdown;
    };
    
    /**
     * Выбирает опцию сортировки
     * @param {string} option - Выбранная опция сортировки
     */
    const selectSort = (option) => {
      sortBy.value = option;
      activeDropdown.value = null;
      loadAnimals();
    };
    
    /**
     * Выбирает класс животного для фильтрации
     * @param {number} classId - ID класса животного
     */
    const selectClass = (classId) => {
      selectedClassId.value = classId === selectedClassId.value ? null : classId;
      activeDropdown.value = null;
      currentPage.value = 1;
      loadAnimals();
    };
    
    /**
     * Выбирает ареал обитания для фильтрации
     * @param {number} habitatId - ID ареала обитания
     */
    const selectHabitat = (habitatId) => {
      selectedHabitatId.value = habitatId === selectedHabitatId.value ? null : habitatId;
      activeDropdown.value = null;
      currentPage.value = 1;
      loadAnimals();
    };
    
    /**
     * Получает метку текущей сортировки
     * @returns {string} Метка текущей сортировки
     */
    const getSortLabel = () => {
      const option = sortOptions.find(o => o.value === sortBy.value);
      return option ? option.label : 'Сортировка';
    };
    
    /**
     * Получает метку выбранного класса животного
     * @returns {string} Метка выбранного класса
     */
    const getClassLabel = () => {
      if (!selectedClassId.value) return 'Класс';
      const classType = animalTypes.value.find(t => t.id === selectedClassId.value);
      return classType ? classType.name : 'Класс';
    };
    
    /**
     * Получает метку выбранного ареала обитания
     * @returns {string} Метка выбранного ареала
     */
    const getHabitatLabel = () => {
      if (!selectedHabitatId.value) return 'Ареал обитания';
      const habitat = habitats.value.find(h => h.id === selectedHabitatId.value);
      return habitat ? habitat.name : 'Ареал обитания';
    };
    
    /**
     * Переход на предыдущую страницу
     */
    const prevPage = () => {
      if (currentPage.value > 1) {
        currentPage.value--;
        loadAnimals();
      }
    };
    
    /**
     * Переход на следующую страницу
     */
    const nextPage = () => {
      if (currentPage.value < totalPages.value) {
        currentPage.value++;
        loadAnimals();
      }
    };
    
    /**
     * Проверяет, является ли текущий пользователь администратором
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
    
    // Инициализация при монтировании компонента
    onMounted(async () => {
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
      
      // Загружаем справочные данные и животных
      await loadReferenceData();
      await loadFavorites();
      await loadAnimals();
    });
    
    return {
      animals,
      loading,
      error,
      searchQuery,
      animalTypes,
      habitats,
      selectedClassId,
      selectedHabitatId,
      sortBy,
      sortOptions,
      showFavorites,
      activeDropdown,
      currentPage,
      totalPages,
      isAdmin,
      
      loadAnimals,
      toggleFavorite,
      isFavorite,
      getImageUrl,
      handleImageError,
      toggleDropdown,
      selectSort,
      selectClass,
      selectHabitat,
      getSortLabel,
      getClassLabel,
      getHabitatLabel,
      prevPage,
      nextPage,
      debouncedSearch
    };
  }
}
</script>

<style scoped>
/* Стили для заголовка и кнопки добавления */
.catalog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.add-animal-button {
  display: flex;
  align-items: center;
  background-color: #4CAF50;
  color: white;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 4px;
  transition: background-color 0.3s;
  font-size: 16px;
}

.add-animal-button:hover {
  background-color: #45a049;
}

.plus-icon {
  margin-right: 8px;
  font-size: 18px;
  font-weight: bold;
}

/* Основные стили контейнера */
.catalog-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  font-size: 24px;
  margin-bottom: 20px;
  color: #333;
}

/* Стили панели фильтров */
.filters-panel {
  background-color: #f5f5f5;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

/* Стили поля поиска */
.search-container {
  position: relative;
  width: 100%;
}

.search-input {
  width: 100%;
  padding: 12px 40px 12px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 16px;
  box-sizing: border-box;
}

.search-icon {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
}

/* Стили выпадающих списков */
.dropdown-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-group {
  position: relative;
  display: inline-block;
  flex: 1;
  min-width: 150px;
}

.dropdown-toggle {
  width: 100%;
  padding: 10px;
  background-color: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  text-align: left;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dropdown-toggle .arrow {
  font-size: 10px;
  margin-left: 5px;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  width: 100%;
  background-color: white;
  border: 1px solid #ccc;
  border-top: none;
  border-radius: 0 0 4px 4px;
  z-index: 10;
  max-height: 200px;
  overflow-y: auto;
}

.dropdown-item {
  padding: 10px;
  cursor: pointer;
}

.dropdown-item:hover {
  background-color: #f0f0f0;
}

.dropdown-item.active {
  background-color: #e8f5e9;
  color: #4CAF50;
}

/* Стили для флажка "Избранное" */
.favorites-filter {
  display: flex;
  align-items: center;
}

.favorite-toggle {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.favorite-toggle input[type="checkbox"] {
  margin-right: 8px;
}

/* Стили для сетки животных */
.animals-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}

.animal-card {
  background-color: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  position: relative;
  transition: transform 0.3s, box-shadow 0.3s;
}

.animal-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.15);
}

.animal-image {
  height: 180px;
  overflow: hidden;
  background-color: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.animal-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.animal-info {
  padding: 10px;
  text-align: center;
}

.animal-name {
  margin: 0;
  font-size: 16px;
  color: #333;
}

/* Стили кнопки избранного */
.favorite-button {
  position: absolute;
  top: 10px;
  right: 10px;
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
}

.favorite-button:hover {
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

/* Стили для загрузки и сообщений об ошибках */
.loading-message,
.error-message,
.no-results {
  text-align: center;
  padding: 20px;
}

.spinner {
  border: 3px solid rgba(0, 0, 0, 0.1);
  border-top: 3px solid #4CAF50;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
  margin: 0 auto 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.retry-button {
  padding: 8px 16px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  margin-top: 10px;
}

/* Стили для пагинации */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 20px;
}

.pagination-button {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 8px 16px;
  margin: 0 10px;
  border-radius: 4px;
  cursor: pointer;
}

.pagination-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
}

/* Медиа-запросы для адаптивности */
@media (max-width: 768px) {
  .dropdown-filters {
    flex-direction: column;
  }
  
  .filter-group {
    min-width: auto;
  }
  
  .animals-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }
}
</style>