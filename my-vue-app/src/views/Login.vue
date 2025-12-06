<!-- src/views/Login.vue -->
<template>
  <div class="cyber-container">
    <!-- Animated Background -->
    <div class="cyber-grid"></div>
    <div class="particles">
      <div v-for="n in 20" :key="n" class="particle" :style="getParticleStyle(n)"></div>
    </div>

    <!-- Terminal Card -->
    <div class="terminal-card">
      <div class="card-header">
        <div class="header-decoration">
          <span class="dot red"></span>
          <span class="dot yellow"></span>
          <span class="dot green"></span>
        </div>
        <div class="header-title">SECURE CONNECTION // ICE_PLATFORM</div>
      </div>

      <div class="card-body">
        <h3 class="glitch-title" data-text="ACCESS CONTROL">ACCESS CONTROL</h3>
        
        <el-form 
          ref="loginFormRef" 
          :model="loginForm" 
          :rules="loginRules" 
          class="cyber-form" 
          label-position="top"
          @keyup.enter="handleLogin"
        >
          <el-form-item prop="username">
            <div class="cyber-input-wrapper">
              <span class="input-label">USER_ID:</span>
              <el-input 
                v-model="loginForm.username" 
                placeholder="ENTER IDENTIFIER" 
                class="cyber-input"
              />
              <div class="scan-line"></div>
            </div>
          </el-form-item>
          
          <el-form-item prop="password">
            <div class="cyber-input-wrapper">
              <span class="input-label">PASSCODE:</span>
              <el-input 
                v-model="loginForm.password" 
                type="password" 
                placeholder="ENTER KEY" 
                show-password 
                class="cyber-input"
              />
              <div class="scan-line"></div>
            </div>
          </el-form-item>

          <el-form-item>
            <button 
              class="cyber-button" 
              :class="{ 'loading': loading }" 
              @click.prevent="handleLogin"
            >
              <span class="btn-content">
                {{ loading ? 'DECRYPTING...' : 'INITIATE SEQUENCE' }}
              </span>
              <span class="btn-glitch"></span>
            </button>
          </el-form-item>
        </el-form>
      </div>

      <div class="card-footer">
        <div class="status-line">
          STATUS: <span class="status-ok">STANDBY</span>
        </div>
        <div class="version">V 1.0.45-BETA</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/modules/userStore'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const loginFormRef = ref<FormInstance>()
const loading = ref(false)

const loginForm = reactive({
  username: 'admin',
  password: 'admin'
})

const loginRules = reactive<FormRules>({
  username: [{ required: true, message: 'IDENTITY REQUIRED', trigger: 'blur' }],
  password: [{ required: true, message: 'KEY REQUIRED', trigger: 'blur' }]
})

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      // Simulate decryption delay for effect
      await new Promise(resolve => setTimeout(resolve, 800))
      
      const success = await userStore.login(loginForm)
      if (success) {
        ElMessage.success({
          message: 'ACCESS GRANTED. WELCOME BACK, COMMANDER.',
          type: 'success',
          duration: 2000,
          customClass: 'cyber-message'
        })
        await router.push('/')
      }
    } finally {
      loading.value = false
    }
  })
}

