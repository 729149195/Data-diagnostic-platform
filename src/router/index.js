import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView/LoginView.vue'
import AnomalyLabelView from "@/views/AnomalyLabelView/AnomalyLabelView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'AnomalyLabelView',
      component: AnomalyLabelView
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    }
  ]
})

export default router
