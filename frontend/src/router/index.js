/**
 * Vue Router 路由配置
 * 定义应用的页面路由映射关系
 */
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      // 首页 - 视频列表
      path: '/',
      name: 'home',
      component: () => import('../views/Home.vue')
    },
    {
      // 登录页
      path: '/login',
      name: 'login',
      component: () => import('../views/Login.vue')
    },
    {
      // 注册页
      path: '/register',
      name: 'register',
      component: () => import('../views/Register.vue')
    },
    {
      // 视频上传页
      path: '/upload',
      name: 'upload',
      component: () => import('../views/Upload.vue')
    },
    {
      // 视频详情页
      path: '/video/:id',
      name: 'video',
      component: () => import('../views/VideoDetail.vue')
    },
    {
      // 管理员审核后台
      path: '/admin',
      name: 'admin',
      component: () => import('../views/AdminAudit.vue')
    },
    {
      // 个人主页
      path: '/profile',
      name: 'profile',
      component: () => import('../views/Profile.vue')
    },
    {
      // 作者主页
      path: '/author/:id',
      name: 'author',
      component: () => import('../views/AuthorPage.vue')
    }
  ]
})

export default router
