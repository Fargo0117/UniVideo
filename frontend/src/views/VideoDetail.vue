<script setup>
/**
 * 视频详情页组件
 * 包含 ArtPlayer 视频播放器（含弹幕）、信息展示、点赞功能、收藏功能、评论区
 */
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api, { followUser, unfollowUser, getFollowStatus } from '@/api'
import Artplayer from 'artplayer'
import artplayerPluginDanmuku from 'artplayer-plugin-danmuku'

const route = useRoute()
const router = useRouter()

// ==================== 数据定义 ====================

// 视频数据
const video = ref(null)
const loading = ref(true)
const error = ref(null)

// 推荐视频列表
const relatedVideos = ref([])
const relatedLoading = ref(false)

// 点赞状态
const liked = ref(false)
const likesCount = ref(0)
const likeLoading = ref(false)

// 收藏状态
const collected = ref(false)
const collectionsCount = ref(0)
const collectLoading = ref(false)

// 关注状态
const isFollowing = ref(false)
const followLoading = ref(false)

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
    
    // 获取视频详情后，立即获取推荐视频
    if (video.value.category_id) {
      fetchRelatedVideos(video.value.category_id)
    }
  } catch (err) {
    error.value = err.response?.data?.msg || '获取视频详情失败'
    console.error('获取视频详情失败:', err)
  } finally {
    loading.value = false
  }
}

/**
 * 获取同分类推荐视频
 * @param {number} categoryId - 分类ID
 */
