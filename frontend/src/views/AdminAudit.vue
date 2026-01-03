<script setup>
/**
 * 管理员视频管理控制台
 * 提供视频列表展示、搜索、筛选、审核和删除功能
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()

// ==================== 数据定义 ====================

// 视频列表
const videos = ref([])
const loading = ref(true)

// 搜索和筛选
const searchKeyword = ref('')
const filterStatus = ref('') // '' 表示全部

// 视频预览模态框
const showPreview = ref(false)
const previewVideo = ref(null)

// 操作加载状态（记录正在操作的视频ID）
const operatingId = ref(null)

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
 * 审核操作：通过或驳回
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
 * 返回首页
 */
const goBack = () => {
  router.push('/')
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
</script>

<template>
  <div class="admin-container">
    <!-- 顶部导航 -->
    <header class="nav-bar">
      <button class="back-btn" @click="goBack">&larr; 返回首页</button>
      <h1 class="page-title">视频管理控制台</h1>
    </header>

    <!-- 内容区域 -->
    <main class="content">
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
              <th class="col-title">标题</th>
              <th class="col-author">作者</th>
              <th class="col-status">状态</th>
              <th class="col-time">上传时间</th>
              <th class="col-actions">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="video in videos" :key="video.id">
              <!-- 封面缩略图 -->
              <td class="col-cover">
                <img 
                  class="cover-thumb" 
                  :src="getFullUrl(video.cover_path)" 
                  :alt="video.title"
                  @error="(e) => e.target.src = 'https://via.placeholder.com/120x68'"
                />
              </td>
              <!-- 标题 -->
              <td class="col-title">
                <span class="video-title">{{ video.title }}</span>
                <p class="video-desc" v-if="video.description">{{ video.description }}</p>
              </td>
              <!-- 作者 -->
              <td class="col-author">
                {{ video.author?.nickname || '未知' }}
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
              <!-- 上传时间 -->
              <td class="col-time">
                {{ formatTime(video.created_at) }}
              </td>
              <!-- 操作按钮 -->
              <td class="col-actions">
                <button 
                  class="btn btn-preview"
                  @click="openPreview(video)"
                >
                  预览
                </button>
                <!-- 仅待审核状态显示通过/驳回按钮 -->
                <template v-if="video.status === 0">
                  <button 
                    class="btn btn-approve"
                    :disabled="operatingId === video.id"
                    @click="handleAudit(video.id, 'approve')"
                  >
                    {{ operatingId === video.id ? '...' : '通过' }}
                  </button>
                  <button 
                    class="btn btn-reject"
                    :disabled="operatingId === video.id"
                    @click="handleAudit(video.id, 'reject')"
                  >
                    {{ operatingId === video.id ? '...' : '驳回' }}
                  </button>
                </template>
                <!-- 删除按钮 -->
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
    </main>

    <!-- 视频预览模态框 -->
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
.admin-container {
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
}

.back-btn:hover {
  text-decoration: underline;
}

.page-title {
  margin-left: 16px;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

/* 内容区域 */
.content {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

/* ==================== 搜索和筛选区域 ==================== */
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  padding: 16px 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
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
  background: #fff;
  border-radius: 8px;
}

/* ==================== 表格样式 ==================== */
.audit-table-wrapper {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
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

.audit-table tr:hover {
  background: #fafafa;
}

/* 列宽定义 */
.col-cover { width: 140px; }
.col-title { min-width: 180px; }
.col-author { width: 100px; }
.col-status { width: 90px; }
.col-time { width: 150px; }
.col-actions { width: 240px; }

/* 封面缩略图 */
.cover-thumb {
  width: 120px;
  height: 68px;
  object-fit: cover;
  border-radius: 4px;
  background: #f0f0f0;
}

/* 标题和描述 */
.video-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  display: block;
  margin-bottom: 4px;
}

.video-desc {
  font-size: 12px;
  color: #999;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
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

/* ==================== 模态框样式 ==================== */
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
</style>
