<script setup>
/**
 * 作者主页组件
 * 展示指定用户的信息和已发布的视频列表
 */
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api, { followUser, unfollowUser, getFollowStatus } from '@/api'

const route = useRoute()
const router = useRouter()

// ==================== 数据定义 ====================

// 用户信息
const author = ref(null)
const loading = ref(true)
const error = ref(null)

// 视频列表
const videos = ref([])

// 关注状态
const isFollowing = ref(false)
const followLoading = ref(false)

// 当前用户ID
const currentUserId = localStorage.getItem('user_id')

// ==================== 工具函数 ====================

/**
 * 获取完整的资源URL
 * @param {string} path - 相对路径
 */
const getFullUrl = (path) => {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `http://localhost:5001/static/${path}`
}

/**
 * 格式化时间显示
 * @param {string} isoString - ISO时间字符串
 */
const formatTime = (isoString) => {
  if (!isoString) return ''
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

/**
 * 格式化状态文本
 */
const getStatusText = (status) => {
  const statusMap = {
    0: '待审核',
    1: '已发布',
    2: '已驳回'
  }
  return statusMap[status] || '未知'
}

/**
 * 获取状态样式类
 */
const getStatusClass = (status) => {
  const classMap = {
    0: 'status-pending',
    1: 'status-published',
    2: 'status-rejected'
  }
  return classMap[status] || ''
}

// ==================== API 调用 ====================

/**
 * 获取作者信息和视频列表
 */
const fetchAuthorData = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await api.get(`/users/${route.params.id}`)
    author.value = response.data.data.user
    videos.value = response.data.data.videos.list
    // 获取关注状态
    if (currentUserId && author.value.id != currentUserId) {
      fetchFollowStatus()
    }
  } catch (err) {
    error.value = err.response?.data?.msg || '获取用户信息失败'
    console.error('获取用户信息失败:', err)
  } finally {
    loading.value = false
  }
}

/**
 * 获取当前用户对作者的关注状态
 */
const fetchFollowStatus = async () => {
  if (!currentUserId || !author.value?.id) return
  
  try {
    const response = await getFollowStatus(author.value.id, currentUserId)
    isFollowing.value = response.data.data?.is_following || false
  } catch (err) {
    console.error('获取关注状态失败:', err)
    isFollowing.value = false
  }
}

/**
 * 关注/取消关注作者
 */
const toggleFollow = async () => {
  if (!currentUserId) {
    alert('请先登录')
    router.push('/login')
    return
  }
  
  if (!author.value?.id) {
    alert('用户信息加载失败')
    return
  }
  
  followLoading.value = true
  try {
    if (isFollowing.value) {
      // 取消关注
      const response = await unfollowUser(author.value.id, currentUserId)
      if (response.data.code === 200) {
        isFollowing.value = false
        alert('取消关注成功')
      }
    } else {
      // 关注
      const response = await followUser(author.value.id, currentUserId)
      if (response.data.code === 200) {
        isFollowing.value = true
        alert('关注成功')
      }
    }
  } catch (err) {
    const message = err.response?.data?.msg || '操作失败'
    alert(message)
  } finally {
    followLoading.value = false
  }
}

/**
 * 跳转到视频详情页
 */
const goToVideo = (videoId) => {
  router.push(`/video/${videoId}`)
}

/**
 * 返回上一页
 */
const goBack = () => {
  router.back()
}

// ==================== 生命周期 ====================

onMounted(() => {
  fetchAuthorData()
})
</script>

