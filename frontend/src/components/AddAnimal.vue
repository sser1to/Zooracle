<template>
  <div class="add-animal-container">
    <h1 class="page-title">Добавление вида</h1>
    
    <div class="form-container">
      <form @submit.prevent="submitForm" class="animal-form">
        <div class="form-row">
          <!-- Поле ввода названия вида -->
          <div class="form-control">
            <input 
              type="text" 
              v-model="animalData.name" 
              placeholder="Название вида" 
              required
              class="input-field"
            />
            <!-- Сообщение об ошибке уникальности имени -->
            <div v-if="nameErrorMessage" class="error-message-inline">{{ nameErrorMessage }}</div>
          </div>
          
          <!-- Кастомный выпадающий список типов животных -->
          <div class="form-control">
            <div class="filter-group custom-select">
              <button 
                type="button"
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
                
                <!-- Доступные классы животных -->
                <div 
                  class="dropdown-item" 
                  v-for="type in animalTypes" 
                  :key="type.id"
                  @click="selectClass(type.id)"
                  :class="{ active: animalData.animal_type_id === type.id }"
                >
                  {{ type.name }}
                </div>
              </div>
            </div>
          </div>
          
          <!-- Кастомный выпадающий список ареалов обитания -->
          <div class="form-control">
            <div class="filter-group custom-select">
              <button 
                type="button"
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
                
                <!-- Доступные ареалы обитания -->
                <div 
                  class="dropdown-item" 
                  v-for="habitat in habitats" 
                  :key="habitat.id"
                  @click="selectHabitat(habitat.id)"
                  :class="{ active: animalData.habitat_id === habitat.id }"
                >
                  {{ habitat.name }}
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Текстовая область для описания -->
        <div class="form-control full-width">
          <textarea 
            v-model="animalData.description" 
            placeholder="Описание" 
            required
            class="textarea-field"
            rows="10"
          ></textarea>
        </div>
        
        <!-- Загрузка обложки (обязательное поле) -->
        <div class="file-upload-section">
          <label class="file-upload-button">
            <input 
              type="file" 
              @change="handleCoverUpload" 
              accept="image/jpeg, image/png, image/webp"
              name="cover"
              id="cover-input"
              ref="coverInput"
            />
            <div class="upload-button-content">
              <span class="icon">📎</span>
              Загрузите обложку
              <span class="required-indicator">*</span>
            </div>
          </label>
          <span class="file-format-info">JPEG, PNG, WEBP до 4 МБ (обязательно)</span>
          
          <!-- Предварительный просмотр обложки -->
          <div v-if="previewCover" class="preview-container">
            <div class="cover-preview-wrapper">
              <img :src="previewCover" alt="Предпросмотр обложки" class="preview-image" />
              <button 
                type="button" 
                @click="removeCover" 
                class="remove-gallery-image-button"
                aria-label="Удалить обложку"
              >
                &times;
              </button>
            </div>
          </div>
          
          <!-- Сообщение о необходимости загрузить обложку, если она не выбрана -->
          <div v-if="showCoverRequiredError" class="cover-required-error">
            Необходимо загрузить обложку!
          </div>
        </div>
        
        <!-- Загрузка изображений -->
        <div class="file-upload-section">
          <label class="file-upload-button" :class="{ 'disabled': previewImages.length >= MAX_IMAGES }">
            <input 
              type="file" 
              @change="handleImagesUpload" 
              accept="image/jpeg, image/png, image/webp"
              multiple
              :disabled="previewImages.length >= MAX_IMAGES"
            />
            <div class="upload-button-content">
              <span class="icon">📎</span>
              Загрузите изображения
              <span v-if="previewImages.length >= MAX_IMAGES" class="limit-indicator">(лимит достигнут)</span>
            </div>
          </label>
          <span class="file-format-info">JPEG, PNG, WEBP до 4 МБ (максимум {{ MAX_IMAGES }} изображений)</span>
          
          <!-- Предварительный просмотр изображений -->
          <div v-if="previewImages.length" class="preview-gallery">
            <div 
              v-for="(image, index) in previewImages" 
              :key="index" 
              class="gallery-item"
            >
              <img :src="image.preview" alt="Предпросмотр изображения" class="gallery-image" />
              <button 
                type="button" 
                @click="removeImage(index)" 
                class="remove-gallery-image-button"
              >
                &times;
              </button>
            </div>
          </div>
          
          <!-- Счетчик изображений -->
          <div v-if="previewImages.length > 0" class="images-counter">
            Загружено изображений: {{ previewImages.length }} из {{ MAX_IMAGES }}
          </div>
        </div>
        
        <!-- Загрузка видео -->
        <div class="file-upload-section">
          <label class="file-upload-button">
            <input 
              type="file" 
              @change="handleVideoUpload" 
              accept="video/mp4, video/avi"
            />
            <div class="upload-button-content">
              <span class="icon">📎</span>
              Загрузите видео
            </div>
          </label>
          <span class="file-format-info">MP4, AVI до 1 ГБ</span>
          
          <!-- Название выбранного видеофайла -->
          <div v-if="selectedVideo" class="selected-video-info">
            <span>{{ selectedVideo.name }}</span>
            <button 
              type="button" 
              @click="removeVideo" 
              class="remove-video-button"
            >
              Удалить
            </button>
          </div>
        </div>
        
        <!-- Сообщения об ошибках -->
        <div v-if="error" class="error-message">
          <p>{{ error }}</p>
        </div>
        
        <!-- Кнопки управления формой -->
        <div class="form-buttons">
          <button 
            type="submit" 
            class="submit-button"
            :disabled="isSubmitting"
          >
            {{ isSubmitting ? 'Добавление...' : 'Добавить' }}
          </button>
          <button 
            type="button" 
            @click="$router.push('/')" 
            class="cancel-button"
          >
            Отмена
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, reactive, onBeforeUnmount } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router';

