<script setup>
/**
 * 管理后台用户管理页面
 * 显示用户列表，支持搜索和封禁/解封操作
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
 * 更新用户状态
 */
const updateUserStatus = async (userId, status) => {
  const action = status === 0 ? '封禁' : '解封'
  if (!confirm(`确定要${action}该用户吗？`)) {
    return
  }
  
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
  return date.toLocaleString('zh-CN')
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
      <input
        v-model="keyword"
        type="text"
        placeholder="搜索用户名..."
        class="search-input"
        @keyup.enter="handleSearch"
      />
      <button class="search-btn" @click="handleSearch">搜索</button>
    </div>

    <!-- 用户列表 -->
    <div class="users-table-container">
      <table class="users-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>头像+昵称</th>
            <th>用户名</th>
            <th>角色</th>
            <th>状态</th>
            <th>注册时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="7" class="loading-cell">加载中...</td>
          </tr>
          <tr v-else-if="users.length === 0">
            <td colspan="7" class="empty-cell">暂无数据</td>
          </tr>
          <tr v-else v-for="user in users" :key="user.id" :class="{ 'banned-row': user.status === 0 }">
            <td>{{ user.id }}</td>
            <td>
              <div class="user-avatar-cell">
                <img 
                  :src="getAvatarUrl(user.avatar)" 
                  :alt="user.nickname"
                  class="user-avatar"
                  @error="(e) => e.target.src = 'https://via.placeholder.com/40'"
                />
                <span class="user-nickname">{{ user.nickname }}</span>
              </div>
            </td>
            <td>{{ user.username }}</td>
            <td>
              <span :class="['role-badge', user.role === 'admin' ? 'admin' : 'user']">
                {{ user.role === 'admin' ? '管理员' : '用户' }}
              </span>
            </td>
            <td>
              <span :class="['status-badge', user.status === 1 ? 'active' : 'banned']">
                {{ user.status === 1 ? '正常' : '封禁' }}
              </span>
            </td>
            <td>{{ formatTime(user.created_at) }}</td>
            <td>
              <button
                v-if="user.status === 1"
                class="btn-action btn-ban"
                @click="updateUserStatus(user.id, 0)"
                :disabled="user.role === 'admin'"
              >
                封禁
              </button>
              <button
                v-else
                class="btn-action btn-unban"
                @click="updateUserStatus(user.id, 1)"
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
        上一页
      </button>
      <span class="page-info">
        第 {{ currentPage }} 页，共 {{ Math.ceil(total / pageSize) }} 页，共 {{ total }} 条
      </span>
      <button
        class="page-btn"
        :disabled="currentPage >= Math.ceil(total / pageSize)"
        @click="handlePageChange(currentPage + 1)"
      >
        下一页
      </button>
    </div>
  </div>
</template>

<style scoped>
.users-container {
  width: 100%;
}

/* 搜索栏 */
.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.search-input {
  flex: 1;
  height: 40px;
  padding: 0 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
}

.search-input:focus {
  outline: none;
  border-color: #1890ff;
}

.search-btn {
  height: 40px;
  padding: 0 24px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.search-btn:hover {
  background: #40a9ff;
}

/* 表格容器 */
.users-table-container {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table thead {
  background: #fafafa;
}

.users-table th {
  padding: 16px;
  text-align: left;
  font-weight: 600;
  color: #262626;
  border-bottom: 1px solid #f0f0f0;
}

.users-table td {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  color: #595959;
}

.users-table tbody tr:hover {
  background: #fafafa;
}

.users-table tbody tr.banned-row {
  background-color: #fff1f0;
  color: #ff4d4f;
}

.users-table tbody tr.banned-row:hover {
  background-color: #ffe7e7;
}

.users-table tbody tr.banned-row td {
  color: #ff4d4f;
  opacity: 0.8;
}

/* 用户头像单元格 */
.user-avatar-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #f0f0f0;
}

.user-nickname {
  font-weight: 500;
}

.loading-cell,
.empty-cell {
  text-align: center;
  color: #8c8c8c;
  padding: 40px !important;
}

/* 角色和状态徽章 */
.role-badge,
.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.role-badge.admin {
  background: #fff7e6;
  color: #fa8c16;
}

.role-badge.user {
  background: #f6ffed;
  color: #52c41a;
}

.status-badge.active {
  background: #f6ffed;
  color: #52c41a;
}

.status-badge.banned {
  background: #fff1f0;
  color: #ff4d4f;
}

/* 操作按钮 */
.btn-action {
  padding: 4px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s;
}

.btn-ban {
  background: #ff4d4f;
  color: #fff;
}

.btn-ban:hover:not(:disabled) {
  background: #ff7875;
}

.btn-unban {
  background: #52c41a;
  color: #fff;
}

.btn-unban:hover {
  background: #73d13d;
}

.btn-action:disabled {
  background: #d9d9d9;
  color: #fff;
  cursor: not-allowed;
}

/* 分页 */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 24px;
}

.page-btn {
  padding: 6px 16px;
  background: #fff;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.page-btn:hover:not(:disabled) {
  border-color: #1890ff;
  color: #1890ff;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: #595959;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .users-table {
    font-size: 12px;
  }
  
  .users-table th,
  .users-table td {
    padding: 8px;
  }
  
  .search-bar {
    flex-direction: column;
  }
  
  .search-input,
  .search-btn {
    width: 100%;
  }
}
</style>
