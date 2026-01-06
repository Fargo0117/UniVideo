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

// 已移除：统计数据、通知相关、发布公告表单（已迁移到其他页面）

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

// 已移除：pendingVideosCount 计算属性（已迁移到 Dashboard）

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


// ==================== 生命周期 ====================

onMounted(() => {
  // 检查是否为管理员
  const role = localStorage.getItem('role')
  if (role !== 'admin') {
    alert('无权访问管理后台')
    router.push('/')
    return
  }
  fetchVideoList()
})

onUnmounted(() => {
  destroyArtPlayer()
})
</script>

<template>
  <div class="audit-page">
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
/* ==================== 审核页面 ==================== */
.audit-page {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* ==================== 审核容器 ==================== */
.audit-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  min-height: 0; /* 允许 flex 子元素收缩 */
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
  flex: 1;
  overflow: auto;
  min-height: 0;
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

/* 已移除：通知管理面板样式（功能已迁移） */

/* ==================== 响应式设计 ==================== */
@media (max-width: 1200px) {
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
