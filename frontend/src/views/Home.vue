<script setup>
/**
 * 首页组件
 * 展示视频列表，提供导航功能
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()

// 视频列表数据
const videos = ref([])
const loading = ref(true)

// 从 localStorage 获取当前用户信息
const nickname = ref(localStorage.getItem('nickname') || '用户')
const userRole = ref(localStorage.getItem('role') || 'user')

// 是否为管理员
const isAdmin = ref(userRole.value === 'admin')

/**
 * 获取视频列表
 * 调用后端接口获取已发布的视频
 */
const fetchVideos = async () => {
  loading.value = true
  try {
    // 后端接口路径是 /videos/list
    const response = await api.get('/videos/list')
    videos.value = response.data.data || []
  } catch (error) {
    console.error('获取视频列表失败:', error)
    videos.value = []
  } finally {
    loading.value = false
  }
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
 * 退出登录
 * 清除本地存储并跳转到登录页
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

// 页面加载时获取视频列表
onMounted(() => {
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
        <span class="welcome-text">欢迎，{{ nickname }}</span>
        <!-- 管理后台入口，仅管理员可见 -->
        <button v-if="isAdmin" class="btn btn-admin" @click="goToAdmin">管理后台</button>
        <button class="btn btn-primary" @click="goToUpload">上传视频</button>
        <button class="btn btn-secondary" @click="logout">退出登录</button>
      </div>
    </header>

    <!-- 内容区域 -->
    <main class="content">
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
/* 页面容器 */
.home-container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

/* 导航栏样式 */
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 60px;
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.navbar-left .logo {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
  margin: 0;
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.welcome-text {
  color: #666;
  font-size: 14px;
}

/* 按钮样式 */
.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-primary {
  background-color: #409eff;
  color: #fff;
}

.btn-primary:hover {
  background-color: #66b1ff;
}

.btn-secondary {
  background-color: #f5f5f5;
  color: #666;
  border: 1px solid #ddd;
}

.btn-secondary:hover {
  background-color: #e8e8e8;
}

/* 管理后台按钮样式 */
.btn-admin {
  background-color: #722ed1;
  color: #fff;
}

.btn-admin:hover {
  background-color: #9254de;
}

/* 内容区域 */
.content {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

/* 加载和空状态 */
.loading-state,
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.empty-state .btn {
  margin-top: 16px;
}

/* 视频网格布局 */
.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

/* 视频卡片样式 */
.video-card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
}

.video-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

/* 封面图样式 */
.video-cover {
  position: relative;
  width: 100%;
  padding-top: 56.25%; /* 16:9 比例 */
  background-color: #f0f0f0;
  overflow: hidden;
}

.video-cover img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 视频信息样式 */
.video-info {
  padding: 12px;
}

.video-title {
  font-size: 16px;
  font-weight: 500;
  color: #333;
  margin: 0 0 8px 0;
  /* 超出两行显示省略号 */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
}

.video-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
}

.video-meta .category {
  color: #409eff;
}

.video-stats {
  font-size: 12px;
  color: #999;
}
</style>
