<script setup>
/**
 * 首页组件
 * 展示视频列表
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api, { searchUsers } from '@/api'

const router = useRouter()
const route = useRoute()

// 视频列表数据
const videos = ref([])
const loading = ref(true)

// 匹配的用户列表（根据关键词搜索）
const matchedUsers = ref([])
const usersLoading = ref(false)

// 搜索和筛选状态
const searchKeyword = ref('')  // 搜索关键词
const activeCategoryId = ref('all')  // 当前选中的分类ID
// 搜索结果类型：'video' | 'user'
const activeSearchType = ref('video')

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
 * 根据关键词搜索用户（用户名 / 昵称）
 */
const fetchUsers = async () => {
  // 仅在有关键字时搜索用户，避免无意义请求
  const keyword = searchKeyword.value.trim()
  if (!keyword) {
    matchedUsers.value = []
    return
  }

  usersLoading.value = true
  try {
    const response = await searchUsers(keyword, 10)
    matchedUsers.value = response.data.data?.list || []
  } catch (error) {
    console.error('搜索用户失败:', error)
    matchedUsers.value = []
  } finally {
    usersLoading.value = false
  }
}

/**
 * 处理导航栏搜索事件
 */
const handleNavbarSearch = (event) => {
  searchKeyword.value = event.detail.keyword
  // 新搜索默认展示视频结果
  activeSearchType.value = 'video'
  fetchVideos()
  fetchUsers()
}

/**
 * 处理导航栏分类筛选事件
 */
const handleNavbarCategoryChange = (event) => {
  activeCategoryId.value = event.detail.categoryId
  fetchVideos()
}

/**
 * 跳转到视频详情页
 */
const goToVideo = (videoId) => {
  router.push(`/video/${videoId}`)
}

/**
 * 跳转到上传页面
 */
const goToUpload = () => {
  router.push('/upload')
}

/**
 * 跳转到作者主页
 */
const goToAuthor = (userId) => {
  router.push(`/author/${userId}`)
}

/**
 * 格式化播放量显示（B站风格）
 * 例如：1234 -> 1.2千, 12345 -> 1.2万
 */
const formatViewCount = (count) => {
  if (count >= 100000000) {
    return (count / 100000000).toFixed(1) + '亿'
  } else if (count >= 10000) {
    return (count / 10000).toFixed(1) + '万'
  } else if (count >= 1000) {
    return (count / 1000).toFixed(1) + '千'
  }
  return count.toString()
}

// 页面加载时获取视频列表
onMounted(() => {
  // 从 URL 参数中获取搜索关键词和分类
  if (route.query.keyword) {
    searchKeyword.value = route.query.keyword
  }
  if (route.query.category_id) {
    activeCategoryId.value = route.query.category_id
  }
  
  fetchVideos()
  fetchUsers()
  
  // 监听来自 NavBar 的事件
  window.addEventListener('navbar-search', handleNavbarSearch)
  window.addEventListener('navbar-category-change', handleNavbarCategoryChange)
})

// 组件卸载时移除事件监听
onUnmounted(() => {
  window.removeEventListener('navbar-search', handleNavbarSearch)
  window.removeEventListener('navbar-category-change', handleNavbarCategoryChange)
})
</script>

