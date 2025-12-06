<template>
  <div class="bubble-wrapper" :class="{'is-docked': isDocked}" @mouseenter="onMouseEnter" @mouseleave="onMouseLeave">
    
    <!-- Input Area (Slides out to the right) - Only show if NOT docked -->
    <!-- Actually, keep it but it will be hidden/collapsed -->
    <div v-show="!isDocked" class="bubble-input-container" :class="{ 'is-expanded': isExpanded }">
       <!-- ... Input content ... -->
         <el-input
        ref="inputRef"
        v-model="inputText"
        placeholder="输入日程 (例如: 明天9点开会)"
        @keyup.enter="handleSubmit"
        :disabled="isLoading"
        class="bubble-input"
        size="small"
      >
        <template #suffix>
          <el-icon v-if="isLoading" class="is-loading"><Loading /></el-icon>
          <el-icon v-else-if="success" class="success-icon"><Check /></el-icon>
          <span v-else class="enter-hint">↵</span>
        </template>
      </el-input>
    </div>

    <!-- Bubble Icon (ICE Text) - Show when NOT docked -->
    <div v-if="!isDocked" class="bubble-icon" @mousedown="onMouseDown">
      <span class="ice-text">ICE</span>
    </div>

    <!-- Dock Bar (Vertical Strip) - Show when DOCKED -->
    <div v-else class="dock-bar" :class="dockSide">
        <span class="dock-arrow">{{ dockSide === 'left' ? '>' : '<' }}</span>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { Loading, Check } from '@element-plus/icons-vue'
import { chatWithAiApi } from '@/api/modules/ai'
import { ElMessage } from 'element-plus'

const isExpanded = ref(false)
const inputText = ref('')
const isLoading = ref(false)
const success = ref(false)
const inputRef = ref()
const dockSide = ref('left') // left or right

// Toggle Expand/Collapse
const toggleExpand = async () => {
  isExpanded.value = !isExpanded.value

  // IPC Resize
  if ((window as any).require) {
    const { ipcRenderer } = (window as any).require('electron')
    // Expanded: 350px width, Collapsed: 70px width (Height fixed 70)
    const newWidth = isExpanded.value ? 350 : 70
    ipcRenderer.send('bubble-resize', { width: newWidth, height: 70 })
  }

  if (isExpanded.value) {
    nextTick(() => inputRef.value?.focus())
  }
}


