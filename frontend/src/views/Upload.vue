<script setup>
/**
 * 视频上传页面组件
 * 提供视频上传功能，包含表单验证、文件上传和视频截取封面功能
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import ImageCropperModal from '@/components/ImageCropperModal.vue'

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

// 视频预览相关
const videoPreviewUrl = ref('')  // 视频预览URL
const videoRef = ref(null)        // video元素引用

// 封面预览相关
const coverPreviewUrl = ref('')   // 封面预览URL
const isCaptured = ref(false)     // 是否为截取的封面

// 图片裁切相关
const showCropper = ref(false)
const tempCoverUrl = ref('')
const cropperAspectRatio = ref(16 / 9) // 封面使用16:9比例

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
 * 选择视频后生成预览URL用于播放器展示
 */
const handleVideoChange = (event) => {
  const file = event.target.files[0]
  if (file) {
    videoFile.value = file
    videoFileName.value = file.name
    
    // 释放之前的预览URL（防止内存泄漏）
    if (videoPreviewUrl.value) {
      URL.revokeObjectURL(videoPreviewUrl.value)
    }
    
    // 生成新的视频预览URL
    videoPreviewUrl.value = URL.createObjectURL(file)
  }
}

/**
 * 处理封面文件选择
 * 手动选择封面会覆盖截取的封面
 */
const handleCoverChange = (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  // 验证文件类型
  const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    alert('请选择有效的图片格式 (png, jpg, jpeg, gif, webp)')
    event.target.value = '' // 清空input
    return
  }
  
  // 验证文件大小 (最大 10MB)
  if (file.size > 10 * 1024 * 1024) {
    alert('封面图片大小不能超过 10MB')
    event.target.value = '' // 清空input
    return
  }
  
  // 读取文件为Base64并打开裁切框
  const reader = new FileReader()
  reader.onload = (e) => {
    tempCoverUrl.value = e.target.result
    cropperAspectRatio.value = 16 / 9 // 封面使用16:9比例
    showCropper.value = true
  }
  reader.readAsDataURL(file)
  
  // 清空input，以便下次选择同一文件也能触发change事件
  event.target.value = ''
}

/**
 * 处理裁切完成
 */
const handleCropConfirm = (blob) => {
  // 将Blob转换为File对象
  const file = new File([blob], 'cover_cropped.png', { type: 'image/png' })
  coverFile.value = file
  coverFileName.value = 'cover_cropped.png'
  isCaptured.value = false // 标记为非截取（而是裁切）
  
  // 释放之前的预览URL
  if (coverPreviewUrl.value) {
    URL.revokeObjectURL(coverPreviewUrl.value)
  }
  
  // 创建预览URL
  coverPreviewUrl.value = URL.createObjectURL(blob)
}

/**
 * 从视频截取当前帧作为封面
 * 使用 Canvas API 抓取视频画面并转换为图片文件
 */
const captureFrame = () => {
  const videoEl = videoRef.value
  
  // 检查视频元素是否存在且已加载
  if (!videoEl || videoEl.readyState < 2) {
    alert('请等待视频加载完成后再截取')
    return
  }
  
  // 创建 Canvas 元素
  const canvas = document.createElement('canvas')
  canvas.width = videoEl.videoWidth
  canvas.height = videoEl.videoHeight
  
  // 在 Canvas 上绘制当前视频帧
  const ctx = canvas.getContext('2d')
  ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height)
  
  // 将 Canvas 内容转换为 Blob
  canvas.toBlob((blob) => {
    if (!blob) {
      alert('截取失败，请重试')
      return
    }
    
    // 将 Blob 转换为 File 对象（模拟上传文件）
    const file = new File([blob], 'cover_snapshot.jpg', { type: 'image/jpeg' })
    
    // 更新封面文件
    coverFile.value = file
    coverFileName.value = '已截取: cover_snapshot.jpg'
    isCaptured.value = true  // 标记为截取的封面
    
    // 释放之前的预览URL
    if (coverPreviewUrl.value) {
      URL.revokeObjectURL(coverPreviewUrl.value)
    }
    
    // 生成预览图URL
    coverPreviewUrl.value = URL.createObjectURL(blob)
  }, 'image/jpeg', 0.9)  // JPEG格式，90%质量
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