<template>
  <div class="home-container">
    <!-- 内容区域 -->
    <main class="content">

      <!-- 关键词存在时，显示“视频/用户”结果类型切换 -->
      <div v-if="searchKeyword.trim()" class="search-toggle-bar">
        <span class="search-label">搜索结果：</span>
        <button
          class="search-type-btn"
          :class="{ active: activeSearchType === 'video' }"
          @click="activeSearchType = 'video'"
        >
          视频
        </button>
        <button
          class="search-type-btn"
          :class="{ active: activeSearchType === 'user' }"
          @click="activeSearchType = 'user'"
        >
          用户
        </button>
      </div>

      <!-- 关键词匹配的用户列表 -->
      <section v-if="searchKeyword.trim() && activeSearchType === 'user'" class="user-result-section">
        <header class="user-result-header">
          <h2 class="section-title">相关用户</h2>
          <span class="section-subtitle">
            {{ matchedUsers.length > 0 ? `找到 ${matchedUsers.length} 位相关用户` : '暂无匹配用户' }}
          </span>
        </header>

        <div v-if="usersLoading" class="loading-state small">
          <p>正在搜索用户...</p>
        </div>
        <div v-else-if="matchedUsers.length === 0" class="empty-state small">
          <p>没有找到相关用户</p>
        </div>
        <div v-else class="user-result-list">
          <div
            v-for="user in matchedUsers"
            :key="user.id"
            class="user-card"
            @click="goToAuthor(user.id)"
          >
            <img
              class="user-avatar"
              :src="user.avatar_url || 'https://via.placeholder.com/48'"
              :alt="user.nickname || user.username"
              @error="(e) => e.target.src = 'https://via.placeholder.com/48'"
            />
            <div class="user-info">
              <div class="user-name-row">
                <span class="user-nickname">{{ user.nickname || '用户' }}</span>
                <span class="user-username">学号：{{ user.username }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 视频结果区域：在没有关键词时，或选择“视频”模式时展示 -->
      <section v-if="!searchKeyword.trim() || activeSearchType === 'video'">
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
            <div class="card-cover">
              <img :src="video.cover_url" :alt="video.title" />
              <!-- 视频时长（右下角） -->
              <div class="duration-badge">12:30</div>
              <!-- 播放量（左下角，带渐变背景） -->
              <div class="stats-overlay">
                <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M4 3l8 5-8 5V3z"/>
                </svg>
                <span>{{ formatViewCount(video.view_count || 0) }}</span>
              </div>
            </div>
            <!-- 视频信息 -->
            <div class="card-info">
              <h3 class="card-title">{{ video.title }}</h3>
              <div class="card-meta">
                <svg class="up-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M8 2C4.69 2 2 4.69 2 8s2.69 6 6 6 6-2.69 6-6-2.69-6-6-6zm1 9H7V7h2v4zm0-5H7V5h2v1z"/>
                </svg>
                <span class="author">{{ video.author?.nickname || '未知作者' }}</span>
                <span class="separator">·</span>
                <span class="category">{{ video.category?.name || '未分类' }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
/* ==================== 页面容器 ==================== */
.home-container {
  min-height: 100vh;
  background-color: #f4f5f7;
}

/* ==================== 内容区域 ==================== */
.content {
  padding: 20px 40px 32px;
  max-width: 1800px;
  margin: 0 auto;
}

/* 搜索结果类型切换条 */
.search-toggle-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.search-label {
  font-size: 14px;
  color: #666;
}

.search-type-btn {
  padding: 4px 12px;
  font-size: 13px;
  border-radius: 999px;
  border: 1px solid transparent;
  background: #f5f5f5;
  color: #666;
  cursor: pointer;
  transition: all 0.2s ease;
}

.search-type-btn:hover {
  background: #e9e9e9;
}

.search-type-btn.active {
  background: #FF5252;
  color: #fff;
  border-color: #FF5252;
  box-shadow: 0 0 0 1px rgba(255, 82, 82, 0.2);
}

/* ==================== 用户搜索结果区域 ==================== */
.user-result-section {
  margin-bottom: 16px;
  padding: 16px 20px;
  background: #ffffff;
  border-radius: 10px;
  box-shadow: 0 4px 18px rgba(15, 23, 42, 0.04);
}

.user-result-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 12px;
}

.section-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #18191C;
}

.section-subtitle {
  font-size: 13px;
  color: #8c8c8c;
}

.user-result-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 999px;
  background: #f5f5f5;
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-card:hover {
  background: rgba(255, 82, 82, 0.06);
  box-shadow: 0 2px 10px rgba(255, 82, 82, 0.08);
  transform: translateY(-1px);
}

.user-card .user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #ffffff;
  box-shadow: 0 0 0 1px rgba(255, 82, 82, 0.35);
}

.user-card .user-info {
  display: flex;
  flex-direction: column;
}

.user-name-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.user-nickname {
  font-size: 14px;
  font-weight: 600;
  color: #18191C;
}

.user-username {
  font-size: 12px;
  color: #8c8c8c;
}

/* ==================== 加载和空状态 ==================== */
.loading-state,
.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: #999;
  font-size: 15px;
}

.loading-state.small,
.empty-state.small {
  padding: 24px 8px;
}

.loading-state::before {
  content: '';
  display: block;
  width: 40px;
  height: 40px;
  margin: 0 auto 16px;
  border: 3px solid #f1f2f3;
  border-top-color: #FF5252;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state .btn {
  margin-top: 20px;
}

/* ==================== 视频网格布局 - Bilibili 高密度风格 ==================== */
.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 20px 14px;
  padding: 0;
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

/* ==================== 视频卡片 - Bilibili 风格 ==================== */
.video-card {
  background: transparent;
  border-radius: 6px;
  overflow: visible;
  cursor: pointer;
  transition: all 0.25s ease;
}

.video-card:hover {
  transform: translateY(-4px);
}

