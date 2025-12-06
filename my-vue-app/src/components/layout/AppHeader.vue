<template>
  <el-header class="app-header">
    <div class="header-content">
      <span><!-- Breadcrumbs could go here --></span>
      <div class="header-actions">
        <!-- Backend Status -->
        <div class="status-indicator" :class="statusClass">
          <span class="status-dot"></span>
          <span class="status-text">{{ statusText }}</span>
        </div>

        <!-- Theme Switcher -->
        <el-dropdown trigger="click">
          <span class="theme-switcher">
            <el-icon><MagicStick /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item disabled><strong>暗色主题</strong></el-dropdown-item>
              <el-dropdown-item @click="onThemeChange('oceanic')">深海幽蓝</el-dropdown-item>
              <el-dropdown-item @click="onThemeChange('stardust')">星尘紫</el-dropdown-item>
              <el-dropdown-item @click="onThemeChange('meltdown')">核心熔毁</el-dropdown-item>

              <el-dropdown-item divided disabled><strong>亮色主题</strong></el-dropdown-item>
              <el-dropdown-item @click="onThemeChange('oceanic-light')">深海 (亮)</el-dropdown-item>
              <el-dropdown-item @click="onThemeChange('stardust-light')">星尘 (亮)</el-dropdown-item>
              <el-dropdown-item @click="onThemeChange('meltdown-light')">熔毁 (亮)</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <!-- Settings & Tools -->
        <el-dropdown trigger="click" class="settings-dropdown">
          <el-button :icon="Setting" circle />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item :icon="Operation" @click="$emit('open-settings')">系统设置 (API)</el-dropdown-item>
              <el-dropdown-item :icon="Download" @click="$emit('export-config')" divided>导出配置</el-dropdown-item>
              <el-dropdown-item :icon="Upload" @click="$emit('import-config')">导入配置</el-dropdown-item>
              <el-dropdown-item :icon="FolderOpened" @click="$emit('change-db-path')" divided>更改存储路径</el-dropdown-item>
              <el-dropdown-item :icon="Monitor" @click="$emit('toggle-devtools')" divided>调试控制台</el-dropdown-item>
              <!-- Auto Update -->
              <el-dropdown-item :icon="Refresh" @click="handleCheckUpdate" divided>检查更新</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <!-- System Power Menu -->
        <el-dropdown trigger="click" class="power-dropdown">
          <el-button type="danger" circle :icon="SwitchButton" class="power-button" />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item :icon="SwitchButton" @click="handleRestart">重启系统 (清除缓存)</el-dropdown-item>
              <el-dropdown-item :icon="Close" @click="$emit('logout')" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </el-header>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue'
import {
  Setting, Download, Upload, MagicStick, Monitor, FolderOpened, Operation, SwitchButton, Close, Refresh
} from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage, ElNotification } from 'element-plus'
import { useTheme, type ThemeName } from '@/hooks/useTheme'
// Simple fetch for health check, bypassing axios interceptors to avoid auth redirect loops if needed
const API_BASE = import.meta.env.PROD ? 'http://127.0.0.1:8000' : '/api'

// Electron IPC
const ipcRenderer = (window as any).require ? (window as any).require('electron').ipcRenderer : null

const status = ref<'connecting' | 'online' | 'offline'>('connecting')
let pollTimer: number | null = null

const statusText = computed(() => {
  switch (status.value) {
    case 'connecting': return '连接中...'
    case 'online': return '系统在线'
    case 'offline': return '连接断开'
  }
})

const statusClass = computed(() => `status-${status.value}`)

const checkHealth = async () => {
  try {
    // Check menus endpoint to verify DB connection
    const res = await fetch(`${API_BASE}/v1/menus/`)
    if (res.ok) {
      status.value = 'online'
      // Slow down polling once connected
      startPolling(30000) 
    } else {
      // If it's a server error (5xx), it means backend is starting up -> Connecting
      // If it's 4xx (e.g. 404), then it's Offline/Error
      if (res.status >= 500) {
        status.value = 'connecting'
      } else {
        status.value = 'offline'
      }
      startPolling(2000)
    }
  } catch (e) {
    status.value = 'connecting' 
    startPolling(1000)
  }
}

const startPolling = (interval: number) => {
  if (pollTimer) clearTimeout(pollTimer)
  pollTimer = window.setTimeout(checkHealth, interval)
}

