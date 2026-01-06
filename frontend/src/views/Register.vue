<script setup>
/**
 * 注册页面组件
 * 提供用户注册功能，成功后跳转到登录页
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()

// 表单数据
const username = ref('')
const nickname = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

/**
 * 处理注册请求
 * 调用后端注册接口，成功后跳转到登录页
 */
const handleRegister = async () => {
  // 清空之前的错误信息
  errorMessage.value = ''
  
  // 表单验证
  if (!username.value || !nickname.value || !password.value) {
    errorMessage.value = '请填写所有必填项'
    return
  }

  // 密码长度验证（后端要求至少6位）
  if (password.value.length < 6) {
    errorMessage.value = '密码长度至少6位'
    return
  }

  loading.value = true
  try {
    // 调用注册接口
    await api.post('/auth/register', {
      username: username.value,
      nickname: nickname.value,
      password: password.value
    })

    alert('注册成功，请登录')
    // 跳转到登录页
    router.push('/login')
  } catch (error) {
    // 显示错误信息（后端返回格式为 { code, msg, data }）
    errorMessage.value = error.response?.data?.msg || '注册失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-container">
    <div class="auth-card">
      <!-- Logo 区域 -->
      <div class="logo-area">
        <h1 class="logo-text">UniVideo</h1>
      </div>
      
      <h2 class="title">用户注册</h2>
      
      <div class="form-group">
        <label for="username">学号/用户名</label>
        <input
          id="username"
          v-model="username"
          type="text"
          placeholder="请输入学号或用户名"
          @input="errorMessage = ''"
        />
      </div>

      <div class="form-group">
        <label for="nickname">昵称</label>
        <input
          id="nickname"
          v-model="nickname"
          type="text"
          placeholder="请输入昵称"
          @input="errorMessage = ''"
        />
      </div>

      <div class="form-group">
        <label for="password">密码</label>
        <input
          id="password"
          v-model="password"
          type="password"
          placeholder="请输入密码（至少6位）"
          @keyup.enter="handleRegister"
          @input="errorMessage = ''"
        />
      </div>

      <!-- 错误提示 -->
      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>

      <button 
        class="submit-btn" 
        :disabled="loading"
        @click="handleRegister"
      >
        {{ loading ? '注册中...' : '注册' }}
      </button>

      <p class="link-text">
        已有账号？
        <router-link to="/login">立即登录</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
/* 入场动画 */
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 全局背景 */
.auth-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f4f5f7;
  padding: 20px;
}

/* 登录/注册卡片 */
.auth-card {
  width: 400px;
  padding: 40px 30px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(255, 82, 82, 0.08);
  animation: slideUp 0.5s ease-out;
}

/* Logo 区域 */
.logo-area {
  text-align: center;
  margin-bottom: 20px;
}

.logo-text {
  color: #FF5252;
  font-size: 32px;
  font-weight: bold;
  margin: 0;
  letter-spacing: 1px;
}

/* 标题样式 */
.title {
  text-align: center;
  color: #FF5252;
  font-weight: bold;
  font-size: 28px;
  margin-bottom: 30px;
  margin-top: 0;
}

/* 表单组样式 */
.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #666;
  font-size: 14px;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  height: 46px;
  padding: 0 14px;
  background: #f9f9f9;
  border: 1px solid #eee;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
  transition: all 0.3s ease;
}

.form-group input:focus {
  outline: none;
  background: #ffffff;
  border: 2px solid #FF5252;
}

/* 错误提示 */
.error-message {
  color: #FF5252;
  font-size: 12px;
  margin-top: -10px;
  margin-bottom: 10px;
  padding-left: 2px;
}

/* 提交按钮 */
.submit-btn {
  width: 100%;
  height: 46px;
  background: linear-gradient(45deg, #FF5252, #FF7676);
  color: #ffffff;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 10px;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(255, 82, 82, 0.3);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  background: #cccccc;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* 底部链接样式 */
.link-text {
  text-align: center;
  margin-top: 20px;
  color: #666;
  font-size: 14px;
}

.link-text a {
  color: #666;
  text-decoration: none;
  transition: all 0.3s ease;
}

.link-text a:hover {
  color: #FF5252;
  text-decoration: underline;
}
</style>
