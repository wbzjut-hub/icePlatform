<template>
  <div class="ai-lab-layout">

    <transition name="fade">
      <div v-if="ENABLE_VOICE && isRecording" class="recording-overlay">
        <div class="recording-content">
          <div class="mic-icon-wrapper">
            <el-icon class="mic-icon is-pulsing"><Microphone /></el-icon>
          </div>
          <div class="recording-text">正在聆听... (松开空格发送)</div>
          <div class="wave-lines">
            <span></span><span></span><span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </transition>

    <aside class="sidebar">
      <div class="sidebar-header">
        <el-button class="new-chat-btn" :icon="Plus" @click="handleNewChat" plain>
          新建随机对话
        </el-button>
      </div>

      <div class="session-list">
        <div
            class="session-item pinned-agent"
            :class="{ active: currentSessionId === FIXED_AGENT_SESSION_ID }"
            @click="handleOpenFixedAgent"
        >
          <div class="session-icon">
            <el-icon><AlarmClock /></el-icon>
          </div>
          <div class="session-title">日程管家 (专属)</div>
          <el-tag size="small" type="success" effect="dark" class="agent-tag">Agent</el-tag>
        </div>

        <div class="divider"></div>

        <div
            v-for="session in sessions"
            :key="session.id"
            class="session-item"
            :class="{ active: currentSessionId === session.id }"
            @click="handleSelectSession(session.id)"
            v-show="session.id !== FIXED_AGENT_SESSION_ID"
        >
          <div class="session-icon"><el-icon><ChatDotSquare /></el-icon></div>
          <div class="session-title">{{ session.title }}</div>
          <div class="session-delete" @click.stop="handleDeleteSession(session.id)">
            <el-icon><Delete /></el-icon>
          </div>
        </div>

        <div v-if="sessions.length === 0" class="no-sessions">
          暂无历史记录
        </div>
      </div>
    </aside>

    <main class="main-content">
      <div class="chat-header">
        <div class="header-left">
          <span class="model-label">智能体模式:</span>
          <el-select
              v-model="currentWorkflowId"
              placeholder="选择模式"
              size="small"
              style="width: 160px"
              class="workflow-select"
          >
            <el-option
                v-for="wf in workflows"
                :key="wf.id"
                :label="wf.name"
                :value="wf.id"
            >
              <span style="float: left">{{ wf.name }}</span>
            </el-option>
          </el-select>
        </div>

        <div class="header-right" v-if="ENABLE_VOICE">
          <el-tooltip content="长按空格键进行语音输入" placement="bottom">
            <el-tag type="info" size="small" effect="plain" style="cursor: help;">
              <el-icon><Microphone /></el-icon> 按住空格说话
            </el-tag>
          </el-tooltip>
        </div>
      </div>

      <div class="chat-window" ref="chatWindowRef">
        <div v-if="messages.length === 0" class="empty-state">
          <el-icon :size="60"><Cpu /></el-icon>
          <p>DeepSeek AI 助手</p>
          <p class="sub-tip">请在上方选择模式，开始体验 AI 能力。</p>
          <div class="quick-tips" v-if="currentWorkflowId === 'wf_agent'">
            <p>试试发送：</p>
            <el-tag size="small" type="info" @click="fillInput('帮我添加一个明天上午9点的会议待办')">帮我添加一个明天上午9点的会议待办</el-tag>
            <el-tag size="small" type="info" @click="fillInput('我明天有什么安排？')">我明天有什么安排？</el-tag>
          </div>
        </div>

        <div v-for="(msg, index) in messages" :key="index" class="message-row" :class="msg.role">
          <div class="avatar">
            <el-icon v-if="msg.role === 'user'"><User /></el-icon>
            <el-icon v-else><Cpu /></el-icon>
          </div>
          <div class="message-content-wrapper">
            <div class="message-bubble">
              <div class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
            </div>
            <div v-if="msg.role === 'assistant' && msg.usage" class="token-usage">
              <span>Input: {{ msg.usage.prompt_tokens }}</span><span class="dot">·</span>
              <span>Output: {{ msg.usage.completion_tokens }}</span><span class="dot">·</span>
              <span>Total: {{ msg.usage.total_tokens }}</span>
            </div>
          </div>
        </div>

        <div v-if="loading" class="message-row assistant thinking-mode">
          <div class="avatar is-spinning"><el-icon><Cpu /></el-icon></div>
          <div class="message-bubble thinking-bubble">
            <div class="thinking-content">
              <span class="wave-bar"></span><span class="wave-bar"></span><span class="wave-bar"></span><span class="wave-bar"></span><span class="wave-bar"></span>
            </div>
            <span class="thinking-text">DeepSeek 正在思考...</span>
          </div>
        </div>
      </div>

      <div class="input-area">
        <el-input
            v-model="userInput"
            type="textarea"
            :rows="3"
            :placeholder="inputPlaceholder"
            @keydown.ctrl.enter="sendMessage"
            resize="none"
            :disabled="loading"
            ref="inputRef"
        />
        <el-button type="primary" :loading="loading" @click="sendMessage" class="send-btn">
          发送
        </el-button>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { useRoute } from 'vue-router'
