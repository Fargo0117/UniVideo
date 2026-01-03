/**
 * Axios 配置文件
 * 用于创建和配置与后端 API 通信的 HTTP 客户端实例
 */

import axios from 'axios'

// 创建 axios 实例，配置后端 API 基础地址
const api = axios.create({
  baseURL: 'http://localhost:5001/api', // 后端 Flask API 地址
  timeout: 10000, // 请求超时时间：10秒
  headers: {
    'Content-Type': 'application/json'
  }
})

/**
 * 请求拦截器
 * 在每次请求发送前执行，用于添加身份认证信息
 */
api.interceptors.request.use(
  (config) => {
    // 从 localStorage 获取用户ID
    const userId = localStorage.getItem('user_id')
    
    // 如果存在用户ID，添加到请求头中进行身份透传
    if (userId) {
      config.headers['X-User-ID'] = userId
    }
    
    return config
  },
  (error) => {
    // 请求错误时的处理
    return Promise.reject(error)
  }
)

// 导出配置好的 axios 实例
export default api
