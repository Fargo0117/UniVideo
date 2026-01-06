<script setup>
/**
 * 管理员视频管理控制台
 * 提供视频列表展示、搜索、筛选、审核和删除功能
 */
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import Artplayer from 'artplayer'

const router = useRouter()

// ==================== 数据定义 ====================

// 视频列表
const videos = ref([])
const loading = ref(true)

// 搜索和筛选
const searchKeyword = ref('')
const filterStatus = ref('') // '' 表示全部

// 视频预览模态框（旧版，保留兼容）
const showPreview = ref(false)
const previewVideo = ref(null)

// 审核弹窗
const showReviewModal = ref(false)
const reviewVideo = ref(null)
const rejectReason = ref('')
const showRejectInput = ref(false)

// ArtPlayer 实例
const artPlayerInstance = ref(null)

// 操作加载状态（记录正在操作的视频ID）
const operatingId = ref(null)
const auditLoading = ref(false)

// 当前激活的菜单项
const activeMenu = ref('dashboard')

// 统计数据
const stats = ref({
  pendingVideos: 0,
  totalUsers: 0,
  todayNew: 0
})

// 通知相关
const notifications = ref([])
const unreadCount = ref(0)
const showNotificationPanel = ref(false)
const notificationsLoading = ref(false)

// 发布公告表单
const sendNotificationForm = ref({
  target_username: '',
  title: '',
  msg_type: 'system',
  content: '',
  related_link: ''
})
const sendingNotification = ref(false)

// 状态选项
const statusOptions = [
  { value: '', label: '全部状态' },
  { value: 0, label: '待审核' },
  { value: 1, label: '已发布' },
  { value: 2, label: '已驳回' }
]

// 状态映射（用于显示状态标签）
const statusMap = {
  0: { text: '待审核', class: 'status-pending' },
  1: { text: '已发布', class: 'status-published' },
  2: { text: '已驳回', class: 'status-rejected' }
}

// ==================== 计算属性 ====================

/**
 * 计算待审核视频数量
 */
const pendingVideosCount = computed(() => {
  return videos.value.filter(v => v.status === 0).length
})

// ==================== 工具函数 ====================

/**
 * 获取完整的资源URL
 */
const getFullUrl = (path) => {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `http://localhost:5001/static/${path}`
}

/**
 * 格式化时间显示
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

/**
 * 获取状态显示信息
 */
const getStatusInfo = (status) => {
  return statusMap[status] || { text: '未知', class: 'status-unknown' }
}

// ==================== API 调用 ====================

/**
 * 获取统计数据
 */
const fetchStats = async () => {
  try {
    const response = await api.get('/admin/stats')
    if (response.data.code === 200) {
      stats.value = {
        pendingVideos: response.data.data.pending_videos || 0,
        totalUsers: response.data.data.total_users || 0,
        todayNew: response.data.data.today_new || 0
      }
    }
  } catch (err) {
    console.error('获取统计数据失败:', err)
  }
}

/**
 * 获取视频列表（支持搜索和筛选）
 */
const fetchVideoList = async () => {
  loading.value = true
  try {
    // 构建查询参数
    const params = {}
    if (searchKeyword.value.trim()) {
      params.keyword = searchKeyword.value.trim()
    }
    if (filterStatus.value !== '') {
      params.status = filterStatus.value
    }
    
    const response = await api.get('/admin/manage/list', { params })
    videos.value = response.data.data?.list || []
    // 更新统计数据
    await fetchStats()
  } catch (err) {
    console.error('获取视频列表失败:', err)
    const message = err.response?.data?.msg || '获取视频列表失败'
    alert(message)
    videos.value = []
  } finally {
    loading.value = false
  }
}

/**
 * 获取通知列表
 */
const fetchNotifications = async () => {
  notificationsLoading.value = true
  try {
    const response = await api.get('/admin/notifications', {
      params: {
        limit: 20,
        offset: 0
      }
    })
    if (response.data.code === 200) {
      notifications.value = response.data.data?.list || []
    }
  } catch (err) {
    console.error('获取通知列表失败:', err)
    notifications.value = []
  } finally {
    notificationsLoading.value = false
  }
}

/**
 * 获取未读通知数量
 */
const fetchUnreadCount = async () => {
  try {
    const response = await api.get('/admin/notifications/unread-count')
    if (response.data.code === 200) {
      unreadCount.value = response.data.data?.unread_count || 0
    }
  } catch (err) {
    console.error('获取未读通知数量失败:', err)
  }
}

/**
 * 标记通知为已读
 */
const markAsRead = async (notificationId) => {
  try {
    await api.put(`/admin/notifications/${notificationId}/read`)
    // 更新本地状态
    const notification = notifications.value.find(n => n.id === notificationId)
    if (notification) {
      notification.is_read = true
    }
    await fetchUnreadCount()
  } catch (err) {
    console.error('标记通知已读失败:', err)
  }
}

/**
 * 标记所有通知为已读
 */