import { User, Cpu, Plus, ChatDotSquare, Delete, AlarmClock, Microphone } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSessionsApi, getMessagesApi, chatWithAiApi, deleteSessionApi, getWorkflowsApi } from '@/api/modules/ai'
import type { ChatSession, ChatMessage, Workflow } from '@/api/modules/ai'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/atom-one-dark.css'

// 🌟 语音模块引入
// 即使搁置功能，只要文件存在，import 就不会报错，打包也正常
import { useAudioRecorder } from '@/hooks/useAudioRecorder'
import { voiceApi } from '@/api/modules/voice'

// ==========================================
// 🛠️ 功能开关：是否启用语音交互
// 设为 true：保留代码和交互 (当前状态)
// 设为 false：彻底隐藏入口和按键监听 (搁置状态)
const ENABLE_VOICE = false
// ==========================================

const route = useRoute()
const FIXED_AGENT_SESSION_ID = "fixed_session_robot"

// Markdown Init
const md = new MarkdownIt({ html: true, linkify: true, typographer: true })
md.options.highlight = (str: string, lang: string) => {
  if (lang && hljs.getLanguage(lang)) {
    try { return '<pre class="hljs"><code>' + hljs.highlight(str, { language: lang, ignoreIllegals: true }).value + '</code></pre>' } catch (__) {}
  }
  return '<pre class="hljs"><code>' + md.utils.escapeHtml(str) + '</code></pre>'
}

// Data
const sessions = ref<ChatSession[]>([])
const workflows = ref<Workflow[]>([])
const currentSessionId = ref<string | null>(null)
const currentWorkflowId = ref('wf_agent')
const messages = ref<ChatMessage[]>([])
const userInput = ref('')
const loading = ref(false)
const chatWindowRef = ref<HTMLElement>()
const inputRef = ref()

// Computed
const inputPlaceholder = computed(() => {
  return ENABLE_VOICE
      ? "输入问题... (Ctrl+Enter发送 / 按住空格语音)"
      : "输入问题... (Ctrl+Enter发送)"
})

// --- 🎤 语音逻辑 (保留代码) ---
const { isRecording, startRecording, stopRecording } = useAudioRecorder()
const isSpacePressed = ref(false)

const handleKeyDown = async (e: KeyboardEvent) => {
  if (!ENABLE_VOICE) return // 搁置时直接跳过

  const target = e.target as HTMLElement
  if (target.tagName === 'TEXTAREA' || target.tagName === 'INPUT') return

  if (e.code === 'Space' && !isSpacePressed.value && !loading.value) {
    e.preventDefault()
    isSpacePressed.value = true
    await startRecording()
  }
}

