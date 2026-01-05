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

// ==================== 关注功能 API ====================

/**
 * 关注用户
 * @param {number} targetUserId - 要关注的用户ID
 * @param {number} currentUserId - 当前登录用户ID
 */
export const followUser = (targetUserId, currentUserId) => {
  return api.post(`/follow/${targetUserId}`, { user_id: currentUserId })
}

/**
 * 取消关注用户
 * @param {number} targetUserId - 要取消关注的用户ID
 * @param {number} currentUserId - 当前登录用户ID
 */
export const unfollowUser = (targetUserId, currentUserId) => {
  return api.post(`/unfollow/${targetUserId}`, { user_id: currentUserId })
}

/**
 * 获取用户的粉丝列表
 * @param {number} userId - 用户ID
 * @param {number} page - 页码（默认1）
 * @param {number} perPage - 每页数量（默认20）
 */
export const getFollowers = (userId, page = 1, perPage = 20) => {
  return api.get(`/users/${userId}/followers`, {
    params: { page, per_page: perPage }
  })
}

/**
 * 获取用户的关注列表
 * @param {number} userId - 用户ID
 * @param {number} page - 页码（默认1）
 * @param {number} perPage - 每页数量（默认20）
 */
export const getFollowing = (userId, page = 1, perPage = 20) => {
  return api.get(`/users/${userId}/following`, {
    params: { page, per_page: perPage }
  })
}

/**
 * 查询当前用户是否关注了指定用户
 * @param {number} targetUserId - 目标用户ID
 * @param {number} currentUserId - 当前登录用户ID
 */
export const getFollowStatus = (targetUserId, currentUserId) => {
  return api.get(`/users/${targetUserId}/follow_status`, {
    params: { current_user_id: currentUserId }
  })
}

// 导出配置好的 axios 实例
export default api