const fetchRelatedVideos = async (categoryId) => {
  relatedLoading.value = true
  try {
    const response = await api.get('/videos/list', { 
      params: { 
        category_id: categoryId
      } 
    })
    // 过滤掉当前视频，取前10个
    const videoList = response.data.data || []
    relatedVideos.value = videoList
      .filter(v => v.id !== parseInt(route.params.id))
      .slice(0, 10)
  } catch (err) {
    console.error('获取推荐视频失败:', err)
    relatedVideos.value = []
  } finally {
    relatedLoading.value = false
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
 * 获取当前用户对UP主的关注状态
 * 进入页面时检查用户是否已关注该UP主
 */
const fetchFollowStatus = async () => {
  // 未登录用户不需要检查关注状态
  if (!currentUserId) return
  // 不能关注自己
  if (!video.value?.author?.id || video.value.author.id == currentUserId) return
  
  try {
    const response = await getFollowStatus(video.value.author.id, currentUserId)
    isFollowing.value = response.data.data?.is_following || false
  } catch (err) {
    console.error('获取关注状态失败:', err)
    isFollowing.value = false
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
 * 关注/取消关注UP主
 */
const toggleFollow = async () => {
  if (!currentUserId) {
    alert('请先登录')
    router.push('/login')
    return
  }
  
  if (!video.value?.author?.id) {
    alert('UP主信息加载失败')
    return
  }
  
  followLoading.value = true
  try {
    if (isFollowing.value) {
      // 取消关注
      const response = await unfollowUser(video.value.author.id, currentUserId)
      if (response.data.code === 200) {
        isFollowing.value = false
        alert('取消关注成功')
      }
    } else {
      // 关注
      const response = await followUser(video.value.author.id, currentUserId)
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
 * 跳转到推荐视频
 * @param {number} videoId - 视频ID
 */
const goToVideo = (videoId) => {
  router.push(`/video/${videoId}`)
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

/**
 * 初始化页面数据
 */
const initPageData = async () => {
  // 销毁旧的播放器实例
  destroyPlayer()
  
  // 重置状态
  liked.value = false
  collected.value = false
  isFollowing.value = false
  comments.value = []
  relatedVideos.value = []
  
  // 加载新数据
  await fetchVideo()
  fetchLikeStatus()    // 获取当前用户的点赞状态
  fetchCollectStatus() // 获取当前用户的收藏状态
  fetchFollowStatus()  // 获取当前用户对UP主的关注状态
  fetchComments()
  
  // 视频数据加载完成后初始化播放器
  if (video.value) {
    initPlayer()
  }
}

onMounted(() => {
  initPageData()
})

onUnmounted(() => {
  destroyPlayer()
})

// 监听路由变化，支持点击推荐视频刷新页面
watch(() => route.params.id, (newId, oldId) => {
  if (newId && newId !== oldId) {
    initPageData()
  }
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
      <!-- 左侧主内容 -->
      <div class="left-column">
        <!-- 视频信息头 -->
        <section class="video-header">
          <h1 class="video-title">{{ video.title }}</h1>
          <div class="video-data">
            <span class="data-item">
              <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
              </svg>
              {{ video.view_count || 0 }}
            </span>
            <span class="data-item">
              <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14l4 4V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/>
              </svg>
              {{ comments.length }}
            </span>
            <span class="data-item date">{{ formatTime(video.created_at) }}</span>
          </div>
        </section>

        <!-- ArtPlayer 视频播放器 -->
        <section class="player-wrapper">
          <div id="artplayer-app" class="artplayer-container"></div>
        </section>

        <!-- 工具栏：点赞、收藏、分享 -->
        <section class="video-toolbar">
          <button 
            class="toolbar-btn like-btn"
            :class="{ 'active': liked }"
            :disabled="likeLoading"
            @click="toggleLike"
          >
            <span class="icon">{{ liked ? '❤️' : '🤍' }}</span>
            <span class="text">{{ liked ? '已点赞' : '点赞' }}</span>
            <span class="count">{{ likesCount }}</span>
          </button>
          
          <button 
            class="toolbar-btn collect-btn"
            :class="{ 'active': collected }"
            :disabled="collectLoading"
            @click="toggleCollect"
          >
            <span class="icon">{{ collected ? '⭐' : '☆' }}</span>
            <span class="text">{{ collected ? '已收藏' : '收藏' }}</span>
            <span class="count">{{ collectionsCount }}</span>
          </button>

          <button class="toolbar-btn share-btn">
            <span class="icon">🔗</span>
            <span class="text">分享</span>
          </button>
        </section>

        <!-- 视频简介 -->
        <section class="video-desc" v-if="video.description">
          <h3 class="desc-title">视频简介</h3>
          <p class="desc-content">{{ video.description }}</p>
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
      </div>

      <!-- 右侧推荐区 -->
      <aside class="right-column">
        <!-- UP主卡片 -->
        <div class="uploader-card">
          <div class="uploader-main">
            <div class="uploader-left" @click="goToAuthor">
              <img 
                class="uploader-avatar" 
                :src="getFullUrl(video.author?.avatar) || '/default-avatar.png'" 
                :alt="video.author?.nickname"
                @error="(e) => e.target.src = 'https://via.placeholder.com/50'"
              />
              <div class="uploader-info">
                <div class="uploader-name">{{ video.author?.nickname || '未知作者' }}</div>
                <div class="uploader-bio">{{ video.author?.bio || '这个UP主很懒，什么都没有留下' }}</div>
              </div>
            </div>
            <button 
              class="follow-btn" 
              :class="{ 'following': isFollowing }"
              v-if="currentUserId && currentUserId != video.author?.id"
              :disabled="followLoading"
              @click="toggleFollow"
            >
              <span class="follow-icon">{{ isFollowing ? '✓' : '+' }}</span>
              <span class="follow-text">{{ isFollowing ? '已关注' : '关注' }}</span>
            </button>
          </div>
        </div>

        <!-- 推荐视频列表 -->
        <div class="rec-list">
          <h3 class="rec-title">相关推荐</h3>
          
          <div v-if="relatedLoading" class="rec-loading">
            <p>加载中...</p>
          </div>
          
          <div v-else-if="relatedVideos.length === 0" class="rec-empty">
            <p>暂无推荐</p>
          </div>
          
          <div v-else class="rec-items">
            <div 
              v-for="item in relatedVideos" 
              :key="item.id"
              class="rec-item"
              @click="goToVideo(item.id)"
            >
              <div class="rec-cover">
                <img 
                  :src="getFullUrl(item.cover_path)" 
                  :alt="item.title"
                  @error="(e) => e.target.src = 'https://via.placeholder.com/140x79'"
                />
                <div class="rec-duration" v-if="item.duration">
                  {{ item.duration }}
                </div>
              </div>
              <div class="rec-info">
                <h4 class="rec-item-title">{{ item.title }}</h4>
                <div class="rec-author">{{ item.author?.nickname || '未知' }}</div>
                <div class="rec-stats">
                  <span>{{ item.view_count || 0 }} 播放</span>
                  <span>·</span>
                  <span>{{ item.danmaku_count || 0 }} 弹幕</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </main>
  </div>
</template>

<style scoped>
/* ==================== 全局布局 - Bilibili 风格 ==================== */
.video-detail-container {
  min-height: 100vh;
  background: #F4F5F7;
}

/* ==================== 导航栏 - 磨砂玻璃 ==================== */
.nav-bar {
  display: flex;
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
}

.back-btn {
  background: none;
  border: none;
  color: var(--primary-color, #FF5252);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: rgba(255, 82, 82, 0.1);
  transform: translateX(-4px);
}

.site-name {
  margin-left: 16px;
  font-size: 22px;
  font-weight: 700;
  background: linear-gradient(135deg, #FF5252 0%, #FF7070 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
}

/* ==================== 加载/错误状态 ==================== */
.loading-state,
.error-state {
  text-align: center;
  padding: 100px 20px;
  color: var(--text-tertiary, #999);
  font-size: 16px;
}

.loading-state::before {
  content: '';
  display: inline-block;
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 82, 82, 0.1);
  border-top-color: var(--primary-color, #FF5252);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ==================== 按钮样式 - Bilibili 风格 ==================== */
.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn:active {
  transform: scale(0.98);
}

.btn-primary {
  background: #00AEEC;
  color: #fff;
  box-shadow: none;
}

.btn-primary:hover {
  background: #00A0DD;
  box-shadow: 0 2px 6px rgba(0, 174, 236, 0.3);
}

.btn-primary:disabled {
  background: #E3E5E7;
  color: #C9CCD0;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

.btn-secondary {
  background: #fff;
  color: #18191C;
  border: 1px solid #E3E5E7;
}

.btn-secondary:hover {
  background: #F6F7F8;
  border-color: #C9CCD0;
}

/* ==================== 主内容区 - Grid布局 ==================== */
.video-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 32px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 350px;
  gap: 30px;
  align-items: start;
}

/* ==================== 左侧主内容列 ==================== */
.left-column {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ==================== 视频信息头 - Bilibili 风格 ==================== */
.video-header {
  background: #fff;
  border-radius: 4px;
  padding: 16px 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.video-title {
  font-size: 20px;
  font-weight: 500;
  color: #18191C;
  margin: 0 0 12px 0;
  line-height: 1.5;
  letter-spacing: 0;
}

.video-data {
  display: flex;
  align-items: center;
  gap: 0;
  font-size: 12px;
  color: #9499A0;
  margin: 0;
}

.data-item {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-right: 20px;
}

.data-item:last-child {
  margin-right: 0;
}

.data-item .icon {
  width: 16px;
  height: 16px;
  opacity: 0.7;
}

.data-item.date {
  margin-left: auto;
}

/* ==================== 播放器容器 - Bilibili 风格 ==================== */
.player-wrapper {
  background: #000;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.artplayer-container {
  width: 100%;
  aspect-ratio: 16 / 9;
  background-color: #000;
}

/* ==================== 视频工具栏 - Bilibili 风格 ==================== */
.video-toolbar {
  background: #fff;
  border-radius: 4px;
  padding: 0 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  display: flex;
  gap: 0;
  border-bottom: 1px solid #E3E5E7;
}

.toolbar-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 16px;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #18191C;
  font-size: 14px;
  position: relative;
}

.toolbar-btn::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 2px;
  background: #00AEEC;
  transition: width 0.2s ease;
}

.toolbar-btn:hover {
  color: #00AEEC;
}

.toolbar-btn:hover::after {
  width: 60%;
}

.toolbar-btn.active {
  color: #00AEEC;
  font-weight: 500;
}

.toolbar-btn.active::after {
  width: 60%;
}

.toolbar-btn .icon {
  font-size: 18px;
}

.toolbar-btn .text {
  font-size: 14px;
  font-weight: inherit;
}

.toolbar-btn .count {
  font-size: 13px;
  color: #9499A0;
  margin-left: 2px;
}

.toolbar-btn.like-btn:hover,
.toolbar-btn.like-btn.active {
  color: #FB7299;
}

.toolbar-btn.like-btn:hover::after,
.toolbar-btn.like-btn.active::after {
  background: #FB7299;
}

.toolbar-btn.collect-btn:hover,
.toolbar-btn.collect-btn.active {
  color: #FFA500;
}

.toolbar-btn.collect-btn:hover::after,
.toolbar-btn.collect-btn.active::after {
  background: #FFA500;
}

.toolbar-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toolbar-btn:disabled:hover {
  color: #18191C;
}

.toolbar-btn:disabled::after {
  width: 0 !important;
}

/* ==================== 视频简介 - Bilibili 风格 ==================== */
.video-desc {
  background: #fff;
  border-radius: 4px;
  padding: 16px 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.desc-title {
  font-size: 14px;
  font-weight: 500;
  color: #18191C;
  margin: 0 0 12px 0;
  padding-bottom: 12px;
  border-bottom: 1px solid #E3E5E7;
}

.desc-content {
  font-size: 13px;
  color: #18191C;
  line-height: 1.8;
  margin: 0;
  white-space: pre-wrap;
}

/* ==================== 评论区 - Bilibili 风格 ==================== */
.comment-section {
  background: #fff;
  border-radius: 4px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.section-title {
  font-size: 16px;
  font-weight: 500;
  color: #18191C;
  margin: 0 0 16px 0;
  padding-bottom: 12px;
  border-bottom: 1px solid #E3E5E7;
}

/* ==================== 评论输入框 - Bilibili 风格 ==================== */
.comment-input-box {
  margin-bottom: 24px;
}

.comment-input-box textarea {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #E3E5E7;
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.6;
  resize: vertical;
  box-sizing: border-box;
  margin-bottom: 10px;
  transition: all 0.2s ease;
  font-family: inherit;
  background: #F6F7F8;
}

.comment-input-box textarea:hover {
  border-color: #C9CCD0;
  background: #fff;
}

.comment-input-box textarea:focus {
  outline: none;
  border-color: #00AEEC;
  box-shadow: 0 0 0 2px rgba(0, 174, 236, 0.1);
  background: #fff;
}

.comment-input-box .btn {
  float: right;
}

.comment-input-box::after {
  content: '';
  display: table;
  clear: both;
}

/* ==================== 评论列表 ==================== */
.comments-loading,
.no-comments {
  text-align: center;
  padding: 60px 0;
  color: var(--text-tertiary, #999);
  font-size: 15px;
}

.comment-list {
  padding-top: 24px;
}

/* ==================== 单条评论 - Bilibili 风格 ==================== */
.comment-item {
  margin-bottom: 20px;
  padding: 16px 0;
  background: transparent;
  border-bottom: 1px solid #E3E5E7;
  transition: all 0.2s ease;
}

.comment-item:last-child {
  margin-bottom: 0;
  border-bottom: none;
}

.comment-main {
  display: flex;
  gap: 16px;
}

.comment-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  background: linear-gradient(135deg, #f0f0f0 0%, #e8e8e8 100%);
}

.comment-body {
  flex: 1;
  min-width: 0;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.comment-author {
  font-size: 13px;
  font-weight: 500;
  color: #18191C;
}

.comment-time {
  font-size: 12px;
  color: #9499A0;
}

.comment-content {
  font-size: 13px;
  color: #18191C;
  line-height: 1.8;
  margin: 0 0 10px 0;
  word-break: break-word;
}

.reply-btn {
  background: none;
  border: none;
  color: #9499A0;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  padding: 4px 10px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.reply-btn:hover {
  color: #00AEEC;
  background: rgba(0, 174, 236, 0.08);
}

/* ==================== 回复输入框 - Bilibili 风格 ==================== */
.reply-input-box {
  margin: 12px 0 0 48px;
  padding: 12px;
  background: #F6F7F8;
  border-radius: 4px;
  border: 1px solid #E3E5E7;
}

.reply-input-box.nested {
  margin-left: 40px;
}

.reply-input-box textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #E3E5E7;
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.6;
  resize: none;
  box-sizing: border-box;
  transition: all 0.2s ease;
  font-family: inherit;
  background: #fff;
}

.reply-input-box textarea:focus {
  outline: none;
  border-color: #00AEEC;
  box-shadow: 0 0 0 2px rgba(0, 174, 236, 0.1);
}

.reply-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 10px;
}

.reply-actions .btn {
  padding: 6px 14px;
  font-size: 12px;
}

/* ==================== 回复列表 - Bilibili 风格 ==================== */
.replies-list {
  margin-left: 48px;
  margin-top: 12px;
  padding-left: 16px;
  border-left: 2px solid #E3E5E7;
}

.reply-item {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
  padding: 10px 0;
  border-radius: 0;
  transition: all 0.2s ease;
}

.reply-item:last-child {
  margin-bottom: 0;
}

.reply-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  background: linear-gradient(135deg, #f0f0f0 0%, #e8e8e8 100%);
}

.reply-body {
  flex: 1;
  min-width: 0;
}

.reply-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.reply-author {
  font-size: 12px;
  font-weight: 500;
  color: #18191C;
}

.reply-time {
  font-size: 11px;
  color: #9499A0;
}

.reply-content {
  font-size: 12px;
  color: #18191C;
  line-height: 1.7;
  margin: 0 0 6px 0;
  word-break: break-word;
}

/* ==================== 右侧推荐列 ==================== */
.right-column {
  position: sticky;
  top: 80px;
  max-height: calc(100vh - 96px);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 优化滚动条样式 */
.right-column::-webkit-scrollbar {
  width: 6px;
}

.right-column::-webkit-scrollbar-track {
  background: transparent;
}

.right-column::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.right-column::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.2);
}

/* ==================== UP主卡片 - Bilibili 风格 ==================== */
.uploader-card {
  background: #fff;
  border-radius: 4px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.uploader-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.uploader-left {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  flex: 1;
  min-width: 0;
  transition: opacity 0.2s ease;
}

.uploader-left:hover {
  opacity: 0.8;
}

.uploader-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  object-fit: cover;
  background: linear-gradient(135deg, #f0f0f0 0%, #e8e8e8 100%);
  flex-shrink: 0;
}

.uploader-info {
  flex: 1;
  min-width: 0;
}

.uploader-name {
  font-size: 14px;
  font-weight: 500;
  color: #18191C;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.uploader-bio {
  font-size: 12px;
  color: #9499A0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.follow-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 16px;
  background: #00AEEC;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.follow-btn:hover {
  background: #00A0DD;
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 174, 236, 0.3);
}

.follow-btn.following {
  background: #E3E5E7;
  color: #9499A0;
}

.follow-btn.following:hover {
  background: #C9CCD0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
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

/* ==================== 推荐视频列表 - Bilibili 风格 ==================== */
.rec-list {
  background: #fff;
  border-radius: 4px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.rec-title {
  font-size: 14px;
  font-weight: 500;
  color: #18191C;
  margin: 0 0 12px 0;
  padding-bottom: 12px;
  border-bottom: 1px solid #E3E5E7;
}

.rec-loading,
.rec-empty {
  text-align: center;
  padding: 40px 0;
  color: var(--text-tertiary, #999);
  font-size: 13px;
}

.rec-items {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.rec-item {
  display: flex;
  gap: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 10px 8px;
  border-radius: 4px;
}

.rec-item:hover {
  background: #F6F7F8;
}

.rec-item:hover .rec-item-title {
  color: #00AEEC;
}

.rec-cover {
  position: relative;
  width: 140px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
  background: #f0f0f0;
}

.rec-cover img {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  display: block;
  transition: transform 0.2s ease;
}

.rec-item:hover .rec-cover img {
  transform: scale(1.05);
}

.rec-duration {
  position: absolute;
  bottom: 4px;
  right: 4px;
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  font-size: 11px;
  padding: 2px 5px;
  border-radius: 2px;
  font-weight: 500;
}

.rec-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 2px 0;
}

.rec-item-title {
  font-size: 13px;
  font-weight: 500;
  color: #18191C;
  line-height: 1.5;
  margin: 0 0 8px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color 0.2s ease;
}

.rec-author {
  font-size: 12px;
  color: #9499A0;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rec-stats {
  font-size: 12px;
  color: #9499A0;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* ==================== 响应式设计 ==================== */
@media (max-width: 1024px) {
  .video-content {
    grid-template-columns: 1fr;
    padding: 16px;
  }

  .right-column {
    position: static;
    max-height: none;
  }

  .rec-list {
    max-height: 600px;
    overflow-y: auto;
  }
}

@media (max-width: 768px) {
  .video-header,
  .video-toolbar,
  .video-desc,
  .comment-section {
    padding: 16px;
  }

  .video-title {
    font-size: 18px;
  }

  .video-toolbar {
    gap: 8px;
  }

  .toolbar-btn {
    padding: 10px 8px;
  }

  .toolbar-btn .text {
    font-size: 12px;
  }

  .replies-list {
    margin-left: 20px;
    padding-left: 12px;
  }

  .reply-input-box {
    margin-left: 20px;
  }

  .reply-input-box.nested {
    margin-left: 12px;
  }
  
  .rec-item {
    flex-direction: column;
  }
  
  .rec-cover {
    width: 100%;
  }
}
</style>