const markAllAsRead = async () => {
  try {
    await api.put('/admin/notifications/read-all')
    // 更新本地状态
    notifications.value.forEach(n => {
      n.is_read = true
    })
    unreadCount.value = 0
  } catch (err) {
    console.error('标记所有通知已读失败:', err)
  }
}

/**
 * 切换通知面板
 */
const toggleNotificationPanel = () => {
  showNotificationPanel.value = !showNotificationPanel.value
  if (showNotificationPanel.value) {
    fetchNotifications()
  }
}

/**
 * 发送通知
 */
const sendNotification = async () => {
  // 验证必填字段
  if (!sendNotificationForm.value.title.trim()) {
    alert('请输入消息标题')
    return
  }
  
  if (!sendNotificationForm.value.content.trim()) {
    alert('请输入消息内容')
    return
  }
  
  sendingNotification.value = true
  try {
    const payload = {
      title: sendNotificationForm.value.title.trim(),
      content: sendNotificationForm.value.content.trim(),
      msg_type: sendNotificationForm.value.msg_type,
      related_link: sendNotificationForm.value.related_link.trim() || null
    }
    
    // 如果填写了用户名，添加到payload（留空则群发）
    if (sendNotificationForm.value.target_username.trim()) {
      payload.target_username = sendNotificationForm.value.target_username.trim()
    }
    
    const response = await api.post('/admin/notifications/send', payload)
    
    if (response.data.code === 200) {
      alert('消息已送达')
      // 清空表单
      sendNotificationForm.value = {
        target_username: '',
        title: '',
        msg_type: 'system',
        content: '',
        related_link: ''
      }
    } else {
      alert(response.data.msg || '发送失败')
    }
  } catch (err) {
    const message = err.response?.data?.msg || '发送失败'
    alert(message)
  } finally {
    sendingNotification.value = false
  }
}

/**
 * 搜索按钮点击事件
 */
const handleSearch = () => {
  fetchVideoList()
}

/**
 * 状态筛选变更事件
 */
const handleFilterChange = () => {
  fetchVideoList()
}

/**
 * 打开审核弹窗
 * @param {Object} video - 视频对象
 */
const openReviewModal = async (video) => {
  reviewVideo.value = video
  showReviewModal.value = true
  showRejectInput.value = false
  rejectReason.value = ''
  
  // 等待 DOM 更新后初始化播放器
  await nextTick()
  initArtPlayer()
}

/**
 * 关闭审核弹窗
 */
const closeReviewModal = () => {
  destroyArtPlayer()
  showReviewModal.value = false
  reviewVideo.value = null
  showRejectInput.value = false
  rejectReason.value = ''
}

/**
 * 初始化 ArtPlayer 播放器
 */
const initArtPlayer = () => {
  if (!reviewVideo.value) return
  
  const videoUrl = getFullUrl(reviewVideo.value.video_path)
  const coverUrl = getFullUrl(reviewVideo.value.cover_path)
  
  // 销毁旧实例
  destroyArtPlayer()
  
  artPlayerInstance.value = new Artplayer({
    container: '#review-artplayer',
    url: videoUrl,
    poster: coverUrl,
    title: reviewVideo.value.title,
    volume: 0.5,
    autoSize: false,
    fullscreen: true,
    fullscreenWeb: true,
    aspectRatio: true
  })
}

/**
 * 销毁 ArtPlayer 实例
 */
const destroyArtPlayer = () => {
  if (artPlayerInstance.value && artPlayerInstance.value.destroy) {
    artPlayerInstance.value.destroy()
    artPlayerInstance.value = null
  }
}

/**
 * 获取下一个待审核视频
 */
const getNextPendingVideo = () => {
  const pendingVideos = videos.value.filter(v => v.status === 0)
  if (pendingVideos.length === 0) return null
  
  const currentIndex = pendingVideos.findIndex(v => v.id === reviewVideo.value?.id)
  const nextIndex = currentIndex + 1
  
  if (nextIndex < pendingVideos.length) {
    return pendingVideos[nextIndex]
  }
  
  return null
}

/**
 * 审核操作：通过或驳回（在弹窗中）
 * @param {string} action - 'approve' 或 'reject'
 */
