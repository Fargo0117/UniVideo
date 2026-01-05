<script setup>
/**
 * 视频详情页组件
 * 包含 ArtPlayer 视频播放器（含弹幕）、信息展示、点赞功能、收藏功能、评论区
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api'
import Artplayer from 'artplayer'
import artplayerPluginDanmuku from 'artplayer-plugin-danmuku'

const route = useRoute()
const router = useRouter()

// ==================== 数据定义 ====================

// 视频数据
const video = ref(null)
const loading = ref(true)
const error = ref(null)

// 点赞状态
const liked = ref(false)
const likesCount = ref(0)
const likeLoading = ref(false)

// 收藏状态
const collected = ref(false)
const collectionsCount = ref(0)
const collectLoading = ref(false)

// 评论数据
const comments = ref([])
const commentsLoading = ref(false)
const commentContent = ref('')
const commentSubmitting = ref(false)

// 回复相关
const replyingTo = ref(null) // 正在回复的评论对象
const replyContent = ref('')
const replySubmitting = ref(false)

// 当前用户ID
const currentUserId = localStorage.getItem('user_id')

// ArtPlayer 实例
const art = ref(null)

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
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// ==================== 评论树结构处理 ====================

/**
 * 将评论列表转换为树状结构
 * 一级评论（root_id=null）作为根节点，其他评论按 root_id 分组挂载
 */
const commentTree = computed(() => {
  if (!comments.value.length) return []
  
  // 分离一级评论和回复
  const rootComments = []
  const repliesMap = {} // { root_id: [replies] }
  
  comments.value.forEach(comment => {
    if (comment.root_id === null) {
      // 一级评论
      rootComments.push({ ...comment, replies: [] })
    } else {
      // 回复评论，按 root_id 分组
      if (!repliesMap[comment.root_id]) {
        repliesMap[comment.root_id] = []
      }
      repliesMap[comment.root_id].push(comment)
    }
  })
  
  // 将回复挂载到对应的一级评论下
  rootComments.forEach(root => {
    root.replies = repliesMap[root.id] || []
  })
  
  return rootComments
})

// ==================== API 调用 ====================

/**
 * 获取视频详情
 */
const fetchVideo = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await api.get(`/videos/${route.params.id}`)
    video.value = response.data.data
    likesCount.value = video.value.likes_count || 0
    collectionsCount.value = video.value.collections_count || 0
  } catch (err) {
    error.value = err.response?.data?.msg || '获取视频详情失败'
    console.error('获取视频详情失败:', err)
  } finally {
    loading.value = false
  }
}

/**
 * 获取当前用户的点赞状态
 * 进入页面时检查用户是否已点赞该视频
 */
const fetchLikeStatus = async () => {
  // 未登录用户不需要检查点赞状态
  if (!currentUserId) return
  
  try {
    const response = await api.get(`/videos/${route.params.id}/like/status`, {
      params: { user_id: currentUserId }
    })
    liked.value = response.data.data?.liked || false
  } catch (err) {
    console.error('获取点赞状态失败:', err)
    liked.value = false
  }
}

/**
 * 获取当前用户的收藏状态
 * 进入页面时检查用户是否已收藏该视频
 */
const fetchCollectStatus = async () => {
  // 未登录用户不需要检查收藏状态
  if (!currentUserId) return
  
  try {
    const response = await api.get(`/videos/${route.params.id}/collect/status`, {
      params: { user_id: currentUserId }
    })
    collected.value = response.data.data?.collected || false
  } catch (err) {
    console.error('获取收藏状态失败:', err)
    collected.value = false
  }
}

/**
 * 获取评论列表
 */
const fetchComments = async () => {
  commentsLoading.value = true
  try {
    const response = await api.get(`/videos/${route.params.id}/comments`)
    comments.value = response.data.data?.list || []
  } catch (err) {
    console.error('获取评论失败:', err)
    comments.value = []
  } finally {
    commentsLoading.value = false
  }
}

/**
 * 点赞/取消点赞
 */
