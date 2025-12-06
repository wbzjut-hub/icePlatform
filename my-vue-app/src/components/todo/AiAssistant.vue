<template>
  <div
      class="ai-pet-container"
      @click="handleClick"
      @drop.prevent="handleDrop"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      :class="{
        'is-loading': loading,
        'is-dragover': isDragOver
      }"
  >
    <div
      class="lottie-wrapper"
      @mouseenter="onMouseEnter"
      @mouseleave="onMouseLeave"
    >
      <Vue3Lottie
          ref="lottieRef"
          :key="currentTheme"
          :animationData="robotData"
          :height="180"
          :width="180"
          :loop="true"
          :autoPlay="true"
      />
    </div>

    <div class="drop-overlay">
      <span class="drop-text">📄 接收数据流...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Vue3Lottie } from 'vue3-lottie'
import { useTheme } from '@/hooks/useTheme'

// Import all theme variants
import robotOceanic from '@/assets/robot-oceanic.json'
import robotStardust from '@/assets/robot-stardust.json'
import robotMeltdown from '@/assets/robot-meltdown.json'
import robotDefault from '@/assets/robot.json'

const props = defineProps<{
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'click'): void
  (e: 'drop-data', text: string): void
}>()

const { currentTheme } = useTheme()
const isDragOver = ref(false)
const lottieRef = ref()

// Dynamically select robot animation based on theme
const robotData = computed(() => {
  const theme = currentTheme.value
  if (theme.includes('stardust')) return robotStardust
  if (theme.includes('meltdown')) return robotMeltdown
  if (theme.includes('oceanic')) return robotOceanic
  return robotDefault
})

const handleClick = () => emit('click')

const onMouseEnter = () => {
  if (lottieRef.value) {
    lottieRef.value.setSpeed(1.5)
  }
}

const onMouseLeave = () => {
  if (lottieRef.value) {
    lottieRef.value.setSpeed(1)
  }
}

const handleDragOver = (e: DragEvent) => { e.preventDefault(); isDragOver.value = true }
const handleDragLeave = (e: DragEvent) => { e.preventDefault(); isDragOver.value = false }

const handleDrop = (e: DragEvent) => {
  e.preventDefault()
  isDragOver.value = false
  const text = e.dataTransfer?.getData('text')
  if (text) {
    emit('drop-data', text)
  }
}
</script>

<style scoped>
/* AI 伴侣容器 (定位修正) */
.ai-pet-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-end; /* 沉底 */
  align-items: center;       /* 居中 */
  padding-bottom: 10px;
  position: relative;
  cursor: pointer;
  z-index: 10;
}

/* Lottie 动画 (防止变形) */
.lottie-wrapper {
  width: 180px; height: 180px; /* Reduced-size slightly for sidebar */
  transition: transform 0.3s ease;
  filter: drop-shadow(0 10px 15px rgba(0,0,0,0.3));
  line-height: 0; display: block;
}
.ai-pet-container:hover .lottie-wrapper {
  transform: scale(1.05) translateY(-5px);
}

/* 拖拽样式 */
.drop-overlay { position: absolute; top: -10px; left: -10px; right: -10px; bottom: -10px; background: rgba(10, 25, 47, 0.8); border: 2px dashed var(--primary-accent-color); border-radius: 20px; display: flex; align-items: center; justify-content: center; opacity: 0; pointer-events: none; transition: opacity 0.2s; backdrop-filter: blur(4px); z-index: 200; }
.ai-pet-container.is-dragover .drop-overlay { opacity: 1; }
.drop-text { background: var(--primary-accent-color); color: #0a192f; padding: 8px 16px; border-radius: 20px; font-weight: bold; box-shadow: 0 0 15px var(--primary-accent-color); }
</style>