const handleReviewAudit = async (action) => {
  if (!reviewVideo.value) return
  
  // 如果是驳回，需要确认是否填写理由
  if (action === 'reject' && !showRejectInput.value) {
    showRejectInput.value = true
    return
  }
  
  const actionText = action === 'approve' ? '通过' : '驳回'
  const confirmText = action === 'approve' 
    ? `确定要${actionText}这个视频吗？`
    : `确定要${actionText}这个视频吗？${rejectReason.value ? `\n驳回理由：${rejectReason.value}` : ''}`
  
  if (!confirm(confirmText)) {
    return
  }
  
  auditLoading.value = true
  try {
    const payload = { action }
    if (action === 'reject' && rejectReason.value.trim()) {
      payload.reason = rejectReason.value.trim()
    }
    
    const response = await api.post(`/admin/audit/${reviewVideo.value.id}`, payload)
    alert(response.data.msg || `${actionText}成功`)
    
    // 获取下一个待审核视频
    const nextVideo = getNextPendingVideo()
    
    // 刷新列表
    await fetchVideoList()
    
    // 如果有下一个待审核视频，自动打开
    if (nextVideo) {
      const updatedVideo = videos.value.find(v => v.id === nextVideo.id)
      if (updatedVideo && updatedVideo.status === 0) {
        openReviewModal(updatedVideo)
      } else {
        closeReviewModal()
      }
    } else {
      closeReviewModal()
    }
  } catch (err) {
    const message = err.response?.data?.msg || `${actionText}失败`
    alert(message)
  } finally {
    auditLoading.value = false
  }
}

/**
 * 审核操作：通过或驳回（旧版，保留兼容）
 * @param {number} videoId - 视频ID
 * @param {string} action - 'approve' 或 'reject'
 */
const handleAudit = async (videoId, action) => {
  const actionText = action === 'approve' ? '通过' : '驳回'
  
  if (!confirm(`确定要${actionText}这个视频吗？`)) {
    return
  }
  
  operatingId.value = videoId
  try {
    const response = await api.post(`/admin/audit/${videoId}`, { action })
    alert(response.data.msg || `${actionText}成功`)
    // 刷新列表
    await fetchVideoList()
  } catch (err) {
    const message = err.response?.data?.msg || `${actionText}失败`
    alert(message)
  } finally {
    operatingId.value = null
  }
}

/**
 * 删除视频
 * @param {number} videoId - 视频ID
 * @param {string} videoTitle - 视频标题
 */
const handleDelete = async (videoId, videoTitle) => {
  if (!confirm(`确定要删除视频《${videoTitle}》吗？\n\n此操作不可恢复！`)) {
    return
  }
  
  operatingId.value = videoId
  try {
    const response = await api.delete(`/admin/manage/video/${videoId}`)
    alert(response.data.msg || '删除成功')
    // 刷新列表
    await fetchVideoList()
  } catch (err) {
    const message = err.response?.data?.msg || '删除失败'
    alert(message)
  } finally {
    operatingId.value = null
  }
}

/**
 * 打开视频预览模态框
 */
const openPreview = (video) => {
  previewVideo.value = video
  showPreview.value = true
}

/**
 * 关闭视频预览模态框
 */
const closePreview = () => {
  showPreview.value = false
  previewVideo.value = null
}


/**
 * 退出登录
 */
const handleLogout = () => {
  if (confirm('确定要退出登录吗？')) {
    localStorage.clear()
    router.push('/login')
  }
}

/**
 * 切换菜单
 */
const switchMenu = (menu) => {
  activeMenu.value = menu
  // 后续可以在这里添加路由跳转逻辑
}

// ==================== 生命周期 ====================

// 监听视频列表变化，更新统计数据
watch(() => videos.value, () => {
  stats.value.pendingVideos = pendingVideosCount.value
}, { immediate: true })

onMounted(() => {
  // 检查是否为管理员
  const role = localStorage.getItem('role')
  if (role !== 'admin') {
    alert('无权访问管理后台')
    router.push('/')
    return
  }
  fetchVideoList()
  fetchStats()
  fetchUnreadCount()
  
  // 定期刷新未读通知数量
  setInterval(() => {
    fetchUnreadCount()
  }, 30000) // 每30秒刷新一次
})

onUnmounted(() => {
  destroyArtPlayer()
})
</script>

