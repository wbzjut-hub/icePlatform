<template>
  <div class="todo-page-container">
    <!-- 1. Top Dashboard Header -->
    <div class="dashboard-header">
      <div class="header-left">
        <h2 class="date-title">{{ formattedDate }}</h2>
        <span class="env-status">System Status: ONLINE</span>
      </div>
      <div class="header-right">
        <div class="stat-card">
          <span class="stat-value">{{ dailyTodos.filter(t => !t.done).length }}</span>
          <span class="stat-label">PENDING</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{{ dailyTodos.filter(t => t.done).length }}</span>
          <span class="stat-label">DONE</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-card">
          <span class="stat-value">{{ dailyNotes.length }}</span>
          <span class="stat-label">NOTES</span>
        </div>
      </div>
    </div>

    <!-- 2. Main Content Area (Sidebar + Columns) -->
    <div class="todo-page-body">
      <div class="left-sidebar">
        <!-- System Log on TOP -->
        <DailyReport
          :text="bubbleText"
          :loading="petLoading"
          @refresh="generateAiBriefing"
          class="sidebar-report"
        />
        
        <!-- Calendar on BOTTOM -->
        <div class="calendar-container">
          <el-calendar v-model="selectedDate" />
        </div>
      </div>

      <div class="content-container">
        <div class="columns-wrapper">
          <TaskColumn
            title="任务待办"
            placeholder="添加待办 (回车)"
            empty-text="无待办任务"
            :items="dailyTodos"
            @add="addTodo"
            @remove="removeTodo"
            @toggle="toggleTodo"
            @update="updateTodo"
            @update:list="(l) => {}"
          />

          <TaskColumn
            title="临时记录"
            placeholder="添加记录 (回车)"
            empty-text="无临时记录"
            :items="dailyNotes"
            @add="addNote"
            @remove="removeNote"
            @toggle="toggleNote"
            @update="updateNote"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import { useTodos } from '@/hooks/useTodos'
import { useAppStore } from '@/store/modules/appStore'
import dayjs from 'dayjs'
import { chatWithAiApi } from '@/api/modules/ai'
import { ElMessage } from 'element-plus'

// Components
// Components
import TaskColumn from '@/components/todo/TaskColumn.vue'
import DailyReport from '@/components/todo/DailyReport.vue'

const router = useRouter()
const appStore = useAppStore()

const ROBOT_SESSION_ID = "fixed_session_robot"

const selectedDate = ref(new Date())
const dateKey = computed(() => dayjs(selectedDate.value).format('YYYY-MM-DD'))

// Hook integration
const {
  dailyTodos, dailyNotes, fetchTodos,
  addTodo, removeTodo, toggleTodo, updateTodo, addNote, removeNote, updateNote, toggleNote
} = useTodos(dateKey)

const formattedDate = computed(() => dayjs(selectedDate.value).format('YYYY 年 M 月 D 日'))

// --- AI Assistant Logic ---
const showBubble = ref(false)
import { getTodayWeatherApi } from '@/api/modules/system'

const bubbleText = ref(`### 🌦️ 天气概述

**天气**: 多云转晴
**温度**: 12°C - 20°C
**建议**: 适宜户外活动，但在网络接入点需注意防护。

### 📜 每日诗句

> "代码如诗，构建未来。
> 在数据的洪流中，保持灵魂的静谧。"`)
const petLoading = ref(false)
let bubbleTimer: any = null

const goToRobotChat = () => {
  router.push({
    path: '/ai-lab',
    query: { session: ROBOT_SESSION_ID }
  })
}

const generateAiBriefing = async () => {
  showBubble.value = true
  petLoading.value = true
  bubbleText.value = ""

  try {
    const targetDate = dateKey.value
    
    // 1. Fetch Real Weather
    let weatherInfo = "未知 (传感器离线)"
    try {
      const wData = await getTodayWeatherApi()
      if (wData) {
        weatherInfo = `天气代码:${wData.weather_code}, 温度:${wData.temp_min}°C ~ ${wData.temp_max}°C, 城市:${wData.city}`
      }
    } catch (e) {
      console.warn("Weather fetch failed", e)
    }

    const prompt = `
你是一个赛博朋克风格的 AI 伴侣。当前日期：${targetDate}。
今日真实天气数据：${weatherInfo}。

请根据真实天气数据，生成一份简报。

请严格按照以下 Markdown 格式输出：

### 🌦️ 天气概述
**天气**: [根据数据描述天气]
**温度**: [根据数据描述温度范围]
**建议**: [根据天气给出赛博风格的生活建议]

### 📜 每日诗句
(请创作或引用一句富有哲理、励志的短诗，最好带有科技或未来感，每天都不一样)
`
    const res = await chatWithAiApi(prompt, ROBOT_SESSION_ID, 'wf_agent')
    if (res && res.reply) {
      bubbleText.value = res.reply
    }
  } catch (e) {
    bubbleText.value = ">> CRITICAL_ERROR: 连接中断，无法读取数据流。"
  } finally {
    petLoading.value = false
    if (bubbleTimer) clearTimeout(bubbleTimer)
    bubbleTimer = setTimeout(() => showBubble.value = false, 30000)
  }
}