// Particle Randomization
const getParticleStyle = (n: number) => {
  return {
    left: `${Math.random() * 100}%`,
    top: `${Math.random() * 100}%`,
    animationDelay: `${Math.random() * 5}s`,
    opacity: Math.random() * 0.5 + 0.1
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=JetBrains+Mono:wght@300;500&display=swap');

/* Container & Background */
.cyber-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #050b14;
  position: relative;
  overflow: hidden;
  font-family: 'JetBrains Mono', monospace;
}

.cyber-grid {
  position: absolute;
  width: 200%;
  height: 200%;
  background-image: 
    linear-gradient(rgba(100, 255, 218, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(100, 255, 218, 0.05) 1px, transparent 1px);
  background-size: 40px 40px;
  transform: perspective(500px) rotateX(60deg) translateY(-100px) translateZ(-200px);
  animation: gridMove 20s linear infinite;
  pointer-events: none;
}

@keyframes gridMove {
  0% { transform: perspective(500px) rotateX(60deg) translateY(0) translateZ(-200px); }
  100% { transform: perspective(500px) rotateX(60deg) translateY(40px) translateZ(-200px); }
}

/* Particles */
.particle {
  position: absolute;
  width: 2px;
  height: 2px;
  background: var(--primary-accent-color);
  border-radius: 50%;
  animation: float 10s infinite linear;
}
@keyframes float {
  0% { transform: translateY(0); opacity: 0; }
  50% { opacity: 0.8; }
  100% { transform: translateY(-100vh); opacity: 0; }
}

/* Terminal Card */
.terminal-card {
  width: 420px;
  background: rgba(10, 25, 47, 0.85); /* Glassmorphism */
  backdrop-filter: blur(10px);
  border: 1px solid rgba(100, 255, 218, 0.3);
  box-shadow: 
    0 0 20px rgba(100, 255, 218, 0.1),
    inset 0 0 20px rgba(100, 255, 218, 0.05);
  border-radius: 4px;
  position: relative;
  z-index: 10;
  clip-path: polygon(
    0 0, 
    100% 0, 
    100% calc(100% - 20px), 
    calc(100% - 20px) 100%, 
    0 100%
  );
  display: flex;
  flex-direction: column;
}

/* Header */
.card-header {
  height: 36px;
  border-bottom: 1px solid rgba(100, 255, 218, 0.2);
  display: flex;
  align-items: center;
  padding: 0 15px;
  justify-content: space-between;
  background: rgba(100, 255, 218, 0.05);
}
.header-decoration {
  display: flex;
  gap: 6px;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  opacity: 0.7;
}
.dot.red { background: #ff5f56; }
.dot.yellow { background: #ffbd2e; }
.dot.green { background: #27c93f; }
.header-title {
  font-size: 10px;
  color: rgba(100, 255, 218, 0.6);
  letter-spacing: 1px;
}

/* Body */
.card-body {
  padding: 30px 40px;
}

.glitch-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 24px;
  color: #ccd6f6;
  text-align: center;
  margin-bottom: 30px;
  position: relative;
  letter-spacing: 2px;
}
.glitch-title::before, .glitch-title::after {
  content: attr(data-text);
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(10, 25, 47, 0.85);
}
.glitch-title::before {
  left: 2px;
  text-shadow: -1px 0 #ff0055;
  clip: rect(44px, 450px, 56px, 0);
  animation: glitch-anim 2s infinite linear alternate-reverse;
}
.glitch-title::after {
  left: -2px;
  text-shadow: -1px 0 #64ffda;
  clip: rect(44px, 450px, 56px, 0);
  animation: glitch-anim 2s infinite linear alternate-reverse;
}
@keyframes glitch-anim {
  0% { clip: rect(10px, 9999px, 30px, 0); }
  20% { clip: rect(60px, 9999px, 80px, 0); }
  40% { clip: rect(20px, 9999px, 50px, 0); }
  60% { clip: rect(80px, 9999px, 100px, 0); }
  80% { clip: rect(30px, 9999px, 40px, 0); }
  100% { clip: rect(50px, 9999px, 70px, 0); }
}

/* Form Styles */
.cyber-input-wrapper {
  position: relative;
  margin-bottom: 10px;
  width: 100%; /* Ensure wrapper is full width */
}
.input-label {
  display: block;
  font-size: 10px;
  color: var(--primary-accent-color);
  margin-bottom: 5px;
  opacity: 0.8;
}
/* Override Element Plus Input */
.cyber-input {
  width: 100%; /* Force input component to full width */
}
:deep(.cyber-input .el-input__wrapper) {
  background: transparent !important;
  box-shadow: none !important;
  border-radius: 0;
  border-bottom: 1px solid rgba(100, 255, 218, 0.3);
  padding: 0;
  transition: all 0.3s;
  width: 100%;
}
:deep(.cyber-input .el-input__inner) {
  color: #fff;
  font-family: 'JetBrains Mono', monospace;
  height: 40px;
  text-align: center; /* Center the text for terminal feel */
  font-size: 16px;
  letter-spacing: 1px;
}
:deep(.cyber-input.is-focus .el-input__wrapper) {
  box-shadow: none !important;
}

/* Scanline Animation on Focus */
.scan-line {
  height: 2px;
  width: 0%;
  background: var(--primary-accent-color);
  transition: width 0.3s ease;
  box-shadow: 0 0 10px var(--primary-accent-color);
}
.cyber-input-wrapper:focus-within .scan-line {
  width: 100%;
}

/* Button */
.cyber-button {
  width: 100%;
  height: 45px;
  background: rgba(100, 255, 218, 0.1);
  border: 1px solid var(--primary-accent-color);
  color: var(--primary-accent-color);
  font-family: 'Orbitron', sans-serif;
  letter-spacing: 2px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
  margin-top: 10px;
}
.cyber-button:hover {
  background: rgba(100, 255, 218, 0.2);
  box-shadow: 0 0 20px rgba(100, 255, 218, 0.4);
  text-shadow: 0 0 5px var(--primary-accent-color);
}
.cyber-button.loading {
  background: rgba(100, 255, 218, 0.2);
  cursor: wait;
}

/* Footer */
.card-footer {
  border-top: 1px dashed rgba(100, 255, 218, 0.2);
  padding: 10px 15px;
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: #8892b0;
  background: rgba(0, 0, 0, 0.2);
}
.status-ok {
  color: var(--primary-accent-color);
  animation: blink 2s infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>