<template>
  <div class="catalog-container">
    <div class="catalog-header">
      <h1>Каталог редких видов</h1>
      
      <div class="header-actions">
        <!-- Кнопка добавления нового вида (только для администраторов) -->
        <router-link v-if="isAdmin" to="/add-animal" class="add-animal-button">
          <span class="plus-icon">+</span> Добавить
        </router-link>

        <!-- Ссылка на личный кабинет -->
        <router-link to="/profile" class="profile-button" title="Личный кабинет">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="profile-icon">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
          </svg>
        </router-link>
      </div>
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
            <!-- Индикатор загрузки для классов животных -->
            <div v-if="!animalTypes.length" class="dropdown-loading">
              <div class="mini-spinner"></div>
              <span>Загрузка классов...</span>
            </div>
            <!-- Опция "Все классы" -->
            <div 
              v-else
              class="dropdown-item" 
              @click="selectClass(null)"
              :class="{ active: selectedClassId === null }"
            >
              Все классы
            </div>
            <!-- Доступные классы животных -->
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
            <!-- Индикатор загрузки для ареалов обитания -->
            <div v-if="!habitats.length" class="dropdown-loading">
              <div class="mini-spinner"></div>
              <span>Загрузка ареалов...</span>
            </div>
            <!-- Опция "Все ареалы" -->
            <div 
              v-else
              class="dropdown-item" 
              @click="selectHabitat(null)"
              :class="{ active: selectedHabitatId === null }"
            >
              Все ареалы
            </div>
            <!-- Доступные ареалы обитания -->
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

        <div class="filter-group favorites-filter" v-if="!isAdmin">
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

    <!-- Информация о количестве найденных видов -->
    <div class="animals-count" v-if="!loading && !error">
      <span>Найдено видов животных: {{ animals.length }}</span>
      <a 
        v-if="isAnyFilterActive" 
        href="#" 
        class="reset-filters-link" 
        @click.prevent="resetAllFilters"
      >Сбросить фильтры</a>
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

    <!-- Каталог животных (с прокруткой) -->
    <div v-if="!loading && !error && animals.length > 0" class="animals-grid">
      <div v-for="animal in animals" :key="animal.id" class="animal-card">
        <!-- Оборачиваем карточку в router-link для перехода на страницу деталей -->
        <router-link 
          :to="`/animal/${animal.id}`" 
          class="animal-card-link"
        >
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
        </router-link>
        
        <!-- Кнопка редактирования для администраторов -->
        <router-link 
          v-if="isAdmin" 
          :to="`/edit-animal/${animal.id}`" 
          class="edit-button"
          title="Редактировать"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="edit-icon">
            <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
          </svg>
        </router-link>
        
        <!-- Кнопка избранного (только для не-администраторов) -->
        <button 
          v-if="!isAdmin"
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
  </div>
</template>

