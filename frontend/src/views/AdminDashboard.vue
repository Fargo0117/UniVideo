<script setup>
/**
 * 管理后台仪表盘页面
 * 显示统计数据和使用图表展示
 */
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import api from '@/api'

// 统计数据
const stats = ref({
  pending_videos: 0,
  total_users: 0,
  today_new: 0
})

// 趋势数据
const trendData = ref({
  dates: [],
  newUsers: [],
  newVideos: []
})

const loading = ref(false)

// 图表实例
let chartInstance = null

/**
 * 获取统计数据
 */
const fetchStats = async () => {
  loading.value = true
  try {
    const response = await api.get('/admin/stats')
    if (response.data.code === 200) {
      stats.value = {
        pending_videos: response.data.data.pending_videos || 0,
        total_users: response.data.data.total_users || 0,
        today_new: response.data.data.today_new || 0
      }
    }
  } catch (err) {
    console.error('获取统计数据失败:', err)
  } finally {
    loading.value = false
  }
}

/**
 * 获取趋势数据（最近7天的新增用户数和新增视频数）
 */
const fetchTrendData = async () => {
  try {
    const response = await api.get('/admin/stats/trend')
    if (response.data.code === 200) {
      trendData.value = {
        dates: response.data.data.dates || [],
        newUsers: response.data.data.new_users || [],
        newVideos: response.data.data.new_videos || []
      }
      // 更新图表
      updateChart()
    }
  } catch (err) {
    console.error('获取趋势数据失败:', err)
    // 如果获取失败，使用空数据
    trendData.value = {
      dates: [],
      newUsers: [],
      newVideos: []
    }
    updateChart()
  }
}

/**
 * 初始化图表
 */
const initChart = () => {
  const chartDom = document.getElementById('trend-chart')
  if (!chartDom || !echarts) {
    console.warn('图表容器或 ECharts 未找到')
    return
  }
  
  try {
    chartInstance = echarts.init(chartDom)
    updateChart()
  } catch (err) {
    console.error('初始化图表失败:', err)
  }
}

/**
 * 更新图表数据
 */
const updateChart = () => {
  if (!chartInstance) return
  
  // 使用从后端获取的真实数据
  const dates = trendData.value.dates.length > 0 
    ? trendData.value.dates 
    : ['01-01', '01-02', '01-03', '01-04', '01-05', '01-06', '01-07'] // 默认占位
  const newUsers = trendData.value.newUsers
  const newVideos = trendData.value.newVideos
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['新增用户数', '新增视频数'],
      top: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisTick: {
        alignWithLabel: true
      }
    },
    yAxis: {
      type: 'value',
      name: '数量'
    },
    series: [
      {
        name: '新增用户数',
        type: 'line',
        smooth: true,
        data: newUsers,
        itemStyle: {
          color: '#1890ff'
        },
        lineStyle: {
          color: '#1890ff',
          width: 2
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
              { offset: 1, color: 'rgba(24, 144, 255, 0.05)' }
            ]
          }
        }
      },
      {
        name: '新增视频数',
        type: 'line',
        smooth: true,
        data: newVideos,
        itemStyle: {
          color: '#2fc25b'
        },
        lineStyle: {
          color: '#2fc25b',
          width: 2
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(47, 194, 91, 0.3)' },
              { offset: 1, color: 'rgba(47, 194, 91, 0.05)' }
            ]
          }
        }
      }
    ]
  }
  
  chartInstance.setOption(option)
}

// 窗口大小变化处理函数
const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

onMounted(async () => {
  // 并行获取统计数据和趋势数据
  await Promise.all([
    fetchStats(),
    fetchTrendData()
  ])
  
  // 延迟初始化图表，确保 DOM 已渲染
  setTimeout(() => {
    initChart()
  }, 100)
  
  // 监听窗口大小变化，自动调整图表大小
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div class="dashboard-container">
    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card stat-card-blue">
        <div class="stat-icon">
          🎬
        </div>
        <div class="stat-content">
          <div class="stat-label">待审核视频</div>
          <div class="stat-value">{{ stats.pending_videos }}</div>
        </div>
      </div>
      
      <div class="stat-card stat-card-cyan">
        <div class="stat-icon">
          👥
        </div>
        <div class="stat-content">
          <div class="stat-label">总用户数</div>
          <div class="stat-value">{{ stats.total_users }}</div>
        </div>
      </div>
      
      <div class="stat-card stat-card-green">
        <div class="stat-icon">
          📈
        </div>
        <div class="stat-content">
          <div class="stat-label">今日新增</div>
          <div class="stat-value">{{ stats.today_new }}</div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="chart-container">
      <div class="chart-card">
        <h3 class="chart-title">平台数据趋势</h3>
        <div v-if="loading" class="chart-loading">加载中...</div>
        <div v-else id="trend-chart" style="width: 100%; height: 450px;"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-container {
  width: 100%;
  display: flex;
  flex-direction: column;
}

/* 统计卡片 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-bottom: 24px;
}

.stat-card {
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  opacity: 0.1;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0) 100%);
  pointer-events: none;
}

.stat-card:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
  transform: translateY(-4px);
}

/* 蓝色渐变卡片 */
.stat-card-blue {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  color: #fff;
}

/* 青色渐变卡片 */
.stat-card-cyan {
  background: linear-gradient(135deg, #13c2c2 0%, #08979c 100%);
  color: #fff;
}

/* 绿色渐变卡片 */
.stat-card-green {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
  color: #fff;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  margin-right: 16px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 8px;
  font-weight: 500;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  line-height: 1;
}

/* 图表区域 */
.chart-container {
  flex: 1;
  margin-top: 0;
}

.chart-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  width: 100%;
  min-height: 500px;
}

.chart-title {
  font-size: 20px;
  font-weight: 600;
  color: #262626;
  margin: 0 0 24px 0;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.chart-loading {
  text-align: center;
  padding: 200px 0;
  color: #8c8c8c;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-cards {
    grid-template-columns: 1fr;
  }
  
  .stat-card {
    padding: 20px;
  }
  
  .stat-icon {
    width: 56px;
    height: 56px;
    font-size: 28px;
    margin-right: 12px;
  }
  
  .stat-value {
    font-size: 28px;
  }
  
  .chart-card {
    padding: 16px;
  }
  
  .chart-title {
    font-size: 18px;
    margin-bottom: 16px;
  }
}
</style>
