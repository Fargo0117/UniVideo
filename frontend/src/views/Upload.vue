<script setup>
/**
 * 视频上传页面组件
 * 提供视频上传功能，包含表单验证和文件上传
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()

// 表单数据
const title = ref('')
const description = ref('')
const categoryId = ref('')
const videoFile = ref(null)
const coverFile = ref(null)

// 分类列表
const categories = ref([])

// 文件名显示
const videoFileName = ref('')
const coverFileName = ref('')

// 加载状态
const loading = ref(false)
const categoriesLoading = ref(true)

/**
 * 获取分类列表
 */
const fetchCategories = async () => {
  categoriesLoading.value = true
  try {
    const response = await api.get('/videos/categories')
    categories.value = response.data.data || []
  } catch (error) {
    console.error('获取分类失败:', error)
    alert('获取分类列表失败')
  } finally {
    categoriesLoading.value = false
  }
}

/**
 * 处理视频文件选择
 */
const handleVideoChange = (event) => {
  const file = event.target.files[0]
  if (file) {
    videoFile.value = file
    videoFileName.value = file.name
  }
}

/**
 * 处理封面文件选择
 */
const handleCoverChange = (event) => {
  const file = event.target.files[0]
  if (file) {
    coverFile.value = file
    coverFileName.value = file.name
  }
}

/**
 * 提交上传表单
 */
const handleSubmit = async () => {
  // 表单验证
  if (!title.value.trim()) {
    alert('请输入视频标题')
    return
  }
  if (!categoryId.value) {
    alert('请选择视频分类')
    return
  }
  if (!videoFile.value) {
    alert('请选择视频文件')
    return
  }
  if (!coverFile.value) {
    alert('请选择封面图片')
    return
  }

  // 获取当前用户ID
  const userId = localStorage.getItem('user_id')
  if (!userId) {
    alert('请先登录')
    router.push('/login')
    return
  }

  loading.value = true

  try {
    // 使用 FormData 包装所有数据
    const formData = new FormData()
    formData.append('user_id', userId)
    formData.append('title', title.value.trim())
    formData.append('description', description.value.trim())
    formData.append('category_id', categoryId.value)
    formData.append('video_file', videoFile.value)
    formData.append('cover_file', coverFile.value)

    // 调用上传接口
    const response = await api.post('/videos/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    // 根据后端返回的消息显示提示（后端已根据角色返回不同信息）
    alert(response.data.msg || '上传成功')
    // 跳转回首页
    router.push('/')
  } catch (error) {
    // 显示错误信息（后端返回格式为 { code, msg, data }）
    const message = error.response?.data?.msg || '上传失败，请稍后重试'
    alert(message)
  } finally {
    loading.value = false
  }
}

/**
 * 返回首页
 */
const goBack = () => {
  router.push('/')
}

// 页面加载时获取分类
onMounted(() => {
  fetchCategories()
})
</script>

<template>
  <div class="upload-container">
    <div class="upload-card">
      <!-- 页面标题 -->
      <div class="card-header">
        <button class="back-btn" @click="goBack">&larr; 返回</button>
        <h2 class="title">上传视频</h2>
      </div>

      <!-- 上传表单 -->
      <form class="upload-form" @submit.prevent="handleSubmit">
        <!-- 标题输入 -->
        <div class="form-group">
          <label for="title">视频标题 <span class="required">*</span></label>
          <input
            id="title"
            v-model="title"
            type="text"
            placeholder="请输入视频标题"
            maxlength="100"
          />
        </div>

        <!-- 简介输入 -->
        <div class="form-group">
          <label for="description">视频简介</label>
          <textarea
            id="description"
            v-model="description"
            placeholder="请输入视频简介（可选）"
            rows="4"
            maxlength="500"
          ></textarea>
        </div>

        <!-- 分类选择 -->
        <div class="form-group">
          <label for="category">视频分类 <span class="required">*</span></label>
          <select id="category" v-model="categoryId" :disabled="categoriesLoading">
            <option value="" disabled>
              {{ categoriesLoading ? '加载中...' : '请选择分类' }}
            </option>
            <option 
              v-for="category in categories" 
              :key="category.id" 
              :value="category.id"
            >
              {{ category.name }}
            </option>
          </select>
        </div>

        <!-- 视频文件选择 -->
        <div class="form-group">
          <label>视频文件 <span class="required">*</span></label>
          <div class="file-input-wrapper">
            <input
              type="file"
              accept="video/mp4,video/avi,video/mov,video/mkv,video/flv,video/wmv"
              @change="handleVideoChange"
              id="video-file"
            />
            <label for="video-file" class="file-input-label">
              <span v-if="videoFileName">{{ videoFileName }}</span>
              <span v-else>点击选择视频文件</span>
            </label>
          </div>
          <span class="hint">支持格式：mp4, avi, mov, mkv, flv, wmv</span>
        </div>

        <!-- 封面图片选择 -->
        <div class="form-group">
          <label>封面图片 <span class="required">*</span></label>
          <div class="file-input-wrapper">
            <input
              type="file"
              accept="image/jpeg,image/jpg,image/png,image/gif,image/webp"
              @change="handleCoverChange"
              id="cover-file"
            />
            <label for="cover-file" class="file-input-label">
              <span v-if="coverFileName">{{ coverFileName }}</span>
              <span v-else>点击选择封面图片</span>
            </label>
          </div>
          <span class="hint">支持格式：jpg, jpeg, png, gif, webp</span>
        </div>

        <!-- 提交按钮 -->
        <button type="submit" class="submit-btn" :disabled="loading">
          {{ loading ? '上传中...' : '提交上传' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
/* 页面容器 */
.upload-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
  padding: 24px;
}

/* 上传卡片 */
.upload-card {
  width: 100%;
  max-width: 600px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 32px;
}

/* 卡片头部 */
.card-header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

.back-btn {
  background: none;
  border: none;
  color: #409eff;
  font-size: 14px;
  cursor: pointer;
  padding: 4px 8px;
  margin-right: 16px;
}

.back-btn:hover {
  text-decoration: underline;
}

.title {
  font-size: 24px;
  color: #333;
  margin: 0;
}

/* 表单样式 */
.upload-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  margin-bottom: 8px;
  color: #666;
  font-size: 14px;
}

.required {
  color: #f56c6c;
}

.form-group input[type="text"],
.form-group textarea,
.form-group select {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: #409eff;
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

/* 文件选择样式 */
.file-input-wrapper {
  position: relative;
}

.file-input-wrapper input[type="file"] {
  position: absolute;
  opacity: 0;
  width: 100%;
  height: 100%;
  cursor: pointer;
}

.file-input-label {
  display: block;
  padding: 24px;
  border: 2px dashed #ddd;
  border-radius: 4px;
  text-align: center;
  color: #999;
  cursor: pointer;
  transition: border-color 0.3s, color 0.3s;
}

.file-input-label:hover {
  border-color: #409eff;
  color: #409eff;
}

/* 提示文字 */
.hint {
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}

/* 提交按钮 */
.submit-btn {
  width: 100%;
  padding: 14px;
  background-color: #67c23a;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
  margin-top: 12px;
}

.submit-btn:hover {
  background-color: #85ce61;
}

.submit-btn:disabled {
  background-color: #b3e19d;
  cursor: not-allowed;
}
</style>
