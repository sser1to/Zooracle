<template>
  <div class="take-test-container">
    <!-- Кнопка-стрелка для возврата к странице животного -->
    <div class="back-link-container">
      <router-link :to="`/animal/${animalId}`" class="back-link">
        <span class="back-arrow">←</span> Вернуться к описанию
      </router-link>
    </div>

    <div v-if="loading" class="loading-message">
      <div class="spinner"></div>
      <p>Загрузка теста...</p>
    </div>

    <div v-else-if="error" class="error-message">
      <p>{{ error }}</p>
      <div class="error-actions">
        <button @click="loadTestData" class="retry-button">Повторить</button>
        <router-link :to="`/animal/${animalId}`" class="back-button">
          Вернуться к описанию животного
        </router-link>
      </div>
    </div>

    <div v-else-if="test && !testCompleted" class="test-content">
      <!-- Заголовок теста -->
      <div class="test-header">
        <h1 class="test-title">{{ test.name }}</h1>
        <div class="progress-container">
          <div 
            class="progress-bar" 
            :style="{ width: `${(currentQuestionIndex / questions.length) * 100}%` }"
          ></div>
          <span class="progress-text">Вопрос {{ currentQuestionIndex + 1 }} из {{ questions.length }}</span>
        </div>
      </div>

      <!-- Блок текущего вопроса -->
      <div v-if="currentQuestion" class="question-block">
        <h2 class="question-text">{{ currentQuestion.name }}</h2>

        <!-- Текстовый ввод для вопроса типа 1 -->
        <div v-if="currentQuestion.question_type_id === 1" class="text-answer-input">
          <input
            type="text"
            v-model.trim="userAnswers[currentQuestionIndex].textAnswer"
            placeholder="Введите ответ"
            class="input-field"
          />
        </div>

        <!-- Радио-кнопки для вопроса типа 2 (один правильный ответ) -->
        <div v-else-if="currentQuestion.question_type_id === 2" class="single-choice-answers">
          <div 
            v-for="(option, index) in currentQuestion.answers" 
            :key="`option-${index}`"
            class="answer-option"
          >
            <input
              type="radio"
              :id="`option-${currentQuestionIndex}-${index}`"
              :name="`question-${currentQuestionIndex}`"
              :value="option.id"
              v-model="userAnswers[currentQuestionIndex].selectedOptions[0]"
              class="radio-input"
            />
            <label :for="`option-${currentQuestionIndex}-${index}`" class="option-label">
              {{ option.name }}
            </label>
          </div>
        </div>

        <!-- Чекбоксы для вопроса типа 3 (множественный выбор) -->
        <div v-else-if="currentQuestion.question_type_id === 3" class="multi-choice-answers">
          <div 
            v-for="(option, index) in currentQuestion.answers" 
            :key="`option-${index}`"
            class="answer-option"
          >
            <input
              type="checkbox"
              :id="`option-${currentQuestionIndex}-${index}`"
              :value="option.id"
              v-model="userAnswers[currentQuestionIndex].selectedOptions"
              class="checkbox-input"
            />
            <label :for="`option-${currentQuestionIndex}-${index}`" class="option-label">
              {{ option.name }}
            </label>
          </div>
        </div>
      </div>

      <!-- Навигация между вопросами -->
      <div class="test-navigation">
        <button 
          v-if="currentQuestionIndex > 0"
          @click="previousQuestion"
          class="prev-button"
        >
          <span class="nav-arrow">←</span> Предыдущий
        </button>

        <button
          v-if="currentQuestionIndex < questions.length - 1"
          @click="nextQuestion"
          :disabled="!canMoveNext"
          class="next-button"
        >
          Следующий <span class="nav-arrow">→</span>
        </button>

        <button
          v-else
          @click="completeTest"
          :disabled="!canMoveNext"
          class="complete-button"
        >
          Завершить тест
        </button>
      </div>
    </div>

    <!-- Блок результатов после завершения теста -->
    <div v-if="testCompleted && !loading" class="test-results-container">
      <div v-if="submitting" class="submitting-results">
        <div class="spinner"></div>
        <p>Проверка ответов...</p>
      </div>

      <div v-else class="test-results">
        <h1 class="results-title">Результаты теста</h1>
        
        <div class="score-info">
          <div class="score-circle">
            <span class="score-percentage">{{ testScore }}%</span>
          </div>
          <p class="score-text">
            Правильных ответов: {{ correctAnswers }} из {{ questions.length }}
          </p>
        </div>

        <div class="result-actions">
          <router-link :to="`/animal/${animalId}`" class="back-to-animal">
            Вернуться к описанию животного
          </router-link>
          <button @click="retakeTest" class="retake-button">
            Пройти тест снова
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

