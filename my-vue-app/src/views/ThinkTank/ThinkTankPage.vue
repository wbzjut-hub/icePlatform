<template>
  <div class="think-tank-container">
    
    <!-- 1. Expert Gallery View -->
    <transition name="zoom-fade" mode="out-in">
      <div v-if="!activeExpert" class="gallery-view" key="gallery">
        <div class="page-header">
          <h2>🧠 全球智囊团 (Universal Think Tank)</h2>
          <div class="header-desc">
            汇聚 21 位全球顶级专家，为您提供跨学科的智慧支持。
          </div>
          <el-button type="primary" plain size="small" class="add-expert-btn" @click="showCreateDialog = true">
             <el-icon><Plus /></el-icon> 新增专家
          </el-button>
        </div>

        <el-tabs v-model="activeTab" class="domain-tabs">
          <el-tab-pane label="全部专家" name="all" />
          <el-tab-pane v-for="(experts, domain) in expertDomains" :key="domain" :label="domain" :name="domain" />
        </el-tabs>

        <el-row :gutter="24" class="expert-grid">
          <el-col
              v-for="expert in filteredExperts"
              :key="expert.id || expert.name"
              :xs="24" :sm="12" :md="8" :lg="6"
              class="expert-col"
          >
            <div class="expert-card" @click="handleOpenChat(expert)">
              <div class="card-glow"></div>
              <div class="card-content">
                <div class="expert-avatar">
                  <span class="avatar-icon">{{ getDomainIcon(expert.name) }}</span>
                </div>
                <div class="expert-info">
                  <h3 class="expert-name">{{ expert.name }}</h3>
                  <p class="expert-title">{{ getExpertTitle(expert.name) }}</p>
                  <p class="expert-desc">{{ expert.description }}</p>
                </div>
                <div class="expert-footer">
                  <el-tag size="small" effect="plain" class="domain-tag">{{ getDomain(expert.name) }}</el-tag>
                  <div class="footer-actions">
                    <el-button link size="small" @click.stop="handleEditPrompt(expert)">
                       <el-icon><Edit /></el-icon> 设定
                    </el-button>
                    <span class="chat-hint">点击咨询 <el-icon><ArrowRight /></el-icon></span>
                  </div>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 2. Chat View (With Sidebar) -->
      <div v-else class="chat-view-container" key="chat">
        
        <!-- Chat Sidebar -->
        <div class="chat-sidebar">
           <div class="sidebar-header">
             <el-button circle plain size="small" @click="handleCloseChat" class="back-home-btn">
                <el-icon><Grid /></el-icon>
             </el-button>
             <span class="sidebar-title">智囊团成员</span>
           </div>
           
           <div class="sidebar-list">
              <div 
                v-for="expert in allThinkTankExperts" 
                :key="expert.id" 
                class="sidebar-item"
                :class="{ active: activeExpert.id === expert.id }"
                @click="handleSwitchExpert(expert)"
              >
                 <span class="item-icon">{{ getDomainIcon(expert.name) }}</span>
                 <div class="item-info">
                    <div class="item-name">{{ getExpertTitle(expert.name) }}</div>
                    <div class="item-domain">{{ getDomain(expert.name) }}</div>
                 </div>
              </div>
           </div>
        </div>

        <!-- Chat Main Area -->
        <div class="chat-main">
          <div class="chat-header">
            <div class="header-left">
              <el-button circle plain size="small" @click="handleCloseChat" class="mobile-back-btn">
                <el-icon><ArrowLeft /></el-icon>
              </el-button>
              
              <div class="expert-avatar-small">
                {{ getDomainIcon(activeExpert.name) }}
              </div>
              <div class="header-info">
                <div class="expert-name-header">{{ activeExpert.name }}</div>
                <div class="expert-title-header">{{ getExpertTitle(activeExpert.name) }}</div>
              </div>
              <el-button link size="small" @click="handleEditPrompt(activeExpert)" class="header-edit-btn">
                <el-icon><Edit /></el-icon>
              </el-button>
            </div>
            <div class="header-right">
               <el-tag effect="dark" type="success" size="small">在线</el-tag>
            </div>
          </div>

          <div class="chat-body" ref="chatWindowRef">
             <div v-if="messages.length === 0 && !streamingContent" class="empty-state">
                <span class="big-icon">{{ getDomainIcon(activeExpert.name) }}</span>
                <h3>我是 {{ getExpertTitle(activeExpert.name) }}</h3>
                <p>{{ activeExpert.system_prompt.split('\n')[0] }}</p>
                <p class="sub-text">请问有什么可以帮您？</p>
             </div>

             <div v-for="(msg, index) in messages" :key="index" class="message-row" :class="msg.role">
                <div class="msg-avatar">
                  <span v-if="msg.role === 'assistant'">{{ getDomainIcon(activeExpert.name) }}</span>
                  <el-icon v-else><User /></el-icon>
                </div>
                <div class="msg-bubble">
                    <div class="markdown-body" v-html="renderMarkdown(msg.content)" @click="handleCodeCopy($event)"></div>
                    <div class="msg-actions">
                      <el-button link size="small" @click="copyMessage(msg.content)" class="copy-msg-btn">
                        <el-icon><CopyDocument /></el-icon> 复制
                      </el-button>
                      <span v-if="msg.role === 'assistant' && msg.usage" class="token-usage">
                        Tokens: {{ msg.usage.total_tokens }}
                      </span>
                    </div>
                </div>
             </div>
             
             <!-- Streaming Message -->
             <div v-if="streamingContent" class="message-row assistant">
               <div class="msg-avatar"><span>{{ getDomainIcon(activeExpert.name) }}</span></div>
               <div class="msg-bubble streaming">
                  <div class="markdown-body" v-html="renderMarkdown(streamingContent)"></div>
                  <span class="cursor-blink">▌</span>
               </div>
             </div>
             
             <!-- Loading indicator (when waiting for first chunk) -->
             <div v-if="loading && !streamingContent" class="message-row assistant">
               <div class="msg-avatar"><span>{{ getDomainIcon(activeExpert.name) }}</span></div>
               <div class="msg-bubble thinking">
                  <span>正在思考...</span>
               </div>
             </div>
          </div>

          <div class="chat-input-area">
             <el-input 
               v-model="userInput" 
               type="textarea" 
               :rows="1" 
               autosize
               resize="none"
               placeholder="输入您的问题..."
               @keydown.ctrl.enter="sendMessage"
               :disabled="loading"
             />
             <el-button type="primary" :loading="loading" @click="sendMessage">发送</el-button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Prompt Edit Dialog -->
    <el-dialog
      v-model="showPromptDialog"
      title="调整专家设定 (System Prompt)"
      width="600px"
      append-to-body
      class="prompt-dialog"
    >
      <div v-if="editingExpert">
        <p class="dialog-tip">您可以修改 <b>{{ editingExpert.name }}</b> 的系统提示词，这将直接影响其回答风格和思维方式。</p>
        <el-input
          v-model="editingPrompt"
          type="textarea"
          :rows="12"
          placeholder="请输入详细的系统提示词..."
        />
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showPromptDialog = false">取消</el-button>
          <el-button type="primary" @click="savePrompt" :loading="savingPrompt">
            保存设定
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Create Expert Dialog -->
    <el-dialog
      v-model="showCreateDialog"
      title="新增专家智能体"
      width="500px"
      append-to-body
      class="prompt-dialog"
    >
      <el-form label-position="top">
        <el-form-item label="专家名称 / 角色">
          <el-input v-model="newExpert.name" placeholder="例如: Data Wizard (数据巫师)" />
        </el-form-item>
        <el-form-item label="简短描述">
          <el-input v-model="newExpert.description" placeholder="例如: 精通大数据的分析专家" />
        </el-form-item>
        <el-form-item label="核心设定 (System Prompt)">
          <el-input 
            v-model="newExpert.system_prompt" 
            type="textarea" 
            :rows="6" 
            placeholder="定义专家的性格、任务和对话风格..." 
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="createExpert" :loading="creatingExpert">
            创建专家
          </el-button>
        </span>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { ArrowRight, ArrowLeft, User, Grid, Edit, Plus, CopyDocument } from '@element-plus/icons-vue'