const handlePetClick = () => {
  if (showBubble.value) {
    goToRobotChat()
  } else {
    generateAiBriefing()
  }
}

const handleDropData = async (text: string) => {
  showBubble.value = true
  petLoading.value = true

  try {
    const prompt = `接收外部数据："${text}"。\n请分析意图并调用 add_todo 添加任务。`
    const res = await chatWithAiApi(prompt, ROBOT_SESSION_ID, 'wf_agent')
    if (res && res.reply) {
      bubbleText.value = res.reply
      ElMessage.success('数据已录入系统')
      await fetchTodos()
    }
  } catch (e) {
    bubbleText.value = ">> ERROR: 数据解析失败。"
  } finally {
    petLoading.value = false
    setTimeout(() => showBubble.value = false, 8000)
  }
}

// Lifecycle
onActivated(() => {
  if (fetchTodos) fetchTodos()
})

onMounted(() => {
  if (fetchTodos) fetchTodos()

  // Briefing Logic
  if (!appStore.hasGeneratedBriefing) {
    // setTimeout(() => {
    //   generateAiBriefing()
    //   appStore.setBriefingGenerated()
    // }, 1000)
  }
})
</script>

<style scoped>
.todo-page-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-color-deep-space);
  overflow: hidden;
}

.dashboard-header {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 30px;
  background: rgba(17, 34, 64, 0.8);
  border-bottom: 1px solid var(--border-color-tech);
  backdrop-filter: blur(10px);
  z-index: 10;
}

.todo-page-body {
  display: flex;
  flex: 1;
  overflow: hidden;
  padding: 20px 30px 30px 30px;
  gap: 24px;
  max-width: 1800px; /* Wider constraint */
  width: 100%;
  margin: 0 auto;
}

.left-sidebar {
  width: 340px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
}

/* Make Report fill the upper space */
.sidebar-report {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.calendar-container {
  flex-shrink: 0;
  padding: 10px;
  border-radius: 8px;
  background-color: var(--bg-color-panel);
  border: 1px solid var(--border-color-tech);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.content-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100%;
}

.header-left {
  display: flex;
  flex-direction: column;
}

.date-title {
  margin: 0;
  color: var(--primary-accent-color);
  font-family: 'Orbitron', 'JetBrains Mono', monospace;
  font-size: 1.8rem;
  text-shadow: 0 0 10px rgba(100, 255, 218, 0.3);
}

.env-status {
  font-size: 0.8rem;
  color: var(--text-color-secondary);
  margin-top: 5px;
  letter-spacing: 1px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(17, 34, 64, 0.6);
  padding: 5px 15px;
  border-radius: 4px;
  border: 1px solid rgba(100, 255, 218, 0.1);
}

.stat-value {
  font-size: 1.2rem;
  font-weight: bold;
  color: var(--text-color-primary);
}

.stat-label {
  font-size: 0.7rem;
  color: var(--text-color-secondary);
  letter-spacing: 0.5px;
}

.stat-divider {
  width: 1px;
  height: 30px;
  background-color: var(--border-color-tech);
}

.columns-wrapper {
  display: flex;
  flex: 1;
  gap: 24px;
  min-height: 0;
  overflow: hidden;
}

/* Calendar Overrides */
:deep(.el-calendar) {
  background-color: transparent;
  --el-calendar-border: none;
}
:deep(.el-calendar__header) {
  padding: 10px 10px 10px;
  border-bottom: 1px solid var(--border-color-tech);
}
:deep(.el-calendar__title) {
  color: var(--text-color-primary);
  font-weight: bold;
}
:deep(.el-calendar__button-group .el-button) {
  background-color: rgba(255,255,255,0.05);
  border-color: var(--border-color-tech);
  color: var(--text-color-secondary);
}
:deep(.el-calendar__button-group .el-button:hover) {
  color: var(--primary-accent-color);
  border-color: var(--primary-accent-color);
}
:deep(.el-calendar-table) {
  color: var(--text-color-secondary);
}
:deep(.el-calendar-table thead th) {
  color: var(--text-color-secondary);
}
:deep(.el-calendar-table .el-calendar-day) {
  height: 36px;
  padding: 4px;
  text-align: center;
  line-height: 28px;
  border: none;
  transition: all 0.2s;
  border-radius: 4px;
}
:deep(.el-calendar-table .el-calendar-day:hover) {
  background-color: rgba(100, 255, 218, 0.1);
  color: var(--primary-accent-color);
}
:deep(.el-calendar-table .is-selected) {
  background-color: var(--primary-accent-color);
  color: #0a192f !important;
  font-weight: bold;
  box-shadow: 0 0 15px rgba(100, 255, 218, 0.4);
}
/* Hide default today indicator if it clashes */
:deep(.el-calendar-table .el-calendar-day:hover) { cursor: pointer; }
</style>