const handleKeyUp = async (e: KeyboardEvent) => {
  if (!ENABLE_VOICE) return // 搁置时直接跳过

  if (e.code === 'Space' && isSpacePressed.value) {
    isSpacePressed.value = false
    const audioBlob = await stopRecording()

    loading.value = true
    try {
      // Need File object for API
      const file = new File([audioBlob], "voice_input.wav", { type: "audio/wav" })
      const res = await voiceApi.transcribe(file)
      if (res && res.data && res.data.text) {
        userInput.value = res.data.text
        await sendMessage()
      } else {
        ElMessage.warning('未检测到语音')
        loading.value = false
      }
    } catch (e) {
      // 搁置期间如果报错，只会在控制台显示，或者你可以把这个提示注释掉
      console.warn('语音识别暂不可用', e)
      ElMessage.info('语音服务连接超时，已转为文字输入模式')
      loading.value = false
    }
  }
}

// Lifecycle
onMounted(async () => {
  await loadWorkflows()
  await loadSessionList()

  // 始终挂载监听，通过 ENABLE_VOICE 在内部控制是否执行
  window.addEventListener('keydown', handleKeyDown)
  window.addEventListener('keyup', handleKeyUp)

  if (route.query.session) {
    const sid = route.query.session as string
    sid === FIXED_AGENT_SESSION_ID ? handleOpenFixedAgent() : handleSelectSession(sid)
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('keyup', handleKeyUp)
})

// Methods
const loadWorkflows = async () => {
  try {
    const res = await getWorkflowsApi()
    workflows.value = res || []
    if (workflows.value.length > 0 && !currentWorkflowId.value) {
      const defaultWf = workflows.value.find(w => w.id === 'wf_agent')
      currentWorkflowId.value = defaultWf?.id || workflows.value[0]?.id || ''
    }
  } catch (e) { console.error(e) }
}

const loadSessionList = async () => {
  try {
    const res = await getSessionsApi()
    sessions.value = res || []
  } catch (e) { console.error(e) }
}

const fillInput = (text: string) => {
  userInput.value = text
  inputRef.value?.focus()
}

const handleOpenFixedAgent = async () => {
  if (currentSessionId.value === FIXED_AGENT_SESSION_ID) return
  currentSessionId.value = FIXED_AGENT_SESSION_ID
  currentWorkflowId.value = 'wf_agent'
  loading.value = true
  messages.value = []
  try {
    const res = await getMessagesApi(FIXED_AGENT_SESSION_ID)
    messages.value = res || []
  } catch (e) { messages.value = [] }
  finally { loading.value = false; scrollToBottom() }
}

const handleSelectSession = async (id: string) => {
  if (currentSessionId.value === id) return
  currentSessionId.value = id
  loading.value = true
  try {
    const res = await getMessagesApi(id)
    messages.value = res || []
    scrollToBottom()
  } catch (e) { ElMessage.error('加载历史失败') }
  finally { loading.value = false }
}

const handleNewChat = () => { currentSessionId.value = null; messages.value = [] }

const handleDeleteSession = async (id: string) => {
  try {
    await ElMessageBox.confirm('确认删除？', '警告', { type: 'warning' })
    await deleteSessionApi(id)
    await loadSessionList()
    if (currentSessionId.value === id) handleNewChat()
    ElMessage.success('已删除')
  } catch (e) {}
}

const renderMarkdown = (text: string) => (text ? md.render(text) : '')

const scrollToBottom = async () => {
  await nextTick()
  if (chatWindowRef.value) chatWindowRef.value.scrollTo({ top: chatWindowRef.value.scrollHeight, behavior: 'smooth' })
}

const sendMessage = async () => {
  const text = userInput.value.trim()
  if (!text || loading.value) return
  messages.value.push({ role: 'user', content: text })
  userInput.value = ''
  scrollToBottom()
  loading.value = true
  const activeSessionId = currentSessionId.value

  try {
    const res = await chatWithAiApi(text, activeSessionId, currentWorkflowId.value)
    if (res && res.reply) {
      if (currentSessionId.value !== res.session_id && activeSessionId !== null) return
      messages.value.push({ role: 'assistant', content: res.reply, usage: res.usage })
      if (!activeSessionId && res.session_id) {
        currentSessionId.value = res.session_id
        await loadSessionList()
      }
    }
  } catch (error: any) {
    const errorMsg = error.response?.data?.message || error.message || 'Error'
    messages.value.push({ role: 'assistant', content: `❌ ${errorMsg}` })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}
</script>

<style scoped>
/* 录音遮罩 */
.recording-overlay {
  position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(10, 25, 47, 0.85); backdrop-filter: blur(8px);
  z-index: 9999; display: flex; align-items: center; justify-content: center; flex-direction: column;
}
.recording-content { text-align: center; color: #fff; }
.mic-icon-wrapper {
  width: 80px; height: 80px; background: var(--primary-accent-color);
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 40px; color: #0a192f; margin-bottom: 20px;
  box-shadow: 0 0 30px rgba(100, 255, 218, 0.4);
}
.mic-icon.is-pulsing { animation: pulse 1.5s infinite; }
.recording-text { font-size: 1.5rem; font-weight: bold; letter-spacing: 1px; margin-bottom: 10px; }
.wave-lines { display: flex; gap: 6px; justify-content: center; height: 30px; align-items: center; }
.wave-lines span { width: 4px; background: var(--primary-accent-color); border-radius: 2px; animation: waveAudio 1s ease-in-out infinite; }
.wave-lines span:nth-child(1) { height: 10px; animation-delay: 0s; }
.wave-lines span:nth-child(2) { height: 20px; animation-delay: 0.1s; }
.wave-lines span:nth-child(3) { height: 30px; animation-delay: 0.2s; }
.wave-lines span:nth-child(4) { height: 20px; animation-delay: 0.3s; }
.wave-lines span:nth-child(5) { height: 10px; animation-delay: 0.4s; }
@keyframes pulse { 0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(100, 255, 218, 0.7); } 70% { transform: scale(1.1); box-shadow: 0 0 0 20px rgba(100, 255, 218, 0); } 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(100, 255, 218, 0); } }
@keyframes waveAudio { 0%, 100% { height: 10px; } 50% { height: 30px; } }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* 基础布局 */
.ai-lab-layout {
  display: flex;
  height: 100%;
  width: 100%;
  background-color: var(--bg-color-deep-space);
  position: relative;
  overflow: hidden; /* 防止溢出 */
}

/* 侧边栏 */
.sidebar {
  width: 250px; /* Spec: 250px */
  background-color: var(--bg-color-panel);
  border-right: 1px solid var(--border-color-tech);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  z-index: 20;
}
.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid var(--border-color-tech);
}
.new-chat-btn {
  width: 100%;
  border-radius: 6px;
  background-color: rgba(100, 255, 218, 0.05);
  border: 1px solid var(--primary-accent-color);
  color: var(--primary-accent-color);
  font-weight: bold;
}
.new-chat-btn:hover {
  background-color: var(--primary-accent-color);
  color: #0a192f;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}
.session-list::-webkit-scrollbar { width: 4px; }
.session-list::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }

.session-item {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  margin-bottom: 8px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-color-secondary);
  transition: all 0.2s ease;
  border: 1px solid transparent;
}
.session-item:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--text-color-primary);
  transform: translateX(2px);
}
.session-item.active {
  background-color: rgba(100, 255, 218, 0.1);
  color: var(--primary-accent-color);
  border-color: rgba(100, 255, 218, 0.3);
}
.session-icon { margin-right: 10px; display: flex; align-items: center; font-size: 16px; }
.session-title { flex: 1; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; font-size: 14px; font-weight: 500; }
.session-delete { opacity: 0; transition: opacity 0.2s; color: var(--text-color-secondary); padding: 4px; }
.session-delete:hover { color: #f56c6c; background: rgba(255,0,0,0.1); border-radius: 4px; }
.session-item:hover .session-delete { opacity: 1; }

.pinned-agent {
  background: linear-gradient(90deg, rgba(100, 255, 218, 0.1) 0%, transparent 100%);
  border-left: 3px solid var(--primary-accent-color);
  color: var(--text-color-primary);
}
.pinned-agent.active {
  background: linear-gradient(90deg, rgba(100, 255, 218, 0.2) 0%, transparent 100%);
}
.agent-tag { transform: scale(0.85); font-weight: bold; border: none; margin-left: auto; }
.divider { height: 1px; background-color: var(--border-color-tech); margin: 15px 0; opacity: 0.3; }
.no-sessions { text-align: center; color: var(--text-color-secondary); margin-top: 60px; font-size: 13px; opacity: 0.5; }

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-color-deep-space);
  min-width: 0;
  position: relative;
}