const toggleLike = async () => {
  if (!currentUserId) {
    alert('请先登录')
    router.push('/login')
    return
  }
  
  likeLoading.value = true
  try {
    const response = await api.post(`/videos/${route.params.id}/like`, {
      user_id: currentUserId
    })
    liked.value = response.data.data.liked
    likesCount.value = response.data.data.likes_count
  } catch (err) {
    const message = err.response?.data?.msg || '操作失败'
    alert(message)
  } finally {
    likeLoading.value = false
  }
}

/**
 * 收藏/取消收藏
 */
const toggleCollect = async () => {
  if (!currentUserId) {
    alert('请先登录')
    router.push('/login')
    return
  }
  
  collectLoading.value = true
  try {
    const response = await api.post(`/videos/${route.params.id}/collect`, {
      user_id: currentUserId
    })
    collected.value = response.data.data.collected
    collectionsCount.value = response.data.data.collections_count
  } catch (err) {
    const message = err.response?.data?.msg || '操作失败'
    alert(message)
  } finally {
    collectLoading.value = false
  }
}

/**
 * 发表主评论
 */
const submitComment = async () => {
  if (!currentUserId) {
    alert('请先登录')
    router.push('/login')
    return
  }
  
  if (!commentContent.value.trim()) {
    alert('请输入评论内容')
    return
  }
  
  commentSubmitting.value = true
  try {
    await api.post(`/videos/${route.params.id}/comments`, {
      user_id: currentUserId,
      content: commentContent.value.trim()
    })
    commentContent.value = ''
    // 重新获取评论列表
    await fetchComments()
  } catch (err) {
    const message = err.response?.data?.msg || '评论失败'
    alert(message)
  } finally {
    commentSubmitting.value = false
  }
}

/**
 * 打开回复输入框
 * @param {Object} comment - 要回复的评论对象
 */
const openReply = (comment) => {
  replyingTo.value = comment
  replyContent.value = ''
}

/**
 * 关闭回复输入框
 */
const closeReply = () => {
  replyingTo.value = null
  replyContent.value = ''
}

/**
 * 提交回复
 */
const submitReply = async () => {
  if (!currentUserId) {
    alert('请先登录')
    router.push('/login')
    return
  }
  
  if (!replyContent.value.trim()) {
    alert('请输入回复内容')
    return
  }
  
  replySubmitting.value = true
  try {
    await api.post(`/videos/${route.params.id}/comments`, {
      user_id: currentUserId,
      content: replyContent.value.trim(),
      parent_id: replyingTo.value.id
    })
    closeReply()
    // 重新获取评论列表
    await fetchComments()
  } catch (err) {
    const message = err.response?.data?.msg || '回复失败'
    alert(message)
  } finally {
    replySubmitting.value = false
  }
}

/**
 * 返回首页
 */
const goBack = () => {
  router.push('/')
}

/**
 * 跳转到作者主页
 */
const goToAuthor = () => {
  if (video.value?.author?.id) {
    router.push(`/author/${video.value.author.id}`)
  }
}

/**
 * 初始化 ArtPlayer 播放器
 */
const initPlayer = () => {
  if (!video.value) return
  
  const videoUrl = getFullUrl(video.value.video_path)
  const coverUrl = getFullUrl(video.value.cover_path)
  
  art.value = new Artplayer({
    container: '#artplayer-app',
    url: videoUrl,
    poster: coverUrl,
    title: video.value.title,
    volume: 0.5,
    autoSize: false,
    fullscreen: true,
    fullscreenWeb: true,
    aspectRatio: true,
    plugins: [
      artplayerPluginDanmuku({
        danmuku: async () => {
          // 获取弹幕列表
          try {
            const response = await api.get(`/videos/${route.params.id}/danmaku`)
            return response.data.data || []
          } catch (err) {
            console.error('获取弹幕失败:', err)
            return []
          }
        },
        speed: 5,
        opacity: 1,
        fontSize: 25,
        color: '#FFFFFF',
        mode: 0,
        margin: [10, '25%'],
        antiOverlap: true,
        useWorker: true,
        synchronousPlayback: false,
        lockTime: 5,
        maxLength: 50,
        minWidth: 200,
        maxWidth: 400,
        theme: 'light',
        // 配置发送弹幕的回调函数
        emit: async (danmu) => {
          // 发送弹幕到后端
          try {
            await api.post(`/videos/${route.params.id}/danmaku`, {
              user_id: currentUserId,
              text: danmu.text,
              time: danmu.time,
              color: danmu.color || '#FFFFFF'
            })
          } catch (err) {
            console.error('发送弹幕失败:', err)
            alert('发送弹幕失败，请稍后重试')
          }
        }
      })
    ]
  })
}