onMounted(() => {
  checkHealth()

  // Setup Update Listeners
  if (ipcRenderer) {
    ipcRenderer.on('update-message', (_event: any, data: any) => {
      console.log('Update Message:', data)
      switch (data.type) {
        case 'checking':
          ElMessage.info('正在检查更新...')
          break
        case 'available':
          ElMessageBox.confirm(`发现新版本 ${data.info.version}，是否立即下载？`, '发现更新', {
            confirmButtonText: '立即更新',
            cancelButtonText: '稍后',
            type: 'info'
          }).then(() => {
            ipcRenderer.send('download-update')
          }).catch(() => {})
          break
        case 'not-available':
          ElMessage.success('当前已是最新版本')
          break
        case 'error':
          ElMessage.error(`更新检查失败: ${data.error}`)
          break
        case 'progress':
          // Optional: Show progress bar notification
          // For simplicity, just log or show non-intrusive message
          // ElMessage.info(`下载进度: ${Math.round(data.progress.percent)}%`)
          break
        case 'downloaded':
          ElMessageBox.confirm('更新已下载完毕，是否立即重启安装？', '更新就绪', {
            confirmButtonText: '立即重启',
            cancelButtonText: '稍后',
            type: 'success'
          }).then(() => {
            ipcRenderer.send('quit-and-install')
          }).catch(() => {})
          break
      }
    })
  }
})

onUnmounted(() => {
  if (pollTimer) clearTimeout(pollTimer)
  if (ipcRenderer) {
    ipcRenderer.removeAllListeners('update-message')
  }
})

const handleCheckUpdate = () => {
  if (ipcRenderer) {
    ipcRenderer.send('check-for-update')
  } else {
    ElMessage.warning('Web 模式不支持自动更新，请在客户端中使用')
  }
}

const emit = defineEmits<{
  (e: 'open-settings'): void
  (e: 'export-config'): void
  (e: 'import-config'): void
  (e: 'change-db-path'): void
  (e: 'logout'): void
  (e: 'toggle-devtools'): void
}>()

const { applyTheme } = useTheme()

const onThemeChange = (theme: ThemeName) => {
  applyTheme(theme)
}

const handleRestart = () => {
  ElMessageBox.confirm(
    '确定要重启系统吗？这将清除界面缓存。',
    '系统重启',
    {
      confirmButtonText: '立即重启',
      cancelButtonText: '取消',
      type: 'warning',
      icon: SwitchButton
    }
  ).then(() => {
    // Preserve Token
    const token = localStorage.getItem('token')
    const theme = localStorage.getItem('ice_platform_theme') // Preserve theme too
    
    // Clear everything
    localStorage.clear()
    sessionStorage.clear()
    
    // Restore critical data
    if (token) localStorage.setItem('token', token)
    if (theme) localStorage.setItem('ice_platform_theme', theme)
    
    window.location.reload()
    ElMessage.success('系统已重启')
  }).catch(() => {})
}
</script>

<style scoped>
.app-header {
  background-color: rgba(10, 25, 47, 0.95); /* Slightly more opaque */
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-color-tech);
  height: 60px;
  /* Window Dragging Logic */
  -webkit-app-region: drag; /* Whole header is draggable */
  user-select: none;
  /* Padding for traffic lights (Mac style hiddenInset) */
  padding-left: 80px; 
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.header-actions {
  display: flex;
  align-items: center;
  /* Critical: Interactive elements must NOT be draggable */
  -webkit-app-region: no-drag; 
  padding-right: 20px;
}

.theme-switcher,
.settings-dropdown {
  height: 100%;
  padding: 0 10px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  font-size: 20px;
  color: var(--text-color-secondary);
  transition: color 0.3s;
}

.theme-switcher:hover,
.settings-dropdown:hover {
  color: var(--primary-accent-color);
}

.settings-dropdown {
  margin-left: 10px;
}

.power-dropdown {
  margin-left: 15px;
}

.power-button {
  background-color: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
  color: #ef4444;
}
.power-button:hover,
.power-button:focus {
  background-color: #ef4444;
  color: white;
  border-color: #ef4444;
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
}
/* Status Indicator */
.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-right: 15px;
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
  padding: 4px 10px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  transition: all 0.3s;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #666;
}

.status-text {
  color: var(--text-color-secondary);
}

/* States */
.status-connecting .status-dot {
  background-color: #e6a23c; /* Warning Yellow */
  animation: pulse 1s infinite;
}
.status-connecting .status-text { color: #e6a23c; }

.status-online .status-dot {
  background-color: #67c23a; /* Success Green */
  box-shadow: 0 0 5px #67c23a;
}
.status-online .status-text { color: #67c23a; }

.status-offline .status-dot {
  background-color: #f56c6c; /* Danger Red */
}
.status-offline .status-text { color: #f56c6c; }

@keyframes pulse {
  0% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
  100% { opacity: 1; transform: scale(1); }
}
</style>