<script>
import { ref, onMounted, watch, onBeforeUnmount, computed } from 'vue';
import axios from 'axios';
import { useRoute } from 'vue-router';

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
    // Константы и настройки
    const BACKEND_PORT = process.env.BACKEND_PORT;
    const SITE_IP = process.env.SITE_IP;
    
    // Определяем базовый URL API в зависимости от окружения
    const apiBase = process.env.NODE_ENV === 'production' 
      ? '/api'
      : `${SITE_IP}:${BACKEND_PORT}/api`;
    const isAdmin = ref(false);  // Статус администратора
    const route = useRoute();
    let refreshInterval = null;
    let authListener = null; // Слушатель событий авторизации
    
    // Параметры фильтрации
    const searchQuery = ref('');
    const selectedClassId = ref(null);
    const selectedHabitatId = ref(null);
    const sortBy = ref('name');
    const sortOrder = ref('asc');
    const showFavorites = ref(false);
    
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
     * @async
     */
    const loadAnimals = async () => {
      try {
        loading.value = true;
        error.value = '';
        
        // Вычисляем параметры сортировки
        const [sortField, sortDirection] = sortBy.value.includes('_') 
          ? sortBy.value.split('_') 
          : [sortBy.value, sortOrder.value];
        
        // Формируем параметры запроса
        const params = {
          skip: 0,
          limit: 10000, // Большой лимит для получения всех записей
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
        
      } catch (err) {
        console.error('Ошибка при загрузке животных:', err);
        error.value = 'Не удалось загрузить данные. Пожалуйста, попробуйте позже.';
      } finally {
        loading.value = false;
      }
    };
    
    /**
     * Загружает справочные данные (типы животных, ареалы обитания)
     * @async
     * @returns {Promise<boolean>} - Успешна ли загрузка данных
     */
    const loadReferenceData = async () => {
      try {
        // Создаем промисы для параллельных запросов
        const typesPromise = axios.get(`${apiBase}/animal-types/`);
        const habitatsPromise = axios.get(`${apiBase}/habitats/`);
        
        // Параллельно загружаем типы/классы животных и ареалы обитания
        const [typesResponse, habitatsResponse] = await Promise.all([typesPromise, habitatsPromise]);
        
        animalTypes.value = typesResponse.data;
        habitats.value = habitatsResponse.data;
        
        // Проверяем, что данные действительно получены
        if (animalTypes.value.length === 0 || habitats.value.length === 0) {
          console.warn('Предупреждение: получены пустые справочные данные');
          if (animalTypes.value.length === 0) {
            console.warn('Классы животных: пустой массив');
          }
          if (habitats.value.length === 0) {
            console.warn('Ареалы обитания: пустой массив');
          }
          
          // Если данные пустые, пытаемся загрузить еще раз через 1 секунду
          if (animalTypes.value.length === 0 || habitats.value.length === 0) {
            console.log('Пытаемся повторно загрузить справочные данные...');
            setTimeout(() => retryLoadReferenceData(), 1000);
            return false;
          }
        }
        
        return true;
        
      } catch (err) {
        console.error('Ошибка при загрузке справочных данных:', err);
        error.value = 'Не удалось загрузить справочные данные.';
        
        // Пытаемся загрузить еще раз через 2 секунды
        setTimeout(() => retryLoadReferenceData(), 2000);
        return false;
      }
    };
    
    /**
     * Повторная попытка загрузки справочных данных
     * @async
     */
    const retryLoadReferenceData = async () => {
      try {
        console.log('Повторная загрузка справочных данных...');
        
        // Загружаем типы/классы животных если они отсутствуют или пусты
        if (!animalTypes.value || animalTypes.value.length === 0) {
          const typesResponse = await axios.get(`${apiBase}/animal-types/`);
          animalTypes.value = typesResponse.data;
          console.log('Справочник классов животных перезагружен:', animalTypes.value);
        }
        
        // Загружаем ареалы обитания если они отсутствуют или пусты
        if (!habitats.value || habitats.value.length === 0) {
          const habitatsResponse = await axios.get(`${apiBase}/habitats/`);
          habitats.value = habitatsResponse.data;
          console.log('Справочник ареалов обитания перезагружен:', habitats.value);
        }
        
        // Если данные все еще не загрузились, показываем сообщение пользователю
        if ((animalTypes.value && animalTypes.value.length === 0) || 
            (habitats.value && habitats.value.length === 0)) {
          error.value = 'Не удалось загрузить некоторые справочные данные. Пожалуйста, обновите страницу.';
        } else {
          // Если данные успешно загрузились, сбрасываем сообщение об ошибке
          if (error.value === 'Не удалось загрузить справочные данные.') {
            error.value = '';
          }
        }
      } catch (err) {
        console.error('Ошибка при повторной загрузке справочных данных:', err);
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
     * Переключает статус избранного для животного
     * @async
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
          loadAnimals();
        }, 500); // Задержка 500 мс
      };
    })();
    
    /**
     * Переключает состояние выпадающего списка
     * @param {string} dropdown - Имя выпадающего списка
     */
    const toggleDropdown = (dropdown) => {
      // Проверка наличия данных при открытии списка и их повторная загрузка при необходимости
      if (dropdown === 'class' && (!animalTypes.value || animalTypes.value.length === 0)) {
        console.log('Попытка открытия выпадающего списка классов, но данные отсутствуют. Загружаем...');
        // Загрузка классов при клике на выпадающий список
        axios.get(`${apiBase}/animal-types/`)
          .then(response => {
            animalTypes.value = response.data;
            console.log('Классы животных загружены при открытии списка:', animalTypes.value);
          })
          .catch(err => {
            console.error('Не удалось загрузить классы животных при открытии списка:', err);
          });
      }
      
      if (dropdown === 'habitat' && (!habitats.value || habitats.value.length === 0)) {
        console.log('Попытка открытия выпадающего списка ареалов, но данные отсутствуют. Загружаем...');
        // Загрузка ареалов при клике на выпадающий список
        axios.get(`${apiBase}/habitats/`)
          .then(response => {
            habitats.value = response.data;
            console.log('Ареалы обитания загружены при открытии списка:', habitats.value);
          })
          .catch(err => {
            console.error('Не удалось загрузить ареалы обитания при открытии списка:', err);
          });
      }
      
      // Переключаем состояние выпадающего списка
      activeDropdown.value = activeDropdown.value === dropdown ? null : dropdown;
    };
    
    /**
     * Закрывает выпадающий список при клике вне его области
     * @param {Event} event - Событие клика
     */
    const closeDropdownOnClickOutside = (event) => {
      // Если нет активного выпадающего списка, ничего не делаем
      if (!activeDropdown.value) return;

      // Проверяем, является ли цель клика элементом выпадающего списка или его кнопкой
      const isDropdownElement = event.target.closest('.dropdown-menu');
      const isDropdownButton = event.target.closest('.dropdown-toggle');

      // Если клик был вне выпадающего списка и его кнопки, закрываем список
      if (!isDropdownElement && !isDropdownButton) {
        activeDropdown.value = null;
      }
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
      loadAnimals();
    };
    
    /**
     * Выбирает ареал обитания для фильтрации
     * @param {number} habitatId - ID ареала обитания
     */
    const selectHabitat = (habitatId) => {
      selectedHabitatId.value = habitatId === selectedHabitatId.value ? null : habitatId;
      activeDropdown.value = null;
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
    
    /**
     * Сбрасывает все фильтры к значениям по умолчанию
     */
    const resetAllFilters = () => {
      searchQuery.value = '';
      selectedClassId.value = null;
      selectedHabitatId.value = null;
      sortBy.value = 'name';
      sortOrder.value = 'asc';
      showFavorites.value = false;
      loadAnimals();
    };
    
    /**
     * Проверяет, активен ли какой-либо фильтр
     * @returns {boolean} true если активен хотя бы один фильтр
     */
    const isAnyFilterActive = computed(() => {
      return (
        searchQuery.value !== '' ||
        selectedClassId.value !== null ||
        selectedHabitatId.value !== null ||
        showFavorites.value === true ||
        sortBy.value !== 'name' ||
        sortOrder.value !== 'asc'
      );
    });
    
    /**
     * Настраивает автоматическое обновление списка животных
     * Запускается при возвращении с формы добавления животного
     */
    const setupRefresh = () => {
      // Проверяем, возвращаемся ли мы с формы добавления животного
      const justAddedAnimal = route.query.refreshCatalog === 'true';
      if (justAddedAnimal) {
        // Загружаем обновленный список животных
        loadAnimals();
      }
      
      // Настраиваем периодическое обновление данных
      refreshInterval = setInterval(() => {
        // Обновляем данные только если страница активна и видима пользователю
        if (!document.hidden) {
          loadAnimals();
        }
      }, 60000); // Обновляем данные каждую минуту
    };
    
    /**
     * Настраивает слушателя событий авторизации
     * Обновляет данные при входе пользователя в систему
     */
    const setupAuthListener = () => {
      // Создаем слушателя события хранилища для отслеживания изменений токена
      authListener = (event) => {
        // Проверяем, что изменился именно ключ 'user' в localStorage
        if (event.key === 'user') {
          // Если добавлен пользователь (вход в систему)
          if (event.newValue && !event.oldValue) {
            console.log('Пользователь авторизовался, обновляем каталог');
            checkAdminStatus();
            loadFavorites().then(() => loadAnimals());
          } 
          // Если удален пользователь (выход из системы)
          else if (!event.newValue && event.oldValue) {
            console.log('Пользователь вышел из системы, обновляем каталог');
            checkAdminStatus();
            favorites.value = []; // Очищаем избранное
            loadAnimals();
          }
          // Если изменены данные пользователя
          else if (event.newValue !== event.oldValue) {
            console.log('Данные пользователя изменились, обновляем каталог');
            checkAdminStatus();
            loadFavorites().then(() => loadAnimals());
          }
        }
      };
      
      // Добавляем слушателя к window.addEventListener
      window.addEventListener('storage', authListener);
      
      // Дополнительно добавляем собственное событие для отслеживания локальных изменений
      window.addEventListener('localAuthChange', () => {
        console.log('Обнаружено локальное изменение авторизации');
        checkAdminStatus();
        loadFavorites().then(() => loadAnimals());
      });
    };
    
    // Следим за изменениями в параметрах URL
    watch(
      () => route.query,
      (newQuery) => {
        // Если есть параметр refreshCatalog, обновляем данные
        if (newQuery.refreshCatalog === 'true') {
          loadAnimals();
        }
      }
    );
    
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
      
      // Настраиваем слушателя авторизации
      setupAuthListener();
      
      try {
        // Запускаем загрузку данных
        console.log('Начинаем загрузку данных...');
        loading.value = true;
        
        // Загружаем справочные данные с возможностью повторных попыток
        const referenceDataLoaded = await loadReferenceData();
        if (!referenceDataLoaded) {
          console.log('Первая попытка загрузки справочных данных не удалась, продолжаем...');
        }
        
        // Загружаем избранные животные и список животных параллельно
        await Promise.all([
          loadFavorites().catch(err => {
            console.error('Ошибка при загрузке избранного:', err);
            // Не останавливаем выполнение при ошибке с избранным
          }),
          loadAnimals()
        ]);
        
        // Проверка наличия данных после загрузки
        if ((!animalTypes.value || animalTypes.value.length === 0) || 
            (!habitats.value || habitats.value.length === 0)) {
          // Если данные не загружены, выполняем ещё одну попытку
          console.log('Данные справочников не были получены, повторная попытка...');
          setTimeout(() => retryLoadReferenceData(), 500);
        }
      } catch (err) {
        console.error('Ошибка при инициализации компонента:', err);
        error.value = 'Не удалось загрузить данные. Попробуйте обновить страницу.';
      } finally {
        loading.value = false;
      }
      
      // Настраиваем автоматическое обновление
      setupRefresh();

      // Добавляем обработчик клика для закрытия выпадающих списков
      document.addEventListener('click', closeDropdownOnClickOutside);
    });
    
    // Очистка при размонтировании компонента
    onBeforeUnmount(() => {
      // Очищаем интервал обновления данных
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
      
      // Удаляем слушателя авторизации
      if (authListener) {
        window.removeEventListener('storage', authListener);
        window.removeEventListener('localAuthChange', () => {});
      }

      // Удаляем обработчик клика для закрытия выпадающих списков
      document.removeEventListener('click', closeDropdownOnClickOutside);
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
      debouncedSearch,
      resetAllFilters,
      isAnyFilterActive
    };
  }
}
</script>