/* Chat Header */
.chat-header {
  height: 60px;
  padding: 0 25px;
  border-bottom: 1px solid var(--border-color-tech);
  background-color: rgba(10, 25, 47, 0.95); /* 增加不透明度 */
  backdrop-filter: blur(10px);
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 10;
  flex-shrink: 0;
}
.model-label { font-size: 14px; color: var(--text-color-secondary); margin-right: 10px; }

/* Chat Window */
.chat-window {
  flex: 1;
  overflow-y: auto;
  padding: 20px 40px;
  scroll-behavior: smooth;
  display: flex;
  flex-direction: column;
}
.chat-window::-webkit-scrollbar { width: 6px; }
.chat-window::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }

/* Empty State */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-color-secondary);
  opacity: 0.8;
  height: 100%; /* Ensure full height alignment */
}
.empty-state .el-icon { margin-bottom: 20px; color: var(--primary-accent-color); opacity: 0.8; animation: float 3s ease-in-out infinite; }
@keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
.sub-tip { font-size: 1rem; margin-top: 10px; margin-bottom: 30px; }
.quick-tips { display: flex; flex-direction: column; gap: 12px; align-items: center; }
.quick-tips .el-tag { padding: 8px 15px; height: auto; font-size: 13px; cursor: pointer; background: rgba(255,255,255,0.05); border: 1px solid var(--border-color-tech); color: var(--text-color-primary); }
.quick-tips .el-tag:hover { border-color: var(--primary-accent-color); color: var(--primary-accent-color); }

