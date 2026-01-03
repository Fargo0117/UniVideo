<script setup>
/**
 * 个人主页组件
 * 展示用户资料、我的投稿、我的收藏
 * 支持修改昵称、密码、头像
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()

// ==================== 数据定义 ====================

// 用户信息
const userInfo = ref(null)
const userLoading = ref(true)

// 当前用户ID
const currentUserId = localStorage.getItem('user_id')

// 选项卡状态
const activeTab = ref('videos') // 'videos' | 'collections'

// 我的投稿
const myVideos = ref([])
const videosLoading = ref(false)

// 我的收藏
const myCollections = ref([])
const collectionsLoading = ref(false)

// 修改资料弹窗
const showEditModal = ref(false)
const editForm = ref({
  nickname: '',
  password: ''
})
const avatarFile = ref(null)
const avatarPreview = ref('')
const editSubmitting = ref(false)

// ==================== 工具函数 ====================

/**
 * 获取完整的资源URL
 */
const getFullUrl = (path) => {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `http://localhost:5001${path}`
}

/**
 * 格式化时间显示
 */
const formatTime = (isoString) => {
  if (!isoString) return ''
  const date = new Date(isoString)
  return date.toLocaleDateString('zh-CN')
}

/**
 * 获取视频状态文本
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
 * 获取视频状态样式类
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
 * 获取用户信息
 */
const fetchUserInfo = async () => {
  if (!currentUserId) {
    router.push('/login')
    return
  }
  
  userLoading.value = true
  try {
    const response = await api.get('/users/me', {
      params: { user_id: currentUserId }
    })
    userInfo.value = response.data.data
    // 初始化编辑表单
    editForm.value.nickname = userInfo.value.nickname
  } catch (err) {
    console.error('获取用户信息失败:', err)
    alert('获取用户信息失败')
  } finally {
    userLoading.value = false
  }
}

/**
 * 获取我的投稿
 */
const fetchMyVideos = async () => {
  videosLoading.value = true
  try {
    const response = await api.get('/users/me/videos', {
      params: { user_id: currentUserId }
    })
    myVideos.value = response.data.data?.list || []
  } catch (err) {
    console.error('获取我的投稿失败:', err)
    myVideos.value = []
  } finally {
    videosLoading.value = false
  }
}

/**
 * 获取我的收藏
 */
const fetchMyCollections = async () => {
  collectionsLoading.value = true
  try {
    const response = await api.get('/users/me/collections', {
      params: { user_id: currentUserId }
    })
    myCollections.value = response.data.data?.list || []
  } catch (err) {
    console.error('获取我的收藏失败:', err)
    myCollections.value = []
  } finally {
    collectionsLoading.value = false
  }
}

/**
 * 切换选项卡
 */
const switchTab = (tab) => {
  activeTab.value = tab
  if (tab === 'videos' && myVideos.value.length === 0) {
    fetchMyVideos()
  } else if (tab === 'collections' && myCollections.value.length === 0) {
    fetchMyCollections()
  }
}

/**
 * 打开修改资料弹窗
 */
const openEditModal = () => {
  editForm.value.nickname = userInfo.value?.nickname || ''
  editForm.value.password = ''
  avatarFile.value = null
  avatarPreview.value = ''
  showEditModal.value = true
}

/**
 * 关闭修改资料弹窗
 */
const closeEditModal = () => {
  showEditModal.value = false
}

/**
 * 处理头像文件选择
 */
const handleAvatarChange = (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  // 验证文件类型
  const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    alert('请选择有效的图片格式 (png, jpg, jpeg, gif, webp)')
    return
  }
  
  // 验证文件大小 (最大 5MB)
  if (file.size > 5 * 1024 * 1024) {
    alert('图片大小不能超过 5MB')
    return
  }
  
  avatarFile.value = file
  // 预览图片
  const reader = new FileReader()
  reader.onload = (e) => {
    avatarPreview.value = e.target.result
  }
  reader.readAsDataURL(file)
}

/**
 * 提交修改资料
 */