/**
 * Компонент для прохождения теста пользователем
 * @component
 * @description Позволяет пользователю пройти тест по выбранному животному и получить результаты
 */
export default {
  name: 'TakeTest',
  setup() {
    // Константы и настройки
    const BACKEND_PORT = process.env.BACKEND_PORT;
    const FRONTEND_URL = process.env.FRONTEND_URL;
    
    // Определяем базовый URL API в зависимости от окружения
    const apiBaseUrl = process.env.NODE_ENV === 'production' 
      ? '/api'
      : `${FRONTEND_URL}:${BACKEND_PORT}/api`;
    
    // Состояния
    const loading = ref(true);
    const error = ref('');
    const test = ref(null);
    const questions = ref([]);
    const currentQuestionIndex = ref(0);
    const userAnswers = ref([]);
    const testCompleted = ref(false);
    const submitting = ref(false);
    const testScore = ref(0);
    const correctAnswers = ref(0);
    
    // Получение параметров из URL
    const route = useRoute();
    const router = useRouter();
    const testId = ref(route.params.testId);
    const animalId = ref(route.params.animalId);
    
    /**
     * Сбрасывает все данные теста
     * @description Полностью очищает данные предыдущего теста и сбрасывает состояния
     */
    const resetTestData = () => {
      console.log('Сброс данных теста...');
      loading.value = true;
      error.value = '';
      test.value = null;
      questions.value = [];
      currentQuestionIndex.value = 0;
      userAnswers.value = [];
      testCompleted.value = false;
      submitting.value = false;
      testScore.value = 0;
      correctAnswers.value = 0;
    };
    
    /**
     * Вычисляемый текущий вопрос
     * @type {import('vue').ComputedRef}
     */
    const currentQuestion = computed(() => {
      if (questions.value.length === 0) return null;
      return questions.value[currentQuestionIndex.value];
    });
    
    /**
     * Определяет, может ли пользователь перейти к следующему вопросу
     * @type {import('vue').ComputedRef<boolean>}
     */
    const canMoveNext = computed(() => {
      if (!currentQuestion.value) return false;
      
      const currentAnswer = userAnswers.value[currentQuestionIndex.value];
      if (!currentAnswer) return false;
      
      // Проверяем разные типы вопросов
      if (currentQuestion.value.question_type_id === 1) {
        // Для текстового ответа требуется ввод
        return currentAnswer.textAnswer.trim().length > 0;
      } else if (currentQuestion.value.question_type_id === 2) {
        // Для единственного выбора должен быть выбран один вариант
        return currentAnswer.selectedOptions.length > 0;
      } else if (currentQuestion.value.question_type_id === 3) {
        // Для множественного выбора должен быть выбран хотя бы один вариант
        return currentAnswer.selectedOptions.length > 0;
      }
      
      return false;
    });
    
    /**
     * Загружает данные теста с сервера
     * @async
     */
    const loadTestData = async () => {
      // Сбрасываем предыдущие данные
      resetTestData();
      
      // Если ID не указан, просто оставляем состояние загрузки
      if (!testId.value) {
        return;
      }
      
      try {
        console.log(`Загрузка данных теста с ID: ${testId.value}`);
        
        // Получаем данные теста
        const testResponse = await axios.get(`${apiBaseUrl}/tests/${testId.value}`);
        test.value = testResponse.data;
        
        // Получаем вопросы теста
        const questionsResponse = await axios.get(`${apiBaseUrl}/tests/${testId.value}/questions`);
        questions.value = questionsResponse.data;
        
        console.log('Тест загружен:', test.value);
        console.log('Вопросы загружены:', questions.value);
        
        // Инициализируем ответы пользователя
        initializeUserAnswers();
        
        error.value = '';
      } catch (err) {
        console.error('Ошибка при загрузке теста:', err);
        error.value = 'Не удалось загрузить тест. Пожалуйста, попробуйте позже.';
      } finally {
        loading.value = false;
      }
    };
    
    /**
     * Инициализирует структуру для ответов пользователя
     */
    const initializeUserAnswers = () => {
      userAnswers.value = questions.value.map(question => ({
        questionId: question.id,
        questionType: question.question_type_id,
        textAnswer: '',
        selectedOptions: [],
        isCorrect: false
      }));
    };
    
    /**
     * Переход к следующему вопросу
     */
    const nextQuestion = () => {
      if (currentQuestionIndex.value < questions.value.length - 1) {
        currentQuestionIndex.value++;
      }
    };
    
    /**
     * Переход к предыдущему вопросу
     */
    const previousQuestion = () => {
      if (currentQuestionIndex.value > 0) {
        currentQuestionIndex.value--;
      }
    };
    
    /**
     * Завершение теста и проверка результатов
     * @async
     */
    const completeTest = async () => {
      testCompleted.value = true;
      submitting.value = true;
      
      try {
        // Подготовка данных для отправки
        const answersData = userAnswers.value.map(answer => {
          if (answer.questionType === 1) {
            // Для текстового ответа
            return {
              question_id: answer.questionId,
              text_answer: answer.textAnswer,
              selected_options: []
            };
          } else {
            // Для выбора одного или нескольких вариантов
            return {
              question_id: answer.questionId,
              text_answer: '',
              selected_options: answer.selectedOptions
            };
          }
        });
        
        // Отправляем ответы на проверку
        const response = await axios.post(`${apiBaseUrl}/tests/${testId.value}/check`, {
          answers: answersData
        });
        
        console.log('Результат проверки:', response.data);
        
        // Обработка результатов
        correctAnswers.value = response.data.correct_answers;
        testScore.value = Math.round((correctAnswers.value / questions.value.length) * 100);
        
        // Сохраняем результат в базу данных
        await saveTestScore(correctAnswers.value, questions.value.length);
        
        // Обновляем статус ответов
        if (response.data.question_results) {
          response.data.question_results.forEach(result => {
            const answerIndex = userAnswers.value.findIndex(a => a.questionId === result.question_id);
            if (answerIndex !== -1) {
              userAnswers.value[answerIndex].isCorrect = result.is_correct;
            }
          });
        }
      } catch (err) {
        console.error('Ошибка при проверке результатов:', err);
        error.value = 'Не удалось проверить результаты теста.';
      } finally {
        submitting.value = false;
      }
    };
    
    /**
     * Сохраняет результат теста в базу данных
     * @async
     * @param {number} correctAnswers - Количество правильных ответов
     * @param {number} totalQuestions - Общее количество вопросов
     */
    const saveTestScore = async (correctAnswers, totalQuestions) => {
      try {
        const response = await axios.post(`${apiBaseUrl}/test-scores/`, {
          test_id: parseInt(testId.value),
          correct_answers: correctAnswers,
          total_questions: totalQuestions
        });
        
        console.log('Результат теста сохранен:', response.data);
      } catch (err) {
        console.error('Ошибка при сохранении результата теста:', err);
      }
    };
    
    /**
     * Перезапуск теста для повторного прохождения
     */
    const retakeTest = () => {
      // Полностью сбрасываем состояние и загружаем тест заново
      resetTestData();
      loadTestData();
    };
    
    /**
     * Переход к другому тесту
     * @param {string} newAnimalId - ID животного для нового теста
     * @param {string} newTestId - ID нового теста
     */
    const goToAnotherTest = (newAnimalId, newTestId) => {
      console.log(`Переход к новому тесту: animalId=${newAnimalId}, testId=${newTestId}`);
      
      // Сбрасываем данные перед навигацией
      resetTestData();
      
      // Обновляем данные маршрута
      router.push({
        name: 'take-test',
        params: { 
          animalId: newAnimalId,
          testId: newTestId 
        }
      });
    };
    
    /**
     * Настраивает axios для работы с токенами
     */
    const configureAxios = () => {
      axios.interceptors.request.use(config => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      });
    };
    
    // Следим за изменениями параметров URL
    watch(
      () => route.params,
      (newParams) => {
        const newTestId = newParams.testId;
        const newAnimalId = newParams.animalId;
        
        // Если изменился ID теста или животного, перезагружаем данные
        if (newTestId !== testId.value || newAnimalId !== animalId.value) {
          console.log(`Изменение параметров: testId ${testId.value} -> ${newTestId}, animalId ${animalId.value} -> ${newAnimalId}`);
          testId.value = newTestId;
          animalId.value = newAnimalId;
          
          // Загружаем данные теста заново
          loadTestData();
        }
      },
      { immediate: false, deep: true }
    );
    
    // Инициализация компонента
    onMounted(() => {
      configureAxios();
      loadTestData();
    });
    
    return {
      loading,
      error,
      test,
      questions,
      currentQuestionIndex,
      currentQuestion,
      userAnswers,
      testCompleted,
      submitting,
      testScore,
      correctAnswers,
      canMoveNext,
      animalId,
      goToAnotherTest,
      loadTestData,
      nextQuestion,
      previousQuestion,
      completeTest,
      retakeTest
    };
  }
}
</script>

