<script setup>
/**
 * 首页组件
 * 展示视频列表，提供导航、搜索、分类筛选和个人中心入口
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()

// 视频列表数据
const videos = ref([])
const loading = ref(true)

// 分类数据
const categories = ref([])
const categoriesLoading = ref(false)

// 搜索和筛选状态
const searchKeyword = ref('')  // 搜索关键词
const activeCategoryId = ref('all')  // 当前选中的分类ID

// 从 localStorage 获取当前用户信息
const nickname = ref(localStorage.getItem('nickname') || '用户')
const userRole = ref(localStorage.getItem('role') || 'user')

// 是否为管理员
const isAdmin = ref(userRole.value === 'admin')

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
 * 获取视频列表（带搜索和筛选功能）
 */
const fetchVideos = async () => {
  loading.value = true
  try {
    // 构建请求参数
    const params = {}
    if (searchKeyword.value.trim()) {
      params.keyword = searchKeyword.value.trim()
    }
    if (activeCategoryId.value && activeCategoryId.value !== 'all') {
      params.category_id = activeCategoryId.value
    }
    
    // 调用后端接口
    const response = await api.get('/videos/list', { params })
    videos.value = response.data.data || []
  } catch (error) {
    console.error('获取视频列表失败:', error)
    videos.value = []
  } finally {
    loading.value = false
  }
}

/**
 * 点击搜索按钮
 */
const handleSearch = () => {
  fetchVideos()
}

/**
 * 点击分类按钮
 */
