import { createRouter, createWebHistory } from 'vue-router';
import LoginForm from './components/Login.vue';
import RegisterForm from './components/Register.vue';
import ResetPasswordForm from './components/ResetPassword.vue';
import ResetPasswordConfirmForm from './components/ResetPasswordConfirm.vue';
import EmailVerification from './components/EmailVerification.vue';
import AnimalCatalog from './components/AnimalCatalog.vue';
import AddAnimal from './components/AddAnimal.vue';
import EditAnimal from './components/EditAnimal.vue';
import AnimalDetail from './components/AnimalDetail.vue';
import EditTest from './components/EditTest.vue';
import TakeTest from './components/TakeTest.vue';
import ProfilePage from './components/ProfilePage.vue';
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
  
  // Маршрут для личного кабинета пользователя
  {
    path: '/profile',
    name: 'profile',
    component: ProfilePage,
    meta: { requiresAuth: true, title: 'Личный кабинет - Zooracle' }
  },
  
  // Альтернативный маршрут для ссылок восстановления пароля с токеном в разных форматах
  {
    path: '/reset-password-confirm',
    redirect: to => {
      return { path: '/reset-password/confirm', query: to.query };
    }
  },
  
  // Маршрут для выхода из аккаунта
  {
    path: '/logout',
    name: 'logout',
    redirect: () => {
      /**
       * Функция выхода из системы и перенаправления
       * Выполняется непосредственно при обработке маршрута
       */
      console.log('Выполняется выход из системы...');
      
      // Выход из аккаунта
      authService.logout();
      
      // Отправляем событие для компонентов, чтобы они знали о выходе пользователя
      window.dispatchEvent(new Event('localAuthChange'));
      
      console.log('Пользователь успешно вышел из системы, перенаправление на /login');
      
      // Возвращаем объект перенаправления
      return { path: '/login' };
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
  
  // Маршрут для просмотра детальной информации о животном
  {
    path: '/animal/:id',
    name: 'animal-detail',
    component: AnimalDetail,
    props: true,
    meta: { requiresAuth: true, title: 'Детальная информация - Zooracle' }
  },
  
  // Маршрут для создания/редактирования теста (только для администраторов)
  {
    path: '/edit-test/:animalId/:testId?',
    name: 'edit-test',
    component: EditTest,
    props: true,
    meta: { 
      requiresAuth: true,
      requiresAdmin: true,
      title: 'Редактирование теста - Zooracle' 
    }
  },
  
  // Маршрут для прохождения теста пользователем
  {
    path: '/take-test/:animalId/:testId',
    name: 'take-test',
    component: TakeTest,
    props: true,
    meta: { 
      requiresAuth: true,
      title: 'Прохождение теста - Zooracle' 
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
        next('/reset-password');
        return;
      } else {
        console.log('Токен найден в URL:', to.query.token);
      }
    }
    
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