/**
 * 销毁 ArtPlayer 实例
 */
const destroyPlayer = () => {
  if (art.value && art.value.destroy) {
    art.value.destroy()
    art.value = null
  }
}

// ==================== 生命周期 ====================

onMounted(async () => {
  await fetchVideo()
  fetchLikeStatus()    // 获取当前用户的点赞状态
  fetchCollectStatus() // 获取当前用户的收藏状态
  fetchComments()
  
  // 视频数据加载完成后初始化播放器
  if (video.value) {
    initPlayer()
  }
})

onUnmounted(() => {
  destroyPlayer()
})
</script>

<template>
  <div class="video-detail-container">
    <!-- 顶部导航 -->
    <header class="nav-bar">
      <button class="back-btn" @click="goBack">&larr; 返回首页</button>
      <span class="site-name">UniVideo</span>
    </header>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <p>加载中...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="goBack">返回首页</button>
    </div>

    <!-- 视频内容 -->
    <main v-else-if="video" class="video-content">
      <!-- ArtPlayer 视频播放器（含弹幕） -->
      <section class="video-player-section">
        <div id="artplayer-app" class="artplayer-container"></div>
      </section>

      <!-- 视频信息区 -->
      <section class="video-info-section">
        <h1 class="video-title">{{ video.title }}</h1>
        
        <div class="video-meta">
          <span class="views">{{ video.view_count || 0 }} 播放</span>
          <span class="separator">·</span>
          <span class="time">{{ formatTime(video.created_at) }}</span>
          <span class="separator">·</span>
          <span class="category">{{ video.category?.name || '未分类' }}</span>
        </div>

        <!-- 作者信息和互动按钮 -->
        <div class="author-like-row">
          <div class="author-info" @click="goToAuthor">
            <img 
              class="author-avatar" 
              :src="getFullUrl(video.author?.avatar) || '/default-avatar.png'" 
              :alt="video.author?.nickname"
              @error="(e) => e.target.src = 'https://via.placeholder.com/40'"
            />
            <span class="author-name">{{ video.author?.nickname || '未知作者' }}</span>
          </div>
          
          <!-- 互动按钮组 -->
          <div class="action-btns">
            <!-- 点赞按钮 -->
            <button 
              class="like-btn"
              :class="{ 'liked': liked }"
              :disabled="likeLoading"
              @click="toggleLike"
            >
              <span class="like-icon">{{ liked ? '❤️' : '🤍' }}</span>
              <span class="like-count">{{ likesCount }}</span>
            </button>
            
            <!-- 收藏按钮 -->
            <button 
              class="collect-btn"
              :class="{ 'collected': collected }"
              :disabled="collectLoading"
              @click="toggleCollect"
            >
              <span class="collect-icon">{{ collected ? '⭐' : '☆' }}</span>
              <span class="collect-count">{{ collectionsCount }}</span>
            </button>
          </div>
        </div>

        <!-- 视频简介 -->
        <div class="video-description" v-if="video.description">
          <h3>简介</h3>
          <p>{{ video.description }}</p>
        </div>
      </section>

      <!-- 评论区 -->
      <section class="comment-section">
        <h2 class="section-title">评论区 ({{ comments.length }})</h2>
        
        <!-- 主评论输入框 -->
        <div class="comment-input-box">
          <textarea
            v-model="commentContent"
            placeholder="发表你的评论..."
            rows="3"
            maxlength="500"
          ></textarea>
          <button 
            class="btn btn-primary"
            :disabled="commentSubmitting || !commentContent.trim()"
            @click="submitComment"
          >
            {{ commentSubmitting ? '发送中...' : '发表评论' }}
          </button>
        </div>

        <!-- 评论列表 -->
        <div v-if="commentsLoading" class="comments-loading">
          <p>加载评论中...</p>
        </div>
        
        <div v-else-if="commentTree.length === 0" class="no-comments">
          <p>暂无评论，快来抢沙发吧！</p>
        </div>

        <div v-else class="comment-list">
          <!-- 一级评论 -->
          <div 
            v-for="comment in commentTree" 
            :key="comment.id" 
            class="comment-item"
          >
            <!-- 评论主体 -->
            <div class="comment-main">
              <img 
                class="comment-avatar" 
                :src="getFullUrl(comment.author?.avatar) || '/default-avatar.png'"
                :alt="comment.author?.nickname"
                @error="(e) => e.target.src = 'https://via.placeholder.com/36'"
              />
              <div class="comment-body">
                <div class="comment-header">
                  <span class="comment-author">{{ comment.author?.nickname || '匿名用户' }}</span>
                  <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
                </div>
                <p class="comment-content">{{ comment.content }}</p>
                <button class="reply-btn" @click="openReply(comment)">回复</button>
              </div>
            </div>

            <!-- 回复输入框（在当前评论下显示） -->
            <div v-if="replyingTo?.id === comment.id" class="reply-input-box">
              <textarea
                v-model="replyContent"
                :placeholder="`回复 @${comment.author?.nickname}...`"
                rows="2"
                maxlength="500"
              ></textarea>
              <div class="reply-actions">
                <button class="btn btn-secondary" @click="closeReply">取消</button>
                <button 
                  class="btn btn-primary"
                  :disabled="replySubmitting || !replyContent.trim()"
                  @click="submitReply"
                >
                  {{ replySubmitting ? '发送中...' : '发送' }}
                </button>
              </div>
            </div>

            <!-- 子评论（回复列表） -->
            <div v-if="comment.replies?.length" class="replies-list">
              <div 
                v-for="reply in comment.replies" 
                :key="reply.id" 
                class="reply-item"
              >
                <img 
                  class="reply-avatar" 
                  :src="getFullUrl(reply.author?.avatar) || '/default-avatar.png'"
                  :alt="reply.author?.nickname"
                  @error="(e) => e.target.src = 'https://via.placeholder.com/28'"
                />
                <div class="reply-body">
                  <div class="reply-header">
                    <span class="reply-author">{{ reply.author?.nickname || '匿名用户' }}</span>
                    <span class="reply-time">{{ formatTime(reply.created_at) }}</span>
                  </div>
                  <p class="reply-content">{{ reply.content }}</p>
                  <button class="reply-btn" @click="openReply(reply)">回复</button>
                </div>
              </div>
              
              <!-- 在回复列表最后显示回复输入框 -->
              <div v-for="reply in comment.replies" :key="'reply-input-' + reply.id">
                <div v-if="replyingTo?.id === reply.id" class="reply-input-box nested">
                  <textarea
                    v-model="replyContent"
                    :placeholder="`回复 @${reply.author?.nickname}...`"
                    rows="2"
                    maxlength="500"
                  ></textarea>
                  <div class="reply-actions">
                    <button class="btn btn-secondary" @click="closeReply">取消</button>
                    <button 
                      class="btn btn-primary"
                      :disabled="replySubmitting || !replyContent.trim()"
                      @click="submitReply"
                    >
                      {{ replySubmitting ? '发送中...' : '发送' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
/* ==================== 全局布局 ==================== */
.video-detail-container {
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

.btn-primary:disabled {
  background-color: #a0cfff;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #f5f5f5;
  color: #666;
}

.btn-secondary:hover {
  background-color: #e8e8e8;
}

/* ==================== 主内容区 ==================== */
.video-content {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

/* 视频播放器 */
.video-player-section {
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 20px;
}

.artplayer-container {
  width: 100%;
  aspect-ratio: 16 / 9;
  max-height: 600px;
  background-color: #000;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ==================== 视频信息区 ==================== */
.video-info-section {
  background: #fff;
  border-radius: 8px;
  padding: 20px 24px;
  margin-bottom: 20px;
}

.video-title {
  font-size: 22px;
  font-weight: 600;
  color: #333;
  margin: 0 0 12px 0;
  line-height: 1.4;
}

.video-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #999;
  margin-bottom: 16px;
}

.separator {
  color: #ddd;
}

.category {
  color: #409eff;
}

/* 作者和互动按钮行 */
.author-like-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: opacity 0.3s;
}

.author-info:hover {
  opacity: 0.7;
}

.author-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  background-color: #f0f0f0;
}

.author-name {
  font-size: 15px;
  font-weight: 500;
  color: #333;
}

/* 互动按钮组 */
.action-btns {
  display: flex;
  gap: 12px;
}

/* 点赞按钮 */
.like-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.like-btn:hover {
  background: #fff0f0;
  border-color: #ffccc7;
}

.like-btn.liked {
  background: #fff0f0;
  border-color: #ff4d4f;
}

.like-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.like-icon {
  font-size: 18px;
}

.like-count {
  font-size: 14px;
  color: #666;
}

/* 收藏按钮 */
.collect-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.collect-btn:hover {
  background: #fffbe6;
  border-color: #ffe58f;
}

.collect-btn.collected {
  background: #fffbe6;
  border-color: #faad14;
}

.collect-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.collect-icon {
  font-size: 18px;
}

.collect-count {
  font-size: 14px;
  color: #666;
}

/* 视频简介 */
.video-description {
  margin-top: 16px;
}

.video-description h3 {
  font-size: 14px;
  color: #999;
  margin: 0 0 8px 0;
}

.video-description p {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin: 0;
  white-space: pre-wrap;
}

/* ==================== 评论区 ==================== */
.comment-section {
  background: #fff;
  border-radius: 8px;
  padding: 20px 24px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0 0 20px 0;
}

/* 评论输入框 */
.comment-input-box {
  margin-bottom: 24px;
}

.comment-input-box textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  resize: vertical;
  box-sizing: border-box;
  margin-bottom: 12px;
}

.comment-input-box textarea:focus {
  outline: none;
  border-color: #409eff;
}

.comment-input-box .btn {
  float: right;
}

.comment-input-box::after {
  content: '';
  display: table;
  clear: both;
}

/* 评论列表 */
.comments-loading,
.no-comments {
  text-align: center;
  padding: 40px 0;
  color: #999;
}

.comment-list {
  border-top: 1px solid #f0f0f0;
  padding-top: 16px;
}

/* 单条评论 */
.comment-item {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f5f5f5;
}

.comment-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.comment-main {
  display: flex;
  gap: 12px;
}

.comment-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  background-color: #f0f0f0;
}

