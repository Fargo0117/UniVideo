<script setup>
/**
 * 管理后台布局组件
 * 提供左侧边栏和右侧内容区域的布局结构
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '@/api'

const router = useRouter()
const route = useRoute()

// 从 localStorage 获取用户信息
const nickname = ref(localStorage.getItem('nickname') || '管理员')
const userId = ref(localStorage.getItem('user_id'))
const userRole = ref(localStorage.getItem('role'))

// 如果当前路径是 /admin，重定向到 /admin/dashboard
onMounted(() => {
  if (route.path === '/admin') {
    router.push('/admin/dashboard')
  }
})

// 菜单项配置
const menuItems = [
  {
    key: 'dashboard',
    icon: '📊',
    label: '仪表盘',
    path: '/admin/dashboard'
  },
  {
    key: 'audit',
    icon: '🎬',
    label: '内容审核',
    path: '/admin/audit'
  },
  {
    key: 'users',
    icon: '👥',
    label: '用户管理',
    path: '/admin/users'
  }
]

// 当前激活的菜单项
const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/admin/dashboard')) return 'dashboard'
  if (path.startsWith('/admin/audit')) return 'audit'
  if (path.startsWith('/admin/users')) return 'users'
  return 'dashboard'
})

/**
 * 切换菜单
 */
const switchMenu = (key) => {
  const item = menuItems.find(m => m.key === key)
  if (item) {
    router.push(item.path)
  }
}

/**
 * 退出登录
 */
const handleLogout = () => {
  localStorage.removeItem('user_id')
  localStorage.removeItem('nickname')
  localStorage.removeItem('role')
  router.push('/login')
}
</script>

<template>
  <div class="admin-layout">
    <!-- 左侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h1 class="logo">UniVideo</h1>
        <p class="subtitle">管理后台</p>
      </div>
      
      <nav class="sidebar-nav">
        <div
          v-for="item in menuItems"
          :key="item.key"
          class="nav-item"
          :class="{ active: activeMenu === item.key }"
          @click="switchMenu(item.key)"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-text">{{ item.label }}</span>
        </div>
      </nav>
    </aside>

    <!-- 右侧内容区 -->
    <div class="main-content">
      <!-- 顶部 Header -->
      <header class="header">
        <div class="header-left">
          <h2 class="page-title">{{ menuItems.find(m => m.key === activeMenu)?.label || '管理后台' }}</h2>
        </div>
        <div class="header-right">
          <span class="user-name">{{ nickname }}</span>
          <button class="btn-logout" @click="handleLogout">退出登录</button>
        </div>
      </header>

      <!-- 主体内容 -->
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
  background-color: #f0f2f5;
}

/* 左侧边栏 */
.sidebar {
  width: 240px;
  background-color: #001529;
  color: #a6adb4;
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 100;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo {
  color: #fff;
  font-size: 24px;
  font-weight: bold;
  margin: 0 0 5px 0;
}

.subtitle {
  color: #a6adb4;
  font-size: 12px;
  margin: 0;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 0;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.3s;
  color: #a6adb4;
}

.nav-item:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: #fff;
}

.nav-item.active {
  background-color: #1890ff;
  color: #fff;
}

.nav-icon {
  font-size: 18px;
  margin-right: 12px;
  width: 20px;
  text-align: center;
}

.nav-text {
  font-size: 14px;
}

/* 右侧内容区 */
.main-content {
  flex: 1;
  margin-left: 240px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* 顶部 Header */
.header {
  height: 64px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-left {
  flex: 1;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #262626;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-name {
  color: #595959;
  font-size: 14px;
}

.btn-logout {
  padding: 6px 16px;
  background: #ff4d4f;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.btn-logout:hover {
  background: #ff7875;
}

/* 主体内容 */
.content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.loading-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #8c8c8c;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    width: 200px;
  }
  
  .main-content {
    margin-left: 200px;
  }
  
  .header {
    padding: 0 16px;
  }
  
  .content {
    padding: 16px;
  }
}
</style>
