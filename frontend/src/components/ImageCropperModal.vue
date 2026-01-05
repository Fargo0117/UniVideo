<template>
  <div v-if="visible" class="cropper-modal-overlay" @click.self="handleClose">
    <div class="cropper-modal-content">
      <div class="cropper-modal-header">
        <h3>裁切图片</h3>
        <button class="close-btn" @click="handleClose">&times;</button>
      </div>
      
      <div class="cropper-modal-body">
        <vue-cropper
          ref="cropper"
          :src="imgSrc"
          :aspect-ratio="aspectRatio"
          :view-mode="1"
          :drag-mode="'move'"
          :guides="true"
          :background="false"
          :auto-crop-area="1"
          :responsive="true"
          :restore="false"
          :check-cross-origin="true"
          :check-orientation="true"
          :modal="true"
          :scalable="true"
          :zoomable="true"
          :zoom-on-wheel="true"
          :crop-box-movable="true"
          :crop-box-resizable="true"
        />
      </div>
      
      <div class="cropper-modal-footer">
        <button class="btn btn-cancel" @click="handleClose">取消</button>
        <button class="btn btn-confirm" @click="handleConfirm">确认裁切</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import VueCropper from 'vue-cropperjs'
import 'vue-cropperjs/node_modules/cropperjs/dist/cropper.css'

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    required: true,
    default: false
  },
  imgSrc: {
    type: String,
    required: true,
    default: ''
  },
  aspectRatio: {
    type: Number,
    default: 1 / 1 // 默认正方形
  }
})

// Emits
const emit = defineEmits(['update:visible', 'confirm'])

// Ref
const cropper = ref(null)

// Methods
const handleClose = () => {
  emit('update:visible', false)
}

const handleConfirm = () => {
  if (cropper.value && cropper.value.cropper) {
    // 获取裁切后的canvas并转换为Blob
    cropper.value.cropper.getCroppedCanvas().toBlob((blob) => {
      if (blob) {
        emit('confirm', blob)
        handleClose()
      }
    }, 'image/png', 0.9) // 使用PNG格式，质量90%
  }
}
</script>

<style scoped>
.cropper-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.cropper-modal-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.cropper-modal-header {
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cropper-modal-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 32px;
  line-height: 1;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.3s;
}

.close-btn:hover {
  color: #333;
}

.cropper-modal-body {
  padding: 20px;
  flex: 1;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.cropper-modal-body :deep(.vue-cropper) {
  width: 100%;
  height: 100%;
  max-height: 500px;
}

.cropper-modal-footer {
  padding: 20px;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn {
  padding: 10px 24px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-cancel {
  background-color: #f5f5f5;
  color: #666;
}

.btn-cancel:hover {
  background-color: #e0e0e0;
}

.btn-confirm {
  background-color: #4CAF50;
  color: white;
}

.btn-confirm:hover {
  background-color: #45a049;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .cropper-modal-content {
    width: 95%;
  }
  
  .cropper-modal-body {
    min-height: 300px;
  }
  
  .cropper-modal-body :deep(.vue-cropper) {
    max-height: 400px;
  }
}
</style>
