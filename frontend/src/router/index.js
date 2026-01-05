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
      component: () => import('../views/Home.vue'),
      meta: { hideNavbar: false }
    },
    {
      // 登录页
      path: '/login',
      name: 'login',
      component: () => import('../views/Login.vue'),
      meta: { hideNavbar: true }
    },
    {
      // 注册页
      path: '/register',
      name: 'register',
      component: () => import('../views/Register.vue'),
      meta: { hideNavbar: true }
    },
    {
      // 视频上传页
      path: '/upload',
      name: 'upload',
      component: () => import('../views/Upload.vue'),
      meta: { hideNavbar: false }
    },
    {
      // 视频详情页
      path: '/video/:id',
      name: 'video',
      component: () => import('../views/VideoDetail.vue'),
      meta: { hideNavbar: false }
    },
    {
      // 管理员审核后台
      path: '/admin',
      name: 'admin',
      component: () => import('../views/AdminAudit.vue'),
      meta: { hideNavbar: true }
    },
    {
      // 个人主页
      path: '/profile',
      name: 'profile',
      component: () => import('../views/Profile.vue'),
      meta: { hideNavbar: false }
    },
    {
      // 作者主页
      path: '/author/:id',
      name: 'author',
      component: () => import('../views/AuthorPage.vue'),
      meta: { hideNavbar: false }
    }
  ]
})

export default router