import { getWorkflowsApi, getMessagesApi, updateWorkflowApi, createWorkflowApi } from '@/api/modules/ai'
import type { Workflow, ChatMessage } from '@/api/modules/ai'
import { ElMessage } from 'element-plus'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/atom-one-dark.css'

// --- Markdown Setup ---
const md = new MarkdownIt({ html: true, linkify: true, typographer: true })
md.options.highlight = (str: string, lang: string) => {
  const codeHtml = lang && hljs.getLanguage(lang)
    ? hljs.highlight(str, { language: lang, ignoreIllegals: true }).value
    : md.utils.escapeHtml(str)
  
  // Wrap in container with copy button
  return `<div class="code-block-wrapper">
    <button class="code-copy-btn" data-code="${encodeURIComponent(str)}">复制</button>
    <pre class="hljs"><code>${codeHtml}</code></pre>
  </div>`
}
const renderMarkdown = (text: string) => text ? md.render(text) : ''

// --- State ---
const activeTab = ref('all')
const allWorkflows = ref<Workflow[]>([])
const activeExpert = ref<Workflow | null>(null)
const messages = ref<ChatMessage[]>([])
const userInput = ref('')
const loading = ref(false)
const chatWindowRef = ref<HTMLElement>()

// Streaming state
const streamingContent = ref('')

