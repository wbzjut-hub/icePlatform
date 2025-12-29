<template>
  <div class="roundtable-page">
    <!-- Compact Header Bar (only when meeting started) -->
    <div class="header-bar" v-if="isPlaying">
      <div class="header-left">
        <span class="header-title">🏙️ 圆桌会议</span>
        <span class="phase-tag" :class="phaseClass">{{ phaseText }}</span>
        <span v-if="state.round_count > 0" class="round-badge">R{{ state.round_count }}</span>
      </div>
      <div class="header-topic" v-if="state.topic">{{ state.topic }}</div>
      <div class="header-experts">
        <div 
          v-for="(expert, index) in state.experts" 
          :key="expert.id"
          class="expert-card"
          :class="{ 'is-speaking': state.current_speaker_idx === index }"
        >
          <span class="expert-icon">{{ getDomainIcon(expert.domain) }}</span>
          <span class="expert-name">{{ getShortName(expert.name) }}</span>
        </div>
      </div>
    </div>

    <!-- Welcome Screen (before meeting starts) -->
    <div class="welcome-screen" v-if="!isPlaying">
      <div class="welcome-content">
        <div class="welcome-icon">🏙️</div>
        <h1 class="welcome-title">专家圆桌会议</h1>
        <p class="welcome-subtitle">AI 会根据议题自动选择 5-7 位相关专家，展开深度讨论</p>
        <div class="topic-input-wrapper">
          <input 
            v-model="topicInput" 
            class="topic-input"
            placeholder="输入讨论议题...例如：如何设计高可用的分布式系统？"
            @keyup.enter="confirmStart"
          />
          <button class="start-btn" @click="confirmStart" :disabled="loading || !topicInput.trim()">
            <span v-if="loading">⚙️ 载入中...</span>
            <span v-else>🚀 开始会议</span>
          </button>
        </div>
        <div class="welcome-tips">
          <span>💡 提示：输入具体、有挑战性的问题，讨论更精彩</span>
        </div>
      </div>
    </div>

    <!-- Dialogue Area -->
    <div class="dialogue-area">
      <div class="dialogue-bg-grid"></div>
      <div class="dialogue-content" ref="dialogueContainer">
        <div 
          v-for="(msg, index) in dialogueMessages" 
          :key="index"
          class="message-bubble"
        :class="{ 'system': msg.speaker === '系统' || msg.speaker === '会议总结', 'moderator': msg.speaker === '主持人' }"
        >
          <div class="message-header">
            <span class="speaker-icon">{{ getSpeakerIcon(msg.speaker) }}</span>
            <span class="speaker-name">{{ msg.speaker }}</span>
          </div>
          <div class="message-text" v-html="msg.content"></div>
        </div>
        
        <!-- Typing message -->
        <div v-if="isTyping" class="message-bubble">
          <div class="message-header">
            <span class="speaker-icon">{{ getSpeakerIcon(typingSpeaker) }}</span>
            <span class="speaker-name">{{ typingSpeaker }}</span>
          </div>
          <div class="message-text">
            {{ typingMessage }}<span class="cursor-blink">|</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Control Panel (only when meeting started) -->
    <div class="control-panel" v-if="isPlaying">
      <button class="ctrl-btn start" @click="handleOpenStart" :disabled="isPlaying">
        <span class="btn-icon">▶</span> 开始会议
      </button>
      <button class="ctrl-btn next" @click="handleNext" :disabled="!isPlaying || isCompleted || isTyping">
        <span class="btn-icon">➤</span> 下一位
      </button>
      <button class="ctrl-btn auto" @click="toggleAutoPlay" :disabled="!isPlaying || isCompleted">
        <span class="btn-icon">{{ autoPlayTimer ? '⏸' : '⏵' }}</span>
        {{ autoPlayTimer ? '暂停' : '自动' }}
      </button>
      <button class="ctrl-btn summarize" @click="handleSummarize" :disabled="!isPlaying || isCompleted || state.round_count < 1 || summarizing">
        <span class="btn-icon">{{ summarizing ? '⏳' : '📝' }}</span> {{ summarizing ? '总结中...' : '结束总结' }}
      </button>
      <button class="ctrl-btn reset" @click="handleReset" :disabled="!state.topic">
        <span class="btn-icon">↺</span> 重置
      </button>
      <button class="ctrl-btn download" @click="handleDownload" :disabled="!state.summary">
        <span class="btn-icon">📥</span> 下载报告
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, onUnmounted, watch } from 'vue'
import { 
  startRoundtableApi, 
  nextSpeakerApi, 
  getRoundtableStatusApi, 
  summarizeRoundtableApi, 
  resetRoundtableApi 
} from '@/api/modules/roundtable'
import type { RoundtableState, DiscussionMessage } from '@/api/modules/roundtable'
import { ElMessage } from 'element-plus'
import MarkdownIt from 'markdown-it'

