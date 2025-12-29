<template>
  <div class="debate-page">
    <!-- Header -->
    <div class="header">
      <h1 class="title">⚡ AI DEBATE ARENA ⚡</h1>
      <div v-if="gameState.topic" class="topic-display">
        <span class="topic-label">TOPIC:</span>
        <span class="topic-text">{{ gameState.topic }}</span>
      </div>
      <div class="phase-indicator">
        <span class="phase-tag" :class="phaseClass">{{ phaseText }}</span>
        <span v-if="gameState.winner" class="winner-badge">🏆 Winner: {{ gameState.winner }}</span>
      </div>
    </div>

    <!-- Main Arena -->
    <div class="arena">
      <!-- Left: Affirmative Lights -->
      <div class="lights-column affirmative">
        <h3 class="team-label">正方</h3>
        <div 
          v-for="player in affirmativePlayers" 
          :key="player.id"
          class="light-orb"
          :class="{ 'is-speaking': isPlayerSpeaking(player.role) }"
        >
          <div class="orb-glow"></div>
          <div class="orb-core"></div>
          <span class="player-label">{{ getRoleLabel(player.role) }}</span>
        </div>
      </div>

      <!-- Center: Dialogue Area -->
      <div class="dialogue-area">
        <div class="dialogue-bg-grid"></div>
        <div class="dialogue-content" ref="dialogueContainer">
          <div 
            v-for="(msg, index) in dialogueMessages" 
            :key="index"
            class="message-bubble"
            :class="msg.side"
          >
            <div class="message-header">
              <span class="speaker-name">{{ msg.speaker }}</span>
              <span class="speaker-side">{{ msg.side === 'affirmative' ? '正方' : '反方' }}</span>
            </div>
            <div class="message-text" v-html="msg.content"></div>
          </div>
          
          <!-- Typing message (正在打字的消息) -->
          <div v-if="isTyping" class="message-bubble" :class="typingSide">
            <div class="message-header">
              <span class="speaker-name">{{ typingSpeaker }}</span>
              <span class="speaker-side">{{ typingSide === 'affirmative' ? '正方' : '反方' }}</span>
            </div>
            <div class="message-text">
              {{ typingMessage }}<span class="cursor-blink">|</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Negative Lights -->
      <div class="lights-column negative">
        <h3 class="team-label">反方</h3>
        <div 
          v-for="player in negativePlayers" 
          :key="player.id"
          class="light-orb"
          :class="{ 'is-speaking': isPlayerSpeaking(player.role) }"
        >
          <div class="orb-glow"></div>
          <div class="orb-core"></div>
          <span class="player-label">{{ getRoleLabel(player.role) }}</span>
        </div>
      </div>
    </div>

    <!-- Control Panel -->
    <div class="control-panel">
      <button class="ctrl-btn start" @click="handleOpenStart" :disabled="isPlaying">
        <span class="btn-icon">▶</span> START
      </button>
      <button class="ctrl-btn next" @click="handleNext" :disabled="isGameOver || !isPlaying">
        <span class="btn-icon">➤</span> NEXT
      </button>
      <button class="ctrl-btn auto" @click="toggleAutoPlay" :disabled="!isPlaying || isGameOver">
        <span class="btn-icon">{{ autoPlayTimer ? '⏸' : '⏵' }}</span>
        {{ autoPlayTimer ? 'STOP' : 'AUTO' }}
      </button>
      <button class="ctrl-btn reset" @click="handleReset" :disabled="!isPlaying">
        <span class="btn-icon">↺</span> RESET
      </button>
    </div>

    <!-- Start Dialog -->
    <el-dialog v-model="showStartDialog" title="Setup Debate" width="500px" class="start-dialog">
      <el-input 
        v-model="topicInput" 
        placeholder="Enter debate topic (e.g., AI will replace doctors)" 
        size="large"
      />
      <template #footer>
        <el-button @click="showStartDialog = false">Cancel</el-button>
        <el-button type="primary" @click="confirmStart" :loading="loading">Confirm</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, onUnmounted, watch } from 'vue'
import { startGameApi, nextStepApi, getGameStatusApi } from '@/api/modules/game'
import type { GameState, Player } from '@/types/game'
import { GamePhase, Role } from '@/types/game'
import { ElMessage } from 'element-plus'

interface DialogueMessage {
  speaker: string
  side: 'affirmative' | 'negative'
  content: string
}

