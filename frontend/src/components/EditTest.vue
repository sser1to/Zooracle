<template>
  <div class="edit-test-container">
    <h1 class="page-title">{{ testId ? 'Редактирование теста' : 'Создание нового теста' }}</h1>
    
    <div v-if="loading" class="loading-message">
      <div class="spinner"></div>
      <p>Загрузка данных...</p>
    </div>
    
    <div v-if="error && !dataLoaded" class="error-message">
      <p>{{ error }}</p>
      <button @click="loadTestData" class="retry-button" v-if="testId">Повторить загрузку</button>
      <button @click="$router.push(`/edit-animal/${animalId}`)" class="back-button">Вернуться к редактированию животного</button>
    </div>
    
    <div v-if="!loading && (dataLoaded || !testId)" class="form-container">
      <!-- Название теста -->
      <div class="form-header">
        <!-- Индикатор загрузки для названия теста -->
        <h2 class="test-title">
          {{ testData.name }}
          <span v-if="isLoadingTestName" class="test-title-loading">
            <span class="loading-dot"></span>
            <span class="loading-dot"></span>
            <span class="loading-dot"></span>
          </span>
        </h2>
      </div>
      
      <!-- Секция с вопросами -->
      <div class="questions-section">
        <!-- Цикл по вопросам -->
        <div 
          v-for="(question, questionIndex) in questions" 
          :key="questionIndex" 
          class="question-item"
        >
          <!-- Номер и поле ввода вопроса -->
          <div class="question-header">
            <div class="question-number">{{ questionIndex + 1 }}.</div>
            <input 
              type="text" 
              v-model="question.name" 
              placeholder="Вопрос" 
              class="input-field question-input"
              required
            />
            
            <!-- Выбор типа вопроса -->
            <select 
              v-model="question.question_type_id" 
              class="select-field question-type-select"
              @change="onQuestionTypeChange(questionIndex)"
              required
            >
              <option :value="1">Ввод ответа</option>
              <option :value="2">Выбор одного правильного ответа</option>
              <option :value="3">Выбор нескольких правильных ответов</option>
            </select>
            
            <!-- Кнопка удаления вопроса -->
            <button 
              type="button" 
              class="remove-question-button" 
              @click="removeQuestion(questionIndex)"
              title="Удалить вопрос"
            >
              <span>&times;</span>
            </button>
          </div>
          
          <!-- Варианты ответов (для типов 2 и 3) -->
          <div v-if="question.question_type_id === 2 || question.question_type_id === 3" class="answer-options">
            <div class="answer-options-header">Варианты ответа</div>
            
            <!-- Цикл по вариантам ответов -->
            <div 
              v-for="(option, optionIndex) in question.answerOptions" 
              :key="`question-${questionIndex}-option-${optionIndex}`" 
              class="answer-option-item"
            >
              <!-- Номер варианта ответа -->
              <div class="option-number">{{ optionIndex + 1 }}.</div>
              
              <!-- Поле ввода варианта ответа -->
              <input 
                type="text" 
                v-model="option.name" 
                placeholder="Вариант ответа" 
                class="input-field option-input"
                required
              />
              
              <!-- Чекбокс для выбора правильного ответа (тип 3 - мультивыбор) -->
              <div v-if="question.question_type_id === 3" class="option-checkbox">
                <input 
                  type="checkbox" 
                  :id="`checkbox-${questionIndex}-${optionIndex}`" 
                  v-model="option.is_correct"
                />
                <label :for="`checkbox-${questionIndex}-${optionIndex}`">Верный</label>
              </div>
              
              <!-- Радио-кнопка для выбора правильного ответа (тип 2 - один правильный) -->
              <div v-else-if="question.question_type_id === 2" class="option-radio">
                <input 
                  type="radio" 
                  :id="`radio-${questionIndex}-${optionIndex}`" 
                  :name="`question-${questionIndex}-correct`" 
                  :checked="option.is_correct"
                  @change="setCorrectOption(questionIndex, optionIndex)"
                />
                <label :for="`radio-${questionIndex}-${optionIndex}`">Верный</label>
              </div>
              
              <!-- Кнопка удаления варианта ответа (не отображается для первых двух вариантов) -->
              <button 
                v-if="optionIndex > 1"
                type="button" 
                class="remove-option-button" 
                @click="removeOption(questionIndex, optionIndex)"
                title="Удалить вариант ответа"
              >
                &times;
              </button>
            </div>
            
            <!-- Кнопка для добавления нового варианта ответа -->
            <button 
              v-if="question.answerOptions.length < MAX_OPTIONS"
              type="button" 
              class="add-option-button" 
              @click="addOption(questionIndex)"
            >
              <span class="add-icon">+</span>
              <span>Добавить вариант ответа</span>
            </button>
            
            <!-- Сообщение о достижении максимального количества вариантов ответа -->
            <div v-else class="max-options-message">
              Достигнуто максимальное количество вариантов ответа ({{ MAX_OPTIONS }})
            </div>
          </div>
          
          <!-- Поле ввода правильного ответа (для типа 1 - ввод ответа) -->
          <div v-if="question.question_type_id === 1" class="text-answer">
            <div class="text-answer-header">Верный ответ</div>
            <input 
              type="text" 
              v-model="question.textAnswer" 
              placeholder="Введите правильный ответ" 
              class="input-field text-answer-input"
              required
            />
          </div>
        </div>
        
        <!-- Кнопка для добавления нового вопроса -->
        <button 
          v-if="!isMaxQuestionsReached"
          type="button" 
          class="add-question-button" 
          @click="addQuestion"
        >
          <span class="add-icon">+</span>
          <span>Добавить вопрос</span>
        </button>

        <!-- Сообщение о достижении максимального количества вопросов -->
        <div v-else class="max-questions-message">
          Достигнуто максимальное количество вопросов ({{ MAX_QUESTIONS }})
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
          class="submit-button"
          @click="saveTest"
          :disabled="isSubmitting || questions.length === 0"
        >
          {{ isSubmitting ? 'Сохранение...' : 'Сохранить' }}
        </button>
        <button 
          type="button" 
          @click="$router.push(`/edit-animal/${animalId}`)" 
          class="cancel-button"
        >
          Отмена
        </button>
      </div>
    </div>
    
  </div>