// Markdown setup with Mermaid support
const md = new MarkdownIt({ html: true, linkify: true, breaks: true })

// Custom fence renderer for mermaid blocks
const defaultFence = md.renderer.rules.fence!.bind(md.renderer.rules)
md.renderer.rules.fence = (tokens, idx, options, env, self) => {
  const token = tokens[idx]
  if (token?.info === 'mermaid') {
    const code = token?.content?.trim() || ''
    return `<div class="mermaid-container"><pre class="mermaid">${code}</pre></div>`
  }
  return defaultFence(tokens, idx, options, env, self)
}

const renderMarkdown = (text: string) => text ? md.render(text) : ''

// Mermaid initialization
let mermaidLoaded = false
const initMermaid = async () => {
  if (mermaidLoaded) return
  try {
    const mermaid = await import('mermaid')
    mermaid.default.initialize({ 
      startOnLoad: false, 
      theme: 'dark',
      flowchart: {
        defaultRenderer: 'dagre-wrapper',
        htmlLabels: true,
        curve: 'basis'
      },
      themeVariables: {
        primaryColor: '#4ecdc4',
        primaryTextColor: '#fff',
        primaryBorderColor: '#4ecdc4',
        lineColor: '#888',
        secondaryColor: '#1e293b',
        tertiaryColor: '#16213e'
      }
    })
    mermaidLoaded = true
  } catch (e) {
    console.warn('Mermaid not available:', e)
  }
}

const renderMermaidDiagrams = async () => {
  if (!mermaidLoaded) await initMermaid()
  try {
    const mermaid = await import('mermaid')
    // Find all unrendered mermaid elements (those without data-processed)
    const elements = document.querySelectorAll('.mermaid:not([data-processed])')
    if (elements.length > 0) {
      await mermaid.default.run({ nodes: Array.from(elements) as HTMLElement[] })
    }
  } catch (e) {
    console.warn('Mermaid render error:', e)
  }
}

// State
const state = ref<RoundtableState>({
  topic: '',
  experts: [],
  phase: 'not_started',
  current_speaker_idx: -1,
  discussion_history: [],
  round_count: 0,
  has_consensus: false
})

const showStartDialog = ref(false)
const loading = ref(false)
const topicInput = ref("如何打造一款成功的金融科技产品？")
const autoPlayTimer = ref<any>(null)
const dialogueContainer = ref<HTMLElement | null>(null)

// Typing effect
const dialogueMessages = ref<DiscussionMessage[]>([])
const isTyping = ref(false)
const typingMessage = ref('')
const typingFullMessage = ref('')
const typingSpeaker = ref('')
const typingSpeed = 25
let typingTimer: any = null
const messageQueue = ref<DiscussionMessage[]>([])

// Computeds
const isPlaying = computed(() => state.value.phase !== 'not_started')
const isCompleted = computed(() => state.value.phase === 'completed')

const phaseText = computed(() => {
  switch(state.value.phase) {
    case 'selecting_experts': return "选择专家中"
    case 'discussing': return "讨论进行中"
    case 'summarizing': return "生成总结中"
    case 'completed': return "会议结束"
    default: return "待开始"
  }
})

const phaseClass = computed(() => {
  if (state.value.phase === 'discussing') return 'phase-primary'
  if (state.value.phase === 'completed') return 'phase-success'
  return 'phase-default'
})

// Helpers
const getDomainIcon = (domain?: string) => {
  switch (domain) {
    case '金融核心': return '💰'
    case '科技前沿': return '⚡'
    case '安全法务': return '🔒'
    case '产品战略': return '🚀'
    case '设计创意': return '🎨'
    case '科学理论': return '🧬'
    case '人文社科': return '📚'
    default: return '🤖'
  }
}

const getShortName = (name: string) => {
  const match = name.match(/\((.*?)\)/)
  return match ? match[1] : name.split(' ')[0]
}

