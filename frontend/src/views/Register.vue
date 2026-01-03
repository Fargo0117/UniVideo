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

/**
 * 处理注册请求
 * 调用后端注册接口，成功后跳转到登录页
 */
const handleRegister = async () => {
  // 表单验证
  if (!username.value || !nickname.value || !password.value) {
    alert('请填写所有必填项')
    return
  }

  // 密码长度验证（后端要求至少6位）
  if (password.value.length < 6) {
    alert('密码长度至少6位')
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
    const message = error.response?.data?.msg || '注册失败，请稍后重试'
    alert(message)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="register-container">
    <div class="register-card">
      <h2 class="title">用户注册</h2>
      
      <div class="form-group">
        <label for="username">学号/用户名</label>
        <input
          id="username"
          v-model="username"
          type="text"
          placeholder="请输入学号或用户名"
        />
      </div>

      <div class="form-group">
        <label for="nickname">昵称</label>
        <input
          id="nickname"
          v-model="nickname"
          type="text"
          placeholder="请输入昵称"
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
        />
        <span class="hint">密码长度至少6位</span>
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
/* 页面容器 - 全屏居中显示 */
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
}

/* 注册卡片样式 */
.register-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

/* 标题样式 */
.title {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
  font-size: 24px;
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
}

.form-group input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
  transition: border-color 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #409eff;
}

/* 提示文字样式 */
.hint {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}

/* 提交按钮样式 */
.submit-btn {
  width: 100%;
  padding: 12px;
  background-color: #67c23a;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.submit-btn:hover {
  background-color: #85ce61;
}

.submit-btn:disabled {
  background-color: #b3e19d;
  cursor: not-allowed;
}

/* 底部链接样式 */
.link-text {
  text-align: center;
  margin-top: 20px;
  color: #666;
  font-size: 14px;
}

.link-text a {
  color: #409eff;
  text-decoration: none;
}

.link-text a:hover {
  text-decoration: underline;
}
</style>