/* Messages */
.message-row {
  display: flex;
  margin-bottom: 30px;
  align-items: flex-start;
  animation: fadeIn 0.3s ease;
  width: 100%;
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

.message-row.user { flex-direction: row-reverse; }

.avatar {
  width: 40px; height: 40px;
  border-radius: 8px; /* Slightly squarer than typical circles to fit theme */
  background-color: var(--bg-color-panel);
  border: 1px solid var(--border-color-tech);
  display: flex; align-items: center; justify-content: center;
  color: var(--text-color-primary);
  margin: 0 15px;
  flex-shrink: 0;
  font-size: 20px;
}
.message-row.user .avatar {
  background-color: var(--primary-accent-color);
  color: #0a192f;
  border: none;
}
.avatar.is-spinning {
  animation: spin 3s linear infinite;
  border-color: var(--primary-accent-color);
  color: var(--primary-accent-color);
}
@keyframes spin { 100% { transform: rotate(360deg); } }

.message-content-wrapper {
  display: flex;
  flex-direction: column;
  max-width: 80%; /* Increased width */
}
.message-row.user .message-content-wrapper {
  align-items: flex-end; /* Align prompt token info to right */
}

.message-bubble {
  padding: 12px 18px;
  border-radius: 12px;
  line-height: 1.6;
  word-wrap: break-word;
  font-size: 15px;
  position: relative;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.user .message-bubble {
  background-color: var(--primary-accent-color);
  color: #0a192f;
  border-top-right-radius: 2px;
}
.assistant .message-bubble {
  background-color: var(--bg-color-panel);
  border: 1px solid var(--border-color-tech);
  color: var(--text-color-primary);
  border-top-left-radius: 2px;
}

.token-usage {
  font-size: 11px;
  color: var(--text-color-secondary);
  margin-top: 6px;
  padding: 0 4px;
  opacity: 0.6;
  font-family: monospace;
}

/* Thinking Indicator */
.thinking-bubble {
  background: transparent !important;
  border: 1px solid var(--primary-accent-color) !important;
  padding: 15px 25px;
  display: flex;
  align-items: center;
  gap: 15px;
  box-shadow: 0 0 15px rgba(100, 255, 218, 0.1);
}
.wave-bar {
  width: 4px;
  background-color: var(--primary-accent-color);
  border-radius: 2px;
  animation: wave 1s ease-in-out infinite;
}
.wave-bar:nth-child(1) { height: 15px; animation-delay: 0.0s; }
.wave-bar:nth-child(2) { height: 25px; animation-delay: 0.1s; }
.wave-bar:nth-child(3) { height: 35px; animation-delay: 0.2s; }
.wave-bar:nth-child(4) { height: 25px; animation-delay: 0.3s; }
.wave-bar:nth-child(5) { height: 15px; animation-delay: 0.4s; }
@keyframes wave { 0%, 100% { transform: scaleY(0.5); opacity: 0.5; } 50% { transform: scaleY(1.2); opacity: 1; } }
.thinking-text {
  color: var(--primary-accent-color);
  font-size: 14px;
  letter-spacing: 1px;
  animation: pulse 2s infinite;
}

/* Input Area */
.input-area {
  padding: 20px 40px;
  background-color: var(--bg-color-deep-space);
  border-top: 1px solid var(--border-color-tech);
  display: flex;
  gap: 15px;
  align-items: flex-end;
  flex-shrink: 0;
  z-index: 10;
}
:deep(.el-textarea__inner) {
  background-color: var(--bg-color-panel);
  border: 1px solid var(--border-color-tech);
  color: var(--text-color-primary);
  border-radius: 8px;
  padding: 12px;
  font-family: inherit;
  font-size: 15px;
  box-shadow: none;
  transition: border-color 0.2s, background-color 0.2s;
}
:deep(.el-textarea__inner:focus) {
  border-color: var(--primary-accent-color);
  background-color: rgba(17, 34, 64, 0.8);
}
.send-btn {
  height: 45px;
  padding: 0 30px;
  border-radius: 8px;
  font-weight: bold;
  letter-spacing: 1px;
}

/* Markdown Customization */
:deep(.markdown-body) {
  font-family: "JetBrains Mono", -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  font-size: 15px;
  line-height: 1.7;
}
:deep(.markdown-body h1), :deep(.markdown-body h2), :deep(.markdown-body h3) {
  border-bottom: 1px solid rgba(255,255,255,0.1);
  padding-bottom: 8px;
  margin-top: 20px;
  margin-bottom: 12px;
  color: #fff;
  font-weight: 600;
}
:deep(.markdown-body p) { margin-bottom: 12px; }
:deep(.markdown-body pre) {
  background-color: #011627 !important; /* Night Owl styled dark bg */
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 15px 0;
  border: 1px solid #1e2d3d;
}
:deep(.markdown-body code) {
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 0.9em;
  background-color: rgba(255, 255, 255, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  color: #e6f7ff;
}
:deep(.markdown-body pre code) {
  background-color: transparent;
  padding: 0;
  color: inherit;
  border: none;
}
:deep(.markdown-body a) {
  color: var(--primary-accent-color);
  text-decoration: none;
  border-bottom: 1px dashed var(--primary-accent-color);
}
:deep(.markdown-body a:hover) {
  border-bottom-style: solid;
}
</style>