const getSpeakerIcon = (speaker: string) => {
  if (speaker === '系统' || speaker === '会议总结') return '🏙️'
  if (speaker === '主持人') return '🎭'
  const expert = state.value.experts.find(e => e.name === speaker)
  return expert ? getDomainIcon(expert.domain) : '👤'
}

// Smart Scroll - only auto-scroll if user is near the bottom
const isNearBottom = () => {
  if (!dialogueContainer.value) return true
  const { scrollTop, scrollHeight, clientHeight } = dialogueContainer.value
  return scrollHeight - scrollTop - clientHeight < 100 // within 100px of bottom
}

const scrollDialogue = (force = false) => {
  nextTick(() => {
    if (dialogueContainer.value && (force || isNearBottom())) {
      dialogueContainer.value.scrollTop = dialogueContainer.value.scrollHeight
    }
  })
}

// Typing effect
const startTyping = (message: DiscussionMessage): Promise<void> => {
  return new Promise((resolve) => {
    isTyping.value = true
    typingSpeaker.value = message.speaker
    typingFullMessage.value = message.content
    typingMessage.value = ''
    
    let index = 0
    const typeNext = () => {
      if (index < typingFullMessage.value.length) {
        typingMessage.value += typingFullMessage.value[index]
        index++
        scrollDialogue()
        typingTimer = setTimeout(typeNext, typingSpeed)
      } else {
        finishTyping()
        resolve()
      }
    }
    typeNext()
  })
}

const finishTyping = () => {
  if (typingFullMessage.value) {
    dialogueMessages.value.push({
      speaker: typingSpeaker.value,
      content: renderMarkdown(typingFullMessage.value)
    })
  }
  isTyping.value = false
  typingMessage.value = ''
  typingFullMessage.value = ''
  if (typingTimer) {
    clearTimeout(typingTimer)
    typingTimer = null
  }
  scrollDialogue()
  // Render any mermaid diagrams after DOM update
  nextTick(() => renderMermaidDiagrams())
}

const processQueue = async () => {
  if (isTyping.value || messageQueue.value.length === 0) return
  
  const nextMsg = messageQueue.value.shift()
  if (nextMsg) {
    await startTyping(nextMsg)
    processQueue()
  }
}

watch(() => messageQueue.value.length, () => {
  processQueue()
})

// API Handlers
const handleOpenStart = () => {
  showStartDialog.value = true
}

const confirmStart = async () => {
  if (!topicInput.value) return ElMessage.warning('请输入议题')
  loading.value = true
  try {
    const res = await startRoundtableApi(topicInput.value)
    state.value = res
    showStartDialog.value = false
    ElMessage.success('圆桌会议开始!')
    
    // Add initial messages to queue
    for (const msg of res.discussion_history) {
      messageQueue.value.push(msg)
    }
  } catch (e) {
    ElMessage.error('启动失败')
  } finally {
    loading.value = false
  }
}

const handleNext = async () => {
  if (isTyping.value || messageQueue.value.length > 0) return
  
  try {
    const prevLen = state.value.discussion_history.length
    const res = await nextSpeakerApi()
    
    const newMessages = res.discussion_history.slice(prevLen)
    state.value = res
    
    for (const msg of newMessages) {
      messageQueue.value.push(msg)
    }
  } catch (e) {
    stopAutoPlay()
  }
}

const summarizing = ref(false)

const handleSummarize = async () => {
  if (isTyping.value || summarizing.value) return
  
  summarizing.value = true
  try {
    const prevLen = state.value.discussion_history.length
    const res = await summarizeRoundtableApi()
    
    const newMessages = res.discussion_history.slice(prevLen)
    state.value = res
    
    for (const msg of newMessages) {
      messageQueue.value.push(msg)
    }
    
    stopAutoPlay()
    ElMessage.success('会议总结已生成')
  } catch (e) {
    ElMessage.error('总结生成失败')
  } finally {
    summarizing.value = false
  }
}

const handleReset = async () => {
  stopAutoPlay()
  try {
    const res = await resetRoundtableApi()
    state.value = res
    dialogueMessages.value = []
    messageQueue.value = []
    isTyping.value = false
    typingMessage.value = ''
    typingFullMessage.value = ''
    ElMessage.info('会议已重置')
  } catch (e) {
    ElMessage.error('重置失败')
  }
}