const gameState = ref<GameState>({
  topic: '',
  players: [],
  phase: GamePhase.NOT_STARTED,
  turn_index: 0,
  history: [],
  hidden_history: [],
  winner: null
})

const showStartDialog = ref(false)
const loading = ref(false)
const topicInput = ref("AI 是否会毁灭人类？")
const autoPlayTimer = ref<any>(null)
const dialogueContainer = ref<HTMLElement | null>(null)

// 已完成打字的消息
const dialogueMessages = ref<DialogueMessage[]>([])
// 打字机效果状态
const isTyping = ref(false)
const typingMessage = ref('')
const typingFullMessage = ref('')
const typingSpeaker = ref('')
const typingSide = ref<'affirmative' | 'negative'>('affirmative')
const typingSpeed = 30 // 毫秒/字
let typingTimer: any = null

// 消息队列
const messageQueue = ref<DialogueMessage[]>([])

// Computeds
const isPlaying = computed(() => !!gameState.value.topic)
const isGameOver = computed(() => gameState.value.phase === GamePhase.GAME_OVER)

const affirmativePlayers = computed(() => 
  gameState.value.players.filter(p => [Role.AFF_1, Role.AFF_2, Role.AFF_3, Role.AFF_4].includes(p.role))
)
const negativePlayers = computed(() => 
  gameState.value.players.filter(p => [Role.NEG_1, Role.NEG_2, Role.NEG_3, Role.NEG_4].includes(p.role))
)

const getRoleLabel = (role: Role) => {
  const labels: Record<Role, string> = {
    [Role.AFF_1]: '一辩',
    [Role.AFF_2]: '二辩',
    [Role.AFF_3]: '三辩',
    [Role.AFF_4]: '四辩',
    [Role.NEG_1]: '一辩',
    [Role.NEG_2]: '二辩',
    [Role.NEG_3]: '三辩',
    [Role.NEG_4]: '四辩',
  }
  return labels[role] || role
}

const phaseText = computed(() => {
  switch(gameState.value.phase) {
    case GamePhase.OPENING: return "OPENING"
    case GamePhase.REBUTTAL: return "REBUTTAL"
    case GamePhase.FREE_DEBATE: return "FREE DEBATE"
    case GamePhase.CLOSING: return "CLOSING"
    case GamePhase.GAME_OVER: return "ENDED"
    default: return "STANDBY"
  }
})

const phaseClass = computed(() => {
  if (gameState.value.phase === GamePhase.FREE_DEBATE) return 'phase-danger'
  if (gameState.value.phase === GamePhase.GAME_OVER) return 'phase-success'
  return 'phase-primary'
})

const isPlayerSpeaking = (role: Role) => {
  return gameState.value.current_speaker_role === role
}

const scrollDialogue = () => {
  nextTick(() => {
    if (dialogueContainer.value) {
      dialogueContainer.value.scrollTop = dialogueContainer.value.scrollHeight
    }
  })
}

// 解析单条日志
const parseSingleLog = (log: string): DialogueMessage | null => {
  // 1. 尝试解析对话格式
  const match = log.match(/^[【\[]([^\]】]+)[】\]]\s*[:：]?\s*(.*)$/)
  if (match && match[1]) {
    const speaker = match[1]
    const content = match[2] || '' // 允许内容为空
    const isNegative = speaker.includes('反') || speaker.includes('NEG') || speaker.includes('neg')
    return { speaker, side: isNegative ? 'negative' : 'affirmative', content }
  }
  
  // 2. 如果不匹配对话格式，作为系统消息返回
  // 这种情况下，整条日志都作为内容
  if (log.trim()) {
      return { speaker: '系统', side: 'affirmative', content: log }
  }
  
  return null
}

// Parse history to dialogue messages (用于初始化)
const parseHistory = (history: string[]) => {
  const messages: DialogueMessage[] = []
  for (const log of history) {
    const parsed = parseSingleLog(log)
    if (parsed) {
      messages.push(parsed)
    }
  }
  return messages
}

