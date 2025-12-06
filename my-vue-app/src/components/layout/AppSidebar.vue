<template>
  <el-aside width="250px" class="app-aside">
      <div class="logo-area">
        <h1>IcePlatform</h1>
      </div>
      <el-menu :default-active="activePath" class="app-menu" router>
        <el-menu-item v-for="item in menuItems" :key="item.id" :index="item.path" class="menu-item-container">
          <el-icon><component :is="item.icon" /></el-icon>
          <span class="menu-item-name">{{ item.name }}</span>
          <el-icon class="delete-icon" @click.stop.prevent="onDeletePage(item)" v-if="!isSystemPage(item.id)">
            <Close />
          </el-icon>
        </el-menu-item>
      </el-menu>
      <!-- Add Button Removed -->
      <div class="sidebar-robot-area">
        <WeatherWidget />
        <div class="holo-platform">
          <!-- 3D Trapezoidal Base Parts -->
          <div class="platform-glass-top"></div> <!-- The surface robot stands on -->
          <div class="platform-side"></div>      <!-- The sloping sides -->
          <div class="platform-bottom"></div>    <!-- The foundation -->
          
          <!-- Effects -->
          <div class="holo-beam"></div>
          <div class="scan-line"></div>
        </div>
        <AiAssistant @click="handleRobotClick" />
      </div>
  </el-aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Close } from '@element-plus/icons-vue'
import type { MenuItem } from '@/types/api'
import AiAssistant from '@/components/todo/AiAssistant.vue'
import WeatherWidget from '@/components/layout/WeatherWidget.vue'

const props = defineProps<{
  menuItems: MenuItem[]
}>()

const emit = defineEmits<{
  (e: 'delete-page', item: MenuItem): void
}>()

const router = useRouter()
const route = useRoute()
const activePath = computed(() => route.path)

const handleRobotClick = () => {
  router.push('/ai-lab')
}

const isSystemPage = (id: string) => {
  return ['menu_api_list', 'menu_todo_list', 'menu_ai_lab', 'menu_agent_manager'].includes(id)
}

const onDeletePage = (item: MenuItem) => emit('delete-page', item)
</script>

<style scoped>
/* --- Cyberpunk Sidebar Styling --- */
.app-aside {
  background: rgba(10, 25, 47, 0.95); /* Slightly transparent */
  border-right: 1px solid rgba(100, 255, 218, 0.1);
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  z-index: 2000;
  box-shadow: 5px 0 20px rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(10px);
}

/* Logo Area */
.logo-area {
  padding: 30px 20px;
  text-align: center;
  flex-shrink: 0;
  position: relative;
}

.logo-area h1 {
  font-family: 'Orbitron', 'JetBrains Mono', sans-serif;
  font-size: 24px;
  margin: 0;
  background: linear-gradient(135deg, var(--primary-accent-color), #fff);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  text-shadow: 0 0 10px rgba(100, 255, 218, 0.3);
  letter-spacing: 1px;
}

/* Menu List */
.app-menu {
  flex-grow: 1;
  background-color: transparent;
  border-right: none;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 10px 0;
}

/* Menu Items */
:deep(.el-menu-item) {
  height: 50px;
  line-height: 50px;
  margin: 4px 12px;
  border-radius: 8px;
  color: var(--text-color-secondary);
  transition: all 0.3s ease;
  border-left: 3px solid transparent;
  padding-left: 15px !important; /* Ensure consistent padding */
}

:deep(.el-menu-item:hover) {
  background-color: rgba(100, 255, 218, 0.05);
  color: var(--primary-accent-color);
  transform: translateX(4px);
}

:deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(100, 255, 218, 0.1), transparent);
  color: var(--primary-accent-color);
  border-left-color: var(--primary-accent-color);
  text-shadow: 0 0 8px rgba(100, 255, 218, 0.4);
}

/* Icons */
:deep(.el-menu-item .el-icon) {
  font-size: 18px;
  margin-right: 10px;
  transition: transform 0.3s;
}

:deep(.el-menu-item:hover .el-icon) {
  transform: scale(1.1);
}

/* Add Page Button Area */


/* Robot Docking Station */
.sidebar-robot-area {
  flex-shrink: 0;
  display: flex;
  flex-direction: column; 
  align-items: center;
  justify-content: flex-end;
  /* Dark Glass Style */
  background: rgba(10, 25, 47, 0.6);
  backdrop-filter: blur(5px);
  margin: 15px; /* Spacing from sidebar edges */
  padding-bottom: 5px; 
  border-radius: 20px;
  position: relative;
  overflow: hidden; /* contain content */
  z-index: 10;
  height: 200px; /* Fixed height for the pod */
  box-shadow: 
    0 4px 15px rgba(0,0,0,0.3),
    inset 0 0 20px rgba(100, 255, 218, 0.1); /* Inner glow */
  border: 1px solid rgba(100, 255, 218, 0.2); /* Tech border */
}

