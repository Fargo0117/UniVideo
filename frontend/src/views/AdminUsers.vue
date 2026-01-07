<script setup>
/**
 * 管理后台用户管理页面
 * 显示用户列表，支持搜索和封禁/解封操作
 * 蓝色商务风格设计
 */
import { ref, onMounted } from 'vue'
import api from '@/api'

// 用户列表
const users = ref([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const keyword = ref('')

// 确认对话框状态
const showConfirm = ref(false)
const confirmAction = ref('')
const confirmUserId = ref(null)
const confirmStatus = ref(null)
const confirmCallback = ref(null)

/**
 * 获取用户列表
 */
const fetchUsers = async () => {
  loading.value = true
  try {
    const response = await api.get('/admin/users', {
      params: {
        page: currentPage.value,
        per_page: pageSize.value,
        keyword: keyword.value
      }
    })
    if (response.data.code === 200) {
      users.value = response.data.data.list || []
      total.value = response.data.data.total || 0
    }
  } catch (err) {
    console.error('获取用户列表失败:', err)
    alert('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 搜索用户
 */
const handleSearch = () => {
  currentPage.value = 1
  fetchUsers()
}

/**
 * 显示确认对话框
 */
const showConfirmDialog = (userId, status, callback) => {
  confirmUserId.value = userId
  confirmStatus.value = status
  confirmAction.value = status === 0 ? '封禁' : '解封'
  confirmCallback.value = callback
  showConfirm.value = true
}

/**
 * 关闭确认对话框
 */
const closeConfirm = () => {
  showConfirm.value = false
  confirmUserId.value = null
  confirmStatus.value = null
  confirmAction.value = ''
  confirmCallback.value = null
}

/**
 * 确认操作
 */
const handleConfirm = () => {
  if (confirmCallback.value) {
    confirmCallback.value()
  }
  closeConfirm()
}

/**
 * 更新用户状态
 */
const updateUserStatus = async (userId, status) => {
  const action = status === 0 ? '封禁' : '解封'
  
  showConfirmDialog(userId, status, async () => {
    try {
      const response = await api.post(`/admin/users/${userId}/status`, {
        status: status
      })
      if (response.data.code === 200) {
        alert(`${action}成功`)
        fetchUsers()
      } else {
        alert(response.data.msg || `${action}失败`)
      }
    } catch (err) {
      const message = err.response?.data?.msg || `${action}失败`
      alert(message)
    }
  })
}

/**
 * 获取头像URL
 */
const getAvatarUrl = (avatar) => {
  if (!avatar) return 'https://via.placeholder.com/40'
  if (avatar.startsWith('http')) return avatar
  return `http://localhost:5001/static/${avatar}`
}

/**
 * 格式化时间
 */
const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * 获取视频数
 */
const getVideoCount = (user) => {
  return user.video_count !== undefined ? user.video_count : '-'
}

/**
 * 切换页码
 */
const handlePageChange = (page) => {
  currentPage.value = page
  fetchUsers()
}

onMounted(() => {
  fetchUsers()
})
</script>

<template>
  <div class="users-container">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <div class="search-input-wrapper">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"></circle>
          <path d="m21 21-4.35-4.35"></path>
        </svg>
        <input
          v-model="keyword"
          type="text"
          placeholder="搜索用户名或昵称..."
          class="search-input"
          @keyup.enter="handleSearch"
        />
      </div>
      <button class="search-btn" @click="handleSearch">
        <span>搜索</span>
      </button>
    </div>

    <!-- 用户列表卡片 -->
    <div class="users-card">
      <div class="card-header">
        <h3 class="card-title">用户列表</h3>
        <span class="card-count">共 {{ total }} 个用户</span>
      </div>
      
      <div class="table-wrapper">
        <table class="users-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>头像/昵称</th>
              <th>用户名</th>
              <th>注册时间</th>
              <th>视频数</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="7" class="loading-cell">
                <div class="loading-spinner"></div>
                <span>加载中...</span>
              </td>
            </tr>
            <tr v-else-if="users.length === 0">
              <td colspan="7" class="empty-cell">
                <div class="empty-icon">📭</div>
                <span>暂无数据</span>
              </td>
            </tr>
            <tr v-else v-for="user in users" :key="user.id" class="table-row">
              <td class="id-cell">{{ user.id }}</td>
              <td>
                <div class="user-avatar-cell">
                  <img 
                    :src="getAvatarUrl(user.avatar)" 
                    :alt="user.nickname"
                    class="user-avatar"
                    @error="(e) => e.target.src = 'https://via.placeholder.com/40'"
                  />
                  <div class="user-info">
                    <span class="user-nickname">{{ user.nickname }}</span>
                    <span :class="['role-tag', user.role === 'admin' ? 'admin-tag' : 'user-tag']">
                      {{ user.role === 'admin' ? '管理员' : '用户' }}
                    </span>
                  </div>
                </div>
              </td>
              <td class="username-cell">{{ user.username }}</td>
              <td class="time-cell">{{ formatTime(user.created_at) }}</td>
              <td class="video-count-cell">{{ getVideoCount(user) }}</td>
              <td>
                <span :class="['status-badge', user.status === 1 ? 'status-active' : 'status-banned']">
                  <span class="status-dot"></span>
                  {{ user.status === 1 ? '正常' : '封禁' }}
                </span>
              </td>
              <td class="action-cell">
                <button
                  v-if="user.status === 1"
                  class="btn-action btn-ban"
                  @click="updateUserStatus(user.id, 0)"
                  :disabled="user.role === 'admin'"
                  :title="user.role === 'admin' ? '不能封禁管理员' : '封禁该用户'"
                >
                  封禁
                </button>
                <button
                  v-else
                  class="btn-action btn-unban"
                  @click="updateUserStatus(user.id, 1)"
                  title="解封该用户"
                >
                  解封
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页 -->
      <div v-if="total > 0" class="pagination">
        <button
          class="page-btn"
          :disabled="currentPage === 1"
          @click="handlePageChange(currentPage - 1)"
        >
          <span>‹</span> 上一页
        </button>
        <div class="page-info">
          <span class="page-current">第 {{ currentPage }} 页</span>
          <span class="page-separator">/</span>
          <span class="page-total">共 {{ Math.ceil(total / pageSize) }} 页</span>
          <span class="page-separator">·</span>
          <span class="page-total-count">共 {{ total }} 条</span>
        </div>
        <button
          class="page-btn"
          :disabled="currentPage >= Math.ceil(total / pageSize)"
          @click="handlePageChange(currentPage + 1)"
        >
          下一页 <span>›</span>
        </button>
      </div>
    </div>

    <!-- 确认对话框 -->
    <div v-if="showConfirm" class="confirm-overlay" @click="closeConfirm">
      <div class="confirm-dialog" @click.stop>
        <div class="confirm-header">
          <h4 class="confirm-title">确认操作</h4>
        </div>
        <div class="confirm-body">
          <p class="confirm-message">
            确定要<strong>{{ confirmAction }}</strong>该用户吗？
          </p>
          <p class="confirm-warning" v-if="confirmStatus === 0">
            ⚠️ 封禁后，该用户的所有内容将不会在公共页面显示
          </p>
        </div>
        <div class="confirm-footer">
          <button class="confirm-btn confirm-btn-cancel" @click="closeConfirm">取消</button>
          <button 
            class="confirm-btn confirm-btn-ok" 
            :class="{ 'btn-ban-confirm': confirmStatus === 0, 'btn-unban-confirm': confirmStatus === 1 }"
            @click="handleConfirm"
          >
            确认{{ confirmAction }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.users-container {
  width: 100%;
}

/* 搜索栏 - 蓝色商务风格 */
.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  align-items: center;
}

.search-input-wrapper {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  width: 18px;
  height: 18px;
  color: #8c8c8c;
  pointer-events: none;
  z-index: 1;
}

.search-input {
  width: 100%;
  height: 44px;
  padding: 0 16px 0 40px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  font-size: 14px;
  background: #fff;
  transition: all 0.3s;
}

.search-input:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
}

.search-btn {
  height: 44px;
  padding: 0 24px;
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s;
  box-shadow: 0 2px 4px rgba(24, 144, 255, 0.2);
}

.search-btn:hover {
  background: linear-gradient(135deg, #40a9ff 0%, #1890ff 100%);
  box-shadow: 0 4px 8px rgba(24, 144, 255, 0.3);
  transform: translateY(-1px);
}

/* 用户列表卡片 - 蓝色商务风格 */
.users-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #262626;
  margin: 0;
}

.card-count {
  font-size: 14px;
  color: #595959;
  background: #e6f7ff;
  padding: 4px 12px;
  border-radius: 12px;
  color: #1890ff;
}

/* 表格包装器 */
.table-wrapper {
  overflow-x: auto;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table thead {
  background: linear-gradient(135deg, #fafafa 0%, #f0f0f0 100%);
}

.users-table th {
  padding: 16px 20px;
  text-align: left;
  font-weight: 600;
  color: #262626;
  font-size: 14px;
  border-bottom: 2px solid #e8e8e8;
  white-space: nowrap;
}

.users-table td {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  color: #595959;
  font-size: 14px;
}

.table-row {
  transition: all 0.2s;
}

.table-row:hover {
  background: #fafafa;
}

.id-cell {
  font-weight: 600;
  color: #1890ff;
  font-family: 'Monaco', 'Courier New', monospace;
}

.username-cell {
  color: #262626;
  font-weight: 500;
}

.time-cell {
  color: #8c8c8c;
  font-size: 13px;
}

.video-count-cell {
  color: #595959;
  font-weight: 500;
}

.action-cell {
  white-space: nowrap;
}

/* 用户头像单元格 */
.user-avatar-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #e8e8e8;
  transition: all 0.3s;
}

.user-avatar:hover {
  border-color: #1890ff;
  transform: scale(1.05);
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-nickname {
  font-weight: 500;
  color: #262626;
  font-size: 14px;
}

.role-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  width: fit-content;
}

.admin-tag {
  background: #fff7e6;
  color: #fa8c16;
}

.user-tag {
  background: #e6f7ff;
  color: #1890ff;
}

/* 加载和空状态 */
.loading-cell,
.empty-cell {
  text-align: center;
  padding: 60px 20px !important;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e8e8e8;
  border-top-color: #1890ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

.loading-cell span,
.empty-cell span {
  color: #8c8c8c;
  font-size: 14px;
}

/* 状态徽章 - 蓝色商务风格 */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
}

.status-active {
  background: #f6ffed;
  color: #52c41a;
}

.status-active .status-dot {
  background: #52c41a;
}

.status-banned {
  background: #fff1f0;
  color: #ff4d4f;
}

.status-banned .status-dot {
  background: #ff4d4f;
}

/* 操作按钮 - 蓝色商务风格 */
.btn-action {
  padding: 6px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.3s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.btn-ban {
  background: linear-gradient(135deg, #ff4d4f 0%, #cf1322 100%);
  color: #fff;
}

.btn-ban:hover:not(:disabled) {
  background: linear-gradient(135deg, #ff7875 0%, #ff4d4f 100%);
  box-shadow: 0 4px 8px rgba(255, 77, 79, 0.3);
  transform: translateY(-1px);
}

.btn-unban {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
  color: #fff;
}

.btn-unban:hover {
  background: linear-gradient(135deg, #73d13d 0%, #52c41a 100%);
  box-shadow: 0 4px 8px rgba(82, 196, 26, 0.3);
  transform: translateY(-1px);
}

.btn-action:disabled {
  background: #d9d9d9;
  color: #fff;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

/* 分页 - 蓝色商务风格 */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 20px 24px;
  border-top: 1px solid #f0f0f0;
}

.page-btn {
  padding: 8px 16px;
  background: #fff;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #595959;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 4px;
}

.page-btn:hover:not(:disabled) {
  border-color: #1890ff;
  color: #1890ff;
  background: #e6f7ff;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #595959;
  font-size: 14px;
}

.page-current {
  color: #1890ff;
  font-weight: 500;
}

.page-separator {
  color: #d9d9d9;
}

.page-total,
.page-total-count {
  color: #8c8c8c;
}

/* 确认对话框 - 蓝色商务风格 */
.confirm-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.confirm-dialog {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  width: 90%;
  max-width: 420px;
  overflow: hidden;
  animation: slideUp 0.3s;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.confirm-header {
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
}

.confirm-title {
  font-size: 18px;
  font-weight: 600;
  color: #262626;
  margin: 0;
}

.confirm-body {
  padding: 24px;
}

.confirm-message {
  font-size: 15px;
  color: #262626;
  line-height: 1.6;
  margin: 0 0 12px 0;
}

.confirm-message strong {
  color: #1890ff;
  font-weight: 600;
}

.confirm-warning {
  font-size: 13px;
  color: #fa8c16;
  background: #fff7e6;
  padding: 10px 12px;
  border-radius: 6px;
  margin: 0;
  border-left: 3px solid #fa8c16;
}

.confirm-footer {
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.confirm-btn {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s;
}

.confirm-btn-cancel {
  background: #f5f5f5;
  color: #595959;
}

.confirm-btn-cancel:hover {
  background: #e8e8e8;
  color: #262626;
}

.confirm-btn-ok {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  color: #fff;
  box-shadow: 0 2px 4px rgba(24, 144, 255, 0.2);
}

.confirm-btn-ok:hover {
  background: linear-gradient(135deg, #40a9ff 0%, #1890ff 100%);
  box-shadow: 0 4px 8px rgba(24, 144, 255, 0.3);
}

.btn-ban-confirm {
  background: linear-gradient(135deg, #ff4d4f 0%, #cf1322 100%);
  box-shadow: 0 2px 4px rgba(255, 77, 79, 0.2);
}

.btn-ban-confirm:hover {
  background: linear-gradient(135deg, #ff7875 0%, #ff4d4f 100%);
  box-shadow: 0 4px 8px rgba(255, 77, 79, 0.3);
}

.btn-unban-confirm {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
  box-shadow: 0 2px 4px rgba(82, 196, 26, 0.2);
}

.btn-unban-confirm:hover {
  background: linear-gradient(135deg, #73d13d 0%, #52c41a 100%);
  box-shadow: 0 4px 8px rgba(82, 196, 26, 0.3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .search-bar {
    flex-direction: column;
  }
  
  .search-input-wrapper,
  .search-btn {
    width: 100%;
  }
  
  .users-table {
    font-size: 12px;
  }
  
  .users-table th,
  .users-table td {
    padding: 12px;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .confirm-dialog {
    width: 95%;
    margin: 20px;
  }
}
</style>