const submitEdit = async () => {
  // 验证昵称
  if (!editForm.value.nickname.trim()) {
    alert('昵称不能为空')
    return
  }
  
  if (editForm.value.nickname.length < 2 || editForm.value.nickname.length > 50) {
    alert('昵称长度需要在2-50个字符之间')
    return
  }
  
  // 验证密码（如果填写了）
  if (editForm.value.password && editForm.value.password.length < 6) {
    alert('密码长度至少6位')
    return
  }
  
  editSubmitting.value = true
  try {
    // 使用 FormData 提交（支持文件上传）
    const formData = new FormData()
    formData.append('user_id', currentUserId)
    formData.append('nickname', editForm.value.nickname.trim())
    
    if (editForm.value.password) {
      formData.append('password', editForm.value.password)
    }
    
    if (avatarFile.value) {
      formData.append('avatar', avatarFile.value)
    }
    
    const response = await api.put('/users/me', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    // 更新本地数据
    userInfo.value = response.data.data
    localStorage.setItem('nickname', userInfo.value.nickname)
    
    alert('资料更新成功')
    closeEditModal()
  } catch (err) {
    const message = err.response?.data?.msg || '更新失败'
    alert(message)
  } finally {
    editSubmitting.value = false
  }
}

/**
 * 跳转到视频详情页
 */
const goToVideo = (videoId) => {
  router.push(`/video/${videoId}`)
}

/**
 * 返回首页
 */
const goBack = () => {
  router.push('/')
}

// ==================== 生命周期 ====================

onMounted(() => {
  fetchUserInfo()
  fetchMyVideos()  // 默认加载我的投稿
})
</script>

<template>
  <div class="profile-container">
    <!-- 顶部导航 -->
    <header class="nav-bar">
      <button class="back-btn" @click="goBack">&larr; 返回首页</button>
      <span class="site-name">UniVideo - 个人主页</span>
    </header>

    <!-- 加载状态 -->
    <div v-if="userLoading" class="loading-state">
      <p>加载中...</p>
    </div>

    <!-- 主内容 -->
    <main v-else class="profile-content">
      <!-- 用户资料卡 -->
      <section class="user-card">
        <div class="avatar-wrapper">
          <img 
            class="user-avatar" 
            :src="getFullUrl(userInfo?.avatar) || 'https://via.placeholder.com/100'"
            :alt="userInfo?.nickname"
            @error="(e) => e.target.src = 'https://via.placeholder.com/100'"
          />
        </div>
        <div class="user-info">
          <h2 class="user-nickname">{{ userInfo?.nickname || '用户' }}</h2>
          <p class="user-meta">
            <span>用户名：{{ userInfo?.username }}</span>
            <span class="separator">|</span>
            <span>注册时间：{{ formatTime(userInfo?.created_at) }}</span>
          </p>
        </div>
        <button class="btn btn-primary edit-btn" @click="openEditModal">修改资料</button>
      </section>

      <!-- 选项卡 -->
      <section class="tabs-section">
        <div class="tabs-header">
          <button 
            class="tab-btn" 
            :class="{ active: activeTab === 'videos' }"
            @click="switchTab('videos')"
          >
            我的投稿 ({{ myVideos.length }})
          </button>
          <button 
            class="tab-btn" 
            :class="{ active: activeTab === 'collections' }"
            @click="switchTab('collections')"
          >
            我的收藏 ({{ myCollections.length }})
          </button>
        </div>

        <!-- 我的投稿内容 -->
        <div v-if="activeTab === 'videos'" class="tab-content">
          <div v-if="videosLoading" class="loading-state">
            <p>加载中...</p>
          </div>
          <div v-else-if="myVideos.length === 0" class="empty-state">
            <p>暂无投稿，快去上传你的第一个视频吧！</p>
            <button class="btn btn-primary" @click="$router.push('/upload')">上传视频</button>
          </div>
          <div v-else class="video-grid">
            <div 
              v-for="video in myVideos" 
              :key="video.id" 
              class="video-card"
              @click="goToVideo(video.id)"
            >
              <div class="video-cover">
                <img :src="video.cover_url" :alt="video.title" />
                <!-- 状态标签 -->
                <span class="status-tag" :class="getStatusClass(video.status)">
                  {{ getStatusText(video.status) }}
                </span>
              </div>
              <div class="video-info">
                <h3 class="video-title">{{ video.title }}</h3>
                <div class="video-stats">
                  <span>{{ video.view_count || 0 }} 播放</span>
                  <span>{{ video.likes_count || 0 }} 点赞</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 我的收藏内容 -->
        <div v-if="activeTab === 'collections'" class="tab-content">
          <div v-if="collectionsLoading" class="loading-state">
            <p>加载中...</p>
          </div>
          <div v-else-if="myCollections.length === 0" class="empty-state">
            <p>暂无收藏，去发现更多有趣的视频吧！</p>
            <button class="btn btn-primary" @click="goBack">浏览视频</button>
          </div>
          <div v-else class="video-grid">
            <div 
              v-for="video in myCollections" 
              :key="video.id" 
              class="video-card"
              @click="goToVideo(video.id)"
            >
              <div class="video-cover">
                <img :src="video.cover_url" :alt="video.title" />
              </div>
              <div class="video-info">
                <h3 class="video-title">{{ video.title }}</h3>
                <div class="video-meta">
                  <span class="author">{{ video.author?.nickname || '未知作者' }}</span>
                </div>
                <div class="video-stats">
                  <span>{{ video.view_count || 0 }} 播放</span>
                  <span>{{ video.likes_count || 0 }} 点赞</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- 修改资料弹窗 -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>修改资料</h3>
          <button class="close-btn" @click="closeEditModal">&times;</button>
        </div>
        <div class="modal-body">
          <!-- 头像上传 -->
          <div class="form-group avatar-group">
            <label>头像</label>
            <div class="avatar-upload">
              <img 
                class="avatar-preview" 
                :src="avatarPreview || getFullUrl(userInfo?.avatar) || 'https://via.placeholder.com/80'"
                alt="头像预览"
              />
              <input 
                type="file" 
                accept="image/png,image/jpeg,image/jpg,image/gif,image/webp"
                @change="handleAvatarChange"
                id="avatar-input"
                class="hidden-input"
              />
              <label for="avatar-input" class="upload-label">选择图片</label>
            </div>
          </div>
          
          <!-- 昵称 -->
          <div class="form-group">
            <label for="nickname">昵称</label>
            <input 
              type="text" 
              id="nickname"
              v-model="editForm.nickname"
              placeholder="请输入昵称"
              maxlength="50"
            />
          </div>
          
          <!-- 新密码 -->
          <div class="form-group">
            <label for="password">新密码（不修改请留空）</label>
            <input 
              type="password" 
              id="password"
              v-model="editForm.password"
              placeholder="请输入新密码"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeEditModal">取消</button>
          <button 
            class="btn btn-primary" 
            @click="submitEdit"
            :disabled="editSubmitting"
          >
            {{ editSubmitting ? '保存中...' : '保存修改' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ==================== 全局布局 ==================== */
.profile-container {
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

/* 加载/空状态 */
.loading-state,
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.empty-state .btn {
  margin-top: 16px;
}

/* 主内容 */
.profile-content {
  max-width: 1000px;
  margin: 0 auto;
  padding: 24px;
}

/* ==================== 用户资料卡 ==================== */
.user-card {
  display: flex;
  align-items: center;
  gap: 24px;
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.avatar-wrapper {
  flex-shrink: 0;
}

.user-avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #f0f0f0;
}

.user-info {
  flex: 1;
}

.user-nickname {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px 0;
}

.user-meta {
  font-size: 14px;
  color: #999;
  margin: 0;
}

.user-meta .separator {
  margin: 0 12px;
  color: #ddd;
}

.edit-btn {
  flex-shrink: 0;
}

/* ==================== 选项卡 ==================== */
.tabs-section {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.tabs-header {
  display: flex;
  border-bottom: 1px solid #f0f0f0;
}

.tab-btn {
  flex: 1;
  padding: 16px;
  background: none;
  border: none;
  font-size: 15px;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
  border-bottom: 2px solid transparent;
}

.tab-btn:hover {
  color: #409eff;
  background: #f9f9f9;
}

.tab-btn.active {
  color: #409eff;
  font-weight: 500;
  border-bottom-color: #409eff;
}

.tab-content {
  padding: 24px;
  min-height: 300px;
}

/* ==================== 视频网格 ==================== */
.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 20px;
}

.video-card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
  border: 1px solid #f0f0f0;
}

.video-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.video-cover {
  position: relative;
  width: 100%;
  padding-top: 56.25%;
  background-color: #f0f0f0;
  overflow: hidden;
}

.video-cover img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 状态标签 */
.status-tag {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-pending {
  background: #fff7e6;
  color: #fa8c16;
}

.status-published {
  background: #f6ffed;
  color: #52c41a;
}

.status-rejected {
  background: #fff2f0;
  color: #ff4d4f;
}

.video-info {
  padding: 12px;
}

.video-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin: 0 0 8px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
}

.video-meta {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.video-stats {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #999;
}

/* ==================== 按钮样式 ==================== */
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

/* ==================== 弹窗样式 ==================== */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #fff;
  border-radius: 12px;
  width: 90%;
  max-width: 420px;
  max-height: 90vh;
  overflow-y: auto;
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
  font-size: 18px;
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
  color: #666;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
}

.form-group input[type="text"],
.form-group input[type="password"] {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #409eff;
}

/* 头像上传 */
.avatar-group {
  text-align: center;
}

.avatar-upload {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.avatar-preview {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #f0f0f0;
}

.hidden-input {
  display: none;
}

.upload-label {
  padding: 8px 16px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
}

.upload-label:hover {
  background: #e8e8e8;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #f0f0f0;
}
</style>