const handleCategoryChange = (categoryId) => {
  activeCategoryId.value = categoryId
  fetchVideos()
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
 * 退出登录
 */
const logout = () => {
  localStorage.removeItem('user_id')
  localStorage.removeItem('nickname')
  localStorage.removeItem('role')
  router.push('/login')
}

/**
 * 跳转到视频详情页
 */
const goToVideo = (videoId) => {
  router.push(`/video/${videoId}`)
}

// 页面加载时获取分类和视频列表
onMounted(() => {
  fetchCategories()
  fetchVideos()
})
</script>

<template>
  <div class="home-container">
    <!-- 顶部导航栏 -->
    <header class="navbar">
      <div class="navbar-left">
        <h1 class="logo">UniVideo</h1>
      </div>
      <div class="navbar-right">
        <!-- 用户昵称，点击跳转个人主页 -->
        <span class="welcome-text" @click="goToProfile" style="cursor: pointer;">
          欢迎，<span class="nickname-link">{{ nickname }}</span>
        </span>
        <!-- 管理后台入口，仅管理员可见 -->
        <button v-if="isAdmin" class="btn btn-admin" @click="goToAdmin">管理后台</button>
        <!-- 个人主页按钮 -->
        <button class="btn btn-profile" @click="goToProfile">个人主页</button>
        <button class="btn btn-primary" @click="goToUpload">上传视频</button>
        <button class="btn btn-secondary" @click="logout">退出登录</button>
      </div>
    </header>

    <!-- 内容区域 -->
    <main class="content">
      <!-- 搜索和筛选区域 -->
      <div class="filter-section">
        <!-- 搜索框 -->
        <div class="search-box">
          <input 
            v-model="searchKeyword" 
            type="text" 
            placeholder="搜索视频标题..."
            @keyup.enter="handleSearch"
            class="search-input"
          />
          <button @click="handleSearch" class="search-btn">搜索</button>
        </div>

        <!-- 分类标签栏 -->
        <div class="category-tabs">
          <button 
            class="category-tab"
            :class="{ active: activeCategoryId === 'all' }"
            @click="handleCategoryChange('all')"
          >
            全部
          </button>
          <button 
            v-for="category in categories" 
            :key="category.id"
            class="category-tab"
            :class="{ active: activeCategoryId === category.id }"
            @click="handleCategoryChange(category.id)"
          >
            {{ category.name }}
          </button>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <p>加载中...</p>
      </div>

      <!-- 空状态 -->
      <div v-else-if="videos.length === 0" class="empty-state">
        <p>暂无视频，快去上传第一个视频吧！</p>
        <button class="btn btn-primary" @click="goToUpload">上传视频</button>
      </div>

      <!-- 视频列表 -->
      <div v-else class="video-grid">
        <div 
          v-for="video in videos" 
          :key="video.id" 
          class="video-card"
          @click="goToVideo(video.id)"
        >
          <!-- 视频封面 -->
          <div class="video-cover">
            <img :src="video.cover_url" :alt="video.title" />
          </div>
          <!-- 视频信息 -->
          <div class="video-info">
            <h3 class="video-title">{{ video.title }}</h3>
            <div class="video-meta">
              <span class="author">{{ video.author_nickname || '未知作者' }}</span>
              <span class="category">{{ video.category_name || '未分类' }}</span>
            </div>
            <div class="video-stats">
              <span>{{ video.view_count || 0 }} 播放</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* ==================== 页面容器 ==================== */
.home-container {
  min-height: 100vh;
  background-color: var(--bg-color, #F9F9F9);
}

/* ==================== 导航栏 - 磨砂玻璃效果 ==================== */
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 32px;
  height: 64px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 1px 0 rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 0;
  z-index: 1000;
  transition: all 0.3s ease;
}

.navbar-left .logo {
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

.navbar-left .logo:hover {
  transform: scale(1.05);
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.welcome-text {
  color: var(--text-secondary, #666);
  font-size: 14px;
  margin-right: 4px;
}

.nickname-link {
  color: var(--primary-color, #FF5252);
  font-weight: 600;
  transition: all 0.2s ease;
}

.nickname-link:hover {
  color: var(--primary-hover, #FF7070);
}

/* ==================== 按钮样式 - 现代化设计 ==================== */
.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.btn:active {
  transform: scale(0.97);
}

.btn-primary {
  background: linear-gradient(135deg, #FF5252 0%, #FF7070 100%);
  color: #fff;
  box-shadow: 0 2px 8px rgba(255, 82, 82, 0.3);
}

.btn-primary:hover {
  background: linear-gradient(135deg, #FF7070 0%, #FF9090 100%);
  box-shadow: 0 4px 12px rgba(255, 82, 82, 0.4);
  transform: translateY(-2px);
}

.btn-profile {
  background: linear-gradient(135deg, #67C23A 0%, #85CE61 100%);
  color: #fff;
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.3);
}

.btn-profile:hover {
  background: linear-gradient(135deg, #85CE61 0%, #95D475 100%);
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.4);
  transform: translateY(-2px);
}

.btn-admin {
  background: linear-gradient(135deg, #722ED1 0%, #9254DE 100%);
  color: #fff;
  box-shadow: 0 2px 8px rgba(114, 46, 209, 0.3);
}

.btn-admin:hover {
  background: linear-gradient(135deg, #9254DE 0%, #B37FEB 100%);
  box-shadow: 0 4px 12px rgba(114, 46, 209, 0.4);
  transform: translateY(-2px);
}

.btn-secondary {
  background: #fff;
  color: var(--text-secondary, #666);
  border: 1px solid var(--border-color, #E0E0E0);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.btn-secondary:hover {
  background: #F9F9F9;
  border-color: var(--text-tertiary, #999);
  transform: translateY(-1px);
}

/* ==================== 内容区域 ==================== */
.content {
  padding: 32px;
  max-width: 1600px;
  margin: 0 auto;
}

/* ==================== 搜索和筛选区域 ==================== */
.filter-section {
  margin-bottom: 32px;
}

.search-box {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.search-input {
  flex: 1;
  padding: 14px 20px;
  border: 2px solid transparent;
  background: #fff;
  border-radius: 12px;
  font-size: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
}

.search-input:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.search-input:focus {
  border-color: var(--primary-color, #FF5252);
  box-shadow: 0 4px 16px rgba(255, 82, 82, 0.2);
}

.search-btn {
  padding: 14px 32px;
  background: linear-gradient(135deg, #FF5252 0%, #FF7070 100%);
  color: #fff;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(255, 82, 82, 0.3);
  transition: all 0.3s ease;
}

.search-btn:hover {
  background: linear-gradient(135deg, #FF7070 0%, #FF9090 100%);
  box-shadow: 0 4px 12px rgba(255, 82, 82, 0.4);
  transform: translateY(-2px);
}

.search-btn:active {
  transform: translateY(0);
}

/* ==================== 分类标签栏 ==================== */
.category-tabs {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.category-tab {
  padding: 10px 20px;
  background: #fff;
  color: var(--text-secondary, #666);
  border: 2px solid transparent;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.category-tab:hover {
  background: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.category-tab.active {
  background: linear-gradient(135deg, #FF5252 0%, #FF7070 100%);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(255, 82, 82, 0.3);
}

.category-tab.active:hover {
  background: linear-gradient(135deg, #FF7070 0%, #FF9090 100%);
  box-shadow: 0 6px 16px rgba(255, 82, 82, 0.4);
}

/* ==================== 加载和空状态 ==================== */
.loading-state,
.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--text-tertiary, #999);
  font-size: 15px;
}

.empty-state .btn {
  margin-top: 20px;
}

/* ==================== 视频网格布局 ==================== */
.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 28px;
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ==================== 视频卡片 - YouTube风格 ==================== */
.video-card {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.video-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.12);
}

/* 封面图样式 - 带悬停缩放 */
.video-cover {
  position: relative;
  width: 100%;
  padding-top: 56.25%; /* 16:9 比例 */
  background: linear-gradient(135deg, #f0f0f0 0%, #e8e8e8 100%);
  overflow: hidden;
}

.video-cover img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.video-card:hover .video-cover img {
  transform: scale(1.08);
}

/* 视频信息样式 */
.video-info {
  padding: 16px;
}

.video-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #333);
  margin: 0 0 10px 0;
  line-height: 1.5;
  /* 超出两行显示省略号 */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  transition: color 0.2s ease;
}

.video-card:hover .video-title {
  color: var(--primary-color, #FF5252);
}

.video-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary, #666);
  margin-bottom: 6px;
}

.video-meta .author {
  font-weight: 500;
}

.video-meta .category {
  color: var(--primary-color, #FF5252);
  font-weight: 500;
  background: rgba(255, 82, 82, 0.08);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.video-stats {
  font-size: 13px;
  color: var(--text-tertiary, #999);
  display: flex;
  align-items: center;
  gap: 4px;
}

.video-stats::before {
  content: '▶';
  font-size: 10px;
  margin-right: 2px;
}

/* ==================== 响应式设计 ==================== */
@media (max-width: 1400px) {
  .video-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 24px;
  }
}

@media (max-width: 768px) {
  .navbar {
    padding: 0 16px;
    height: 56px;
  }

  .navbar-left .logo {
    font-size: 22px;
  }

  .navbar-right {
    gap: 8px;
  }

  .btn {
    padding: 8px 14px;
    font-size: 13px;
  }

  .content {
    padding: 20px 16px;
  }

  .video-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 20px;
  }

  .welcome-text {
    display: none;
  }
}

@media (max-width: 480px) {
  .video-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .search-box {
    flex-direction: column;
  }

  .search-btn {
    width: 100%;
  }

  .category-tabs {
    gap: 8px;
  }

  .category-tab {
    padding: 8px 16px;
    font-size: 13px;
  }
}
</style>