</template>

<script>
import { ref, onMounted, reactive, onBeforeUnmount, watch, computed } from 'vue';
import axios from 'axios';
import { useRouter, useRoute } from 'vue-router';

/**
 * Компонент редактирования/создания теста для животного
 * @component
 * @description Позволяет создавать новые тесты и редактировать существующие
 */
export default {
  name: 'EditTest',
  setup() {
    const MAX_QUESTIONS = 10;
    const MAX_OPTIONS = 6;
    
    // Константы и настройки
    const BACKEND_PORT = process.env.BACKEND_PORT;
    const FRONTEND_URL = process.env.FRONTEND_URL;
    
    // Определяем базовый URL API в зависимости от окружения
    const apiBaseUrl = process.env.NODE_ENV === 'production' 
      ? '/api'
      : `${FRONTEND_URL}:${BACKEND_PORT}/api`;
    
    // Получение параметров из URL
    const router = useRouter();
    const route = useRoute();
    const animalId = ref(route.params.animalId);
    const testId = ref(route.params.testId);
    
    // Состояния для управления UI
    const loading = ref(true);
    const dataLoaded = ref(false);
    const error = ref(null);
    const formError = ref(null);
    const isSubmitting = ref(false);
    const unsavedChanges = ref(false);
    const isLoadingTestName = ref(true);
    
    // Данные теста
    const testData = reactive({
      id: null,
      name: 'Загрузка...',
      animalId: animalId.value
    });
    
    // Список вопросов
    const questions = ref([]);
    
    // Вычисляемое свойство для проверки достижения максимального количества вопросов
    // eslint-disable-next-line
    const isMaxQuestionsReached = computed(() => {
      return questions.value.length >= MAX_QUESTIONS;
    });

    /**
     * Сбрасывает все данные формы для начала работы с чистого листа
     * @description Очищает все загруженные данные и сбрасывает состояния
     */
    const resetAllData = () => {
      // Очищаем данные теста
      testData.id = null;
      testData.name = 'Загрузка...';
      
      // Очищаем вопросы
      questions.value = [];
      
      // Сбрасываем состояния
      loading.value = true;
      dataLoaded.value = false;
      error.value = null;
      formError.value = null;
      unsavedChanges.value = false;
      isLoadingTestName.value = true;
      
      console.log('Данные компонента EditTest сброшены');
    };
    
    /**
     * Инициализация данных нового теста
     * @async
     * @description Загружает информацию о животном и создает название теста на основе его имени
     */
    const initializeNewTest = async () => {
      // Начинаем с чистого листа
      resetAllData();
      
      isLoadingTestName.value = true;
      testData.animalId = animalId.value;
      
      // Если указан ID животного, загружаем его имя для заголовка теста
      if (animalId.value) {
        try {
          const response = await axios.get(`${apiBaseUrl}/animals/${animalId.value}`);
          testData.name = `Тест по животному: ${response.data.name}`;
          console.log('Загружены данные животного для нового теста:', response.data);
          
          // Проверяем, есть ли уже тест у животного
          if (response.data.test_id) {
            console.log(`У животного уже есть тест с ID: ${response.data.test_id}`);
            testId.value = response.data.test_id;
            
            // Загружаем данные существующего теста
            await loadTestData();
            return;
          }
        } catch (e) {
          console.error('Ошибка загрузки данных животного:', e);
          testData.name = 'Новый тест';
        }
      } else {
        testData.name = 'Новый тест';
      }
      
      // Добавляем пустой вопрос для начала работы с новым тестом
      addQuestion();
      isLoadingTestName.value = false;
      loading.value = false;
      dataLoaded.value = true;
    };
    
    /**
     * Загружает данные существующего теста
     * @async
     * @description Получает информацию о тесте и его вопросах с сервера
     */
    const loadTestData = async () => {
      if (!testId.value) return;
      
      // Начинаем с чистого листа
      resetAllData();
      
      loading.value = true;
      error.value = null;
      isLoadingTestName.value = true;
      
      try {
        console.log(`Загрузка данных теста с ID: ${testId.value}`);
        const response = await axios.get(`${apiBaseUrl}/tests/${testId.value}`);
        testData.id = response.data.id;
        testData.name = response.data.name;
        testData.animalId = animalId.value;
        
        console.log('Получены данные теста:', response.data);
        
        // Получаем вопросы теста
        console.log(`Загрузка вопросов теста ${testId.value}`);
        const questionsResponse = await axios.get(`${apiBaseUrl}/tests/${testId.value}/questions`);
        console.log('Получены вопросы теста:', questionsResponse.data);
        
        questions.value = await processQuestionsData(questionsResponse.data);
        
        dataLoaded.value = true;
        error.value = null;
      } catch (e) {
        console.error('Ошибка загрузки данных теста:', e);
        error.value = 'Не удалось загрузить данные теста. Пожалуйста, обновите страницу или попробуйте позже.';
        dataLoaded.value = false;
      } finally {
        loading.value = false;
        isLoadingTestName.value = false;
      }
    };
    
    // Наблюдатель за изменениями параметров маршрута
    watch(() => route.params, (newParams) => {
      // Проверяем изменение ID животного или теста
      const newAnimalId = newParams.animalId;
      const newTestId = newParams.testId;
      
      console.log(`Обнаружено изменение параметров: animalId ${animalId.value} -> ${newAnimalId}, testId ${testId.value} -> ${newTestId}`);
      
      // Если изменились параметры, обновляем их
      if (newAnimalId !== animalId.value || newTestId !== testId.value) {
        animalId.value = newAnimalId;
        testId.value = newTestId;
        
        // Перезагружаем данные с новыми параметрами
        if (newTestId) {
          console.log('Загружаем данные существующего теста');
          loadTestData();
        } else {
          console.log('Инициализируем новый тест');
          initializeNewTest();
        }
      }
    }, { deep: true });
    
    /**
     * Обрабатывает данные вопросов, полученных с сервера
     * @async
     * @param {Array} questionsData - Данные вопросов с сервера
     * @returns {Array} Обработанный массив вопросов для отображения в UI
     */
    const processQuestionsData = async (questionsData) => {
      const processedQuestions = [];
      
      for (const question of questionsData) {
        const processedQuestion = {
          id: question.id,
          name: question.name,
          question_type_id: question.question_type_id,
          answerOptions: [],
          textAnswer: ''
        };
        
        // Обрабатываем разные типы вопросов
        if (question.question_type_id === 1) {
          // Для текстового ответа ищем правильный вариант
          if (question.answers && question.answers.length > 0) {
            const correctAnswer = question.answers.find(a => a.is_correct);
            if (correctAnswer) {
              processedQuestion.textAnswer = correctAnswer.name;
            }
          }
        } else { // Варианты ответов (radio или checkbox)
          if (question.answers && question.answers.length > 0) {
            processedQuestion.answerOptions = question.answers.map(a => ({
              id: a.id,
              name: a.name,
              is_correct: a.is_correct
            }));
          }
          
          // Если вариантов ответов меньше 2, добавляем пустые до 2-х
          while (processedQuestion.answerOptions.length < 2) {
            processedQuestion.answerOptions.push({
              id: null,
              name: '',
              is_correct: false
            });
          }
        }
        
        processedQuestions.push(processedQuestion);
      }
      
      // Если после обработки нет вопросов, добавляем хотя бы один пустой
      if (processedQuestions.length === 0) {
        // Добавляем пустой вопрос для начала работы
        processedQuestions.push({
          id: null,
          name: '',
          question_type_id: 1,
          answerOptions: [],
          textAnswer: ''
        });
      }
      
      return processedQuestions;
    };
    
    /**
     * Добавление нового вопроса
     */
    const addQuestion = () => {
      questions.value.push({
        id: null,
        name: '',
        question_type_id: 1, // По умолчанию - текстовый ответ
        answerOptions: [],
        textAnswer: ''
      });
      
      unsavedChanges.value = true;
    };
    
    /**
     * Удаление вопроса
     * @param {number} index - Индекс удаляемого вопроса
     */
    const removeQuestion = (index) => {
      questions.value.splice(index, 1);
      unsavedChanges.value = true;
    };
    
    /**
     * Изменение типа вопроса
     * @param {number} index - Индекс вопроса, у которого меняется тип
     */
    const onQuestionTypeChange = (index) => {
      const question = questions.value[index];
      
      if (question.question_type_id === 2 || question.question_type_id === 3) {
        // Если выбран тип с вариантами ответов, но варианты пустые - добавляем 2 пустых варианта
        if (!question.answerOptions || question.answerOptions.length < 2) {
          question.answerOptions = [
            { id: null, name: '', is_correct: question.question_type_id === 2 }, // Первый вариант по умолчанию выбран для radio
            { id: null, name: '', is_correct: false }
          ];
        } else if (question.question_type_id === 2) {
          // Для radio убеждаемся, что только один вариант выбран
          const hasSelected = question.answerOptions.some(opt => opt.is_correct);
          if (!hasSelected) {
            question.answerOptions[0].is_correct = true;
          }
        }
      }
      
      unsavedChanges.value = true;
    };
    
    /**
     * Добавление варианта ответа
     * @param {number} questionIndex - Индекс вопроса, к которому добавляется вариант
     */
    const addOption = (questionIndex) => {
      questions.value[questionIndex].answerOptions.push({
        id: null,
        name: '',
        is_correct: false
      });
      
      unsavedChanges.value = true;
    };
    
    /**
     * Удаление варианта ответа
     * @param {number} questionIndex - Индекс вопроса
     * @param {number} optionIndex - Индекс удаляемого варианта
     */
    const removeOption = (questionIndex, optionIndex) => {
      if (questions.value[questionIndex].answerOptions.length <= 2) {
        return; // Не даем удалить варианты, если их меньше 2
      }
      
      questions.value[questionIndex].answerOptions.splice(optionIndex, 1);
      
      // Если тип вопроса - radio, и удалили выбранный вариант, выбираем первый
      if (questions.value[questionIndex].question_type_id === 2 && 
          !questions.value[questionIndex].answerOptions.some(opt => opt.is_correct)) {
        questions.value[questionIndex].answerOptions[0].is_correct = true;
      }
      
      unsavedChanges.value = true;
    };
    
    /**
     * Установка правильного варианта для radio-button
     * @param {number} questionIndex - Индекс вопроса
     * @param {number} optionIndex - Индекс выбранного варианта
     */
    const setCorrectOption = (questionIndex, optionIndex) => {
      const options = questions.value[questionIndex].answerOptions;
      
      // Сбрасываем все варианты
      options.forEach(opt => opt.is_correct = false);
      
      // Устанавливаем выбранный вариант
      options[optionIndex].is_correct = true;
      
      unsavedChanges.value = true;
    };
    
    /**
     * Валидация данных формы
     * @returns {boolean} Результат валидации
     */
    const validateForm = () => {
      // Проверяем наличие вопросов
      if (questions.value.length === 0) {
        formError.value = 'Добавьте хотя бы один вопрос';
        return false;
      }
      
      for (let i = 0; i < questions.value.length; i++) {
        const question = questions.value[i];
        
        // Проверяем, что вопрос имеет текст
        if (!question.name.trim()) {
          formError.value = `Вопрос ${i + 1} должен содержать текст`;
          return false;
        }
        
        if (question.question_type_id === 1) {
          // Проверяем правильный ответ для текстового типа
          if (!question.textAnswer.trim()) {
            formError.value = `Укажите правильный ответ для вопроса ${i + 1}`;
            return false;
          }
        } else if (question.question_type_id === 2 || question.question_type_id === 3) {
          // Проверяем варианты ответов
          if (!question.answerOptions || question.answerOptions.length < 2) {
            formError.value = `Добавьте как минимум 2 варианта ответа для вопроса ${i + 1}`;
            return false;
          }
          
          // Проверяем, что все варианты ответов имеют текст
          for (let j = 0; j < question.answerOptions.length; j++) {
            if (!question.answerOptions[j].name.trim()) {
              formError.value = `Заполните текст для варианта ответа ${j + 1} в вопросе ${i + 1}`;
              return false;
            }
          }
          
          // Проверяем, что выбран хотя бы один правильный ответ для checkbox
          if (question.question_type_id === 3 && 
              !question.answerOptions.some(opt => opt.is_correct)) {
            formError.value = `Выберите хотя бы один правильный ответ для вопроса ${i + 1}`;
            return false;
          }
        }
      }
      
      return true;
    };
    
    /**
     * Сохранение теста
     * @async
     */
    const saveTest = async () => {
      // Валидация формы
      formError.value = null;
      if (!validateForm()) {
        return;
      }
      
      isSubmitting.value = true;
      
      try {
        let testResponseData;
        
        // Если тест уже существует - обновляем его
        if (testId.value) {
          console.log(`Обновление существующего теста с ID: ${testId.value}`);
          const testUpdateResponse = await axios.put(`${apiBaseUrl}/tests/${testId.value}`, {
            name: testData.name
          });
          testResponseData = testUpdateResponse.data;
          console.log('Ответ на обновление теста:', testResponseData);
        } else {
          // Иначе создаем новый тест
          console.log('Создание нового теста');
          const testCreateResponse = await axios.post(`${apiBaseUrl}/tests/`, {
            name: testData.name,
            animal_id: animalId.value ? parseInt(animalId.value) : null
          });
          testResponseData = testCreateResponse.data;
          testId.value = testResponseData.id;
          console.log(`Создан новый тест с ID: ${testId.value}`);
          
          // Обновляем связь с животным
          if (animalId.value) {
            console.log(`Обновление связи животного ${animalId.value} с тестом ${testId.value}`);
            await axios.put(`${apiBaseUrl}/animals/${animalId.value}`, {
              test_id: parseInt(testResponseData.id)
            });
          }
        }
        
        // Преобразуем вопросы в формат для отправки на сервер
        const questionsData = questions.value.map(q => {
          const questionData = {
            id: q.id,
            name: q.name,
            question_type_id: parseInt(q.question_type_id),
          };
          
          if (q.question_type_id === 1) { // Текстовый ответ
            questionData.answers = [{
              id: null,
              name: q.textAnswer,
              is_correct: true
            }];
          } else {
            questionData.answers = q.answerOptions.map(opt => ({
              id: opt.id,
              name: opt.name,
              is_correct: opt.is_correct
            }));
          }
          
          return questionData;
        });
        
        console.log(`Сохранение вопросов для теста ${testId.value}:`, questionsData);
        
        // Сохраняем вопросы и ответы
        const questionsResponse = await axios.post(`${apiBaseUrl}/tests/${testId.value}/questions`, {
          questions: questionsData
        });
        
        console.log('Ответ на сохранение вопросов:', questionsResponse.data);
        
        // Обновляем данные в UI
        questions.value = await processQuestionsData(questionsResponse.data);
        unsavedChanges.value = false;
        
        // Возвращаемся к редактированию животного с параметром для обновления данных о тесте
        router.push(`/edit-animal/${animalId.value}?refreshTest=true`);
      } catch (e) {
        console.error('Ошибка сохранения теста:', e);
        
        // Получаем детали ошибки
        let errorMessage = 'Не удалось сохранить тест. Пожалуйста, попробуйте позже.';
        
        if (e.response && e.response.data) {
          if (e.response.data.detail) {
            errorMessage = `Ошибка: ${e.response.data.detail}`;
          }
        }
        
        formError.value = errorMessage;
      } finally {
        isSubmitting.value = false;
      }
    };
    
    // Настраиваем axios для работы с токенами
    const configureAxios = () => {
      axios.interceptors.request.use(config => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      });
    };
    
    /**
     * Предупреждение о несохраненных изменениях при уходе со страницы
     * @returns {undefined} Возвращает undefined для отмены стандартного предупреждения браузера
     */
    const unloadHandler = () => {
      // Отключаем предупреждение о несохраненных данных
      /*
      if (unsavedChanges.value) {
        e.preventDefault();
        e.returnValue = '';
        return '';
      }
      */
      // Никогда не показываем предупреждение при закрытии страницы
      return undefined;
    };
    
    // При монтировании компонента
    onMounted(() => {
      configureAxios();
      
      // Добавляем обработчик перед уходом со страницы
      window.addEventListener('beforeunload', unloadHandler);
      
      // Загружаем данные теста или инициализируем новый тест
      if (testId.value) {
        loadTestData();
      } else {
        initializeNewTest();
      }
    });
    
    // Очищаем обработчик при размонтировании
    onBeforeUnmount(() => {
      window.removeEventListener('beforeunload', unloadHandler);
      
      // Сбрасываем состояние компонента перед удалением для избежания проблем с кешированием
      resetAllData();
    });
    
    return {
      animalId,
      testId,
      loading,
      error,
      formError,
      dataLoaded,
      isSubmitting,
      testData,
      questions,
      isLoadingTestName,
      addQuestion,
      removeQuestion,
      onQuestionTypeChange,
      addOption,
      removeOption,
      setCorrectOption,
      loadTestData,
      saveTest,
      resetAllData,
      MAX_OPTIONS,
      MAX_QUESTIONS,
      isMaxQuestionsReached
    };
  }
};
</script>