<style scoped>
/* Основной контейнер */
.take-test-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
  min-height: calc(100vh - 40px);
  display: flex;
  flex-direction: column;
}

/* Стили для кнопки возврата */
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

/* Стили для заголовка теста */
.test-header {
  margin-bottom: 30px;
}

.test-title {
  font-size: 28px;
  color: #333;
  margin-bottom: 15px;
  text-align: left;
}

/* Индикатор прогресса */
.progress-container {
  height: 10px;
  background-color: #e0e0e0;
  border-radius: 5px;
  margin-bottom: 10px;
  overflow: hidden;
  position: relative;
}

.progress-bar {
  height: 100%;
  background-color: #8BC34A;
  border-radius: 5px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 14px;
  color: #757575;
}

/* Блок вопроса */
.question-block {
  background-color: #fff;
  border-radius: 8px;
  padding: 25px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  margin-bottom: 30px;
  min-height: 200px;
}

.question-text {
  font-size: 20px;
  color: #333;
  margin-bottom: 20px;
  line-height: 1.5;
  text-align: left;
}

/* Стили для текстового ввода */
.text-answer-input {
  margin-top: 20px;
}

.input-field {
  width: 90%;
  padding: 12px 15px;
  font-size: 16px;
  border: 1px solid #ccc;
  border-radius: 4px;
  transition: border-color 0.3s;
}

