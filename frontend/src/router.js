import { createRouter, createWebHistory } from 'vue-router';
import LoginForm from './components/Login.vue';
import RegisterForm from './components/Register.vue';
import ResetPasswordForm from './components/ResetPassword.vue';
import ResetPasswordConfirmForm from './components/ResetPasswordConfirm.vue';
import EmailVerification from './components/EmailVerification.vue';
import AnimalCatalog from './components/AnimalCatalog.vue';
import AddAnimal from './components/AddAnimal.vue';
import EditAnimal from './components/EditAnimal.vue'; // Импортируем компонент редактирования
import authService from './services/auth';

/**
 * Конфигурация маршрутов приложения
 * @type {Array}
 */
const routes = [
  // Маршрут страницы входа
  {
    path: '/login',
    name: 'login',
    component: LoginForm,
    meta: { requiresAuth: false, title: 'Вход - Zooracle' }
  },
  
  // Маршрут страницы регистрации
  {
    path: '/register',
    name: 'register',
    component: RegisterForm,
    meta: { requiresAuth: false, title: 'Регистрация - Zooracle' }
  },
  
  // Маршрут страницы запроса на сброс пароля
  {
    path: '/reset-password',
    name: 'reset-password',
    component: ResetPasswordForm,
    meta: { requiresAuth: false, title: 'Восстановление пароля - Zooracle' }
  },
  
  // Маршрут страницы подтверждения сброса пароля с передачей токена через props
  {
    path: '/reset-password/confirm',
    name: 'reset-password-confirm',
    component: ResetPasswordConfirmForm,
    // Передаем query параметры в качестве пропсов компонента
    props: (route) => ({ token: route.query.token }),
    meta: { requiresAuth: false, title: 'Установка нового пароля - Zooracle' }
  },
  
  // Маршрут страницы подтверждения email
  {
    path: '/verify-email/:email',
    name: 'verify-email',
    component: EmailVerification,
    props: true,
    meta: { requiresAuth: false, title: 'Подтверждение email - Zooracle' }
  },
  
  // Альтернативный маршрут для ссылок восстановления пароля с токеном в разных форматах
  {
    path: '/reset-password-confirm',
    redirect: to => {
      // Перенаправление на стандартный маршрут с сохранением параметров запроса
      return { path: '/reset-password/confirm', query: to.query };
    }
  },
  
  // Маршрут для выхода из аккаунта
  {
    path: '/logout',
    name: 'logout',
    // Используем простой компонент вместо redirect для более надежной работы
    component: {
      /**
       * Компонент логаута, который выполняет выход и перенаправляет пользователя
       * @returns {null} Не возвращает элементы DOM
       */
      render: () => null,
      /**
       * Хук жизненного цикла, выполняющийся при создании компонента
       * Обеспечивает выход из системы и перенаправление на страницу входа
       */
      created() {
        // Проверка аутентификации и выход из аккаунта
        if (authService.isAuthenticated()) {
          console.log('Выполняется выход из системы...');
          authService.logout();
          console.log('Пользователь успешно вышел из системы');
        } else {
          console.log('Пользователь не был авторизован, перенаправление на страницу входа');
        }
        
        // Перенаправление на страницу входа
        this.$router.push('/login');
      }
    },
    meta: { title: 'Выход - Zooracle' }
  },
  
  // Маршрут главной страницы - каталог животных
  {
    path: '/',
    name: 'home',
    component: AnimalCatalog,
    meta: { requiresAuth: true, title: 'Каталог животных - Zooracle' }
  },
  
  // Маршрут для добавления нового вида животных (только для администраторов)
  {
    path: '/add-animal',
    name: 'add-animal',
    component: AddAnimal,
    meta: { 
      requiresAuth: true,
      requiresAdmin: true,
      title: 'Добавление нового вида - Zooracle' 
    }
  },
  
  // Маршрут для редактирования вида животных (только для администраторов)
  {
    path: '/edit-animal/:id',
    name: 'edit-animal',
    component: EditAnimal,
    props: true,
    meta: { 
      requiresAuth: true,
      requiresAdmin: true,
      title: 'Редактирование вида - Zooracle' 
    }
  },
  
  // Маршрут для обработки несуществующих маршрутов (перенаправление на логин)
  { 
    path: '/:pathMatch(.*)*', 
    redirect: '/login',
    meta: { title: 'Страница не найдена - Zooracle' }
  }
];

/**
 * Создание экземпляра роутера с использованием HTML5 истории
 * Важно: всегда используем корневой путь '/' для корректной работы с вложенными маршрутами
 * @type {Router}
 */
const router = createRouter({
  history: createWebHistory('/'),
  routes,
  // Настройка прокрутки страницы при переходах
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition;
    } else {
      return { top: 0 };
    }
  }
});

/**
 * Глобальный обработчик переходов между маршрутами
 * Проверяет необходимость аутентификации и выполняет перенаправление
 */
router.beforeEach((to, from, next) => {
  // Для отладки
  console.log(`Переход с маршрута "${from.path}" на "${to.path}"`);
  console.log('Параметры URL:', to.query);
  
  // Устанавливаем заголовок страницы из метаданных маршрута
  if (to.meta.title) {
    document.title = to.meta.title;
  }
  
  // Проверка аутентификации пользователя
  const isAuthenticated = authService.isAuthenticated();
  
  // Проверка на админские права для маршрутов, требующих их
  if (to.meta.requiresAdmin) {
    // Получаем данные пользователя из localStorage
    const userData = localStorage.getItem('user');
    const user = userData ? JSON.parse(userData) : null;
    const isAdmin = user && user.is_admin === true;
    
    if (!isAdmin) {
      console.log('Доступ запрещен: требуются права администратора');
      next('/'); // Перенаправляем на главную страницу
      return;
    }
  }
  
  // Перенаправление в зависимости от статуса аутентификации
  if (to.meta.requiresAuth && !isAuthenticated) {
    console.log('Требуется аутентификация. Перенаправление на /login');
    next('/login');
  } else if ((to.path === '/login' || to.path === '/register') && isAuthenticated) {
    console.log('Пользователь уже аутентифицирован. Перенаправление на главную');
    next('/');
  } else {
    // Специальная проверка для страницы сброса пароля
    if (to.name === 'reset-password-confirm') {
      if (!to.query.token) {
        console.warn('Попытка доступа к странице сброса пароля без токена');
        next('/reset-password'); // Перенаправляем на страницу запроса сброса
        return;
      } else {
        console.log('Токен найден в URL:', to.query.token);
      }
    }
    
    // Продолжаем нормальный переход
    next();
  }
});

/**
 * Обработчик события завершения перехода между маршрутами
 * Используется для логирования и аналитики
 */
router.afterEach((to) => {
  console.log(`Переход завершен. Текущий маршрут: ${to.path}`);
});

export default router;