/* --- Holographic Emitter Base (Trapezoidal 3D Cylinder) --- */
.holo-platform {
  position: absolute;
  bottom: -15px; /* Moved down significantly */
  left: 50%;
  transform: translateX(-50%);
  width: 160px;
  height: 80px;
  z-index: 5;
  perspective: 1000px; /* Stronger perspective */
  pointer-events: none;
  display: flex;
  justify-content: center;
  align-items: flex-end;
}

/* 1. Top Surface (Glassy/Metallic) */
.platform-glass-top {
  position: absolute;
  bottom: 30px; /* Height of the platform */
  width: 100px;
  height: 100px;
  background: radial-gradient(circle, #333, #000);
  border: 1px solid rgba(100, 255, 218, 0.5);
  border-radius: 50%;
  transform: rotateX(70deg);
  z-index: 5;
  box-shadow: 0 0 20px rgba(100, 255, 218, 0.2);
}

/* 2. Sloping Side (Trapezoid Body) */
.platform-side {
  position: absolute;
  bottom: 15px; /* Sits between top and bottom */
  width: 120px;
  height: 30px; /* Vertical height */
  background: linear-gradient(to bottom, #222, #000);
  opacity: 0.9;
  z-index: 4;
  /* Simulate cylinder side using a tilted element or stacking */
  /* Reverting to a simple visual hack: A wider dark oval behind/below the top one */
  width: 130px;
  height: 130px;
  background: radial-gradient(circle, #111, #000);
  border: 1px solid rgba(100, 255, 218, 0.1);
  border-radius: 50%;
  transform: rotateX(70deg) translateZ(-10px); /* Just below the top */
  box-shadow: 0 10px 20px rgba(0,0,0,0.8);
  display: block; /* FORCE DISPLAY */
}

/* 3. The Bottom Foundation */
.platform-bottom {
  position: absolute;
  bottom: 10px;
  width: 150px;
  height: 150px;
  background: #000;
  border-radius: 50%;
  transform: rotateX(70deg) translateZ(-20px);
  z-index: 3;
  box-shadow: 0 0 30px rgba(0,0,0,0.8);
  border: 4px solid #333;
}

/* A "Wireframe" connecting top and bottom to show it's a solid */
.platform-side::after {
   content: '';
   position: absolute;
   top: 50%; left: 50%;
   transform: translate(-50%, -50%);
   width: 115%; height: 115%;
   border-radius: 50%;
   border: 1px dashed rgba(100, 255, 218, 0.2);
   animation: rotate-base 30s linear infinite;
}

@keyframes rotate-base { from { transform: translate(-50%, -50%) rotate(0deg); } to { transform: translate(-50%, -50%) rotate(360deg); } }

/* Beam & Scanline adjustments */
.holo-beam {
  bottom: 45px; /* Sit on glass top */
  transform: perspective(600px) rotateX(10deg); 
  z-index: 8;
}

.scan-line {
  bottom: 45px;
  z-index: 9;
}

/* 3. The "Beam" Effect */
.holo-beam {
  position: absolute;
  bottom: 40px; /* Start from top surface */
  width: 120px;
  height: 160px;
  background: linear-gradient(to top, rgba(100, 255, 218, 0.2), transparent 70%);
  /* Tilted to match the perspective of the base/robot */
  transform: perspective(600px) rotateX(10deg); 
  clip-path: polygon(15% 100%, 85% 100%, 100% 0%, 0% 0%);
  filter: blur(8px);
  pointer-events: none;
  z-index: 8; 
  animation: beam-pulse 4s infinite alternate;
}

@keyframes beam-pulse {
  0% { opacity: 0.5; height: 150px; }
  100% { opacity: 0.8; height: 165px; }
}

/* 4. Scan Line */
.scan-line {
  position: absolute;
  bottom: 40px;
  width: 130px;
  height: 130px;
  border-radius: 50%;
  background: radial-gradient(transparent 40%, rgba(100, 255, 218, 0.6) 90%, rgba(100, 255, 218, 0.9) 100%);
  opacity: 0;
  transform: rotateX(70deg) translateZ(0px);
  animation: scan-laser 4s ease-in-out infinite;
  box-shadow: 0 0 10px rgba(100, 255, 218, 0.5);
  z-index: 9;
}

@keyframes scan-laser {
  0% { transform: rotateX(75deg) translateZ(0px); opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { transform: rotateX(75deg) translateZ(120px); opacity: 0; }
}

@keyframes disc-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* A subtle "platform" effect under the robot */
.sidebar-robot-area::after {
  content: '';
  position: absolute;
  bottom: 10px;
  width: 140px;
  height: 10px;
  background: radial-gradient(ellipse at center, rgba(100, 255, 218, 0.2), transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}

.menu-item-container {
  display: flex;
  align-items: center;
  position: relative;
}

.menu-item-name {
  flex-grow: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 25px;
  font-size: 14px;
}

.delete-icon {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-color-secondary);
  font-size: 12px;
  display: none;
  padding: 6px;
  border-radius: 50%;
  background: rgba(0,0,0,0.3);
}

:deep(.el-menu-item:hover .delete-icon) {
  display: inline-flex;
}

.delete-icon:hover {
  color: var(--secondary-accent-color);
  background: rgba(239, 68, 68, 0.2);
}
</style>
