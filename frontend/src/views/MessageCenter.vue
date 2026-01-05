<script setup>
/**
 * 消息中心组件
 * 展示用户的所有通知消息，根据消息类型进行多态渲染
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()

// ==================== 数据定义 ====================

// 当前用户ID
const currentUserId = localStorage.getItem('user_id')

// 通知列表
const notifications = ref([])
const loading = ref(true)

// 展开状态（记录哪些消息的内容已展开）
const expandedMessages = ref(new Set())

// 筛选状态
const filterType = ref('all') // 'all', 'unread', 'system', 'audit', 'interaction'

// ==================== 计算属性 ====================

/**
 * 过滤后的通知列表
 */
const filteredNotifications = computed(() => {
  let result = notifications.value

  // 按类型筛选
  if (filterType.value !== 'all') {
    if (filterType.value === 'unread') {
      result = result.filter(n => !n.is_read)
    } else {
      result = result.filter(n => n.msg_type === filterType.value)
    }
  }

  return result
})

/**
 * 未读消息数量
 */
const unreadCount = computed(() => {
  return notifications.value.filter(n => !n.is_read).length
})

// ==================== 工具函数 ====================

/**
 * 格式化时间显示
 */
const formatTime = (isoString) => {
  if (!isoString) return ''
  const date = new Date(isoString)
  const now = new Date()
  const diff = now - date
  
  // 小于1分钟
  if (diff < 60000) {
    return '刚刚'
  }
  // 小于1小时
  if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`
  }
  // 小于24小时
  if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`
  }
  // 小于7天
  if (diff < 604800000) {
    return `${Math.floor(diff / 86400000)}天前`
  }
  // 显示完整时间
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * 获取消息类型配置
 */
const getMessageConfig = (notification) => {
  const { msg_type, content } = notification
  
  // 审核类型需要判断是通过还是驳回
  if (msg_type === 'audit') {
    // 通过关键词判断（包含"通过"、"已发布"等为通过，否则为驳回）
    const isApproved = content.includes('通过') || content.includes('已发布')
    
    if (isApproved) {
      return {
        icon: '✅',
        iconBg: '#52c41a',
        titleColor: '#52c41a',
        titleText: '审核通过',
        iconClass: 'icon-success'
      }
    } else {
      return {
        icon: '❌',
        iconBg: '#ff4d4f',
        titleColor: '#ff4d4f',
        titleText: '审核驳回',
        iconClass: 'icon-error'
      }
    }
  }
  
  // 系统公告
  if (msg_type === 'system') {
    return {
      icon: '📢',
      iconBg: '#1890ff',
      titleColor: '#262626',
      titleText: '系统公告',
      iconClass: 'icon-system'
    }
  }
  
  // 互动通知
  if (msg_type === 'interaction') {
    return {
      icon: '💬',
      iconBg: '#fa8c16',
      titleColor: '#262626',
      titleText: '互动通知',
      iconClass: 'icon-interaction'
    }
  }
  
  // 默认
  return {
    icon: '📢',
    iconBg: '#8c8c8c',
    titleColor: '#262626',
    titleText: '通知',
    iconClass: 'icon-default'
  }
}

/**
 * 判断内容是否需要折叠（超过100字符）
 */
const shouldCollapse = (content) => {
  return content && content.length > 100
}

/**
 * 切换消息展开/折叠
 */
const toggleExpand = (messageId) => {
  if (expandedMessages.value.has(messageId)) {
    expandedMessages.value.delete(messageId)
  } else {
    expandedMessages.value.add(messageId)
  }
}

/**
 * 判断消息是否已展开
 */
const isExpanded = (messageId) => {
  return expandedMessages.value.has(messageId)
}

/**
 * 获取内容预览（折叠时显示）
 */
const getContentPreview = (content) => {
  if (!content) return ''
  if (content.length <= 100) return content
  return content.substring(0, 100) + '...'
}

// ==================== API 调用 ====================

/**
 * 获取通知列表
 */