.video-card:hover .card-cover {
  box-shadow: 0 8px 20px rgba(255, 82, 82, 0.12);
}

/* ==================== 封面区域 ==================== */
.card-cover {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  background: linear-gradient(135deg, #f8f8f8 0%, #f1f2f3 100%);
  border-radius: 6px;
  overflow: hidden;
}

.card-cover img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.video-card:hover .card-cover img {
  transform: scale(1.05);
}

/* 视频时长标签（右下角） */
.duration-badge {
  position: absolute;
  bottom: 6px;
  right: 6px;
  padding: 2px 6px;
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  font-size: 11px;
  font-weight: 500;
  border-radius: 4px;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

/* 播放量覆盖层（左下角） */
.stats-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 8px 6px 6px 6px;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.6), transparent);
  color: #fff;
  font-size: 11px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.stats-overlay svg {
  width: 14px;
  height: 14px;
  opacity: 0.95;
}

/* ==================== 信息区域 ==================== */
.card-info {
  padding-top: 8px;
}

.card-title {
  font-size: 14px;
  font-weight: 500;
  color: #18191C;
  margin: 0 0 6px 0;
  line-height: 1.4;
  /* 超出两行显示省略号 */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  transition: color 0.2s ease;
}

.video-card:hover .card-title {
  color: #FF5252;
}

/* 元数据区域 */
.card-meta {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

.card-meta .up-icon {
  width: 15px;
  height: 15px;
  margin-right: 2px;
  color: #909399;
  flex-shrink: 0;
  transition: color 0.2s ease;
}

.video-card:hover .card-meta .up-icon {
  color: #FF5252;
}

.card-meta .author {
  max-width: 110px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color 0.2s ease;
}

.video-card:hover .card-meta .author {
  color: #606266;
}

.card-meta .separator {
  margin: 0 4px;
  color: #DCDFE6;
}

.card-meta .category {
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 2px 8px;
  background: #f1f2f3;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.video-card:hover .card-meta .category {
  background: rgba(255, 82, 82, 0.08);
  color: #FF5252;
}

/* ==================== 响应式设计 - Bilibili 风格 ==================== */

/* 超大屏幕 (1920px+): 6-7列 */
@media (min-width: 1920px) {
  .video-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 22px 16px;
  }
  
  .content {
    max-width: 2000px;
    padding: 20px 60px 32px;
  }
}

/* 大屏幕 (1600px-1919px): 5-6列 */
@media (min-width: 1600px) and (max-width: 1919px) {
  .video-grid {
    grid-template-columns: repeat(auto-fill, minmax(235px, 1fr));
    gap: 20px 14px;
  }
}

/* 标准屏幕 (1200px-1599px): 4-5列 */
@media (max-width: 1599px) {
  .video-grid {
    grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
    gap: 18px 12px;
  }
  
  .content {
    padding: 20px 32px 32px;
  }
}

/* 平板横屏 (768px-1199px): 3-4列 */
@media (max-width: 1024px) {
  .video-grid {
    grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
    gap: 16px 10px;
  }
  
  .content {
    padding: 16px 24px 24px;
  }
}

@media (max-width: 1024px) {
  .dynamic-search-box.focus {
    width: 400px;
  }
}

@media (max-width: 768px) {
  .content {
    padding: 16px 12px 20px;
  }

  .video-grid {
    grid-template-columns: repeat(auto-fill, minmax(165px, 1fr));
    gap: 14px 8px;
  }
}

/* 移动端 (<=600px): 双列布局 */
@media (max-width: 600px) {
  .content {
    padding: 12px 10px 16px;
  }

  .video-grid {
    grid-template-columns: repeat(2, minmax(155px, 1fr));
    gap: 12px 8px;
  }

  .card-title {
    font-size: 12px;
    -webkit-line-clamp: 2;
  }

  .card-meta {
    font-size: 10px;
  }

  .card-meta .up-icon {
    width: 12px;
    height: 12px;
  }

  .duration-badge {
    font-size: 10px;
    padding: 1px 4px;
  }

  .stats-overlay {
    font-size: 10px;
    padding: 6px 4px 4px 4px;
  }

  .stats-overlay svg {
    width: 12px;
    height: 12px;
  }
}

/* 超小屏幕 (<=400px): 优化双列显示 */
@media (max-width: 400px) {
  .content {
    padding: 10px 8px 12px;
  }

  .video-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px 6px;
  }

  .card-cover {
    border-radius: 4px;
  }
  
  .card-title {
    font-size: 11px;
  }
  
  .card-meta {
    font-size: 9px;
  }
}
</style>