// Handle Submit
const handleSubmit = async () => {
  if (!inputText.value.trim()) return

  isLoading.value = true
  success.value = false

  try {
    const sessionId = 'fixed_session_robot'
    const workflowId = 'wf_agent'
    const res = await chatWithAiApi(inputText.value, sessionId, workflowId)

    if (res && res.actions && res.actions.includes('add_todo')) {
      success.value = true
      inputText.value = ''
      
      if ((window as any).require) {
        const { ipcRenderer } = (window as any).require('electron')
        ipcRenderer.send('notify-main-refresh')
      }
      
      setTimeout(() => {
        success.value = false
        toggleExpand()
      }, 1500)
    } else {
      ElMessage.warning('未能识别日程，请重试')
      success.value = false
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('添加失败，请重试')
  } finally {
    isLoading.value = false
  }
}

// --- Auto-Docking Logic ---
let dockTimer: any = null
const isDocked = ref(false)

const onMouseEnter = () => {
    if (dockTimer) clearTimeout(dockTimer)
    if (isDocked.value) {
        // Undock
        if ((window as any).require) {
            const { ipcRenderer } = (window as any).require('electron')
            ipcRenderer.send('bubble-undock')
        }
        // Actually wait for IPC to confirm undock?
        // Or just set immediate. 
        // Main process sends 'dock-side-changed' -> 'none'.
    }
}

const onMouseLeave = () => {
    if (isExpanded.value) return 
    
    // Start Timer
    dockTimer = setTimeout(() => {
        if (!isExpanded.value) { 
             if ((window as any).require) {
                const { ipcRenderer } = (window as any).require('electron')
                ipcRenderer.send('bubble-dock')
            }
            // Wait for IPC to set isDocked=true
        }
    }, 2000) 
}

const startDrag = (e: MouseEvent) => { /* ... */ }

let isDragging = false
let dragOffsetX = 0
let dragOffsetY = 0
let initialClickX = 0
let initialClickY = 0

const onMouseDown = async (e: MouseEvent) => {
  
  initialClickX = e.screenX
  initialClickY = e.screenY
  isDragging = false

  if ((window as any).require) {
     const { ipcRenderer } = (window as any).require('electron')
     
     const winX = e.screenX - e.clientX
     const winY = e.screenY - e.clientY
     
     dragOffsetX = e.clientX
     dragOffsetY = e.clientY
     
     isDragging = true
     
     document.addEventListener('mousemove', onMouseMove)
     document.addEventListener('mouseup', onMouseUp)
  }
}

const onMouseMove = (e: MouseEvent) => {
  if (!isDragging) return
  
  const newX = e.screenX - dragOffsetX
  const newY = e.screenY - dragOffsetY
  
  if ((window as any).require) {
    const { ipcRenderer } = (window as any).require('electron')
    ipcRenderer.send('bubble-move', { x: newX, y: newY })
  }
}

const onMouseUp = (e: MouseEvent) => {
  isDragging = false
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', onMouseUp)
  
  const dist = Math.sqrt(Math.pow(e.screenX - initialClickX, 2) + Math.pow(e.screenY - initialClickY, 2))
  if (dist < 5) {
    toggleExpand()
  }
}

onMounted(() => {
  if ((window as any).require) {
    const { ipcRenderer } = (window as any).require('electron')
    ipcRenderer.on('bubble-toggle-input', () => {
      if (isDocked.value) {
           onMouseEnter() 
      }
      toggleExpand()
    })
    
    // Listen for Dock Side Change
    ipcRenderer.on('dock-side-changed', (event: any, side: string) => {
        if (side === 'none') {
            isDocked.value = false
        } else {
            isDocked.value = true
            dockSide.value = side
        }
    })
  }
})
</script>

<style scoped>
/* Wrapper: Default to Center alignment for collapsed state */
.bubble-wrapper {
  display: flex;
  align-items: center;
  justify-content: center; 
  height: 100vh;
  padding: 0;
  overflow: hidden;
  user-select: none;
}
.bubble-wrapper.is-docked {
    padding: 0; 
    justify-content: center; 
}

/* Input Container */
.bubble-input-container {
  width: 0;
  padding: 0; /* Reset padding when collapsed */
  margin: 0;  /* Reset margin when collapsed */
  overflow: hidden;
  transition: all 0.3s ease; /* Animate width, padding, margin */
  background: rgba(10, 25, 47, 0.9);
  border-radius: 0 20px 20px 0; 
  height: 50px;
  display: flex;
  align-items: center;
}

.bubble-input-container.is-expanded {
  width: 260px; 
  padding-left: 15px; /* Restore padding */
  margin-left: -10px; /* Restore overlap margin */
  border: 1px solid var(--primary-accent-color);
  border-left: none; 
}

.bubble-input {
  margin-right: 15px; 
  width: 230px !important;
  --el-input-bg-color: transparent;
  --el-input-border-color: transparent;
  --el-input-text-color: #fff;
}

/* Icon Container */
.bubble-icon {
  width: 60px;
  height: 60px;
  background: rgba(10, 25, 47, 0.9);
  backdrop-filter: blur(5px);
  border-radius: 50%;
  border: 2px solid var(--primary-accent-color);
  box-shadow: 0 0 15px rgba(100, 255, 218, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: grab;
  z-index: 10;
  transition: transform 0.2s;
  flex-shrink: 0; 
  user-select: none;
}

.bubble-icon:active {
  cursor: grabbing;
  transform: scale(0.95);
}

.ice-text {
  font-family: 'Outfit', sans-serif, system-ui;
  font-weight: 800;
  font-size: 20px;
  color: var(--primary-accent-color);
  letter-spacing: 1px;
}

/* Dock Bar Style */
.dock-bar {
    width: 20px;
    height: 60px;
    background: rgba(10, 25, 47, 0.95);
    border: 1px solid var(--primary-accent-color);
    display: flex;
    justify-content: center;
    align-items: center;
    cursor: pointer;
    box-shadow: 0 0 10px rgba(100, 255, 218, 0.3);
}

.dock-bar.left {
    border-radius: 0 8px 8px 0; /* Round Right side only */
    border-left: none;
    margin-left: auto; /* Push to right of container (window) */
}

.dock-bar.right {
    border-radius: 8px 0 0 8px; /* Round Left side only */
    border-right: none;
    margin-right: auto; /* Push to left of container */
}

.dock-arrow {
    color: var(--primary-accent-color);
    font-weight: bold;
    font-size: 14px;
}

.fallback-icon {
  font-size: 30px;
  user-select: none;
}

.success-icon {
  color: #67c23a;
  font-weight: bold;
}

.enter-hint {
  font-size: 10px;
  color: #8892b0;
}
</style>