// Download Summary as Markdown
const handleDownload = () => {
  if (!state.value.summary) {
    ElMessage.warning('暂无总结内容')
    return
  }
  
  // Build full report content
  const date = new Date().toLocaleDateString('zh-CN')
  const experts = state.value.experts.map(e => `- ${e.name}`).join('\n')
  
  let content = `# 专家圆桌会议报告

**议题**: ${state.value.topic}
**日期**: ${date}
**轮数**: ${state.value.round_count} 轮
**专家组成员**:
${experts}

---

${state.value.summary}

---

## 讨论记录

`
  // Add discussion history
  for (const msg of state.value.discussion_history) {
    if (msg.speaker !== '系统') {
      content += `### ${msg.speaker}\n\n${msg.content}\n\n`
    }
  }
  
  // Create and download file
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `圆桌会议_${state.value.topic.slice(0, 20)}_${date.replace(/\//g, '-')}.md`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  
  ElMessage.success('报告已下载')
}

// Auto Play
const toggleAutoPlay = () => {
  if (autoPlayTimer.value) stopAutoPlay()
  else startAutoPlay()
}

const startAutoPlay = () => {
  const autoStep = async () => {
    if (isCompleted.value || isTyping.value || messageQueue.value.length > 0) {
      if (isCompleted.value) stopAutoPlay()
      return
    }
    await handleNext()
  }
  
  const scheduleNext = () => {
    autoPlayTimer.value = setTimeout(async () => {
      await autoStep()
      if (autoPlayTimer.value && !isCompleted.value) {
        scheduleNext()
      }
    }, 1500)
  }
  scheduleNext()
}

const stopAutoPlay = () => {
  if (autoPlayTimer.value) {
    clearTimeout(autoPlayTimer.value)
    autoPlayTimer.value = null
  }
}

onMounted(async () => {
  try {
    const res = await getRoundtableStatusApi()
    if (res && res.topic) {
      state.value = res
      // Render existing messages with markdown
      dialogueMessages.value = res.discussion_history.map(msg => ({
        speaker: msg.speaker,
        content: renderMarkdown(msg.content)
      }))
    }
    scrollDialogue()
  } catch(e) {}
})

onUnmounted(() => {
  stopAutoPlay()
})
</script>

<style scoped>
.roundtable-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  color: #e0e0e0;
  overflow: hidden;
  font-family: 'Inter', 'PingFang SC', sans-serif;
}

/* Compact Header Bar */
.header-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px 24px;
  background: rgba(0, 0, 0, 0.5);
  border-bottom: 1px solid rgba(255, 215, 0, 0.2);
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title {
  font-size: 1.2rem;
  color: #ffd700;
  font-weight: 600;
}

.header-topic {
  flex: 1;
  color: #4ecdc4;
  font-size: 1rem;
  font-weight: 500;
}

.header-experts {
  display: flex;
  gap: 12px;
}

.expert-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  border: 2px solid rgba(255, 255, 255, 0.15);
  transition: all 0.3s ease;
}

.expert-card.is-speaking {
  background: rgba(255, 215, 0, 0.15);
  border-color: #ffd700;
  box-shadow: 0 0 15px rgba(255, 215, 0, 0.4);
}

.expert-icon {
  font-size: 20px;
}

.expert-name {
  font-size: 0.7rem;
  color: #aaa;
  max-width: 60px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.expert-card.is-speaking .expert-name {
  color: #ffd700;
  font-weight: 600;
}

/* Legacy header styles (can remove if not used) */
.header {
  text-align: center;
  padding: 15px 20px;
  background: rgba(0, 0, 0, 0.4);
  border-bottom: 1px solid rgba(255, 215, 0, 0.2);
}

.title {
  margin: 0;
  font-size: 1.6rem;
  color: #ffd700;
  text-shadow: 0 0 15px rgba(255, 215, 0, 0.4);
  letter-spacing: 3px;
}

/* Welcome Screen */
.welcome-screen {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.welcome-content {
  text-align: center;
  max-width: 700px;
}

.welcome-icon {
  font-size: 80px;
  margin-bottom: 20px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-15px); }
}

.welcome-title {
  font-size: 2.5rem;
  color: #ffd700;
  margin: 0 0 16px;
  text-shadow: 0 0 30px rgba(255, 215, 0, 0.5);
  letter-spacing: 4px;
}