// Prompt Editing State
const showPromptDialog = ref(false)
const editingExpert = ref<Workflow | null>(null)
const editingPrompt = ref('')
const savingPrompt = ref(false)

// Create Expert State
const showCreateDialog = ref(false)
const creatingExpert = ref(false)
const newExpert = ref({
    name: '',
    description: '',
    system_prompt: '',
    tools_config: [] as string[]
})

// --- Domain Logic ---
const expertDomains: Record<string, string[]> = {
  '金融核心': ['Macro Strategist', 'Quant Analyst', 'Risk Manager', 'Crypto Native', 'Macro_Master', 'Quant_Wizard', 'Risk_Guardian'],
  '科技前沿': ['System Architect', 'Algo Geek', 'Security Spec Ops', 'Data Alchemist', 'DevOps Master', 'Code_God', 'Tech_Architect'],
  '科学实证': ['Complex Systems Physicist', 'Evolutionary Biologist', 'Statistician'],
  '创意美学': ['Design Lead', 'Game Producer', 'Space Architect', 'User Researcher', 'Design_Lead'],
  '人文社科': ['Historian', 'Behavioral Psychologist', 'Legal Counsel', 'History_Sage'],
  '战略决策': ['Product Visionary', 'Startup Founder']
}

const getDomain = (name: string) => {
  for (const [domain, keywords] of Object.entries(expertDomains)) {
    if (keywords.some(k => name.includes(k))) return domain
  }
  return '通用领域'
}

const getDomainIcon = (name: string) => {
  const domain = getDomain(name)
  switch (domain) {
    case '金融核心': return '💰'
    case '科技前沿': return '⚡'
    case '科学实证': return '🧬'
    case '创意美学': return '🎨'
    case '人文社科': return '📚'
    case '战略决策': return '♟️'
    default: return '🤖'
  }
}

const getExpertTitle = (name: string) => {
   const match = name.match(/\((.*?)\)/)
   return match ? match[1] : name
}

// --- Data Loading ---
onMounted(async () => {
    await loadExperts()
})

const loadExperts = async () => {
    try {
        const res = await getWorkflowsApi()
        allWorkflows.value = res || []
    } catch (e) { console.error(e) }
}

const allThinkTankExperts = computed(() => {
    return allWorkflows.value.filter(wf => !['wf_general', 'wf_agent'].includes(wf.id!))
})

