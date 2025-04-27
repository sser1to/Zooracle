<template>
  <div class="add-animal-container">
    <h1 class="page-title">Добавление вида животных</h1>
    
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
          </div>
          
          <!-- Выпадающий список типов животных -->
          <div class="form-control">
            <select 
              v-model="animalData.animal_type_id" 
              required
              class="select-field"
            >
              <option value="" disabled selected>Класс</option>
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
              <option value="" disabled selected>Ареал обитания</option>
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
            <img :src="previewCover" alt="Предпросмотр обложки" class="preview-image" />
            <button 
              type="button" 
              @click="removeCover" 
              class="remove-image-button"
            >
              Удалить
            </button>
          </div>
          
          <!-- Сообщение о необходимости загрузить обложку, если она не выбрана -->
          <div v-if="showCoverRequiredError" class="cover-required-error">
            Необходимо загрузить обложку!
          </div>
        </div>
        
        <!-- Загрузка изображений -->
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
              Загрузите изображения
            </div>
          </label>
          <span class="file-format-info">JPEG, PNG, WEBP до 4 МБ</span>
          
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
            {{ isSubmitting ? 'Добавление...' : 'Добавить' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, reactive } from 'vue';
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
    const apiBase = 'http://localhost:8000/api';
    const router = useRouter();
    
    // Реактивные переменные состояния
    const animalTypes = ref([]);
    const habitats = ref([]);
    const error = ref('');
    const isSubmitting = ref(false);
    const showCoverRequiredError = ref(false); // Флаг для отображения ошибки обязательной обложки
    
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
     * Обработчик загрузки обложки
     * @param {Event} event - Событие загрузки файла
     */
    const handleCoverUpload = (event) => {
      const file = event.target.files[0];
      if (!file) return;
      
      // Проверка на размер файла (4MB = 4 * 1024 * 1024 байт)
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
        // Не генерируем исключение, а просто возвращаем null
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
    };
    
    /**
     * Отправляет форму на сервер
     * @async
     */
    const submitForm = async () => {
      try {
        error.value = '';
        isSubmitting.value = true;
        
        // Проверка наличия обложки (обязательное поле)
        if (!selectedCover.value) {
          showCoverRequiredError.value = true;
          isSubmitting.value = false;
          return;
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
          // Используем null вместо undefined, если ID не был получен
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
                  // Добавляем фото к животному только если загрузка прошла успешно
                  return axios.post(`${apiBase}/animals/${animalId}/photos/`, {
                    photo_id: imageId
                  }).catch(err => {
                    console.warn(`Не удалось связать фото ${imageId} с животным:`, err);
                    return null;
                  });
                }
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
      handleCoverUpload,
      removeCover,
      handleImagesUpload,
      removeImage,
      handleVideoUpload,
      removeVideo,
      submitForm
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
</style>