.comment-body {
  flex: 1;
  min-width: 0;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
}

.comment-author {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.comment-time {
  font-size: 12px;
  color: #999;
}

.comment-content {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
  margin: 0 0 8px 0;
  word-break: break-word;
}

.reply-btn {
  background: none;
  border: none;
  color: #999;
  font-size: 12px;
  cursor: pointer;
  padding: 0;
}

.reply-btn:hover {
  color: #409eff;
}

/* 回复输入框 */
.reply-input-box {
  margin: 12px 0 12px 48px;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 8px;
}

.reply-input-box.nested {
  margin-left: 40px;
}

.reply-input-box textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 13px;
  resize: none;
  box-sizing: border-box;
}

.reply-input-box textarea:focus {
  outline: none;
  border-color: #409eff;
}

.reply-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}

.reply-actions .btn {
  padding: 6px 12px;
  font-size: 13px;
}

/* 回复列表 */
.replies-list {
  margin-left: 48px;
  margin-top: 12px;
  padding-left: 12px;
  border-left: 2px solid #f0f0f0;
}

.reply-item {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.reply-item:last-child {
  margin-bottom: 0;
}

.reply-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  background-color: #f0f0f0;
}

.reply-body {
  flex: 1;
  min-width: 0;
}

.reply-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.reply-author {
  font-size: 13px;
  font-weight: 500;
  color: #333;
}

.reply-time {
  font-size: 11px;
  color: #999;
}

.reply-content {
  font-size: 13px;
  color: #333;
  line-height: 1.5;
  margin: 0 0 6px 0;
  word-break: break-word;
}
</style>