<style scoped>
/* Основные стили контейнера */
.edit-test-container {
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

/* Стили для заголовка формы и названия теста */
.form-header {
  margin-bottom: 25px;
}

.test-title {
  font-size: 18px;
  font-weight: 500;
  color: #333;
  display: flex;
  align-items: center;
}

.test-title-loading {
  display: flex;
  margin-left: 10px;
}

.loading-dot {
  width: 6px;
  height: 6px;
  margin: 0 2px;
  background-color: #4CAF50;
  border-radius: 50%;
  animation: blink 1.4s infinite both;
}

.loading-dot:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dot:nth-child(2) {
  animation-delay: -0.16s;
}

.loading-dot:nth-child(3) {
  animation-delay: 0s;
}

@keyframes blink {
  0%, 80%, 100% {
    opacity: 0;
  }
  40% {
    opacity: 1;
  }
}

.test-name-input {
  width: 100%;
  padding: 15px;
  font-size: 18px;
  font-weight: 500;
  border: 1px solid #ccc;
  border-radius: 4px;
  transition: border-color 0.3s;
}

.test-name-input:focus {
  border-color: #4CAF50;
  outline: none;
}

/* Стили для секции с вопросами */
.questions-section {
  display: flex;
  flex-direction: column;
  gap: 25px;
  margin-bottom: 30px;
}

/* Стили для отдельного вопроса */
.question-item {
  background-color: #f9f9f9;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 15px;
  position: relative;
}

.question-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.question-number {
  font-size: 18px;
  font-weight: bold;
  color: #333;
  width: 30px;
  text-align: right;
}

.question-input {
  flex-grow: 1;
}

.question-type-select {
  width: 220px;
  flex-shrink: 0;
}

.remove-question-button {
  background-color: #ff5252;
  color: white;
  border: none;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 20px;
  padding: 0;
  line-height: 1;
}

.remove-question-button:hover {
  background-color: #d32f2f;
}

/* Стили для вариантов ответов */
.answer-options {
  margin-left: 40px;
}

.answer-options-header,
.text-answer-header {
  font-weight: 500;
  color: #333;
  margin-bottom: 10px;
}

.answer-option-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.option-number {
  font-size: 16px;
  width: 25px;
  text-align: right;
}

.option-input {
  flex-grow: 1;
}

.option-radio,
.option-checkbox {
  display: flex;
  align-items: center;
  gap: 5px;
  width: 80px;
}

.option-radio input,
.option-checkbox input {
  margin: 0;
  cursor: pointer;
}

.option-radio label,
.option-checkbox label {
  cursor: pointer;
  user-select: none;
}

.remove-option-button {
  background-color: #ff5252;
  color: white;
  border: none;
  border-radius: 50%;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 16px;
  padding: 0;
  line-height: 1;
}

.remove-option-button:hover {
  background-color: #d32f2f;
}

/* Стили для текстового ответа */
.text-answer {
  margin-left: 40px;
}

.text-answer-input {
  width: 80%;
}

/* Стили для кнопки добавления вопроса и варианта ответа */
.add-question-button,
.add-option-button {
  background-color: transparent;
  border: 1px dashed #4CAF50;
  border-radius: 4px;
  padding: 10px;
  color: #4CAF50;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  width: fit-content;
  font-size: 14px;
  transition: background-color 0.3s;
}

.add-question-button {
  align-self: center;
  padding: 12px 20px;
  font-size: 16px;
  margin-top: 10px;
}

.add-question-button:hover,
.add-option-button:hover {
  background-color: rgba(76, 175, 80, 0.1);
}

.add-icon {
  font-size: 18px;
  margin-right: 5px;
}

.add-option-button {
  margin-left: 35px;
  margin-top: 5px;
}

/* Стили для сообщения о достижении максимального количества вариантов ответа */
.max-options-message {
  margin-left: 35px;
  margin-top: 10px;
  font-size: 14px;
  color: #d32f2f;
}

/* Стили полей ввода и селекторов */
.input-field,
.select-field {
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 15px;
  transition: border-color 0.3s;
}

.input-field:focus,
.select-field:focus {
  border-color: #4CAF50;
  outline: none;
}

/* Стили для ошибок */
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
  .question-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .question-number {
    width: auto;
    text-align: left;
  }
  
  .question-type-select {
    width: 100%;
  }
  
  .remove-question-button {
    position: absolute;
    top: 15px;
    right: 15px;
  }
  
  .answer-options,
  .text-answer {
    margin-left: 0;
  }
  
  .answer-option-item {
    flex-wrap: wrap;
  }
  
  .option-input {
    width: 100%;
    margin-left: 35px;
    order: 2;
  }
  
  .option-radio,
  .option-checkbox {
    order: 3;
  }
  
  .remove-option-button {
    order: 4;
  }
  
  .add-option-button {
    margin-left: 0;
  }
  
  .form-buttons {
    flex-direction: column;
  }
  
  .cancel-button, 
  .submit-button {
    width: 100%;
  }
}
</style>