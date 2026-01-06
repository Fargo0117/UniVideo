<script setup>
/**
 * 全局导航栏组件
 * 包含 Logo、搜索框、分类栏、用户信息和操作按钮
 */
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '@/api'

const router = useRouter()
const route = useRoute()

// 搜索和筛选状态
const searchKeyword = ref('')  // 搜索关键词
const activeCategoryId = ref('all')  // 当前选中的分类ID
const isSearchFocused = ref(false)  // 搜索框焦点状态

// 分类数据
const categories = ref([])
const categoriesLoading = ref(false)

// 从 localStorage 获取当前用户信息
const nickname = ref(localStorage.getItem('nickname') || '用户')
const userRole = ref(localStorage.getItem('role') || 'user')
const userId = ref(localStorage.getItem('user_id'))

// 是否为管理员
const isAdmin = ref(userRole.value === 'admin')

// 未读消息数量
const unreadMessageCount = ref(0)

/**
 * 获取分类列表
 */
const fetchCategories = async () => {
  categoriesLoading.value = true
  try {
    const response = await api.get('/videos/categories')
    categories.value = response.data.data || []
  } catch (error) {
    console.error('获取分类列表失败:', error)
    categories.value = []
  } finally {
    categoriesLoading.value = false
  }
}

/**
 * 点击搜索按钮
 */
const handleSearch = () => {
  // 如果不在首页，先跳转到首页
  if (route.path !== '/') {
    router.push({
      path: '/',
      query: { keyword: searchKeyword.value.trim() }
    })
  } else {
    // 触发首页搜索事件
    window.dispatchEvent(new CustomEvent('navbar-search', { 
      detail: { keyword: searchKeyword.value.trim() } 
    }))
  }
}

/**
 * 点击分类按钮
 */
const handleCategoryChange = (categoryId) => {
  activeCategoryId.value = categoryId
  
  // 如果不在首页，先跳转到首页
  if (route.path !== '/') {
    router.push({
      path: '/',
      query: { category_id: categoryId }
    })
  } else {
    // 触发首页分类筛选事件
    window.dispatchEvent(new CustomEvent('navbar-category-change', { 
      detail: { categoryId } 
    }))
  }
}

/**
 * 跳转到首页
 */
const goToHome = () => {
  router.push('/')
}

/**
 * 跳转到上传页面
 */
const goToUpload = () => {
  router.push('/upload')
}

/**
 * 跳转到管理后台（仅管理员可用）
 */
const goToAdmin = () => {
  router.push('/admin')
}

/**
 * 跳转到个人主页
 */
const goToProfile = () => {
  router.push('/profile')
}

/**
 * 跳转到消息中心
 */
const goToMessages = () => {
  router.push('/messages')
}

/**
 * 获取未读消息数量
 */
const fetchUnreadCount = async () => {
  if (!userId.value) return
  
  try {
    const response = await api.get('/admin/notifications/unread-count', {
      params: { user_id: parseInt(userId.value) }
    })
    if (response.data.code === 200) {
      unreadMessageCount.value = response.data.data?.unread_count || 0
    }
  } catch (err) {
    console.error('获取未读消息数量失败:', err)
  }
}

/**
 * 退出登录
 */
const logout = () => {
  localStorage.removeItem('user_id')
  localStorage.removeItem('nickname')
  localStorage.removeItem('role')
  router.push('/login')
}

// 定时器ID（用于清理）
let unreadCountTimer = null

// 页面加载时获取分类和未读消息数量
onMounted(() => {
  fetchCategories()
  if (userId.value) {
    fetchUnreadCount()
    // 定期刷新未读消息数量（每30秒）
    unreadCountTimer = setInterval(fetchUnreadCount, 30000)
  }
  
  // 监听页面可见性变化，当页面重新可见时刷新未读数量
  document.addEventListener('visibilitychange', handleVisibilityChange)
  
  // 监听 localStorage 变化（用于检测登录/登出）
  window.addEventListener('storage', handleStorageChange)
  
  // 使用轮询方式检查 userId 变化（因为同源页面 storage 事件可能不触发）
  const checkUserIdInterval = setInterval(() => {
    const currentUserId = localStorage.getItem('user_id')
    if (currentUserId !== userId.value) {
      userId.value = currentUserId
      if (currentUserId) {
        fetchUnreadCount()
        if (!unreadCountTimer) {
          unreadCountTimer = setInterval(fetchUnreadCount, 30000)
        }
      } else {
        unreadMessageCount.value = 0
        if (unreadCountTimer) {
          clearInterval(unreadCountTimer)
          unreadCountTimer = null
        }
      }
    }
  }, 1000) // 每秒检查一次
  
  // 保存检查定时器ID以便清理
  window._userIdCheckInterval = checkUserIdInterval
})