// 页面卸载时释放预览URL，防止内存泄漏
onUnmounted(() => {
  if (videoPreviewUrl.value) {
    URL.revokeObjectURL(videoPreviewUrl.value)
  }
  if (coverPreviewUrl.value) {
    URL.revokeObjectURL(coverPreviewUrl.value)
  }
})
</script>

<template>
  <div class="upload-container">
    <!-- 独立顶部工具栏 -->
    <header class="upload-header">
      <button class="exit-btn" @click="goBack">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        <span>退出创作</span>
      </button>
      <h1 class="header-title">投稿工作室</h1>
      <div class="header-spacer"></div>
    </header>

    <!-- 内容区域 -->
    <div class="upload-card">

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

        <!-- 视频预览区域（选择视频后显示） -->
        <div v-if="videoPreviewUrl" class="form-group">
          <label>视频预览 <span class="hint-inline">（拖动进度条选择封面画面）</span></label>
          <div class="video-preview-container">
            <video 
              ref="videoRef"
              :src="videoPreviewUrl" 
              controls
              class="video-preview"
            >
              您的浏览器不支持视频播放
            </video>
            <button 
              type="button" 
              class="capture-btn"
              @click="captureFrame"
            >
              📷 截取当前帧作为封面
            </button>
          </div>
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
              <span v-if="coverFileName" :class="{ 'captured-text': isCaptured }">{{ coverFileName }}</span>
              <span v-else>点击选择封面图片（或从视频截取）</span>
            </label>
          </div>
          <span class="hint">支持格式：jpg, jpeg, png, gif, webp；也可以从上方视频截取</span>
          
          <!-- 封面预览（截取或手动选择后显示） -->
          <div v-if="coverPreviewUrl" class="cover-preview-container">
            <img :src="coverPreviewUrl" alt="封面预览" class="cover-preview" />
            <span v-if="isCaptured" class="capture-badge">已截取</span>
          </div>
        </div>

        <!-- 提交按钮 -->
        <button type="submit" class="submit-btn" :disabled="loading">
          {{ loading ? '上传中...' : '提交上传' }}
        </button>
      </form>
    </div>

    <!-- 图片裁切弹窗 -->
    <ImageCropperModal
      :visible="showCropper"
      :img-src="tempCoverUrl"
      :aspect-ratio="cropperAspectRatio"
      @update:visible="showCropper = $event"
      @confirm="handleCropConfirm"
    />
  </div>
</template>

<style scoped>
/* 页面容器 */
.upload-container {
  min-height: 100vh;
  background-color: #f4f5f7;
  display: flex;
  flex-direction: column;
}

/* ==================== 顶部工具栏 ==================== */
.upload-header {
  position: sticky;
  top: 0;
  z-index: 100;
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #E3E5E7;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.exit-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: none;
  border: 1px solid #E3E5E7;
  border-radius: 4px;
  color: #18191C;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.exit-btn:hover {
  background: #F6F7F8;
  border-color: #C9CCD0;
  color: #FF5252;
}

.exit-btn svg {
  transition: transform 0.2s ease;
}

.exit-btn:hover svg {
  transform: translateX(-2px);
}

.header-title {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  font-size: 18px;
  font-weight: 600;
  color: #18191C;
  margin: 0;
}

.header-spacer {
  width: 120px; /* 占位，保持居中 */
}

/* ==================== 内容区域 ==================== */
.upload-card {
  width: 100%;
  max-width: 700px;
  margin: 40px auto;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  padding: 40px;
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

.hint-inline {
  font-size: 12px;
  color: #999;
  font-weight: normal;
}

/* 视频预览区域 */
.video-preview-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
}

.video-preview {
  width: 100%;
  max-height: 300px;
  border-radius: 8px;
  background: #000;
}

/* 截取封面按钮 */
.capture-btn {
  padding: 12px 20px;
  background-color: #409eff;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.capture-btn:hover {
  background-color: #66b1ff;
}

/* 封面预览区域 */
.cover-preview-container {
  position: relative;
  margin-top: 12px;
  display: inline-block;
}

.cover-preview {
  max-width: 200px;
  max-height: 150px;
  border-radius: 8px;
  border: 2px solid #67c23a;
  object-fit: cover;
}

.capture-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: #67c23a;
  color: #fff;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.captured-text {
  color: #67c23a;
  font-weight: 500;
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