const fetchNotifications = async () => {
  if (!currentUserId) {
    router.push('/login')
    return
  }
  
  loading.value = true
  try {
    const response = await api.get('/admin/notifications', {
      params: {
        user_id: currentUserId,
        limit: 100,
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
    loading.value = false
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
  } catch (err) {
    console.error('标记通知已读失败:', err)
  }
}

/**
 * 标记所有通知为已读
 */
const markAllAsRead = async () => {
  try {
    await api.put('/admin/notifications/read-all', null, {
      params: { user_id: currentUserId }
    })
    // 更新本地状态
    notifications.value.forEach(n => {
      n.is_read = true
    })
  } catch (err) {
    console.error('标记所有通知已读失败:', err)
  }
}

/**
 * 处理点击消息卡片
 */
const handleMessageClick = (notification) => {
  // 如果未读，标记为已读
  if (!notification.is_read) {
    markAsRead(notification.id)
  }
  
  // 如果有关联链接，跳转
  if (notification.related_link) {
    router.push(notification.related_link)
  }
}

// ==================== 生命周期 ====================

onMounted(() => {
  if (!currentUserId) {
    router.push('/login')
    return
  }
  fetchNotifications()
})
</script>

<template>
  <div class="message-center-container">
    <!-- 页面头部 -->
    <header class="page-header">
      <h1 class="page-title">消息中心</h1>
      <div class="header-actions">
        <span class="unread-badge" v-if="unreadCount > 0">
          未读 {{ unreadCount }}
        </span>
        <button 
          class="btn-mark-all-read" 
          @click="markAllAsRead"
          v-if="unreadCount > 0"
        >
          全部已读
        </button>
      </div>
    </header>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <button 
        class="filter-btn"
        :class="{ active: filterType === 'all' }"
        @click="filterType = 'all'"
      >
        全部
      </button>
      <button 
        class="filter-btn"
        :class="{ active: filterType === 'unread' }"
        @click="filterType = 'unread'"
      >
        未读
      </button>
      <button 
        class="filter-btn"
        :class="{ active: filterType === 'system' }"
        @click="filterType = 'system'"
      >
        系统公告
      </button>
      <button 
        class="filter-btn"
        :class="{ active: filterType === 'audit' }"
        @click="filterType = 'audit'"
      >
        审核通知
      </button>
      <button 
        class="filter-btn"
        :class="{ active: filterType === 'interaction' }"
        @click="filterType = 'interaction'"
      >
        互动通知
      </button>
    </div>

    <!-- 消息列表 -->
    <div class="messages-container">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <p>加载中...</p>
      </div>

      <!-- 空状态 -->
      <div v-else-if="filteredNotifications.length === 0" class="empty-state">
        <p>暂无消息</p>
      </div>

      <!-- 消息卡片列表 -->
      <div v-else class="messages-list">
        <div
          v-for="notification in filteredNotifications"
          :key="notification.id"
          class="message-card"
          :class="{ 
            'unread': !notification.is_read,
            'has-link': notification.related_link
          }"
          @click="handleMessageClick(notification)"
        >
          <!-- 左侧图标 -->
          <div 
            class="message-icon"
            :style="{ backgroundColor: getMessageConfig(notification).iconBg }"
          >
            <span class="icon-emoji">{{ getMessageConfig(notification).icon }}</span>
          </div>

          <!-- 中间内容区 -->
          <div class="message-content">
            <!-- 标题行 -->
            <div class="message-header">
              <span 
                class="message-type"
                :style="{ color: getMessageConfig(notification).titleColor }"
              >
                {{ getMessageConfig(notification).titleText }}
              </span>
              <span class="message-time">{{ formatTime(notification.created_at) }}</span>
            </div>

            <!-- 消息标题 -->
            <div class="message-title">{{ notification.title }}</div>

            <!-- 消息内容 -->
            <div class="message-body">
              <template v-if="shouldCollapse(notification.content) && !isExpanded(notification.id)">
                <span class="content-preview">{{ getContentPreview(notification.content) }}</span>
                <button 
                  class="btn-expand"
                  @click.stop="toggleExpand(notification.id)"
                >
                  展开
                </button>
              </template>
              <template v-else>
                <span class="content-full">{{ notification.content }}</span>
                <button 
                  v-if="shouldCollapse(notification.content)"
                  class="btn-collapse"
                  @click.stop="toggleExpand(notification.id)"
                >
                  收起
                </button>
              </template>
            </div>

            <!-- 关联链接 -->
            <div v-if="notification.related_link" class="message-link">
              <span class="link-text" @click.stop="router.push(notification.related_link)">
                查看详情 >
              </span>
            </div>
          </div>

          <!-- 右侧操作区 -->
          <div class="message-actions">
            <!-- 未读标识 -->
            <div v-if="!notification.is_read" class="unread-dot"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ==================== 全局布局 ==================== */
.message-center-container {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

/* ==================== 页面头部 ==================== */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 20px 24px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #262626;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.unread-badge {
  padding: 4px 12px;
  background: #ff4d4f;
  color: #fff;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
}

.btn-mark-all-read {
  padding: 6px 16px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-mark-all-read:hover {
  background: #40a9ff;
}

/* ==================== 筛选栏 ==================== */
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  padding: 16px 24px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  flex-wrap: wrap;
}

.filter-btn {
  padding: 6px 16px;
  background: #f5f5f5;
  color: #595959;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.filter-btn:hover {
  background: #e8e8e8;
}

.filter-btn.active {
  background: #1890ff;
  color: #fff;
}

/* ==================== 消息容器 ==================== */
.messages-container {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: #8c8c8c;
  font-size: 15px;
}

.messages-list {
  padding: 8px 0;
}

/* ==================== 消息卡片 ==================== */
.message-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px 24px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.message-card:hover {
  background: #fafafa;
}

.message-card.unread {
  background: #f9f9f9;
}

.message-card.unread:hover {
  background: #f0f0f0;
}

.message-card.has-link {
  cursor: pointer;
}

.message-card:last-child {
  border-bottom: none;
}

/* 左侧图标 */
.message-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.icon-emoji {
  font-size: 24px;
  line-height: 1;
}

/* 中间内容区 */
.message-content {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.message-type {
  font-size: 13px;
  font-weight: 600;
}

.message-time {
  font-size: 12px;
  color: #8c8c8c;
  flex-shrink: 0;
}

.message-title {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 8px;
  line-height: 1.5;
}

.message-body {
  font-size: 14px;
  color: #595959;
  line-height: 1.6;
  margin-bottom: 8px;
}

.content-preview,
.content-full {
  display: inline;
}

.btn-expand,
.btn-collapse {
  margin-left: 8px;
  padding: 0;
  background: none;
  border: none;
  color: #1890ff;
  font-size: 14px;
  cursor: pointer;
  text-decoration: underline;
}

.btn-expand:hover,
.btn-collapse:hover {
  color: #40a9ff;
}

.message-link {
  margin-top: 8px;
}

.link-text {
  font-size: 13px;
  color: #1890ff;
  cursor: pointer;
  transition: color 0.2s;
}

.link-text:hover {
  color: #40a9ff;
  text-decoration: underline;
}

/* 右侧操作区 */
.message-actions {
  display: flex;
  align-items: flex-start;
  flex-shrink: 0;
  padding-top: 4px;
}

.unread-dot {
  width: 8px;
  height: 8px;
  background: #ff4d4f;
  border-radius: 50%;
  flex-shrink: 0;
}

/* ==================== 响应式设计 ==================== */
@media (max-width: 768px) {
  .message-center-container {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .filter-bar {
    padding: 12px 16px;
  }

  .message-card {
    padding: 12px 16px;
  }

  .message-icon {
    width: 40px;
    height: 40px;
  }

  .icon-emoji {
    font-size: 20px;
  }
}
</style>