<style scoped>
/* Стили для заголовка и кнопок */
.catalog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.profile-button {
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #2196F3;
  color: white;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  text-decoration: none;
  transition: background-color 0.3s;
}

.profile-button:hover {
  background-color: #1976D2;
}

.profile-icon {
  width: 24px;
  height: 24px;
  fill: white;
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
  padding: 10px 20px;
  /* Вместо фиксированной высоты и запрета прокрутки используем min-height */
  min-height: calc(100vh - 20px);
  /* Разрешаем прокрутку контейнера */
  overflow-y: auto;
  /* Добавляем отступ снизу для десктопной версии */
  padding-bottom: 50px; /* Значительный отступ снизу для предотвращения обрезания карточек */
}

/* Стили для сетки животных без ограничения высоты */
.animals-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
  padding-right: 10px;
  padding-top: 15px;
  padding-left: 10px;
  padding-bottom: 15px;
  /* Добавляем отступ снизу для контейнера животных */
  margin-bottom: 30px;
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

/* Стили для индикатора загрузки в выпадающих списках */
.dropdown-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
  color: #666;
  font-size: 14px;
}

.mini-spinner {
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-top: 2px solid #4CAF50;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  animation: spin 1s linear infinite;
  margin-right: 8px;
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

/* Стили для карточки животного */
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

/* Стили для ссылки на детальную страницу */
.animal-card-link {
  display: block;
  color: inherit;
  text-decoration: none;
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

/* Стили для блока с количеством найденных видов */
.animals-count {
  margin: 0 0 15px 5px;
  font-size: 14px;
}

.animals-count span {
  color: #555; /* Темно-серый цвет текста */
}

.reset-filters-link {
  margin-left: 10px;
  color: #4CAF50;
  text-decoration: none;
  cursor: pointer;
  font-size: 14px;
}

.reset-filters-link:hover {
  text-decoration: underline;
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
  
  /* Отменяем фиксированную высоту и запрет прокрутки для контейнера */
  .catalog-container {
    height: auto;
    overflow: visible;
  }
  
  /* Убираем собственную прокрутку у сетки животных */
  .animals-grid {
    max-height: none;
    overflow-y: visible;
  }
  
  /* Разрешаем прокрутку всей страницы */
  body {
    overflow: auto !important;
  }
}

/* Стили кнопки редактирования */
.edit-button {
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
  text-decoration: none;
}

.edit-button:hover {
  background-color: white;
}

.edit-icon {
  width: 20px;
  height: 20px;
  fill: #2196F3;
}
</style>

<style>
body {
  overflow: hidden;
}
</style>