// 处理 localStorage 变化
const handleStorageChange = (e) => {
  if (e.key === 'user_id') {
    userId.value = e.newValue
    if (e.newValue) {
      fetchUnreadCount()
      if (!unreadCountTimer) {
        unreadCountTimer = setInterval(fetchUnreadCount, 30000)
      }
    } else {
      unreadMessageCount.value = 0
      if (unreadCountTimer) {
        clearInterval(unreadCountTimer)
        unreadCountTimer = null
      }
    }
  }
}

// 处理页面可见性变化
const handleVisibilityChange = () => {
  if (document.visibilityState === 'visible' && userId.value) {
    fetchUnreadCount()
  }
}

// 监听路由变化，从消息中心返回时刷新未读数量
watch(() => route.path, (newPath, oldPath) => {
  // 如果从消息中心页面离开，刷新未读数量
  if (oldPath === '/messages' && newPath !== '/messages' && userId.value) {
    fetchUnreadCount()
  }
  // 每次路由变化时都刷新一次（确保数据最新）
  if (userId.value && newPath !== '/messages') {
    fetchUnreadCount()
  }
})

// 组件卸载时清理定时器和事件监听
onUnmounted(() => {
  if (unreadCountTimer) {
    clearInterval(unreadCountTimer)
  }
  if (window._userIdCheckInterval) {
    clearInterval(window._userIdCheckInterval)
    delete window._userIdCheckInterval
  }
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  window.removeEventListener('storage', handleStorageChange)
})
</script>

<template>
  <header class="sticky-header">
    <!-- 第一层：Top Bar -->
    <div class="top-bar">
      <!-- 左侧 Logo -->
      <div class="logo-section">
        <h1 class="logo" @click="goToHome">UniVideo</h1>
      </div>

      <!-- 中间：灵动搜索框 -->
      <div class="search-section">
        <div 
          class="dynamic-search-box" 
          :class="{ focus: isSearchFocused }"
        >
          <input 
            v-model="searchKeyword" 
            type="text" 
            placeholder="搜索视频标题..."
            @keyup.enter="handleSearch"
            @focus="isSearchFocused = true"
            @blur="isSearchFocused = false"
            class="search-input"
          />
          <button @click="handleSearch" class="search-icon-btn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <circle cx="11" cy="11" r="8"/>
              <path d="m21 21-4.35-4.35"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- 右侧：用户信息和操作按钮 -->
      <div class="user-section">
        <!-- 消息按钮（仅登录用户显示） -->
        <button 
          v-if="userId" 
          class="message-btn" 
          @click="goToMessages"
          title="消息中心"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          <span v-if="unreadMessageCount > 0" class="message-badge">
            {{ unreadMessageCount > 99 ? '99+' : unreadMessageCount }}
          </span>
        </button>

        <!-- 上传按钮 -->
        <button class="upload-btn" @click="goToUpload">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          <span>上传</span>
        </button>

        <!-- 用户头像下拉菜单 -->
        <div class="user-dropdown">
          <div class="user-avatar-box" @click="goToProfile">
            <div class="user-avatar">
              {{ nickname.charAt(0).toUpperCase() }}
            </div>
          </div>
          <!-- 下拉菜单 -->
          <div class="dropdown-menu">
            <div class="dropdown-item user-info">
              <div class="user-name">{{ nickname }}</div>
              <div class="user-role">{{ isAdmin ? '管理员' : '普通用户' }}</div>
            </div>
            <div class="dropdown-divider"></div>
            <button class="dropdown-item" @click="goToProfile">
              <span>个人主页</span>
            </button>
            <button class="dropdown-item" @click="goToMessages">
              <span>消息中心</span>
              <span v-if="unreadMessageCount > 0" class="dropdown-badge">
                {{ unreadMessageCount > 99 ? '99+' : unreadMessageCount }}
              </span>
            </button>
            <button v-if="isAdmin" class="dropdown-item" @click="goToAdmin">
              <span>管理后台</span>
            </button>
            <div class="dropdown-divider"></div>
            <button class="dropdown-item logout" @click="logout">
              <span>退出登录</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 第二层：Category Bar -->
    <div class="category-bar">
      <div class="category-scroll">
        <button 
          class="category-item"
          :class="{ active: activeCategoryId === 'all' }"
          @click="handleCategoryChange('all')"
        >
          全部
        </button>
        <button 
          v-for="category in categories" 
          :key="category.id"
          class="category-item"
          :class="{ active: activeCategoryId === category.id }"
          @click="handleCategoryChange(category.id)"
        >
          {{ category.name }}
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped>
/* ==================== 吸顶导航栏 ==================== */
.sticky-header {
  position: sticky;
  top: 0;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

/* ==================== Top Bar（第一层） ==================== */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 32px;
  gap: 24px;
}

/* Logo 区域 */
.logo-section {
  flex-shrink: 0;
}