<template>
  <div class="admin-layout">
    <!-- 左侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2 class="logo">UniVideo</h2>
        <p class="logo-subtitle">管理后台</p>
      </div>
      <nav class="sidebar-nav">
        <div 
          class="nav-item" 
          :class="{ active: activeMenu === 'dashboard' }"
          @click="switchMenu('dashboard')"
        >
          <span class="nav-icon">📊</span>
          <span class="nav-text">仪表盘</span>
        </div>
        <div 
          class="nav-item" 
          :class="{ active: activeMenu === 'audit' }"
          @click="switchMenu('audit')"
        >
          <span class="nav-icon">🎬</span>
          <span class="nav-text">内容审核</span>
        </div>
        <div 
          class="nav-item" 
          :class="{ active: activeMenu === 'users' }"
          @click="switchMenu('users')"
        >
          <span class="nav-icon">👥</span>
          <span class="nav-text">用户管理</span>
        </div>
        <div 
          class="nav-item" 
          :class="{ active: activeMenu === 'notifications' }"
          @click="switchMenu('notifications')"
        >
          <span class="nav-icon">📢</span>
          <span class="nav-text">通知管理</span>
        </div>
        <div 
          class="nav-item" 
          :class="{ active: activeMenu === 'settings' }"
          @click="switchMenu('settings')"
        >
          <span class="nav-icon">⚙️</span>
          <span class="nav-text">系统设置</span>
        </div>
      </nav>
    </aside>

    <!-- 右侧主内容区 -->
    <div class="main-content">
      <!-- 顶部栏 -->
      <header class="top-header">
        <h1 class="page-title">管理员控制台</h1>
        <div class="header-actions">
          <!-- 通知图标 -->
          <div class="notification-icon-wrapper" @click="toggleNotificationPanel">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
            <span v-if="unreadCount > 0" class="notification-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
          </div>
          <button class="btn-logout" @click="handleLogout">退出登录</button>
        </div>
      </header>

      <!-- 通知面板 -->
      <div v-if="showNotificationPanel" class="notification-panel">
        <div class="notification-panel-header">
          <h3>通知中心</h3>
          <div class="notification-actions">
            <button class="btn-mark-all-read" @click="markAllAsRead" v-if="unreadCount > 0">
              全部已读
            </button>
            <button class="btn-close-panel" @click="showNotificationPanel = false">×</button>
          </div>
        </div>
        <div class="notification-panel-body">
          <div v-if="notificationsLoading" class="notifications-loading">
            <p>加载中...</p>
          </div>
          <div v-else-if="notifications.length === 0" class="notifications-empty">
            <p>暂无通知</p>
          </div>
          <div v-else class="notifications-list">
            <div 
              v-for="notification in notifications" 
              :key="notification.id"
              class="notification-item"
              :class="{ 'unread': !notification.is_read }"
              @click="markAsRead(notification.id)"
            >
              <div class="notification-icon-small">
                <span v-if="notification.msg_type === 'audit'">📋</span>
                <span v-else-if="notification.msg_type === 'interaction'">💬</span>
                <span v-else>📢</span>
              </div>
              <div class="notification-content">
                <div class="notification-title">{{ notification.title }}</div>
                <div class="notification-text">{{ notification.content }}</div>
                <div class="notification-time">{{ formatTime(notification.created_at) }}</div>
              </div>
              <div v-if="!notification.is_read" class="notification-dot"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 内容区域 -->
      <main class="content-area">
        <!-- 通知管理面板 -->
        <div v-if="activeMenu === 'notifications'" class="notification-management">
          <div class="management-header">
            <h2 class="management-title">发布公告</h2>
            <p class="management-desc">向指定用户或全体用户发送系统通知</p>
          </div>

          <div class="send-notification-form">
            <div class="form-group">
              <label class="form-label">
                接收账号（用户名）
                <span class="form-hint">（留空则发送给所有人）</span>
              </label>
              <input
                type="text"
                v-model="sendNotificationForm.target_username"
                placeholder="留空则发送给所有人 (输入用户名精确发送)"
                class="form-input"
              />
            </div>

            <div class="form-group">
              <label class="form-label">
                标题 <span class="required">*</span>
              </label>
              <input
                type="text"
                v-model="sendNotificationForm.title"
                placeholder="请输入消息标题"
                class="form-input"
                required
              />
            </div>

            <div class="form-group">
              <label class="form-label">
                类型 <span class="required">*</span>
              </label>
              <select
                v-model="sendNotificationForm.msg_type"
                class="form-select"
              >
                <option value="system">系统通知</option>
                <option value="audit">审核通知</option>
                <option value="interaction">互动通知</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">
                内容 <span class="required">*</span>
              </label>
              <textarea
                v-model="sendNotificationForm.content"
                placeholder="请输入消息内容"
                rows="6"
                class="form-textarea"
                required
              ></textarea>
            </div>

            <div class="form-group">
              <label class="form-label">
                关联链接
                <span class="form-hint">（可选，用户点击消息时跳转的链接，如：/video/123）</span>
              </label>
              <input
                type="text"
                v-model="sendNotificationForm.related_link"
                placeholder="例如：/video/123 或 /upload"
                class="form-input"
              />
            </div>

            <div class="form-actions">
              <button
                class="btn-send"
                :disabled="sendingNotification || !sendNotificationForm.title.trim() || !sendNotificationForm.content.trim()"
                @click="sendNotification"
              >
                {{ sendingNotification ? '发送中...' : '发送通知' }}
              </button>
            </div>
          </div>
        </div>

        <!-- 仪表盘和审核列表（默认显示） -->
        <template v-else>
          <!-- 统计卡片 -->
          <div class="stats-cards">
          <div class="stat-card">
            <div class="stat-icon">🕒</div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.pendingVideos }}</div>
              <div class="stat-label">待审核视频</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">👥</div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.totalUsers }}</div>
              <div class="stat-label">总用户数</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">📈</div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.todayNew }}</div>
              <div class="stat-label">今日新增</div>
            </div>
          </div>
        </div>

        <!-- 审核列表容器 -->
        <div class="audit-container">
          <div class="audit-header">
            <h2 class="audit-title">待处理任务</h2>
          </div>

          <!-- 搜索和筛选区域 -->
          <div class="filter-bar">
            <div class="search-box">
              <input 
                type="text" 
                v-model="searchKeyword"
                placeholder="输入视频标题搜索..."
                @keyup.enter="handleSearch"
              />
              <button class="btn btn-primary" @click="handleSearch">搜索</button>
            </div>
            <div class="status-filter">
              <label>状态筛选：</label>
              <select v-model="filterStatus" @change="handleFilterChange">
                <option 
                  v-for="option in statusOptions" 
                  :key="option.value" 
                  :value="option.value"
                >
                  {{ option.label }}
                </option>
              </select>
            </div>
          </div>

          <!-- 加载状态 -->
          <div v-if="loading" class="loading-state">
            <p>加载中...</p>
          </div>

          <!-- 空状态 -->
          <div v-else-if="videos.length === 0" class="empty-state">
            <p>暂无视频数据</p>
          </div>

          <!-- 视频列表表格 -->
          <div v-else class="audit-table-wrapper">
            <table class="audit-table">
              <thead>
                <tr>
                  <th class="col-cover">封面</th>
                  <th class="col-info">视频信息</th>
                  <th class="col-author">UP主</th>
                  <th class="col-time">提交时间</th>
                  <th class="col-status">状态</th>
                  <th class="col-actions">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="video in videos" :key="video.id" class="table-row">
                  <!-- 封面缩略图 -->
                  <td class="col-cover">
                    <img 
                      class="cover-thumb" 
                      :src="getFullUrl(video.cover_path)" 
                      :alt="video.title"
                      @error="(e) => e.target.src = 'https://via.placeholder.com/80x45'"
                    />
                  </td>
                  <!-- 视频信息（标题+简介） -->
                  <td class="col-info">
                    <div class="video-info-cell">
                      <span class="video-title">{{ video.title }}</span>
                      <p class="video-desc" v-if="video.description">{{ video.description }}</p>
                    </div>
                  </td>
                  <!-- UP主 -->
                  <td class="col-author">
                    {{ video.author?.nickname || '未知' }}
                  </td>
                  <!-- 提交时间 -->
                  <td class="col-time">
                    {{ formatTime(video.created_at) }}
                  </td>
                  <!-- 状态 -->
                  <td class="col-status">
                    <span 
                      class="status-tag" 
                      :class="getStatusInfo(video.status).class"
                    >
                      {{ getStatusInfo(video.status).text }}
                    </span>
                  </td>
                  <!-- 操作按钮 -->
                  <td class="col-actions">
                    <!-- 待审核状态显示审核按钮 -->
                    <template v-if="video.status === 0">
                      <button 
                        class="btn btn-review"
                        @click="openReviewModal(video)"
                      >
                        🔍 审核
                      </button>
                    </template>
                    <!-- 其他状态显示预览和删除 -->
                    <template v-else>
                      <button 
                        class="btn btn-preview"
                        @click="openPreview(video)"
                      >
                        预览
                      </button>
                    </template>
                    <button 
                      class="btn btn-delete"
                      :disabled="operatingId === video.id"
                      @click="handleDelete(video.id, video.title)"
                    >
                      {{ operatingId === video.id ? '...' : '删除' }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        </template>
      </main>
    </div>

    <!-- 审核弹窗 -->
    <div v-if="showReviewModal" class="review-modal-overlay" @click.self="closeReviewModal">
      <div class="review-modal-content">
        <div class="review-modal-header">
          <h3 class="review-title">{{ reviewVideo?.title }}</h3>
          <button class="close-btn" @click="closeReviewModal">&times;</button>
        </div>
        <div class="review-modal-body">
          <!-- 左侧：ArtPlayer 播放器 -->
          <div class="review-player-section">
            <div id="review-artplayer" class="review-artplayer-container"></div>
          </div>
          
          <!-- 右侧：审核操作区 -->
          <div class="review-action-section">
            <div class="review-video-info">
              <h4 class="info-title">视频信息</h4>
              <div class="info-item">
                <span class="info-label">UP主：</span>
                <span class="info-value">{{ reviewVideo?.author?.nickname || '未知' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">分类：</span>
                <span class="info-value">{{ reviewVideo?.category?.name || '未分类' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">提交时间：</span>
                <span class="info-value">{{ formatTime(reviewVideo?.created_at) }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">状态：</span>
                <span 
                  class="status-tag" 
                  :class="getStatusInfo(reviewVideo?.status).class"
                >
                  {{ getStatusInfo(reviewVideo?.status).text }}
                </span>
              </div>
              <div class="info-item" v-if="reviewVideo?.description">
                <span class="info-label">简介：</span>
                <p class="info-desc">{{ reviewVideo.description }}</p>
              </div>
            </div>
            
            <!-- 驳回理由输入框 -->
            <div v-if="showRejectInput" class="reject-reason-box">
              <label class="reason-label">驳回理由（可选）：</label>
              <textarea
                v-model="rejectReason"
                placeholder="请输入驳回理由..."
                rows="3"
                maxlength="200"
                class="reason-input"
              ></textarea>
            </div>
            
            <!-- 操作按钮 -->
            <div class="review-actions">
              <button 
                class="btn-review-action btn-approve-action"
                :disabled="auditLoading"
                @click="handleReviewAudit('approve')"
              >
                ✅ 通过
              </button>
              <button 
                class="btn-review-action btn-reject-action"
                :disabled="auditLoading"
                @click="handleReviewAudit('reject')"
              >
                {{ showRejectInput ? '❌ 确认驳回' : '❌ 驳回' }}
              </button>
              <button 
                class="btn-review-action btn-cancel-action"
                :disabled="auditLoading"
                @click="closeReviewModal"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 视频预览模态框（旧版，保留兼容） -->
    <div v-if="showPreview" class="modal-overlay" @click.self="closePreview">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ previewVideo?.title }}</h3>
          <button class="close-btn" @click="closePreview">&times;</button>
        </div>
        <div class="modal-body">
          <video 
            class="preview-player"
            :src="getFullUrl(previewVideo?.video_path)"
            :poster="getFullUrl(previewVideo?.cover_path)"
            controls
            autoplay
          >
            您的浏览器不支持视频播放
          </video>
          <div class="video-info">
            <p><strong>作者：</strong>{{ previewVideo?.author?.nickname || '未知' }}</p>
            <p><strong>分类：</strong>{{ previewVideo?.category?.name || '未分类' }}</p>
            <p>
              <strong>状态：</strong>
              <span 
                class="status-tag" 
                :class="getStatusInfo(previewVideo?.status).class"
              >
                {{ getStatusInfo(previewVideo?.status).text }}
              </span>
            </p>
            <p><strong>简介：</strong>{{ previewVideo?.description || '暂无简介' }}</p>
          </div>
        </div>
        <div class="modal-footer">
          <template v-if="previewVideo?.status === 0">
            <button 
              class="btn btn-approve"
              @click="handleAudit(previewVideo?.id, 'approve'); closePreview()"
            >
              通过
            </button>
            <button 
              class="btn btn-reject"
              @click="handleAudit(previewVideo?.id, 'reject'); closePreview()"
            >
              驳回
            </button>
          </template>
          <button 
            class="btn btn-delete"
            @click="handleDelete(previewVideo?.id, previewVideo?.title); closePreview()"
          >
            删除
          </button>
          <button class="btn btn-secondary" @click="closePreview">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ==================== 全局布局 ==================== */
.admin-layout {
  display: flex;
  min-height: 100vh;
  background-color: #f0f2f5;
}

/* ==================== 左侧边栏 ==================== */
.sidebar {
  width: 240px;
  background-color: #001529;
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
}

.sidebar-header {
  padding: 24px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 4px;
}

.logo-subtitle {
  margin: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.65);
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
  color: rgba(255, 255, 255, 0.65);
  cursor: pointer;
  transition: all 0.3s;
  border-left: 3px solid transparent;
}

.nav-item:hover {
  background-color: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.nav-item.active {
  background-color: rgba(24, 144, 255, 0.15);
  color: #1890ff;
  border-left-color: #1890ff;
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

/* ==================== 右侧主内容区 ==================== */
.main-content {
  flex: 1;
  margin-left: 240px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* 顶部栏 */
.top-header {
  background: #fff;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  position: sticky;
  top: 0;
  z-index: 100;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #262626;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 通知图标 */
.notification-icon-wrapper {
  position: relative;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.notification-icon-wrapper:hover {
  background-color: #f0f0f0;
}

.notification-icon-wrapper svg {
  display: block;
  color: #666;
}

.notification-badge {
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
}

.btn-logout {
  padding: 6px 16px;
  background: #ff4d4f;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-logout:hover {
  background: #ff7875;
}

/* 通知面板 */
.notification-panel {
  position: fixed;
  top: 60px;
  right: 24px;
  width: 400px;
  max-height: 600px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  z-index: 1500;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.notification-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.notification-panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

.notification-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-mark-all-read {
  padding: 4px 12px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-mark-all-read:hover {
  background: #40a9ff;
}

.btn-close-panel {
  background: none;
  border: none;
  font-size: 24px;
  color: #8c8c8c;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close-panel:hover {
  color: #262626;
}

.notification-panel-body {
  flex: 1;
  overflow-y: auto;
  max-height: 500px;
}

.notifications-loading,
.notifications-empty {
  text-align: center;
  padding: 40px 20px;
  color: #8c8c8c;
  font-size: 14px;
}

.notifications-list {
  padding: 8px 0;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 20px;
  cursor: pointer;
  transition: background-color 0.2s;
  border-bottom: 1px solid #f0f0f0;
  position: relative;
}

.notification-item:hover {
  background-color: #fafafa;
}

.notification-item.unread {
  background-color: #f0f7ff;
}

.notification-item.unread:hover {
  background-color: #e6f4ff;
}

.notification-icon-small {
  font-size: 20px;
  flex-shrink: 0;
  margin-top: 2px;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-size: 14px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 4px;
}

.notification-text {
  font-size: 13px;
  color: #595959;
  line-height: 1.5;
  margin-bottom: 6px;
  word-break: break-word;
}

.notification-time {
  font-size: 12px;
  color: #8c8c8c;
}

.notification-dot {
  position: absolute;
  top: 16px;
  right: 12px;
  width: 8px;
  height: 8px;
  background: #1890ff;
  border-radius: 50%;
  flex-shrink: 0;
}

/* 内容区域 */
.content-area {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

/* ==================== 统计卡片 ==================== */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-bottom: 24px;
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s;
}

.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.stat-icon {
  font-size: 48px;
  margin-right: 20px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: #262626;
  line-height: 1.2;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #8c8c8c;
}

/* ==================== 审核列表容器 ==================== */
.audit-container {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.audit-header {
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.audit-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}

/* ==================== 搜索和筛选区域 ==================== */
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #f0f0f0;
  flex-wrap: wrap;
  gap: 16px;
}

.search-box {
  display: flex;
  gap: 8px;
}

.search-box input {
  width: 280px;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
}

.search-box input:focus {
  outline: none;
  border-color: #409eff;
}

.status-filter {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-filter label {
  font-size: 14px;
  color: #666;
}

.status-filter select {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
}

.status-filter select:focus {
  outline: none;
  border-color: #409eff;
}

/* 加载/空状态 */
.loading-state,
.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: #999;
}

/* ==================== 表格样式 ==================== */
.audit-table-wrapper {
  overflow-x: auto;
}

.audit-table {
  width: 100%;
  border-collapse: collapse;
}

.audit-table th,
.audit-table td {
  padding: 14px 12px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.audit-table th {
  background: #fafafa;
  font-weight: 600;
  color: #666;
  font-size: 14px;
}

.table-row {
  transition: background-color 0.2s;
}

.table-row:hover {
  background: #f5f7fa;
}

/* 列宽定义 */
.col-cover { width: 100px; }
.col-info { min-width: 300px; }
.col-author { width: 120px; }
.col-time { width: 160px; }
.col-status { width: 100px; }
.col-actions { width: 180px; }

/* 封面缩略图 */
.cover-thumb {
  width: 80px;
  height: 45px;
  object-fit: cover;
  border-radius: 4px;
  background: #f0f0f0;
  display: block;
}

/* 视频信息单元格 */
.video-info-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* 标题和描述 */
.video-title {
  font-size: 14px;
  font-weight: 600;
  color: #262626;
  display: block;
  line-height: 1.4;
}

.video-desc {
  font-size: 12px;
  color: #8c8c8c;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.5;
}

/* 状态标签 */
.status-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-pending {
  background: #fff7e6;
  color: #fa8c16;
  border: 1px solid #ffd591;
}

.status-published {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.status-rejected {
  background: #fff2f0;
  color: #ff4d4f;
  border: 1px solid #ffccc7;
}

/* ==================== 按钮样式 ==================== */
.btn {
  padding: 5px 10px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
  margin-right: 6px;
}

.btn:last-child {
  margin-right: 0;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #409eff;
  color: #fff;
}

.btn-primary:hover {
  background: #66b1ff;
}

.btn-review {
  background: #1890ff;
  color: #fff;
  border: 1px solid #1890ff;
  font-weight: 500;
}

.btn-review:hover {
  background: #40a9ff;
  border-color: #40a9ff;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
}

.btn-preview {
  background: #e6f7ff;
  color: #1890ff;
  border: 1px solid #91d5ff;
}

.btn-preview:hover {
  background: #1890ff;
  color: #fff;
}

.btn-approve {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.btn-approve:hover {
  background: #52c41a;
  color: #fff;
}

.btn-reject {
  background: #fff7e6;
  color: #fa8c16;
  border: 1px solid #ffd591;
}

.btn-reject:hover {
  background: #fa8c16;
  color: #fff;
}

.btn-delete {
  background: #fff2f0;
  color: #ff4d4f;
  border: 1px solid #ffccc7;
}

.btn-delete:hover {
  background: #ff4d4f;
  color: #fff;
}

.btn-secondary {
  background: #f5f5f5;
  color: #666;
  border: 1px solid #d9d9d9;
}

.btn-secondary:hover {
  background: #e8e8e8;
}

/* ==================== 审核弹窗样式 ==================== */
.review-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 20px;
}

.review-modal-content {
  background: #fff;
  border-radius: 12px;
  width: 100%;
  max-width: 1400px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.review-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
  background: #fff;
}

.review-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
  flex: 1;
}

.review-modal-body {
  display: flex;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

/* 左侧播放器区域 */
.review-player-section {
  flex: 1;
  min-width: 0;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.review-artplayer-container {
  width: 100%;
  max-width: 100%;
  aspect-ratio: 16 / 9;
  background: #000;
}

/* 右侧审核操作区 */
.review-action-section {
  width: 380px;
  background: #fafafa;
  display: flex;
  flex-direction: column;
  border-left: 1px solid #f0f0f0;
  overflow-y: auto;
}

.review-video-info {
  padding: 24px;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
}

.info-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

.info-item {
  margin-bottom: 12px;
  display: flex;
  align-items: flex-start;
}

.info-item:last-child {
  margin-bottom: 0;
}

.info-label {
  font-size: 14px;
  color: #8c8c8c;
  min-width: 80px;
  flex-shrink: 0;
}

.info-value {
  font-size: 14px;
  color: #262626;
  flex: 1;
}

.info-desc {
  font-size: 14px;
  color: #262626;
  line-height: 1.6;
  margin: 0;
  white-space: pre-wrap;
}

/* 驳回理由输入框 */
.reject-reason-box {
  padding: 20px 24px;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
}

.reason-label {
  display: block;
  font-size: 14px;
  color: #262626;
  margin-bottom: 8px;
  font-weight: 500;
}

.reason-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
  font-family: inherit;
  box-sizing: border-box;
}

.reason-input:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
}

/* 审核操作按钮 */
.review-actions {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #fff;
  margin-top: auto;
}

.btn-review-action {
  padding: 12px 20px;
  border: none;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  width: 100%;
}

.btn-review-action:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-approve-action {
  background: #52c41a;
  color: #fff;
}

.btn-approve-action:hover:not(:disabled) {
  background: #73d13d;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(82, 196, 26, 0.3);
}

.btn-reject-action {
  background: #ff4d4f;
  color: #fff;
}

.btn-reject-action:hover:not(:disabled) {
  background: #ff7875;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(255, 77, 79, 0.3);
}

.btn-cancel-action {
  background: #f5f5f5;
  color: #666;
  border: 1px solid #d9d9d9;
}

.btn-cancel-action:hover:not(:disabled) {
  background: #e8e8e8;
  border-color: #bfbfbf;
}

/* ==================== 模态框样式（旧版，保留兼容） ==================== */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #fff;
  border-radius: 8px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #999;
  cursor: pointer;
  line-height: 1;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.preview-player {
  width: 100%;
  max-height: 400px;
  background: #000;
  border-radius: 4px;
}

.video-info {
  margin-top: 16px;
  padding: 12px;
  background: #fafafa;
  border-radius: 4px;
}

.video-info p {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #666;
}

.video-info p:last-child {
  margin-bottom: 0;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid #f0f0f0;
}

/* ==================== 通知管理面板样式 ==================== */
.notification-management {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.management-header {
  padding: 24px;
  border-bottom: 1px solid #f0f0f0;
}

.management-title {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
  color: #262626;
}

.management-desc {
  margin: 0;
  font-size: 14px;
  color: #8c8c8c;
}

.send-notification-form {
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #262626;
  margin-bottom: 8px;
}

.form-hint {
  font-size: 12px;
  color: #8c8c8c;
  font-weight: normal;
}

.required {
  color: #ff4d4f;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
  box-sizing: border-box;
  transition: all 0.3s;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
}

.form-input::placeholder,
.form-textarea::placeholder {
  color: #bfbfbf;
}

.form-textarea {
  resize: vertical;
  min-height: 120px;
  line-height: 1.6;
}

.form-select {
  cursor: pointer;
  background: #fff;
}

.form-actions {
  margin-top: 32px;
  display: flex;
  justify-content: flex-end;
}

.btn-send {
  padding: 10px 24px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  min-width: 120px;
}

.btn-send:hover:not(:disabled) {
  background: #40a9ff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
}

.btn-send:disabled {
  background: #d9d9d9;
  color: #fff;
  cursor: not-allowed;
  opacity: 0.6;
  transform: none;
  box-shadow: none;
}

/* ==================== 响应式设计 ==================== */
@media (max-width: 1200px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .review-modal-body {
    flex-direction: column;
  }
  
  .review-action-section {
    width: 100%;
    max-height: 50vh;
  }
  
  .review-player-section {
    min-height: 400px;
  }
}

@media (max-width: 768px) {
  .stats-cards {
    grid-template-columns: 1fr;
  }
  
  .sidebar {
    width: 200px;
  }
  
  .main-content {
    margin-left: 200px;
  }
  
  .stat-icon {
    font-size: 36px;
    margin-right: 16px;
  }
  
  .stat-value {
    font-size: 24px;
  }
  
  .review-modal-content {
    max-width: 100%;
    max-height: 100vh;
    border-radius: 0;
  }
  
  .review-modal-overlay {
    padding: 0;
  }
  
  .review-action-section {
    max-height: 40vh;
  }
  
  .audit-table-wrapper {
    overflow-x: scroll;
  }
  
  .col-info {
    min-width: 200px;
  }
}
</style>
