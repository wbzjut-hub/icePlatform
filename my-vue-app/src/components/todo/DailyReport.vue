<template>
  <div class="daily-report-container">


    <div class="report-content" :class="{ 'is-loading': loading }">
       <div v-if="loading" class="scan-loader">
          <div class="scan-line"></div>
          <span>ANALYZING DATA...</span>
       </div>
       
       <!-- Structured Display -->
       <div v-else-if="parsedData" class="structured-report">
          
          <!-- 1. Compact Weather (No Title) -->
          <div class="weather-compact">
            <div class="weather-main">
              <span class="weather-cond">{{ parsedData.overview['天气'] || '未知天气' }}</span>
              <span class="weather-divider">|</span>
              <span class="weather-temp">{{ parsedData.overview['温度'] || '--' }}</span>
            </div>
            <div class="weather-advice" v-if="parsedData.overview['建议']">
              <span class="advice-icon">💡</span>
              {{ parsedData.overview['建议'] }}
            </div>
          </div>

          <!-- 2. Poetry (No Title) -->
          <div class="poetry-card">
            <div class="poetry-content">
              {{ parsedData.poetry }}
            </div>
          </div>

       </div>
       
       <div v-else class="empty-state">
          <span>NO DATA</span>
       </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Refresh } from '@element-plus/icons-vue'

const props = defineProps<{
  text: string
  loading: boolean
}>()

defineEmits<{
  (e: 'refresh'): void
}>()

// ... script continues ...

// --- Parsing Logic ---
const parsedData = computed(() => {
  if (!props.text) return null
  
  const result = {
    overview: {} as Record<string, string>,
    poetry: ''
  }

  try {
    const sections = props.text.split('### ')
    
    sections.forEach(sec => {
      const lines = sec.trim().split('\n').map(l => l.trim()).filter(l => l)
      if (lines.length === 0) return
      
      const title = lines[0] || ''
      const contentLines = lines.slice(1)

      if (title.includes('天气概述') || title.includes('系统概况')) {
        contentLines.forEach(l => {
          // Parse keys flexibly (Date, Weather, Temp, Advice)
          const match = l.match(/\*\*(.*?)\*\*[:：](.*)/)
          if (match && match[1]) {
            result.overview[match[1].trim()] = (match[2] || '').trim()
          }
        })
      } else if (title.includes('每日诗句') || title.includes('系统指令')) {
        result.poetry = contentLines.map(l => l.replace(/^>\s*/, '')).join('\n')
      }
    })
  } catch (e) {
    console.error("Parse error", e)
    return null 
  }
  
  return result
})
</script>

<style scoped>
.daily-report-container {
  background: rgba(10, 25, 47, 0.4); /* Transparent dark */
  border: 1px solid rgba(100, 255, 218, 0.1);
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%; 
  overflow: hidden; 
  box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(5px);
}

.report-content {
  flex: 1;
  overflow: hidden; /* No scroll on content */
  display: flex;
  flex-direction: column;
}

/* --- Structured Layout Styles --- */
.structured-report {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
  height: 100%;
  overflow: hidden;
}

/* 1. Compact Weather */
.weather-compact {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px 10px;
  background: rgba(17, 34, 64, 0.4);
  border-radius: 6px;
  border-left: 3px solid var(--primary-accent-color);
  flex-shrink: 0; /* Keep weather size fixed */
}

/* ... weather styles same ... */
.weather-main {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: 'Orbitron', sans-serif;
}
.weather-cond { font-size: 14px; color: #fff; font-weight: bold; }
.weather-divider { color: rgba(255, 255, 255, 0.3); font-size: 12px; }
.weather-temp { font-size: 14px; color: var(--primary-accent-color); }
.weather-advice {
  font-size: 12px; color: #8892b0; line-height: 1.4;
  display: flex; align-items: flex-start; gap: 6px;
}
.advice-icon { font-size: 12px; margin-top: 1px; }

/* 2. Poetry Card */
.poetry-card {
  background: linear-gradient(135deg, rgba(17, 34, 64, 0.3), rgba(10, 25, 47, 0.4));
  border: 1px dashed rgba(100, 255, 218, 0.15);
  padding: 10px;
  border-radius: 6px;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1; /* Take remaining space */
  min-height: 0; /* Allow shrinking */
  overflow: hidden; /* Hide overflow if text is too long (user wanted no scroll) */
}

.poetry-content {
  font-family: "STXingkai", "Xingkai SC", "KaiTi", "楷体", serif;
  font-size: 20px;
  color: #e6f1ff;
  line-height: 1.6;
  white-space: pre-wrap;
  text-align: left;
  text-indent: 2em;
  letter-spacing: 1px;
  width: 100%;
}

/* Loader */
.scan-loader {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--primary-accent-color);
  font-size: 12px;
  opacity: 0.8;
  gap: 8px;
}
.scan-line {
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--primary-accent-color), transparent);
  animation: scan 1.5s infinite;
}
@keyframes scan {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

/* Scrollbar Hidden */
.report-content::-webkit-scrollbar { display: none; }
</style>