<template>
  <div class="author-page-container">
    <!-- 顶部导航 -->
    <header class="nav-bar">
      <button class="back-btn" @click="goBack">&larr; 返回</button>
      <span class="site-name">UniVideo</span>
    </header>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <p>加载中...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="goBack">返回</button>
    </div>

    <!-- 主内容 -->
    <main v-else-if="author" class="author-content">
      <!-- 作者信息卡片 -->
      <section class="author-info-card">
        <div class="author-header">
          <img 
            class="author-avatar-large" 
            :src="getFullUrl(author.avatar) || '/default-avatar.png'" 
            :alt="author.nickname"
            @error="(e) => e.target.src = 'https://via.placeholder.com/100'"
          />
          <div class="author-details">
            <h1 class="author-name">{{ author.nickname || '未知用户' }}</h1>
            <p class="author-username">学号：{{ author.username }}</p>
            <p class="author-stats">
              <span class="stat-item">
                <span class="stat-value">{{ videos.length }}</span>
                <span class="stat-label">投稿视频</span>
              </span>
            </p>
          </div>
          <!-- 关注按钮 -->
          <button 
            v-if="currentUserId && currentUserId != author.id"
            class="follow-btn"
            :class="{ 'following': isFollowing }"
            :disabled="followLoading"
            @click="toggleFollow"
          >
            <span class="follow-icon">{{ isFollowing ? '✓' : '+' }}</span>
            <span class="follow-text">{{ isFollowing ? '已关注' : '关注' }}</span>
          </button>
        </div>
      </section>

      <!-- 投稿视频列表 -->
      <section class="videos-section">
        <h2 class="section-title">TA的投稿 ({{ videos.length }})</h2>
        
        <div v-if="videos.length === 0" class="no-videos">
          <p>该用户还没有发布任何视频</p>
        </div>

        <div v-else class="video-grid">
          <div 
            v-for="video in videos" 
            :key="video.id" 
            class="video-card"
            @click="goToVideo(video.id)"
          >
            <div class="video-cover-wrapper">
              <img 
                :src="getFullUrl(video.cover_path)" 
                :alt="video.title"
                class="video-cover"
                @error="(e) => e.target.src = 'https://via.placeholder.com/320x180?text=No+Image'"
              />
              <div class="video-duration">
                <span class="view-count">{{ video.view_count || 0 }} 播放</span>
              </div>
            </div>
            <div class="video-info">
              <h3 class="video-title">{{ video.title }}</h3>
              <p class="video-meta">
                <span class="video-category">{{ video.category?.name }}</span>
                <span class="separator">·</span>
                <span class="video-time">{{ formatTime(video.created_at) }}</span>
              </p>
              <p class="video-stats">
                <span>👍 {{ video.likes_count || 0 }}</span>
                <span>⭐ {{ video.collections_count || 0 }}</span>
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
/* ==================== 全局布局 ==================== */
.author-page-container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

/* 导航栏 */
.nav-bar {
  display: flex;
  align-items: center;
  padding: 0 24px;
  height: 56px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 100;
}

.back-btn {
  background: none;
  border: none;
  color: #409eff;
  font-size: 14px;
  cursor: pointer;
  padding: 8px 0;
}

.back-btn:hover {
  text-decoration: underline;
}

.site-name {
  margin-left: 16px;
  font-size: 18px;
  font-weight: bold;
  color: #409eff;
}

/* 加载/错误状态 */
.loading-state,
.error-state {
  text-align: center;
  padding: 80px 20px;
  color: #999;
}

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

/* ==================== 主内容区 ==================== */
.author-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

/* 作者信息卡片 */
.author-info-card {
  background: #fff;
  border-radius: 8px;
  padding: 32px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.author-header {
  display: flex;
  align-items: center;
  gap: 24px;
}

.author-avatar-large {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
  background-color: #f0f0f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.author-details {
  flex: 1;
}

.author-name {
  font-size: 28px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px 0;
}

.author-username {
  font-size: 14px;
  color: #999;
  margin: 0 0 16px 0;
}

.author-stats {
  display: flex;
  gap: 32px;
  margin: 0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #409eff;
}

.stat-label {
  font-size: 13px;
  color: #999;
  margin-top: 4px;
}

/* ==================== 视频列表区 ==================== */
.videos-section {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin: 0 0 20px 0;
}

.no-videos {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

/* 视频卡片 */
.video-card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
  border: 1px solid #f0f0f0;
}

.video-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.video-cover-wrapper {
  position: relative;
  width: 100%;
  padding-top: 56.25%; /* 16:9 比例 */
  overflow: hidden;
  background-color: #f0f0f0;
}

.video-cover {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-duration {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.75);
  color: #fff;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.view-count {
  font-size: 12px;
}

.video-info {
  padding: 12px;
}

.video-title {
  font-size: 15px;
  font-weight: 500;
  color: #333;
  margin: 0 0 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.4;
  min-height: 42px;
}

.video-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #999;
  margin: 0 0 8px 0;
}

.video-category {
  color: #409eff;
}

.separator {
  color: #ddd;
}

.video-stats {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #666;
  margin: 0;
}

.video-stats span {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 关注按钮 */
.follow-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 24px;
  background: #409eff;
  color: #fff;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  align-self: flex-start;
  margin-top: 8px;
}

.follow-btn:hover {
  background: #66b1ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.follow-btn.following {
  background: #f0f0f0;
  color: #666;
}

.follow-btn.following:hover {
  background: #e0e0e0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.follow-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.follow-icon {
  font-size: 16px;
  line-height: 1;
}

.follow-text {
  line-height: 1;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .author-header {
    flex-direction: column;
    text-align: center;
  }

  .author-stats {
    justify-content: center;
  }

  .video-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 16px;
  }
}
</style>