/**
 * Компонент для добавления нового вида животных
 * @component
 */
export default {
  name: 'AddAnimal',
  
  setup() {
    // Константы и настройки
    const BACKEND_PORT = process.env.BACKEND_PORT;
    const FRONTEND_URL = process.env.FRONTEND_URL;
    
    // Определяем базовый URL API в зависимости от окружения
    const apiBase = process.env.NODE_ENV === 'production' 
      ? '/api'
      : `${FRONTEND_URL}:${BACKEND_PORT}/api`;
    
    const router = useRouter();
    
    // Константа для максимального количества дополнительных изображений
    const MAX_IMAGES = 3;
    
    // Реактивные переменные состояния
    const animalTypes = ref([]);
    const habitats = ref([]);
    const error = ref('');
    const isSubmitting = ref(false);
    const showCoverRequiredError = ref(false);
    const nameErrorMessage = ref('');
    const isCheckingName = ref(false);
    
    // Данные животного
    const animalData = reactive({
      name: '',
      animal_type_id: '',
      habitat_id: '',
      description: ''
    });
    
    // Файлы и предпросмотры
    const selectedCover = ref(null);
    const previewCover = ref('');
    const selectedVideo = ref(null);
    const selectedImages = ref([]);
    const previewImages = ref([]);

    // Состояние UI для кастомных выпадающих списков
    const activeDropdown = ref(null);
    
    /**
     * Проверяет уникальность имени вида животного
     * @async
     * @param {string} name - Имя животного для проверки
     * @returns {Promise<boolean>} - true если имя уникально, false если уже существует
     */
    const checkNameUnique = async (name) => {
      try {
        isCheckingName.value = true;
        nameErrorMessage.value = '';
        
        // Ищем животных с таким же именем через поисковый запрос
        const response = await axios.get(`${apiBase}/animals/`, {
          params: {
            search: name,
            limit: 100
          }
        });
        
        // Проверяем, есть ли точное совпадение по имени
        const exactMatch = response.data.find(animal => 
          animal.name.toLowerCase() === name.toLowerCase()
        );
        
        // Если найдено точное совпадение, имя не уникально
        if (exactMatch) {
          nameErrorMessage.value = 'Вид животного с таким названием уже существует';
          return false;
        }
        
        return true;
      } catch (err) {
        console.error('Ошибка при проверке уникальности имени:', err);
        return true;
      } finally {
        isCheckingName.value = false;
      }
    };
    
    /**
     * Загружает справочные данные (типы животных, ареалы обитания)
     * @async
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
     * Получает метку выбранного класса животного
     * @returns {string} Метка выбранного класса
     */
    const getClassLabel = () => {
      if (!animalData.animal_type_id) return 'Класс';
      const classType = animalTypes.value.find(t => t.id === animalData.animal_type_id);
      return classType ? classType.name : 'Класс';
    };
    
    /**
     * Получает метку выбранного ареала обитания
     * @returns {string} Метка выбранного ареала
     */
    const getHabitatLabel = () => {
      if (!animalData.habitat_id) return 'Ареал обитания';
      const habitat = habitats.value.find(h => h.id === animalData.habitat_id);
      return habitat ? habitat.name : 'Ареал обитания';
    };

    /**
     * Выбирает класс животного для формы
     * @param {number} classId - ID класса животного
     */
    const selectClass = (classId) => {
      animalData.animal_type_id = classId;
      activeDropdown.value = null;
    };
    
    /**
     * Выбирает ареал обитания для формы
     * @param {number} habitatId - ID ареала обитания
     */
    const selectHabitat = (habitatId) => {
      animalData.habitat_id = habitatId;
      activeDropdown.value = null;
    };
    
    /**
     * Обработчик загрузки обложки
     * @param {Event} event - Событие загрузки файла
     */
    const handleCoverUpload = (event) => {
      const file = event.target.files[0];
      if (!file) return;
      
      // Проверка на размер файла
      if (file.size > 4 * 1024 * 1024) {
        error.value = 'Размер файла обложки не должен превышать 4 МБ';
        return;
      }
      
      // Сохраняем файл и создаем предпросмотр
      selectedCover.value = file;
      previewCover.value = URL.createObjectURL(file);
      showCoverRequiredError.value = false; // Сбрасываем ошибку после загрузки обложки
    };
    
    /**
     * Удаляет выбранную обложку
     */
    const removeCover = () => {
      selectedCover.value = null;
      previewCover.value = '';
    };
    
    /**
     * Обработчик загрузки изображений
     * @param {Event} event - Событие загрузки файлов
     */
    const handleImagesUpload = (event) => {
      const files = Array.from(event.target.files);
      if (!files.length) return;
      
      // Проверяем, не превышен ли лимит загрузки изображений
      if (selectedImages.value.length + files.length > MAX_IMAGES) {
        error.value = `Превышен лимит загрузки изображений. Максимум ${MAX_IMAGES} изображений.`;
        return;
      }
      
      // Обрабатываем каждый файл
      files.forEach(file => {
        // Проверка на размер файла (4MB)
        if (file.size > 4 * 1024 * 1024) {
          error.value = `Размер файла "${file.name}" превышает 4 МБ`;
          return;
        }
        
        // Добавляем файл в список и создаем предпросмотр
        selectedImages.value.push(file);
        previewImages.value.push({
          file: file,
          preview: URL.createObjectURL(file)
        });
      });
      
      // Сбрасываем ошибку, если после обработки файлов её не возникло
      if (error.value.includes('Превышен лимит') && selectedImages.value.length <= MAX_IMAGES) {
        error.value = '';
      }
    };
    
    /**
     * Удаляет изображение из списка по индексу
     * @param {number} index - Индекс изображения для удаления
     */
    const removeImage = (index) => {
      // Освобождаем URL для предотвращения утечек памяти
      URL.revokeObjectURL(previewImages.value[index].preview);
      
      // Удаляем файл из обоих массивов
      selectedImages.value.splice(index, 1);
      previewImages.value.splice(index, 1);
    };
    
    /**
     * Обработчик загрузки видео
     * @param {Event} event - Событие загрузки файла
     */
    const handleVideoUpload = (event) => {
      const file = event.target.files[0];
      if (!file) return;
      
      // Проверка на размер файла (1GB = 1024 * 1024 * 1024 байт)
      if (file.size > 1024 * 1024 * 1024) {
        error.value = 'Размер видеофайла не должен превышать 1 ГБ';
        return;
      }
      
      // Сохраняем файл
      selectedVideo.value = file;
    };
    
    /**
     * Удаляет выбранное видео
     */
    const removeVideo = () => {
      selectedVideo.value = null;
    };
    
    /**
     * Загружает файл на сервер через API
     * @async
     * @param {File} file - Файл для загрузки
     * @returns {Promise<string|null>} - ID загруженного файла или null при ошибке
     */
    const uploadFile = async (file) => {
      // Создаем объект FormData для отправки файла
      const formData = new FormData();
      formData.append('file', file);
      
      try {
        const response = await axios.post(`${apiBase}/media/upload/`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        return response.data.file_id;
      } catch (err) {
        console.error('Ошибка при загрузке файла:', err);
        return null;
      }
    };

    /**
     * Очищает форму после добавления животного
     */
    const resetForm = () => {
      // Сбрасываем данные формы
      animalData.name = '';
      animalData.animal_type_id = '';
      animalData.habitat_id = '';
      animalData.description = '';
      
      // Сбрасываем файлы
      selectedCover.value = null;
      previewCover.value = '';
      
      selectedVideo.value = null;
      
      // Очищаем изображения и освобождаем ресурсы
      previewImages.value.forEach(image => {
        URL.revokeObjectURL(image.preview);
      });
      selectedImages.value = [];
      previewImages.value = [];
      
      // Сбрасываем сообщения об ошибках
      error.value = '';
      showCoverRequiredError.value = false;
      nameErrorMessage.value = '';
    };
    
    /**
     * Отправляет форму на сервер
     * @async
     */
    const submitForm = async () => {
      try {
        error.value = '';
        nameErrorMessage.value = '';
        isSubmitting.value = true;
        
        // Проверка наличия обложки (обязательное поле)
        if (!selectedCover.value) {
          showCoverRequiredError.value = true;
          isSubmitting.value = false;
          return;
        }
        
        // Проверяем уникальность имени перед отправкой
        if (animalData.name) {
          const isUnique = await checkNameUnique(animalData.name);
          if (!isUnique) {
            isSubmitting.value = false;
            return;
          }
        }
        
        // Создаем массив для хранения всех загрузок
        const uploadPromises = [];
        let previewId = null;
        let videoId = null;
        
        // Загружаем обложку (обязательное поле)
        if (selectedCover.value) {
          uploadPromises.push(
            uploadFile(selectedCover.value)
              .then(id => { 
                previewId = id;
                if (!id) {
                  throw new Error('Не удалось загрузить обложку');
                }
              })
          );
        }
        
        // Загружаем видео (если есть)
        if (selectedVideo.value) {
          uploadPromises.push(
            uploadFile(selectedVideo.value)
              .then(id => { videoId = id; })
          );
        }
        
        // Ожидаем завершения всех загрузок
        await Promise.all(uploadPromises);
        
        // Преобразуем данные животного в правильный формат для API
        const animalPayload = {
          name: animalData.name,
          description: animalData.description,
          animal_type_id: animalData.animal_type_id ? parseInt(animalData.animal_type_id, 10) : null,
          habitat_id: animalData.habitat_id ? parseInt(animalData.habitat_id, 10) : null,
          preview_id: previewId,
          video_id: videoId
        };
        
        console.log('Отправляемые данные животного:', animalPayload);
        
        // Отправляем запрос на создание животного
        const animalResponse = await axios.post(`${apiBase}/animals/`, animalPayload);
        const animalId = animalResponse.data.id;
        
        // Массив для хранения обещаний загрузки дополнительных изображений
        const imageUploadPromises = [];
        
        // Загружаем и привязываем дополнительные изображения
        if (selectedImages.value.length) {
          for (const image of selectedImages.value) {
            imageUploadPromises.push(
              uploadFile(image).then(imageId => {
                if (imageId) {
                  // Логируем идентификатор загруженного файла
                  console.log(`Загружено изображение с ID: ${imageId}`);
                  
                  const photoData = {
                    photo_id: imageId
                  };
                  
                  console.log(`Отправляем запрос на добавление фото к животному ${animalId}:`, photoData);
                  
                  // Добавляем фото к животному только если загрузка прошла успешно
                  return axios.post(`${apiBase}/animals/${animalId}/photos/`, photoData)
                    .then(response => {
                      console.log(`Фото ${imageId} успешно связано с животным:`, response.data);
                      return response.data;
                    })
                    .catch(err => {
                      console.error(`Не удалось связать фото ${imageId} с животным:`, err);
                      
                      // Детализируем ошибку для отладки
                      if (err.response) {
                        console.error('Данные ответа:', err.response.data);
                        console.error('Статус:', err.response.status);
                        console.error('Заголовки:', err.response.headers);
                      } else if (err.request) {
                        console.error('Запрос был сделан, но ответ не получен:', err.request);
                      } else {
                        console.error('Ошибка при настройке запроса:', err.message);
                      }
                      
                      return null;
                    });
                }
                return null;
              }).catch(err => {
                console.error('Ошибка при загрузке изображения:', err);
                return null;
              })
            );
          }
        }
        
        // Ожидаем завершения связывания всех изображений
        await Promise.allSettled(imageUploadPromises);
        
        // Очищаем форму после успешного добавления
        resetForm();
        
        // Перенаправляем на главную с параметром для обновления каталога
        router.push({ path: '/', query: { refreshCatalog: 'true' } });
      } catch (err) {
        console.error('Ошибка при добавлении животного:', err);
        
        // Получаем детальное описание ошибки из ответа API
        if (err.response && err.response.data && err.response.data.detail) {
          if (Array.isArray(err.response.data.detail)) {
            // Если ошибка содержит массив деталей, объединяем их
            error.value = err.response.data.detail.map(item => item.msg).join(', ');
          } else {
            // Если ошибка содержит строку
            error.value = err.response.data.detail;
          }
        } else {
          error.value = err.message || 'Произошла ошибка при добавлении животного';
        }
      } finally {
        isSubmitting.value = false;
      }
    };
    
    // Загружаем справочные данные при монтировании компонента
    onMounted(() => {
      // Настраиваем axios для работы с токенами
      axios.interceptors.request.use(config => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      });
      
      // Очищаем форму при каждом монтировании компонента
      resetForm();
      
      // Загружаем справочные данные
      loadReferenceData();
      
      // Добавляем обработчик клика для закрытия выпадающих списков
      document.addEventListener('click', closeDropdownOnClickOutside);
    });
    
    // Очищаем при размонтировании компонента
    onBeforeUnmount(() => {
      // Удаляем обработчик клика для закрытия выпадающих списков
      document.removeEventListener('click', closeDropdownOnClickOutside);
    });
    
    return {
      animalTypes,
      habitats,
      animalData,
      error,
      isSubmitting,
      selectedCover,
      previewCover,
      selectedVideo,
      previewImages,
      showCoverRequiredError,
      nameErrorMessage,
      isCheckingName,
      handleCoverUpload,
      removeCover,
      handleImagesUpload,
      removeImage,
      handleVideoUpload,
      removeVideo,
      submitForm,
      MAX_IMAGES,
      toggleDropdown,
      getClassLabel,
      getHabitatLabel,
      selectClass,
      selectHabitat,
      activeDropdown
    };
  }
};
</script>

