<template>
  <div class="edit-animal-container">
    <h1 class="page-title">Редактирование вида животных</h1>
    
    <div v-if="loading" class="loading-message">
      <div class="spinner"></div>
      <p>Загрузка данных...</p>
    </div>
    
    <div v-if="error && !dataLoaded" class="error-message">
      <p>{{ error }}</p>
      <button @click="loadAnimalData" class="retry-button">Повторить загрузку</button>
      <button @click="$router.push('/')" class="back-button">Вернуться в каталог</button>
    </div>
    
    <div v-if="!loading && dataLoaded" class="form-container">
      <!-- Добавляем кнопку удаления животного в верхней части формы -->
      <div class="delete-animal-container">
        <button 
          type="button" 
          @click="showDeleteConfirmation = true" 
          class="delete-animal-button"
        >
          Удалить вид
        </button>
      </div>

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
            <div v-if="nameErrorMessage" class="error-message">{{ nameErrorMessage }}</div>
          </div>
          
          <!-- Выпадающий список типов животных -->
          <div class="form-control">
            <select 
              v-model="animalData.animal_type_id" 
              required
              class="select-field"
            >
              <option value="" disabled>Класс</option>
              <option 
                v-for="type in animalTypes" 
                :key="type.id" 
                :value="type.id"
              >
                {{ type.name }}
              </option>
            </select>
          </div>
          
          <!-- Выпадающий список ареалов обитания -->
          <div class="form-control">
            <select 
              v-model="animalData.habitat_id" 
              required
              class="select-field"
            >
              <option value="" disabled>Ареал обитания</option>
              <option 
                v-for="habitat in habitats" 
                :key="habitat.id" 
                :value="habitat.id"
              >
                {{ habitat.name }}
              </option>
            </select>
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
        
        <!-- Существующая обложка и возможность загрузить новую -->
        <div class="file-upload-section">
          <div v-if="(currentPreviewUrl && !previewCover) || previewCover" class="current-preview">
            <h3>Обложка:</h3>
            <!-- Контейнер для изображения обложки и кнопки удаления -->
            <div class="cover-preview-wrapper">
              <img 
                :src="previewCover || currentPreviewUrl" 
                alt="Обложка" 
                class="preview-image" 
              />
              <button 
                v-if="previewCover"
                type="button" 
                @click="removeCover" 
                class="remove-gallery-image-button"
                aria-label="Удалить обложку"
              >
                &times;
              </button>
            </div>
          </div>
          
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
              {{ currentPreviewUrl || previewCover ? 'Заменить обложку' : 'Загрузить обложку' }}
              <span v-if="!currentPreviewUrl && !previewCover" class="required-indicator">*</span>
            </div>
          </label>
          <span class="file-format-info">JPEG, PNG, WEBP до 4 МБ</span>
          
          <!-- Сообщение о необходимости загрузить обложку, если она не выбрана и нет текущей -->
          <div v-if="showCoverRequiredError" class="cover-required-error">
            Необходимо загрузить обложку!
          </div>
        </div>
        
        <!-- Существующие изображения -->
        <div v-if="existingImages.length > 0 || previewImages.length > 0" class="existing-images-section">
          <h3>Изображения:</h3>
          <div class="preview-gallery">
            <!-- Существующие изображения -->
            <div 
              v-for="(image, index) in existingImages" 
              :key="`existing-${index}`" 
              class="gallery-item"
            >
              <img 
                :src="getImageUrl(image.photo_id)" 
                alt="Изображение" 
                class="gallery-image"
                @click="openImagePreview(image.photo_id)"
                @error="handleImageError"
              />
              <button 
                type="button" 
                @click="removeExistingImage(index)" 
                class="remove-gallery-image-button"
              >
                &times;
              </button>
            </div>
            
            <!-- Новые изображения в той же галерее -->
            <div 
              v-for="(image, index) in previewImages" 
              :key="`new-${index}`" 
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
        </div>
        
        <!-- Загрузка новых изображений -->
        <div class="file-upload-section">
          <label class="file-upload-button">
            <input 
              type="file" 
              @change="handleImagesUpload" 
              accept="image/jpeg, image/png, image/webp"
              multiple
            />
            <div class="upload-button-content">
              <span class="icon">📎</span>
              Добавить изображения
            </div>
          </label>
          <span class="file-format-info">JPEG, PNG, WEBP до 4 МБ</span>
        </div>
        
        <!-- Информация о текущем видео и возможность просмотра -->
        <div v-if="currentVideoId" class="existing-video-section">
          <h3>Текущее видео:</h3>
          <div class="current-video-info">
            <div class="video-controls-wrapper">
              <button 
                type="button"
                @click="openVideoPreview"
                class="play-video-button"
              >
                Просмотреть
              </button>
              <button 
                type="button" 
                @click="removeCurrentVideo" 
                class="remove-video-button"
              >
                Удалить
              </button>
            </div>
          </div>
          
          <!-- Предпросмотр видео в модальном окне -->
          <div v-if="showVideoPreview" class="video-modal" @click="closeVideoPreview">
            <div class="video-modal-content" @click.stop>
              <button @click="closeVideoPreview" class="close-modal">&times;</button>
              <div class="video-container">
                <video controls class="video-player">
                  <source :src="getVideoUrl(currentVideoId)" type="video/mp4">
                  Ваш браузер не поддерживает видео.
                </video>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Загрузка нового видео -->
        <div class="file-upload-section">
          <label class="file-upload-button">
            <input 
              type="file" 
              @change="handleVideoUpload" 
              accept="video/mp4, video/avi"
            />
            <div class="upload-button-content">
              <span class="icon">📎</span>
              {{ currentVideoId && !removeVideoFlag ? 'Заменить видео' : 'Загрузить видео' }}
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
              Отменить
            </button>
          </div>
        </div>
        
        <!-- Модальное окно просмотра изображения -->
        <div v-if="showImagePreview" class="image-modal" @click="closeImagePreview">
          <div class="image-modal-content" @click.stop>
            <button @click="closeImagePreview" class="close-modal">&times;</button>
            <img :src="previewMediaUrl" class="image-preview-full" alt="Просмотр изображения" />
          </div>
        </div>
        
        <!-- Сообщения об ошибках при отправке формы -->
        <div v-if="formError" class="error-message">
          <p>{{ formError }}</p>
        </div>
        
        <!-- Кнопки управления формой -->
        <div class="form-buttons">
          <button 
            type="button" 
            @click="$router.push('/')" 
            class="cancel-button"
          >
            Отмена
          </button>
          <button 
            type="submit" 
            class="submit-button"
            :disabled="isSubmitting"
          >
            {{ isSubmitting ? 'Сохранение...' : 'Сохранить' }}
          </button>
        </div>
      </form>
    </div>

    <!-- Модальное окно подтверждения удаления -->
    <div v-if="showDeleteConfirmation" class="confirmation-modal" @click.self="showDeleteConfirmation = false">
      <div class="confirmation-content">
        <h3>Удаление вида животного</h3>
        <p>Вы действительно хотите удалить вид "{{ animalData.name }}"?</p>
        <p class="warning-text">Это действие нельзя отменить!</p>
        <div class="confirmation-buttons">
          <button 
            type="button" 
            @click="showDeleteConfirmation = false" 
            class="cancel-delete-button"
          >
            Отмена
          </button>
          <button 
            type="button" 
            @click="deleteAnimal" 
            class="confirm-delete-button"
            :disabled="isDeleting"
          >
            {{ isDeleting ? 'Удаление...' : 'Удалить' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, reactive, computed, watch, onBeforeUnmount, onActivated } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router';

/**
 * Компонент для редактирования вида животных
 * @component
 * @description Позволяет редактировать существующий вид животного
 */
export default {
  name: 'EditAnimal',
  props: {
    id: {
      type: String,
      required: true
    }
  },
  
  setup(props) {
    // Константы и настройки
    const apiBase = 'http://localhost:8000/api';
    const router = useRouter();
    
    // Реактивные переменные состояния
    const animalTypes = ref([]);
    const habitats = ref([]);
    const error = ref('');
    const formError = ref('');
    const isSubmitting = ref(false);
    const loading = ref(true);
    const showCoverRequiredError = ref(false); // Флаг для отображения ошибки обязательной обложки
    const dataLoaded = ref(false); // Флаг, указывающий, что данные успешно загружены
    const nameErrorMessage = ref(''); // Сообщение об ошибке для имени животного
    const isCheckingName = ref(false); // Флаг проверки имени
    const originalName = ref(''); // Оригинальное имя животного для сравнения
    
    // Переменные для предпросмотра медиафайлов
    const showVideoPreview = ref(false);
    const showImagePreview = ref(false);
    const previewMediaUrl = ref('');
    
    // Переменные для управления удалением
    const showDeleteConfirmation = ref(false);
    const isDeleting = ref(false);
    
    // Данные о существующем животном
    const animalId = computed(() => props.id);
    const currentPreviewId = ref(null);
    const currentPreviewUrl = ref('');
    const currentVideoId = ref(null);
    const existingImages = ref([]);  // Массив с существующими изображениями
    const imagesToDelete = ref([]);  // ID изображений для удаления
    const removeVideoFlag = ref(false);  // Флаг для удаления текущего видео
    
    // Данные животного для редактирования
    const animalData = reactive({
      name: '',
      animal_type_id: '',
      habitat_id: '',
      description: ''
    });
    
    // Файлы и предпросмотры для новых загружаемых файлов
    const selectedCover = ref(null);
    const previewCover = ref('');
    const selectedVideo = ref(null);
    const selectedImages = ref([]);
    const previewImages = ref([]);

    /**
     * Проверяет уникальность имени вида животного
     * @async
     * @param {string} name - Имя животного для проверки
     * @returns {Promise<boolean>} - true если имя уникально или совпадает с исходным, false если уже существует
     */
    const checkNameUnique = async (name) => {
      try {
        isCheckingName.value = true;
        nameErrorMessage.value = '';
        
        // Если имя не изменилось, считаем его уникальным
        if (name.toLowerCase() === originalName.value.toLowerCase()) {
          return true;
        }
        
        // Ищем животных с таким же именем через поисковый запрос
        const response = await axios.get(`${apiBase}/animals/`, {
          params: {
            search: name,
            limit: 100
          }
        });
        
        // Проверяем, есть ли точное совпадение по имени (кроме текущего животного)
        const exactMatch = response.data.find(animal => 
          animal.name.toLowerCase() === name.toLowerCase() && animal.id.toString() !== animalId.value
        );
        
        // Если найдено точное совпадение, имя не уникально
        if (exactMatch) {
          nameErrorMessage.value = 'Вид животного с таким названием уже существует';
          return false;
        }
        
        return true;
      } catch (err) {
        console.error('Ошибка при проверке уникальности имени:', err);
        // При ошибке лучше разрешить продолжение, но залогировать проблему
        return true;
      } finally {
        isCheckingName.value = false;
      }
    };

    /**
     * Полностью очищает файлы предпросмотра и освобождает ресурсы
     * @description Освобождает ресурсы URL объектов для предотвращения утечек памяти
     */
    const clearPreviewResources = () => {
      // Освобождаем ресурсы для текущей обложки
      if (previewCover.value) {
        URL.revokeObjectURL(previewCover.value);
        previewCover.value = '';
      }

      // Освобождаем ресурсы для всех изображений галереи
      previewImages.value.forEach(image => {
        if (image.preview) {
          URL.revokeObjectURL(image.preview);
        }
      });
      previewImages.value = [];
    };
    
    /**
     * Сбрасывает состояние формы для подготовки к загрузке новых данных
     * @description Очищает все данные в форме перед загрузкой новых данных животного
     */
    const resetFormData = () => {
      console.log('Сбрасываем данные формы');
      
      // Очищаем данные формы
      animalData.name = '';
      animalData.description = '';
      animalData.animal_type_id = '';
      animalData.habitat_id = '';
      
      // Сбрасываем данные медиафайлов
      currentPreviewId.value = null;
      currentPreviewUrl.value = '';
      currentVideoId.value = null;
      
      // Очищаем изображения и освобождаем ресурсы
      clearPreviewResources();
      
      // Сбрасываем загруженные файлы
      selectedCover.value = null;
      selectedVideo.value = null;
      selectedImages.value = [];
      
      // Очищаем массивы изображений
      existingImages.value = [];
      imagesToDelete.value = [];
      
      // Сбрасываем флаги
      removeVideoFlag.value = false;
      formError.value = '';
      showCoverRequiredError.value = false;
      showVideoPreview.value = false;
      showImagePreview.value = false;
      previewMediaUrl.value = '';
      nameErrorMessage.value = '';
      originalName.value = '';
    };
    
    /**
     * Полностью сбрасывает состояние формы и загруженные данные
     * @description Очищает все поля формы и сбрасывает состояние компонента
     */
    const resetAllFormData = () => {
      // Очищаем данные формы
      resetFormData();
      
      // Сбрасываем все флаги и состояния
      dataLoaded.value = false;
      loading.value = false;
      error.value = '';
      formError.value = '';
      
      console.log('Все данные формы сброшены');
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
     * Возвращает URL видео из ID видео
     * @param {string} videoId - ID видео
     * @returns {string} URL видео
     */
    const getVideoUrl = (videoId) => {
      if (!videoId) return '';
      return `${apiBase}/media/${videoId}`;
    };
    
    /**
     * Открывает предпросмотр изображения в модальном окне
     * @param {string} imageId - ID изображения для просмотра
     */
    const openImagePreview = (imageId) => {
      previewMediaUrl.value = getImageUrl(imageId);
      showImagePreview.value = true;
    };
    
    /**
     * Закрывает предпросмотр изображения
     */
    const closeImagePreview = () => {
      showImagePreview.value = false;
    };
    
    /**
     * Открывает предпросмотр видео в модальном окне
     */
    const openVideoPreview = () => {
      showVideoPreview.value = true;
    };
    
    /**
     * Закрывает предпросмотр видео
     */
    const closeVideoPreview = () => {
      showVideoPreview.value = false;
      
      // Останавливаем видео при закрытии модального окна
      const videoPlayer = document.querySelector('.video-player');
      if (videoPlayer) {
        videoPlayer.pause();
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
     * Загружает данные редактируемого животного
     * @async
     */
    const loadAnimalData = async () => {
      try {
        // Сначала сбрасываем все предыдущие данные
        resetFormData();
        
        loading.value = true;
        error.value = '';
        dataLoaded.value = false; // Сбрасываем флаг загрузки данных
        
        // Получаем информацию о животном
        const animalResponse = await axios.get(`${apiBase}/animals/${animalId.value}`);
        const animal = animalResponse.data;
        
        // Заполняем форму данными животного
        animalData.name = animal.name;
        originalName.value = animal.name; // Сохраняем оригинальное имя для проверки уникальности
        animalData.description = animal.description;
        animalData.animal_type_id = animal.animal_type_id;
        animalData.habitat_id = animal.habitat_id;
        
        // Сохраняем ID обложки
        currentPreviewId.value = animal.preview_id;
        if (animal.preview_id) {
          currentPreviewUrl.value = getImageUrl(animal.preview_id);
        }
        
        // Сохраняем ID видео
        currentVideoId.value = animal.video_id;
        
        // Получаем все фотографии животного
        try {
          console.log(`Запрашиваем фотографии для животного с ID: ${animalId.value}`);
          const photosResponse = await axios.get(`${apiBase}/animals/${animalId.value}/photos`);
          console.log('Получен ответ с фотографиями:', photosResponse.data);
          
          // Проверка структуры ответа
          if (Array.isArray(photosResponse.data)) {
            existingImages.value = photosResponse.data || [];
            
            // Подробное логирование каждой фотографии для отладки
            existingImages.value.forEach((photo, index) => {
              console.log(`Фото ${index + 1}:`, photo);
            });
            
            // Нормализация структуры данных фотографий для единообразия
            existingImages.value = existingImages.value.map(photo => {
              // Проверяем все возможные структуры данных
              if (photo.photo_id) {
                console.log(`Фото имеет поле photo_id: ${photo.photo_id}`);
                return photo;
              } else if (photo.id) {
                console.log(`Фото имеет поле id: ${photo.id}, создаем photo_id`);
                return { photo_id: photo.id };
              } else {
                console.warn('Обнаружена неизвестная структура фото:', photo);
                return photo;
              }
            });
            
            console.log('Нормализованные фотографии:', existingImages.value);
          } else {
            console.warn('Ответ API не содержит массив фотографий:', photosResponse.data);
            existingImages.value = [];
          }
        } catch (err) {
          console.error('Ошибка при запросе фотографий:', err);
          existingImages.value = [];
        }
        
        console.log('Загружены данные животного:', animal);
        console.log('Загружены фотографии:', existingImages.value);

        // Устанавливаем флаг успешной загрузки данных
        dataLoaded.value = true;
        
      } catch (err) {
        console.error('Ошибка при загрузке данных животного:', err);
        error.value = 'Не удалось загрузить данные животного.';
        dataLoaded.value = false; // Сбрасываем флаг при ошибке
      } finally {
        loading.value = false;
      }
    };
    
    // Отслеживаем изменение ID животного в props
    watch(() => props.id, (newId, oldId) => {
      if (newId && newId !== oldId) {
        console.log(`Изменен ID животного: ${oldId} -> ${newId}`);
        loadAnimalData(); // Загружаем данные нового животного
      }
    });
    
    /**
     * Обработчик загрузки обложки
     * @param {Event} event - Событие загрузки файла
     */
    const handleCoverUpload = (event) => {
      const file = event.target.files[0];
      if (!file) return;
      
      // Проверка на размер файла (4MB = 4 * 1024 * 1024 байт)
      if (file.size > 4 * 1024 * 1024) {
        formError.value = 'Размер файла обложки не должен превышать 4 МБ';
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
      
      // Обрабатываем каждый файл
      files.forEach(file => {
        // Проверка на размер файла (4MB)
        if (file.size > 4 * 1024 * 1024) {
          formError.value = `Размер файла "${file.name}" превышает 4 МБ`;
          return;
        }
        
        // Добавляем файл в список и создаем предпросмотр
        selectedImages.value.push(file);
        previewImages.value.push({
          file: file,
          preview: URL.createObjectURL(file)
        });
      });
    };
    
    /**
     * Удаляет изображение из списка новых изображений по индексу
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
     * Удаляет существующее изображение
     * @param {number} index - Индекс изображения для удаления
     */
    const removeExistingImage = (index) => {
      const imageToRemove = existingImages.value[index];
      
      // Добавляем ID изображения в список для удаления на сервере
      if (imageToRemove) {
        // В зависимости от структуры данных, ID может быть в разных полях
        const imageId = imageToRemove.photo_id || imageToRemove.id;
        if (imageId) {
          imagesToDelete.value.push(imageId);
          console.log(`Добавлен ID ${imageId} в список для удаления`);
        }
      }
      
      // Удаляем изображение из списка существующих
      existingImages.value.splice(index, 1);
    };
    
    /**
     * Устанавливает флаг для удаления текущего видео
     */
    const removeCurrentVideo = () => {
      removeVideoFlag.value = true;
      currentVideoId.value = null;
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
        formError.value = 'Размер видеофайла не должен превышать 1 ГБ';
        return;
      }
      
      // Если загружается новое видео, удаляем старое
      removeVideoFlag.value = true;
      
      // Сохраняем файл
      selectedVideo.value = file;
    };
    
    /**
     * Удаляет выбранное видео
     */
    const removeVideo = () => {
      selectedVideo.value = null;
      
      // Если не было выбрано новое видео для замены, восстанавливаем текущее
      if (removeVideoFlag.value && !selectedVideo.value) {
        removeVideoFlag.value = false;
        currentVideoId.value = animalData.video_id;
      }
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
        // Не генерируем исключение, а просто возвращаем null
        return null;
      }
    };

    /**
     * Отправляет форму на сервер
     * @async
     */
    const submitForm = async () => {
      try {
        formError.value = '';
        nameErrorMessage.value = '';
        isSubmitting.value = true;
        
        // Проверка наличия обложки (если нет текущей и не выбрана новая)
        if (!currentPreviewId.value && !selectedCover.value) {
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
        let previewId = currentPreviewId.value;
        let videoId = removeVideoFlag.value ? null : currentVideoId.value;
        
        // Загружаем новую обложку (если выбрана)
        if (selectedCover.value) {
          uploadPromises.push(
            uploadFile(selectedCover.value)
              .then(id => { 
                if (id) {
                  previewId = id;
                } else {
                  throw new Error('Не удалось загрузить обложку');
                }
              })
          );
        }
        
        // Загружаем новое видео (если выбрано)
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
          // Используем null вместо undefined, если ID не был получен
          preview_id: previewId,
          video_id: videoId
        };
        
        console.log('Отправляемые данные животного:', animalPayload);
        
        // Отправляем запрос на обновление животного
        await axios.put(`${apiBase}/animals/${animalId.value}`, animalPayload);
        
        // Обрабатываем удаление изображений
        if (imagesToDelete.value.length > 0) {
          console.log('Удаляемые изображения:', imagesToDelete.value);
          
          const deleteImagePromises = imagesToDelete.value.map(imageId => 
            axios.delete(`${apiBase}/animals/${animalId.value}/photos/${imageId}`)
              .catch(err => {
                console.warn(`Не удалось удалить фото ${imageId}:`, err);
                return null;
              })
          );
          
          // Выполняем все запросы на удаление изображений
          await Promise.allSettled(deleteImagePromises);
        }
        
        // Массив для хранения обещаний загрузки новых изображений
        const imageUploadPromises = [];
        
        // Загружаем и привязываем новые изображения
        if (selectedImages.value.length) {
          for (const image of selectedImages.value) {
            imageUploadPromises.push(
              uploadFile(image).then(imageId => {
                if (imageId) {
                  // Логируем идентификатор загруженного файла
                  console.log(`Загружено изображение с ID: ${imageId}`);
                  
                  // Формируем правильную структуру данных для API - только photo_id, без animal_id
                  const photoData = {
                    photo_id: imageId
                  };
                  
                  console.log(`Отправляем запрос на добавление фото к животному ${animalId.value}:`, photoData);
                  
                  // Добавляем фото к животному только если загрузка прошла успешно
                  return axios.post(`${apiBase}/animals/${animalId.value}/photos/`, photoData)
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
        
        // Ожидаем завершения связывания всех новых изображений
        await Promise.allSettled(imageUploadPromises);
        
        // Перенаправляем на главную с параметром для обновления каталога
        router.push({ path: '/', query: { refreshCatalog: 'true' } });
      } catch (err) {
        console.error('Ошибка при обновлении животного:', err);
        
        // Получаем детальное описание ошибки из ответа API
        if (err.response && err.response.data && err.response.data.detail) {
          if (Array.isArray(err.response.data.detail)) {
            // Если ошибка содержит массив деталей, объединяем их
            formError.value = err.response.data.detail.map(item => item.msg).join(', ');
          } else {
            // Если ошибка содержит строку
            formError.value = err.response.data.detail;
          }
        } else {
          formError.value = err.message || 'Произошла ошибка при обновлении данных';
        }
      } finally {
        isSubmitting.value = false;
      }
    };
    
    // Удаляет животное с сервера
    const deleteAnimal = async () => {
      try {
        isDeleting.value = true;
        
        // Отправляем запрос на удаление животного
        await axios.delete(`${apiBase}/animals/${animalId.value}`);
        
        // Закрываем модальное окно
        showDeleteConfirmation.value = false;
        
        // Перенаправляем на главную с параметром для обновления каталога
        router.push({ path: '/', query: { refreshCatalog: 'true' } });
      } catch (err) {
        console.error('Ошибка при удалении животного:', err);
        
        // Получаем детальное описание ошибки из ответа API
        if (err.response && err.response.data && err.response.data.detail) {
          if (Array.isArray(err.response.data.detail)) {
            // Если ошибка содержит массив деталей, объединяем их
            formError.value = err.response.data.detail.map(item => item.msg).join(', ');
          } else {
            // Если ошибка содержит строку
            formError.value = err.response.data.detail;
          }
        } else {
          formError.value = err.message || 'Произошла ошибка при удалении данных';
        }
        
        // Закрываем модальное окно подтверждения
        showDeleteConfirmation.value = false;
      } finally {
        isDeleting.value = false;
      }
    };

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
      
      // Загружаем справочные данные и данные животного
      Promise.all([loadReferenceData(), loadAnimalData()]);
    });
    
    // Сбрасываем все данные формы при размонтировании компонента
    onBeforeUnmount(() => {
      console.log('Компонент EditAnimal размонтируется - сбрасываем все данные');
      resetAllFormData();
    });
    
    // Добавляем обработчик события активации компонента (для сброса данных при повторном входе)
    onActivated(() => {
      console.log('Компонент EditAnimal активирован - перезагружаем данные');
      // Полностью перезагружаем данные при каждой активации компонента
      Promise.all([loadReferenceData(), loadAnimalData()]);
    });
    
    // Очищаем форму при переходе на другую страницу
    router.beforeEach((to, from, next) => {
      // Если уходим со страницы редактирования
      if (from.name === 'EditAnimal' && to.name !== 'EditAnimal') {
        console.log('Переход со страницы редактирования - сбрасываем все данные');
        resetAllFormData();
      }
      next();
    });

    return {
      animalTypes,
      habitats,
      animalData,
      error,
      formError,
      loading,
      isSubmitting,
      currentPreviewUrl,
      currentVideoId,
      selectedCover,
      previewCover,
      selectedVideo,
      existingImages,
      previewImages,
      showCoverRequiredError,
      removeVideoFlag,
      dataLoaded,
      nameErrorMessage,
      isCheckingName,
      originalName,
      // Переменные и методы для удаления
      showDeleteConfirmation,
      isDeleting,
      deleteAnimal,
      // Просмотр медиафайлов
      showVideoPreview,
      showImagePreview,
      previewMediaUrl,
      openImagePreview,
      closeImagePreview,
      openVideoPreview,
      closeVideoPreview,
      // Основные методы
      handleCoverUpload,
      removeCover,
      handleImagesUpload,
      removeImage,
      removeExistingImage,
      handleVideoUpload,
      removeVideo,
      removeCurrentVideo,
      submitForm,
      loadAnimalData,
      getImageUrl,
      getVideoUrl,
      resetAllFormData,
      clearPreviewResources,
      checkNameUnique
    };
  }
};
</script>

<style scoped>
/* Существующие стили */
.edit-animal-container {
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

/* Стили для загрузки файлов */
.file-upload-section {
  margin-bottom: 20px;
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

/* Стили для существующей обложки */
.current-preview {
  margin-bottom: 15px;
}

.current-preview h3 {
  font-size: 16px;
  margin-bottom: 10px;
  font-weight: 500;
  color: #333;
}

/* Стили для предпросмотра изображений */
.preview-container {
  margin-top: 15px;
}

.preview-container h3 {
  font-size: 16px;
  margin-bottom: 10px;
  font-weight: 500;
  color: #333;
}

.preview-image {
  max-width: 200px;
  max-height: 200px;
  border-radius: 4px;
}

/* Стили для галереи изображений */
.existing-images-section,
.preview-gallery {
  margin-top: 15px;
}

.existing-images-section h3,
.preview-gallery h3 {
  font-size: 16px;
  margin-bottom: 10px;
  font-weight: 500;
  color: #333;
  text-align: center; /* Центрируем заголовок */
}

.preview-gallery {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center; /* Центрируем элементы в галерее */
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

/* Стили для видео */
.existing-video-section {
  margin-bottom: 20px;
}

.existing-video-section h3 {
  font-size: 16px;
  margin-bottom: 10px;
  font-weight: 500;
  color: #333;
}

/* Центрирование кнопок видео */
.video-controls-wrapper {
  display: flex;
  justify-content: center;
  width: 100%;
}

.current-video-info,
.selected-video-info {
  margin-top: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
}

/* Стили сообщений об ошибках */
.error-message {
  background-color: #ffebee;
  color: #d32f2f;
  padding: 15px;
  border-radius: 4px;
  font-size: 14px;
  margin-bottom: 20px;
  text-align: center;
}

/* Стили для загрузки */
.loading-message {
  text-align: center;
  padding: 30px 0;
}

.spinner {
  border: 3px solid rgba(0, 0, 0, 0.1);
  border-top: 3px solid #4CAF50;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  animation: spin 1s linear infinite;
  margin: 0 auto 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.retry-button,
.back-button {
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 10px 15px;
  margin: 0 5px;
  cursor: pointer;
}

.back-button {
  background-color: #f0f0f0;
  color: #333;
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

/* Стили для кнопки воспроизведения видео */
.play-video-button {
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
  margin-right: 10px;
  display: flex;
  align-items: center;
}

.play-video-button::before {
  content: "▶";
  margin-right: 5px;
}

/* Стили для модального окна с видео */
.video-modal,
.image-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.video-modal-content,
.image-modal-content {
  position: relative;
  background-color: #fff;
  padding: 20px;
  border-radius: 8px;
  max-width: 65%; /* Уменьшаем максимальную ширину модального окна */
  max-height: 70%; /* Уменьшаем максимальную высоту модального окна */
  overflow: hidden;
  width: auto; /* Отменяем фиксированную ширину */
}

/* Стили для контейнера видео с фиксированными размерами */
.video-container {
  position: relative;
  width: 1280px; /* Фиксированная ширина контейнера */
  max-width: 100%; /* Ограничиваем максимальную ширину для адаптивности */
  height: 0;
  padding-bottom: 56.25%; /* Соотношение сторон 16:9 */
  background-color: #000;
  overflow: hidden;
  margin: 0 auto; /* Центрируем контейнер */
}

/* Стили для видеоплеера */
.video-player {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain; /* Сохраняет соотношение сторон видео */
  z-index: 5;
}

/* Улучшенный стиль для кнопки закрытия модального окна */
.close-modal {
  position: absolute;
  top: 7px;
  right: 7px;
  width: 30px;
  height: 30px;
  font-size: 22px;
  line-height: 1;
  font-weight: bold;
  color: #ffffff;
  background-color: #ff5252; /* Красный фон для лучшей видимости */
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 100; /* Убеждаемся, что кнопка находится поверх всего */
  box-shadow: 0 0 5px rgba(0,0,0,0.5);
}

/* Адаптивные стили для видеоплеера */
@media (max-width: 768px) {
  .video-modal-content {
    padding: 15px;
    max-width: 90%; /* Увеличиваем занимаемое пространство на мобильных */
    min-height: 300px; /* Минимальная высота для размещения видео и контроллеров */
  }
  
  .video-container {
    padding-bottom: 75%; /* Увеличенное соотношение для мобильных устройств */
  }
}

/* Адаптивные стили для очень маленьких экранов */
@media (max-width: 480px) {
  .video-modal-content {
    padding: 10px;
    max-width: 98%;
  }
  
  .video-container {
    padding-bottom: 75%; /* Сохраняем то же соотношение */
  }
}

/* Стили для кнопки удаления и контейнера */
.delete-animal-container {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 20px;
}

.delete-animal-button {
  background-color: #ff5252;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 10px 20px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.delete-animal-button:hover {
  background-color: #d32f2f;
}

/* Стили для модального окна подтверждения */
.confirmation-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1100;
}

.confirmation-content {
  background-color: white;
  border-radius: 8px;
  padding: 30px;
  width: 400px;
  max-width: 90%;
  text-align: center;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
}

.confirmation-content h3 {
  margin-top: 0;
  color: #333;
  font-size: 20px;
  font-weight: 500;
  margin-bottom: 15px;
}

.warning-text {
  color: #ff5252;
  font-weight: bold;
  margin: 20px 0;
}

.confirmation-buttons {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 20px;
}

.cancel-delete-button,
.confirm-delete-button {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.cancel-delete-button {
  background-color: #f0f0f0;
  color: #333;
}

.cancel-delete-button:hover {
  background-color: #e0e0e0;
}

.confirm-delete-button {
  background-color: #ff5252;
  color: white;
}

.confirm-delete-button:hover {
  background-color: #d32f2f;
}

.confirm-delete-button:disabled {
  background-color: #ffb4b4;
  cursor: not-allowed;
}
</style>

<style>
body {
  overflow: auto;
}
</style>