const filteredExperts = computed(() => {
    if (activeTab.value === 'all') return allThinkTankExperts.value
    return allThinkTankExperts.value.filter(wf => getDomain(wf.name) === activeTab.value)
})

// --- Chat Logic ---
const handleOpenChat = async (expert: Workflow) => {
    if (activeExpert.value && activeExpert.value.id === expert.id) return
    
    activeExpert.value = expert
    messages.value = []
    streamingContent.value = ''
    loading.value = true
    
    const sessionId = `thinktank_${expert.id}`
    try {
       const res = await getMessagesApi(sessionId)
       messages.value = res || []
       scrollToBottom()
    } catch (e) { 
       // New session
    } finally {
       loading.value = false
    }
}

const handleSwitchExpert = (expert: Workflow) => {
    handleOpenChat(expert)
}

const handleCloseChat = () => {
    activeExpert.value = null
    messages.value = []
    streamingContent.value = ''
}

const scrollToBottom = async () => {
    await nextTick()
    if (chatWindowRef.value) {
        chatWindowRef.value.scrollTop = chatWindowRef.value.scrollHeight
    }
}

// 🌟 Streaming Message Send
const sendMessage = async () => {
    const text = userInput.value.trim()
    if (!text || !activeExpert.value || loading.value) return
    
    // Add user message
    messages.value.push({ role: 'user', content: text })
    const currentInput = text
    userInput.value = ''
    scrollToBottom()
    
    loading.value = true
    streamingContent.value = ''
    const sessionId = `thinktank_${activeExpert.value.id}`
    
    // 🌟 Fix: Use full URL in production (Electron), relative in Dev (Vite proxy)
    const isProduction = import.meta.env.PROD
    const baseURL = isProduction ? 'http://127.0.0.1:8008/api/v1' : '/api/v1'
    
    try {
        // Use streaming endpoint
        const response = await fetch(`${baseURL}/ai/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: currentInput,
                session_id: sessionId,
                workflow_id: activeExpert.value.id
            })
        })

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }

        const reader = response.body?.getReader()
        const decoder = new TextDecoder()
        let usageData = null

        if (reader) {
            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                const chunk = decoder.decode(value, { stream: true })
                const lines = chunk.split('\n')

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6))
                            
                            if (data.type === 'content') {
                                streamingContent.value += data.content
                                scrollToBottom()
                            } else if (data.type === 'usage') {
                                usageData = data.usage
                            } else if (data.type === 'done') {
                                // Move streaming content to messages
                                if (streamingContent.value) {
                                    messages.value.push({
                                        role: 'assistant',
                                        content: streamingContent.value,
                                        usage: usageData
                                    })
                                    streamingContent.value = ''
                                }
                            } else if (data.type === 'error') {
                                ElMessage.error(data.error)
                            }
                        } catch (e) {
                            // Ignore parse errors for incomplete chunks
                        }
                    }
                }
            }
        }
    } catch (e: any) {
        ElMessage.error(e.message || 'Error sending message')
        // If streaming failed, clear the streaming content
        if (streamingContent.value) {
            messages.value.push({
                role: 'assistant',
                content: streamingContent.value
            })
            streamingContent.value = ''
        }
    } finally {
        loading.value = false
        scrollToBottom()
    }
}

// --- Prompt Editing Logic ---
const handleEditPrompt = (expert: Workflow) => {
    editingExpert.value = { ...expert }
    editingPrompt.value = expert.system_prompt
    showPromptDialog.value = true
}

const savePrompt = async () => {
    if (!editingExpert.value || !editingExpert.value.id) return
    
    savingPrompt.value = true
    try {
        const updatedWorkflow = {
            ...editingExpert.value,
            system_prompt: editingPrompt.value
        }
        
        await updateWorkflowApi(editingExpert.value.id, updatedWorkflow)
        
        const index = allWorkflows.value.findIndex(w => w.id === editingExpert.value?.id)
        if (index !== -1 && allWorkflows.value[index]) {
            allWorkflows.value[index]!.system_prompt = editingPrompt.value
        }
        
        if (activeExpert.value && activeExpert.value.id === editingExpert.value.id) {
            activeExpert.value.system_prompt = editingPrompt.value
        }

        ElMessage.success('专家设定已更新')
        showPromptDialog.value = false
    } catch (e) {
        ElMessage.error('保存失败')
        console.error(e)
    } finally {
        savingPrompt.value = false
    }
}

// --- Create Expert Logic ---
const createExpert = async () => {
    if (!newExpert.value.name || !newExpert.value.system_prompt) {
        ElMessage.warning('名称和核心设定（Prompt）不能为空')
        return
    }
    
    creatingExpert.value = true
    try {
        await createWorkflowApi({
            name: newExpert.value.name,
            description: newExpert.value.description,
            system_prompt: newExpert.value.system_prompt,
            tools_config: []
        })
        
        ElMessage.success('专家创建成功')
        showCreateDialog.value = false
        newExpert.value = { name: '', description: '', system_prompt: '', tools_config: [] }
        await loadExperts()
    } catch (e) {
        ElMessage.error('创建失败')
        console.error(e)
    } finally {
        creatingExpert.value = false
    }
}

// --- Copy Functions ---
const handleCodeCopy = (event: MouseEvent) => {
    const target = event.target as HTMLElement
    if (target.classList.contains('code-copy-btn')) {
        const code = decodeURIComponent(target.dataset.code || '')
        navigator.clipboard.writeText(code).then(() => {
            target.textContent = '已复制!'
            setTimeout(() => { target.textContent = '复制' }, 2000)
        }).catch(() => {
            ElMessage.error('复制失败')
        })
    }
}

const copyMessage = (content: string) => {
    navigator.clipboard.writeText(content).then(() => {
        ElMessage.success('已复制到剪贴板')
    }).catch(() => {
        ElMessage.error('复制失败')
    })
}
</script>

<style scoped>
.think-tank-container {
  height: 100vh;
  width: 100%;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  color: #fff;
}

/* --- Gallery View --- */
.gallery-view {
  height: 100%;
  overflow-y: auto;
  padding: 30px;
  box-sizing: border-box;
}

.page-header { text-align: center; margin-bottom: 30px; position: relative; }
.page-header h2 { 
  font-size: 32px; 
  background: linear-gradient(to right, #64ffda, #48b0ff); 
  -webkit-background-clip: text; 
  -webkit-text-fill-color: transparent;
  margin-bottom: 10px;
}
.header-desc { color: #94a3b8; font-size: 16px; margin-bottom: 15px; }
.add-expert-btn { position: absolute; right: 0; top: 0; }

.domain-tabs { margin-bottom: 30px; }
:deep(.el-tabs__item) { color: #94a3b8; font-size: 16px; }
:deep(.el-tabs__item.is-active) { color: #64ffda; }
:deep(.el-tabs__nav-wrap::after) { background-color: #334155; }

.expert-col { margin-bottom: 24px; }
.expert-card {
  position: relative;
  background: rgba(30, 41, 59, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.expert-card:hover {
  transform: translateY(-5px);
  border-color: rgba(100, 255, 218, 0.5);
  background: rgba(30, 41, 59, 0.9);
}
.card-glow {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  background: radial-gradient(circle at top right, rgba(100, 255, 218, 0.1), transparent 60%);
  opacity: 0; transition: opacity 0.3s ease;
}
.expert-card:hover .card-glow { opacity: 1; }
.card-content { position: relative; z-index: 1; display: flex; flex-direction: column; height: 100%; }
.expert-avatar {
  width: 60px; height: 60px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  margin-bottom: 16px; font-size: 32px;
}
.expert-name { font-size: 18px; font-weight: bold; color: #f1f5f9; margin: 0 0 4px 0; }
.expert-title { font-size: 13px; color: #64ffda; margin: 0 0 12px 0; font-weight: 500; }
.expert-desc {
  font-size: 14px; color: #94a3b8; line-height: 1.5; margin-bottom: 20px;
  flex: 1; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}
.expert-footer {
  display: flex; justify-content: space-between; align-items: center;
  border-top: 1px solid rgba(255, 255, 255, 0.05); padding-top: 16px;
}
.footer-actions { display: flex; align-items: center; gap: 10px; }
.domain-tag { background: rgba(255, 255, 255, 0.05); border-color: rgba(255, 255, 255, 0.1); color: #94a3b8; }
.chat-hint { font-size: 12px; color: var(--primary-accent-color); display: flex; align-items: center; gap: 4px; }

/* --- Chat View Layout --- */
.chat-view-container {
  display: flex;
  height: 100%;
  background-color: var(--bg-color-deep-space);
}

.chat-sidebar {
  width: 260px;
  background: rgba(15, 23, 42, 0.8);
  border-right: 1px solid rgba(255,255,255,0.1);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  height: 70px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  gap: 15px;
}
.back-home-btn { border-color: rgba(255,255,255,0.2); color: #fff; background: transparent; }
.back-home-btn:hover { border-color: var(--primary-accent-color); color: var(--primary-accent-color); }
.sidebar-title { font-weight: bold; color: #e2e8f0; font-size: 15px; }

.sidebar-list { flex: 1; overflow-y: auto; padding: 15px 10px; }
.sidebar-item {
  display: flex; align-items: center;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: all 0.2s;
  color: #94a3b8;
}
.sidebar-item:hover { background: rgba(255,255,255,0.05); color: #fff; }
.sidebar-item.active { background: rgba(100, 255, 218, 0.1); color: var(--primary-accent-color); }

.item-icon { margin-right: 12px; font-size: 18px; }
.item-info { display: flex; flex-direction: column; overflow: hidden; }
.item-name { font-size: 13px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.item-domain { font-size: 11px; opacity: 0.6; margin-top: 2px; }

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  min-width: 0;
}

.chat-header {
  height: 70px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex; justify-content: space-between; align-items: center;
  padding: 0 30px;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(10px);
}
.header-left { display: flex; align-items: center; gap: 15px; }
.mobile-back-btn { display: none; }
.header-edit-btn { margin-left: 10px; color: #94a3b8; }
.header-edit-btn:hover { color: var(--primary-accent-color); }
.expert-avatar-small { font-size: 24px; width: 40px; height: 40px; background: rgba(255,255,255,0.05); border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.header-info { display: flex; flex-direction: column; }
.expert-name-header { font-weight: bold; font-size: 16px; }
.expert-title-header { font-size: 12px; color: #94a3b8; }

.chat-body { flex: 1; overflow-y: auto; padding: 30px; display: flex; flex-direction: column; }
.empty-state { margin: auto; text-align: center; opacity: 0.8; }
.big-icon { font-size: 80px; display: block; margin-bottom: 20px; animation: float 3s ease-in-out infinite; }
.sub-text { margin-top: 10px; color: #64ffda; }

.message-row { display: flex; margin-bottom: 24px; gap: 15px; max-width: 95%; margin-left: auto; margin-right: auto; width: 100%; }
.message-row.user { flex-direction: row-reverse; }
.msg-avatar { 
  width: 40px; height: 40px; flex-shrink: 0; 
  background: rgba(255,255,255,0.1); border-radius: 8px; 
  display: flex; align-items: center; justify-content: center; border: 1px solid rgba(255,255,255,0.1);
}
.user .msg-avatar { background: var(--primary-accent-color); color: #000; border: none; }
.msg-bubble {
  background: rgba(30, 41, 59, 1);
  padding: 16px 20px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.1);
  line-height: 1.6;
  flex: 1;
  max-width: 80%;
}
.user .msg-bubble {
  background: var(--primary-accent-color);
  color: #0f172a;
  border: none;
  border-top-right-radius: 2px;
  flex: 0 1 auto;
}
.assistant .msg-bubble { border-top-left-radius: 2px; }
.thinking { font-style: italic; opacity: 0.7; }
.token-usage { text-align: right; font-size: 10px; opacity: 0.5; margin-top: 5px; font-family: monospace; }

/* Streaming cursor */
.streaming { position: relative; }
.cursor-blink {
  display: inline;
  animation: blink 1s step-end infinite;
  color: var(--primary-accent-color);
  font-weight: bold;
}
@keyframes blink { 50% { opacity: 0; } }

.chat-input-area {
  padding: 24px;
  background: rgba(15, 23, 42, 0.95);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  gap: 15px;
  max-width: 95%;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}
.chat-input-area :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  color: #fff;
  border-radius: 8px;
}
.chat-input-area :deep(.el-textarea__inner:focus) { border-color: var(--primary-accent-color); }

/* --- Transitions --- */
.zoom-fade-enter-active, .zoom-fade-leave-active { transition: all 0.4s cubic-bezier(0.25, 1, 0.5, 1); }
.zoom-fade-enter-from, .zoom-fade-leave-to { opacity: 0; transform: scale(0.95); }
@keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }

/* Dialog Customization */
.dialog-tip { margin-bottom: 20px; color: #94a3b8; line-height: 1.5; }
:deep(.el-dialog) { background: #1e293b; border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; }
:deep(.el-dialog__title) { color: #fff; font-weight: bold; }
:deep(.el-dialog__body) { padding-top: 10px; }
:deep(.el-form-item__label) { color: #94a3b8; }
:deep(.el-input) { --el-input-bg-color: rgba(255,255,255,0.05); --el-input-text-color: #fff; --el-input-border-color: rgba(255,255,255,0.1); }
:deep(.el-textarea__inner) { background-color: rgba(15, 23, 42, 0.8) !important; color: #e2e8f0; font-family: monospace; border-color: rgba(255,255,255,0.1); }

/* Markdown Styles */
:deep(.markdown-body) { font-size: 15px; }
:deep(.markdown-body h3) { margin-top: 0; color: #fff; border-bottom: none; }
:deep(.markdown-body code) { background: rgba(0,0,0,0.2); padding: 2px 4px; border-radius: 4px; font-family: monospace; }
:deep(.markdown-body pre) { background: #011627; padding: 12px; border-radius: 8px; margin: 0; overflow: visible; }
:deep(.markdown-body pre code) { display: block; overflow-x: auto; }
:deep(.markdown-body p) { margin-bottom: 8px; }

/* Code Block with Copy Button */
:deep(.code-block-wrapper) {
  position: relative;
  overflow: visible;
}
:deep(.code-block-wrapper pre) {
  padding-top: 12px;
  padding-right: 70px;
  position: relative;
}
:deep(.code-copy-btn) {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 4px 10px;
  font-size: 12px;
  background: rgba(100, 255, 218, 0.15);
  border: 1px solid rgba(100, 255, 218, 0.3);
  border-radius: 4px;
  color: #64ffda;
  cursor: pointer;
  transition: all 0.2s;
  z-index: 10;
}
:deep(.code-copy-btn:hover) {
  background: rgba(100, 255, 218, 0.3);
}

/* Message Actions */
.msg-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid rgba(255,255,255,0.05);
}
.copy-msg-btn {
  color: #64748b;
  font-size: 12px;
}
.copy-msg-btn:hover {
  color: #64ffda;
}
.user .msg-actions { border-top-color: rgba(0,0,0,0.1); }
.user .copy-msg-btn { color: rgba(0,0,0,0.5); }
.user .copy-msg-btn:hover { color: #000; }
</style>

<!-- Global styles for v-html content (code copy button) -->
<style>
.code-block-wrapper {
  position: relative;
  margin: 8px 0;
}
.code-copy-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 4px 12px;
  font-size: 12px;
  background: rgba(100, 255, 218, 0.2);
  border: 1px solid rgba(100, 255, 218, 0.4);
  border-radius: 4px;
  color: #64ffda;
  cursor: pointer;
  transition: all 0.2s;
  z-index: 100;
}
.code-copy-btn:hover {
  background: rgba(100, 255, 218, 0.4);
}
</style>