// 打字机效果函数
const startTyping = (message: DialogueMessage): Promise<void> => {
  return new Promise((resolve) => {
    isTyping.value = true
    typingSpeaker.value = message.speaker
    typingSide.value = message.side
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
      side: typingSide.value,
      content: typingFullMessage.value
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
}

// 处理队列中的消息
const processQueue = async () => {
  if (isTyping.value || messageQueue.value.length === 0) return
  
  const nextMsg = messageQueue.value.shift()
  if (nextMsg) {
    await startTyping(nextMsg)
    // 处理完一条后，继续检查队列
    processQueue()
  }
}

// 监听队列变化，自动开始处理
watch(() => messageQueue.value.length, () => {
    processQueue()
})

// API
const handleOpenStart = () => {
  showStartDialog.value = true
}

const confirmStart = async () => {
  if (!topicInput.value) return ElMessage.warning('Please enter a topic')
  loading.value = true
  try {
    const res = await startGameApi(topicInput.value)
    
    // 计算新消息
    const newMessages = res.history.slice(gameState.value.history.length)
    
    // 更新状态
    gameState.value = res
    showStartDialog.value = false
    ElMessage.success('Debate Started!')
    
    // 将新消息加入队列
    for (const log of newMessages) {
      const parsed = parseSingleLog(log)
      if (parsed) {
        messageQueue.value.push(parsed)
      }
    }
    
  } catch (e) {
    ElMessage.error('Failed to start')
  } finally {
    loading.value = false
  }
}

const handleNext = async () => {
  // 如果正在打字或队列不为空，不允许下一步
  if (isTyping.value || messageQueue.value.length > 0) return
  
  try {
    const prevHistoryLen = gameState.value.history.length
    const res = await nextStepApi()
    
    // 获取新增加的消息
    const newLogs = res.history.slice(prevHistoryLen)
    
    gameState.value = res
    
    // 将所有新消息加入队列
    for (const log of newLogs) {
      const parsed = parseSingleLog(log)
      if (parsed) {
        messageQueue.value.push(parsed)
      }
    }

    if (res.phase === GamePhase.GAME_OVER) {
      if (autoPlayTimer.value) {
        stopAutoPlay()
      }
      ElMessage.success('Debate Ended')
    }
  } catch (e) {
    stopAutoPlay()
  }
}

// Auto Play
const toggleAutoPlay = () => {
  if (autoPlayTimer.value) stopAutoPlay()
  else startAutoPlay()
}

const startAutoPlay = () => {
  const autoStep = async () => {
    if (isGameOver.value || isTyping.value || messageQueue.value.length > 0) {
      if (isGameOver.value) stopAutoPlay()
      return
    }
    await handleNext()
  }
  
  // 使用 setTimeout 代替 setInterval，确保上一步完成后才执行下一步
  const scheduleNext = () => {
    autoPlayTimer.value = setTimeout(async () => {
      await autoStep()
      if (autoPlayTimer.value && !isGameOver.value) {
        scheduleNext()
      }
    }, 1500) // 打字完成后等待 1.5 秒再进行下一步
  }
  scheduleNext()
}

const stopAutoPlay = () => {
  if (autoPlayTimer.value) {
    clearTimeout(autoPlayTimer.value)
    autoPlayTimer.value = null
  }
}

const handleReset = () => {
  stopAutoPlay()
  gameState.value = {
    topic: '',
    players: [],
    phase: GamePhase.NOT_STARTED,
    turn_index: 0,
    history: [],
    hidden_history: [],
    winner: null
  }
  dialogueMessages.value = []
  messageQueue.value = []
  isTyping.value = false
  typingMessage.value = ''
  typingFullMessage.value = ''
  
  if (typingTimer) {
    clearTimeout(typingTimer)
    typingTimer = null
  }
  
  ElMessage.info('Reset Game')
}

onMounted(async () => {
  try {
    const res = await getGameStatusApi()
    if (res && res.players) {
      gameState.value = res
      // 这里仍然使用直接解析，避免每次刷新页面都重播
      dialogueMessages.value = parseHistory(res.history)
    }
    scrollDialogue()
  } catch(e) {}
})

onUnmounted(() => {
  stopAutoPlay()
})
</script>

<style scoped>
.debate-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #0a0a0f;
  background-image: 
    radial-gradient(ellipse at center, #0d1a2d 0%, #0a0a0f 70%);
  color: #e0e0e0;
  overflow: hidden;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

/* Header */
.header {
  text-align: center;
  padding: 15px 20px;
  background: rgba(0, 0, 0, 0.5);
  border-bottom: 1px solid rgba(100, 255, 218, 0.2);
}

.title {
  margin: 0;
  font-size: 1.8rem;
  color: #00ffd5;
  text-shadow: 0 0 20px rgba(0, 255, 213, 0.5);
  letter-spacing: 4px;
}

.topic-display {
  margin-top: 10px;
  font-size: 1.1rem;
}

.topic-label {
  color: #666;
  margin-right: 10px;
}

.topic-text {
  color: #ffd700;
  font-weight: bold;
}

.phase-indicator {
  margin-top: 10px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
}

.phase-tag {
  padding: 4px 16px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: bold;
  letter-spacing: 2px;
}

.phase-primary {
  background: rgba(0, 255, 213, 0.2);
  color: #00ffd5;
  border: 1px solid #00ffd5;
}

.phase-danger {
  background: rgba(255, 85, 85, 0.2);
  color: #ff5555;
  border: 1px solid #ff5555;
  animation: phase-pulse 1s infinite;
}

.phase-success {
  background: rgba(100, 255, 100, 0.2);
  color: #64ff64;
  border: 1px solid #64ff64;
}

@keyframes phase-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.winner-badge {
  color: #ffd700;
  font-size: 1.1rem;
}

/* Arena */
.arena {
  flex: 1;
  display: flex;
  padding: 20px;
  gap: 20px;
  overflow: hidden;
}

/* Lights Column */
.lights-column {
  width: 100px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 20px 10px;
}

.team-label {
  margin: 0 0 10px 0;
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 3px;
}

.affirmative .team-label {
  color: #00ffd5;
  text-shadow: 0 0 10px rgba(0, 255, 213, 0.5);
}

.negative .team-label {
  color: #ff5555;
  text-shadow: 0 0 10px rgba(255, 85, 85, 0.5);
}

/* Light Orb */
.light-orb {
  position: relative;
  width: 70px;
  height: 70px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.orb-glow {
  display: none; /* 不用单独的光晕元素了 */
}

.orb-core {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  transition: all 0.3s ease;
  z-index: 2;
}

.player-label {
  position: absolute;
  bottom: 0px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.75rem;
  color: #888;
  white-space: nowrap;
}

/* Affirmative Orb */
.affirmative .orb-core {
  background: linear-gradient(135deg, #1a3a3a 0%, #0d2d2d 100%);
  border: 3px solid #00ffd5;
  box-shadow: 0 0 8px rgba(0, 255, 213, 0.3);
}

.affirmative .light-orb.is-speaking .orb-core {
  background: linear-gradient(135deg, #00ffd5 0%, #00b896 100%);
  box-shadow: 
    0 0 15px rgba(0, 255, 213, 0.8),
    0 0 30px rgba(0, 255, 213, 0.5),
    0 0 45px rgba(0, 255, 213, 0.3);
  animation: pulse-cyan 1.5s ease-in-out infinite;
}

/* Negative Orb */
.negative .orb-core {
  background: linear-gradient(135deg, #3a1a1a 0%, #2d0d0d 100%);
  border: 3px solid #ff5555;
  box-shadow: 0 0 8px rgba(255, 85, 85, 0.3);
}

.negative .light-orb.is-speaking .orb-core {
  background: linear-gradient(135deg, #ff5555 0%, #cc3333 100%);
  box-shadow: 
    0 0 15px rgba(255, 85, 85, 0.8),
    0 0 30px rgba(255, 85, 85, 0.5),
    0 0 45px rgba(255, 85, 85, 0.3);
  animation: pulse-red 1.5s ease-in-out infinite;
}

@keyframes pulse-cyan {
  0%, 100% { 
    box-shadow: 
      0 0 15px rgba(0, 255, 213, 0.8),
      0 0 30px rgba(0, 255, 213, 0.5),
      0 0 45px rgba(0, 255, 213, 0.3);
  }
  50% { 
    box-shadow: 
      0 0 20px rgba(0, 255, 213, 1),
      0 0 40px rgba(0, 255, 213, 0.7),
      0 0 60px rgba(0, 255, 213, 0.5);
  }
}

@keyframes pulse-red {
  0%, 100% { 
    box-shadow: 
      0 0 15px rgba(255, 85, 85, 0.8),
      0 0 30px rgba(255, 85, 85, 0.5),
      0 0 45px rgba(255, 85, 85, 0.3);
  }
  50% { 
    box-shadow: 
      0 0 20px rgba(255, 85, 85, 1),
      0 0 40px rgba(255, 85, 85, 0.7),
      0 0 60px rgba(255, 85, 85, 0.5);
  }
}

.light-orb.is-speaking .player-label {
  color: #fff;
}

/* Dialogue Area */
.dialogue-area {
  flex: 1;
  position: relative;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 10px;
  border: 1px solid rgba(100, 255, 218, 0.1);
  overflow: hidden;
}

.dialogue-bg-grid {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(0, 255, 213, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 255, 213, 0.03) 1px, transparent 1px);
  background-size: 30px 30px;
  pointer-events: none;
}

.dialogue-content {
  position: relative;
  height: 100%;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

/* Message Bubble */
.message-bubble {
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 12px;
  background: rgba(30, 30, 40, 0.9);
}

.message-bubble.affirmative {
  align-self: flex-start;
  border-left: 3px solid #00ffd5;
  background: linear-gradient(135deg, rgba(0, 50, 50, 0.8) 0%, rgba(30, 30, 40, 0.9) 100%);
}

.message-bubble.negative {
  align-self: flex-end !important;
  margin-left: auto !important;
  border-left: none !important;
  border-right: 3px solid #ff5555 !important;
  background: linear-gradient(135deg, rgba(50, 20, 20, 0.8) 0%, rgba(30, 30, 40, 0.9) 100%) !important;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 0.8rem;
}

.speaker-name {
  font-weight: bold;
}

.message-bubble.affirmative .speaker-name {
  color: #00ffd5;
}

.message-bubble.negative .speaker-name {
  color: #ff5555;
}

.speaker-side {
  color: #666;
  font-size: 0.7rem;
}

.message-text {
  line-height: 1.6;
  font-size: 0.95rem;
}

.cursor-blink {
  animation: blink 0.8s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* Control Panel */
.control-panel {
  display: flex;
  justify-content: center;
  gap: 20px;
  padding: 15px;
  background: rgba(0, 0, 0, 0.7);
  border-top: 1px solid rgba(100, 255, 218, 0.2);
}

.ctrl-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 25px;
  border: 2px solid;
  border-radius: 30px;
  background: transparent;
  font-family: inherit;
  font-size: 0.9rem;
  font-weight: bold;
  letter-spacing: 2px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.ctrl-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.ctrl-btn.start {
  color: #00ffd5;
  border-color: #00ffd5;
}

.ctrl-btn.start:hover:not(:disabled) {
  background: rgba(0, 255, 213, 0.2);
  box-shadow: 0 0 20px rgba(0, 255, 213, 0.4);
}

.ctrl-btn.next {
  color: #ffd700;
  border-color: #ffd700;
}

.ctrl-btn.next:hover:not(:disabled) {
  background: rgba(255, 215, 0, 0.2);
  box-shadow: 0 0 20px rgba(255, 215, 0, 0.4);
}

.ctrl-btn.auto {
  color: #ff69b4;
  border-color: #ff69b4;
}

.ctrl-btn.auto:hover:not(:disabled) {
  background: rgba(255, 105, 180, 0.2);
  box-shadow: 0 0 20px rgba(255, 105, 180, 0.4);
}

.ctrl-btn.reset {
  color: #ff5555;
  border-color: #ff5555;
}

.ctrl-btn.reset:hover:not(:disabled) {
  background: rgba(255, 85, 85, 0.2);
  box-shadow: 0 0 20px rgba(255, 85, 85, 0.4);
}

.btn-icon {
  font-size: 1.1rem;
}

/* Scrollbar */
.dialogue-content::-webkit-scrollbar {
  width: 6px;
}

.dialogue-content::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.3);
}

.dialogue-content::-webkit-scrollbar-thumb {
  background: rgba(0, 255, 213, 0.3);
  border-radius: 3px;
}

/* Dialog Override */
:deep(.el-dialog) {
  background: #1a1a2e;
  border: 1px solid rgba(100, 255, 218, 0.3);
}

:deep(.el-dialog__title) {
  color: #00ffd5;
}

:deep(.el-input__wrapper) {
  background: rgba(0, 0, 0, 0.3);
  box-shadow: 0 0 0 1px rgba(100, 255, 218, 0.3) inset;
}

:deep(.el-input__inner) {
  color: #e0e0e0;
}
</style>