<style scoped>
.add-animal-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 500;
  color: #333;
  margin-bottom: 20px;
  text-align: left;
}

.form-container {
  background-color: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.animal-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-row {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.form-control {
  flex: 1;
  min-width: 200px;
}

.full-width {
  width: 100%;
}

.input-field,
.select-field,
.textarea-field {
  width: 100%;
  padding: 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 16px;
  box-sizing: border-box;
  transition: border-color 0.3s;
}

.input-field:focus,
.select-field:focus,
.textarea-field:focus {
  border-color: #4CAF50;
  outline: none;
}

.textarea-field {
  resize: vertical;
  min-height: 150px;
}

/* Стили для кастомных выпадающих списков */
.custom-select {
  position: relative;
}

.dropdown-toggle {
  width: 100%;
  padding: 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 16px;
  background-color: #fff;
  text-align: left;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  width: 100%;
  background-color: #fff;
  border: 1px solid #ccc;
  border-radius: 0 0 4px 4px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 10;
  max-height: 200px;
  overflow-y: auto;
}

.dropdown-item {
  padding: 10px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.dropdown-item:hover {
  background-color: #f0f0f0;
}

.dropdown-item.active {
  background-color: #4CAF50;
  color: #fff;
}

.dropdown-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
  font-size: 14px;
  color: #666;
}

.mini-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-top: 2px solid #4CAF50;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 8px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.arrow {
  font-size: 10px;
  margin-left: 5px;
}

/* Стили для загрузки файлов */
.file-upload-section {
  margin-bottom: 10px;
}

.file-upload-button {
  display: inline-block;
  cursor: pointer;
}

.file-upload-button input[type="file"] {
  display: none;
}

.upload-button-content {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 15px;
  background-color: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  transition: background-color 0.3s;
}

.upload-button-content:hover {
  background-color: #e0e0e0;
}

.icon {
  font-size: 18px;
}

.file-format-info {
  margin-left: 10px;
  font-size: 12px;
  color: #666;
}

/* Стили для предпросмотра изображений */
.preview-container {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* Контейнер для изображения обложки и кнопки удаления */
.cover-preview-wrapper {
  position: relative;
  display: inline-block;
}

.preview-image {
  max-width: 200px;
  max-height: 200px;
  border-radius: 4px;
  margin-top: 10px;
}

.preview-gallery {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
  justify-content: center;
}

.gallery-item {
  position: relative;
}

.gallery-image {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 4px;
}

.remove-image-button,
.remove-video-button {
  margin-left: 10px;
  background-color: #ff5252;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 5px 10px;
  cursor: pointer;
}

.remove-gallery-image-button {
  position: absolute;
  top: -8px;
  right: -8px;
  background-color: #ff5252;
  color: white;
  border: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 16px;
}

.selected-video-info {
  margin-top: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

/* Стили сообщений об ошибках */
.error-message {
  background-color: #ffebee;
  color: #d32f2f;
  padding: 10px;
  border-radius: 4px;
  font-size: 14px;
}

.error-message-inline {
  color: #d32f2f;
  font-size: 12px;
  margin-top: 5px;
}

/* Стили кнопок формы */
.form-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  margin-top: 20px;
}

.cancel-button,
.submit-button {
  padding: 12px 24px;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.cancel-button {
  background-color: #f0f0f0;
  color: #333;
}

.cancel-button:hover {
  background-color: #e0e0e0;
}

.submit-button {
  background-color: #4CAF50;
  color: white;
}

.submit-button:hover {
  background-color: #45a049;
}

.submit-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

/* Адаптивные стили */
@media (max-width: 768px) {
  .form-row {
    flex-direction: column;
  }
  
  .form-buttons {
    flex-direction: column;
  }
  
  .cancel-button, 
  .submit-button {
    width: 100%;
  }
}

/* Стиль для индикатора обязательного поля */
.required-indicator {
  color: #ff5252;
  font-weight: bold;
  margin-left: 4px;
}

/* Стиль для сообщения об обязательной обложке */
.cover-required-error {
  color: #ff5252;
  font-size: 14px;
  margin-top: 5px;
}

/* Стиль для неактивной кнопки загрузки файлов */
.file-upload-button.disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.file-upload-button.disabled .upload-button-content {
  background-color: #e0e0e0;
  color: #888;
}

/* Стиль для индикатора достигнутого лимита */
.limit-indicator {
  font-size: 12px;
  color: #ff5252;
  margin-left: 8px;
}

/* Стиль для счетчика изображений */
.images-counter {
  font-size: 14px;
  color: #666;
  margin-top: 8px;
  text-align: center;
}
</style>

<style>
body {
  overflow: auto;
}
</style>