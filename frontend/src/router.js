import { createRouter, createWebHistory } from 'vue-router';
import LoginForm from './components/Login.vue';
import RegisterForm from './components/Register.vue';
import ResetPasswordForm from './components/ResetPassword.vue';
import authService from './services/auth';

const routes = [
  {
    path: '/login',
    name: 'login',
    component: LoginForm,
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterForm,
    meta: { requiresAuth: false }
  },
  {
    path: '/reset-password',
    name: 'reset-password',
    component: ResetPasswordForm,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'home',
    component: () => import('./App.vue'),
    meta: { requiresAuth: true }
  },
  { 
    path: '/:catchAll(.*)', 
    redirect: '/login' 
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, from, next) => {
  const isAuthenticated = authService.isAuthenticated();
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login');
  } else if ((to.path === '/login' || to.path === '/register') && isAuthenticated) {
    next('/');
  } else {
    next();
  }
});

export default router;