.input-field:focus {
  border-color: #8BC34A;
  outline: none;
}

/* Стили для вариантов ответа */
.single-choice-answers,
.multi-choice-answers {
  margin-top: 20px;
}

.answer-option {
  display: flex;
  align-items: flex-start;
  margin-bottom: 15px;
  padding: 10px 15px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.answer-option:hover {
  background-color: #f5f5f5;
}

.radio-input,
.checkbox-input {
  margin-right: 10px;
  margin-top: 3px;
}

.option-label {
  flex-grow: 1;
  text-align: left;
  font-size: 16px;
  line-height: 1.4;
  user-select: none;
  cursor: pointer;
}

/* Навигация между вопросами */
.test-navigation {
  display: flex;
  justify-content: space-between;
  margin-top: auto;
}

.prev-button,
.next-button,
.complete-button {
  padding: 10px 20px;
  font-size: 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.prev-button {
  background-color: #f0f0f0;
  color: #333;
  border: 1px solid #ccc;
}

.prev-button:hover {
  background-color: #e0e0e0;
}

.next-button,
.complete-button {
  background-color: #8BC34A;
  color: white;
  border: none;
}

.next-button:hover,
.complete-button:hover {
  background-color: #7CB342;
}

.next-button:disabled,
.complete-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.nav-arrow {
  display: inline-block;
  margin: 0 5px;
}

/* Результаты теста */
.test-results-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.test-results {
  text-align: center;
  background-color: #fff;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 15px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 600px;
}

.results-title {
  font-size: 28px;
  color: #333;
  margin-bottom: 30px;
}

.score-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 40px;
}

.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background-color: #8BC34A;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.score-percentage {
  font-size: 36px;
  font-weight: bold;
}

.score-text {
  font-size: 18px;
  color: #333;
}

.result-actions {
  margin-top: 30px;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 15px;
}

.back-to-animal,
.retake-button {
  padding: 12px 20px;
  font-size: 16px;
  border-radius: 4px;
  text-decoration: none;
  transition: background-color 0.3s;
  display: inline-block;
}

.back-to-animal {
  background-color: #f0f0f0;
  color: #333;
  border: 1px solid #ccc;
}

.back-to-animal:hover {
  background-color: #e0e0e0;
}

.retake-button {
  background-color: #8BC34A;
  color: white;
  border: none;
  cursor: pointer;
}

.retake-button:hover {
  background-color: #7CB342;
}

/* Состояния загрузки и ошибок */
.loading-message,
.submitting-results,
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
  width: 30px;
  height: 30px;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  color: #d32f2f;
}

.error-actions {
  margin-top: 20px;
  display: flex;
  gap: 10px;
}

.retry-button,
.back-button {
  padding: 10px 15px;
  font-size: 14px;
  border-radius: 4px;
  cursor: pointer;
  text-decoration: none;
}

.retry-button {
  background-color: #8BC34A;
  color: white;
  border: none;
}

.back-button {
  background-color: #f0f0f0;
  color: #333;
  border: 1px solid #ccc;
}

/* Адаптивные стили */
@media (max-width: 768px) {
  .question-block {
    padding: 15px;
  }
  
  .test-title {
    font-size: 24px;
  }
  
  .question-text {
    font-size: 18px;
  }
  
  .test-navigation {
    flex-direction: column;
    gap: 15px;
  }
  
  .prev-button,
  .next-button,
  .complete-button {
    width: 100%;
  }
  
  .score-circle {
    width: 100px;
    height: 100px;
  }
  
  .score-percentage {
    font-size: 30px;
  }
  
  .result-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .back-to-animal,
  .retake-button {
    width: 100%;
    text-align: center;
  }
}
</style>