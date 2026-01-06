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
      meta: { hideNavbar: true, requiresAuth: true }
    },
    {
      // 视频详情页
      path: '/video/:id',
      name: 'video',
      component: () => import('../views/VideoDetail.vue'),
      meta: { hideNavbar: false }
    },
    {
      // 管理后台（嵌套路由）
      path: '/admin',
      component: () => import('../views/AdminLayout.vue'),
      meta: { requiresAuth: true, requiresAdmin: true, hideNavbar: true },
      children: [
        {
          path: '',
          redirect: '/admin/dashboard'
        },
        {
          path: 'dashboard',
          name: 'admin-dashboard',
          component: () => import('../views/AdminDashboard.vue')
        },
        {
          path: 'audit',
          name: 'admin-audit',
          component: () => import('../views/AdminAudit.vue')
        },
        {
          path: 'users',
          name: 'admin-users',
          component: () => import('../views/AdminUsers.vue')
        }
      ]
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
    },
    {
      // 消息中心
      path: '/messages',
      name: 'messages',
      component: () => import('../views/MessageCenter.vue'),
      meta: { hideNavbar: false, requiresAuth: true }
    }
  ]
})

// 路由守卫：权限验证
router.beforeEach((to, from, next) => {
  // 检查是否需要登录
  if (to.meta.requiresAuth) {
    const userId = localStorage.getItem('user_id')
    if (!userId) {
      next('/login')
      return
    }
    
    // 检查是否需要管理员权限
    if (to.meta.requiresAdmin) {
      const role = localStorage.getItem('role')
      if (role !== 'admin') {
        next('/')
        return
      }
    }
  }
  
  next()
})

export default router
