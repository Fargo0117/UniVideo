<script setup>
/**
 * 登录页面组件
 * 提供用户登录功能，成功后保存用户信息并跳转首页
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()

// 表单数据
const username = ref('')
const password = ref('')
const loading = ref(false)

/**
 * 处理登录请求
 * 调用后端登录接口，成功后存储用户信息并跳转
 */
const handleLogin = async () => {
  // 表单验证
  if (!username.value || !password.value) {
    alert('请输入用户名和密码')
    return
  }

  loading.value = true
  try {
    // 调用登录接口
    const response = await api.post('/auth/login', {
      username: username.value,
      password: password.value
    })

    // 存储用户信息到 localStorage（后端返回格式为 { code, msg, data }）
    const { id, nickname, role } = response.data.data
    localStorage.setItem('user_id', id)
    localStorage.setItem('nickname', nickname)
    localStorage.setItem('role', role)

    alert('登录成功')
    // 跳转到首页
    router.push('/')
  } catch (error) {
    // 显示错误信息（后端返回格式为 { code, msg, data }）
    const message = error.response?.data?.msg || '登录失败，请检查用户名和密码'
    alert(message)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <h2 class="title">用户登录</h2>
      
      <div class="form-group">
        <label for="username">学号/用户名</label>
        <input
          id="username"
          v-model="username"
          type="text"
          placeholder="请输入学号或用户名"
          @keyup.enter="handleLogin"
        />
      </div>

      <div class="form-group">
        <label for="password">密码</label>
        <input
          id="password"
          v-model="password"
          type="password"
          placeholder="请输入密码"
          @keyup.enter="handleLogin"
        />
      </div>

      <button 
        class="submit-btn" 
        :disabled="loading"
        @click="handleLogin"
      >
        {{ loading ? '登录中...' : '登录' }}
      </button>

      <p class="link-text">
        还没有账号？
        <router-link to="/register">立即注册</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
/* 页面容器 - 全屏居中显示 */
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
}

/* 登录卡片样式 */
.login-card {
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

/* 提交按钮样式 */
.submit-btn {
  width: 100%;
  padding: 12px;
  background-color: #409eff;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.submit-btn:hover {
  background-color: #66b1ff;
}

.submit-btn:disabled {
  background-color: #a0cfff;
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