.logo {
  font-size: 26px;
  font-weight: 700;
  background: linear-gradient(135deg, #FF5252 0%, #FF7070 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  letter-spacing: -0.5px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.logo:hover {
  transform: scale(1.05);
}

/* ==================== 灵动搜索框区域 ==================== */
.search-section {
  flex: 1;
  display: flex;
  justify-content: center;
  max-width: 800px;
}

.dynamic-search-box {
  position: relative;
  width: 250px;
  height: 42px;
  background: #f1f2f3;
  border-radius: 21px;
  border: 2px solid transparent;
  display: flex;
  align-items: center;
  padding: 0 16px;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.dynamic-search-box.focus {
  width: 500px;
  background: #fff;
  border-color: transparent;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
}

.dynamic-search-box .search-input {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font-size: 14px;
  color: #333;
  padding: 0;
}

.dynamic-search-box .search-input:focus {
  outline: none;
  border: none;
  box-shadow: none;
}

.dynamic-search-box .search-input::placeholder {
  color: #999;
}

.dynamic-search-box .search-icon-btn {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.dynamic-search-box .search-icon-btn:hover {
  background: rgba(255, 82, 82, 0.1);
  color: #FF5252;
}

.dynamic-search-box.focus .search-icon-btn {
  color: #FF5252;
}

/* ==================== 用户区域 ==================== */
.user-section {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

/* 消息按钮 */
.message-btn {
  position: relative;
  width: 40px;
  height: 40px;
  border: none;
  background: transparent;
  color: #666;
  cursor: pointer;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  padding: 0;
}

.message-btn:hover {
  background: rgba(255, 82, 82, 0.1);
  color: #FF5252;
}

.message-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  background: #ff4d4f;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
  line-height: 1.2;
  box-shadow: 0 2px 4px rgba(255, 77, 79, 0.3);
}

/* 上传按钮 */
.upload-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #FF5252 0%, #FF7070 100%);
  color: #fff;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(255, 82, 82, 0.3);
  transition: all 0.3s ease;
}

.upload-btn:hover {
  background: linear-gradient(135deg, #FF7070 0%, #FF9090 100%);
  box-shadow: 0 4px 12px rgba(255, 82, 82, 0.4);
  transform: translateY(-2px);
}

.upload-btn:active {
  transform: translateY(0);
}

/* 用户头像下拉菜单 */
.user-dropdown {
  position: relative;
}

.user-avatar-box {
  cursor: pointer;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #FF5252 0%, #FF7070 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(255, 82, 82, 0.3);
  transition: all 0.3s ease;
}

.user-avatar-box:hover .user-avatar {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(255, 82, 82, 0.4);
}

/* 下拉菜单 */
.dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 200px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  opacity: 0;
  visibility: hidden;
  transform: translateY(-10px);
  transition: all 0.3s ease;
  overflow: hidden;
}

.user-dropdown:hover .dropdown-menu {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.dropdown-item {
  width: 100%;
  padding: 12px 20px;
  border: none;
  background: none;
  text-align: left;
  font-size: 14px;
  color: #333;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.dropdown-badge {
  background: #ff4d4f;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
  line-height: 1.2;
}

.dropdown-item:hover {
  background: #f5f5f5;
}

.dropdown-item.user-info {
  flex-direction: column;
  align-items: flex-start;
  cursor: default;
  padding: 16px 20px;
}

.dropdown-item.user-info:hover {
  background: none;
}

.user-name {
  font-weight: 600;
  font-size: 15px;
  color: #333;
}

.user-role {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.dropdown-divider {
  height: 1px;
  background: #f0f0f0;
  margin: 4px 0;
}

.dropdown-item.logout {
  color: #FF5252;
}

.dropdown-item.logout:hover {
  background: rgba(255, 82, 82, 0.05);
}

/* ==================== Category Bar（第二层） ==================== */
.category-bar {
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  padding: 12px 32px;
  overflow: hidden;
}

.category-scroll {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
  padding-bottom: 2px;
}

.category-scroll::-webkit-scrollbar {
  display: none; /* Chrome/Safari/Opera */
}

.category-item {
  flex-shrink: 0;
  padding: 8px 20px;
  background: transparent;
  color: #666;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.category-item:hover {
  background: rgba(255, 82, 82, 0.08);
  color: #FF5252;
}

.category-item.active {
  background: linear-gradient(135deg, #FF5252 0%, #FF7070 100%);
  color: #fff;
  box-shadow: 0 2px 8px rgba(255, 82, 82, 0.25);
}

.category-item.active:hover {
  background: linear-gradient(135deg, #FF7070 0%, #FF9090 100%);
  box-shadow: 0 4px 12px rgba(255, 82, 82, 0.3);
}

/* ==================== 响应式设计 ==================== */
@media (max-width: 1024px) {
  .top-bar {
    padding: 12px 20px;
  }

  .category-bar {
    padding: 12px 20px;
  }

  .dynamic-search-box.focus {
    width: 350px;
  }
}

@media (max-width: 768px) {
  .logo {
    font-size: 22px;
  }

  .dynamic-search-box {
    width: 200px;
  }

  .dynamic-search-box.focus {
    width: 280px;
  }

  .upload-btn span {
    display: none;
  }

  .upload-btn {
    padding: 8px 12px;
  }
}
</style>