.welcome-subtitle {
  color: #94a3b8;
  font-size: 1.1rem;
  margin: 0 0 40px;
  line-height: 1.6;
}

.topic-input-wrapper {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.topic-input {
  flex: 1;
  padding: 16px 24px;
  font-size: 1.1rem;
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid rgba(255, 215, 0, 0.3);
  border-radius: 50px;
  color: #fff;
  outline: none;
  transition: all 0.3s ease;
}

.topic-input::placeholder {
  color: #64748b;
}

.topic-input:focus {
  border-color: #ffd700;
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 0 30px rgba(255, 215, 0, 0.2);
}

.start-btn {
  padding: 16px 32px;
  font-size: 1.1rem;
  font-weight: 600;
  background: linear-gradient(135deg, #ffd700 0%, #ffaa00 100%);
  border: none;
  border-radius: 50px;
  color: #1a1a2e;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.start-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 0 40px rgba(255, 215, 0, 0.5);
}

.start-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.welcome-tips {
  color: #64748b;
  font-size: 0.9rem;
}

.topic-display {
  margin-top: 8px;
  font-size: 1rem;
}

.topic-label {
  color: #888;
  margin-right: 8px;
}

.topic-text {
  color: #4ecdc4;
  font-weight: 500;
}

.phase-indicator {
  margin-top: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
}

.phase-tag {
  padding: 4px 14px;
  border-radius: 16px;
  font-size: 0.8rem;
  font-weight: 500;
}

.phase-default {
  background: rgba(255, 255, 255, 0.1);
  color: #aaa;
}

.phase-primary {
  background: rgba(255, 215, 0, 0.2);
  color: #ffd700;
  border: 1px solid rgba(255, 215, 0, 0.4);
}

.phase-success {
  background: rgba(78, 205, 196, 0.2);
  color: #4ecdc4;
  border: 1px solid rgba(78, 205, 196, 0.4);
}

.round-badge {
  color: #ffd700;
  font-size: 0.85rem;
  background: rgba(255, 215, 0, 0.15);
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}

/* Expert Seats */
.expert-seats {
  display: flex;
  justify-content: center;
  gap: 20px;
  padding: 20px;
  flex-wrap: wrap;
  background: rgba(0, 0, 0, 0.2);
}

.expert-seat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.seat-orb {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  transition: all 0.3s ease;
}

.expert-seat.is-speaking .seat-orb {
  background: rgba(255, 215, 0, 0.3);
  border-color: #ffd700;
  box-shadow: 0 0 20px rgba(255, 215, 0, 0.5);
  animation: pulse-gold 1.5s ease-in-out infinite;
}

@keyframes pulse-gold {
  0%, 100% { box-shadow: 0 0 20px rgba(255, 215, 0, 0.5); }
  50% { box-shadow: 0 0 35px rgba(255, 215, 0, 0.8); }
}

.seat-name {
  font-size: 0.75rem;
  color: #aaa;
  max-width: 80px;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.expert-seat.is-speaking .seat-name {
  color: #ffd700;
  font-weight: bold;
}

/* Dialogue Area */
.dialogue-area {
  flex: 1;
  position: relative;
  background: rgba(0, 0, 0, 0.4);
  margin: 10px 20px;
  border-radius: 12px;
  border: 1px solid rgba(255, 215, 0, 0.1);
  overflow: hidden;
}

.dialogue-bg-grid {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(255, 215, 0, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 215, 0, 0.02) 1px, transparent 1px);
  background-size: 25px 25px;
  pointer-events: none;
}

.dialogue-content {
  position: relative;
  height: 100%;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Message Bubble - Wide Layout */
.message-bubble {
  width: 100%;
  padding: 20px 24px;
  border-radius: 12px;
  background: rgba(30, 40, 60, 0.85);
  border-left: 4px solid #4ecdc4;
  margin-bottom: 4px;
}

.message-bubble:hover {
  background: rgba(30, 40, 60, 0.95);
}

.message-bubble.system {
  border-left-color: #ffd700;
  background: linear-gradient(90deg, rgba(255, 215, 0, 0.08) 0%, rgba(30, 40, 60, 0.85) 100%);
}

.message-bubble.moderator {
  border-left-color: #a78bfa;
  background: linear-gradient(90deg, rgba(167, 139, 250, 0.08) 0%, rgba(30, 40, 60, 0.85) 100%);
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.speaker-icon {
  font-size: 18px;
}

.speaker-name {
  font-weight: 600;
  color: #4ecdc4;
  font-size: 0.9rem;
}

.message-bubble.system .speaker-name {
  color: #ffd700;
}

.message-text {
  text-align: left;
  text-indent: 2em;
  line-height: 1.7;
  font-size: 0.95rem;
  color: #e0e0e0;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.message-text :deep(p) {
  margin: 0.5em 0;
}

.message-text :deep(p:first-child) {
  margin-top: 0;
}

.message-text :deep(p:last-child) {
  margin-bottom: 0;
}

.cursor-blink {
  animation: blink 0.8s infinite;
  color: #ffd700;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* Control Panel */
.control-panel {
  display: flex;
  justify-content: center;
  gap: 15px;
  padding: 15px;
  background: rgba(0, 0, 0, 0.5);
  border-top: 1px solid rgba(255, 215, 0, 0.2);
  flex-wrap: wrap;
}

.ctrl-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border: 2px solid;
  border-radius: 25px;
  background: transparent;
  font-family: inherit;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.ctrl-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.ctrl-btn.start {
  color: #4ecdc4;
  border-color: #4ecdc4;
}

.ctrl-btn.start:hover:not(:disabled) {
  background: rgba(78, 205, 196, 0.2);
  box-shadow: 0 0 15px rgba(78, 205, 196, 0.4);
}

.ctrl-btn.next {
  color: #ffd700;
  border-color: #ffd700;
}

.ctrl-btn.next:hover:not(:disabled) {
  background: rgba(255, 215, 0, 0.2);
  box-shadow: 0 0 15px rgba(255, 215, 0, 0.4);
}

.ctrl-btn.auto {
  color: #a78bfa;
  border-color: #a78bfa;
}

.ctrl-btn.auto:hover:not(:disabled) {
  background: rgba(167, 139, 250, 0.2);
}

.ctrl-btn.summarize {
  color: #34d399;
  border-color: #34d399;
}

.ctrl-btn.summarize:hover:not(:disabled) {
  background: rgba(52, 211, 153, 0.2);
}

.ctrl-btn.reset {
  color: #f87171;
  border-color: #f87171;
}

.ctrl-btn.reset:hover:not(:disabled) {
  background: rgba(248, 113, 113, 0.2);
}

.ctrl-btn.download {
  color: #60a5fa;
  border-color: #60a5fa;
}

.ctrl-btn.download:hover:not(:disabled) {
  background: rgba(96, 165, 250, 0.2);
}

/* Dialog */
:deep(.el-dialog) {
  background: #1e293b;
  border: 1px solid rgba(255, 215, 0, 0.2);
  border-radius: 12px;
}

:deep(.el-dialog__title) {
  color: #ffd700;
}

:deep(.el-input__inner) {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  color: #fff;
}

/* Moderator bubble */
.message-bubble.moderator {
  border-left-color: #a78bfa;
  background: linear-gradient(135deg, rgba(167, 139, 250, 0.15) 0%, rgba(30, 40, 60, 0.9) 100%);
}
.message-bubble.moderator .speaker-name {
  color: #a78bfa;
}

/* Markdown rendering in messages */
.message-text :deep(h2) { 
  font-size: 1.1rem; 
  color: #ffd700; 
  margin: 12px 0 8px; 
  border-bottom: 1px solid rgba(255, 215, 0, 0.2);
  padding-bottom: 4px;
}
.message-text :deep(h3) { font-size: 1rem; color: #4ecdc4; margin: 10px 0 6px; }
.message-text :deep(strong) { color: #fff; }
.message-text :deep(ul), .message-text :deep(ol) { padding-left: 20px; margin: 8px 0; }
.message-text :deep(li) { margin: 4px 0; }
.message-text :deep(p) { margin: 6px 0; }
.message-text :deep(code) { background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px; font-family: monospace; }

/* Mermaid diagrams */
.message-text :deep(.mermaid-container) {
  margin: 16px 0;
  padding: 16px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  border: 1px solid rgba(78, 205, 196, 0.2);
  overflow-x: auto;
  text-indent: 0;
}
.message-text :deep(.mermaid) {
  display: flex;
  justify-content: center;
}
.message-text :deep(.mermaid svg) {
  max-width: 100%;
  height: auto;
}

/* SVG inline support */
.message-text :deep(svg) {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
}
</style>
