<!-- src/views/AgentManager/AgentManagerPage.vue -->
<template>
  <div class="agent-manager-container">
    <div class="page-header">
      <h2>🤖 智能体中心 (Agent Store)</h2>
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">
        创建智能体
      </el-button>
    </div>

    <p class="page-desc">
      在这里配置您的 AI 员工。通过设定不同的人设 (Prompt) 和赋予不同的工具 (Tools)，打造专属的工作流。
    </p>

    <!-- 卡片网格 -->
    <el-row :gutter="20">
      <el-col
          v-for="wf in workflows"
          :key="wf.id"
          :xs="24" :sm="12" :md="8" :lg="6"
          class="card-col"
      >
        <el-card class="agent-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="agent-name">{{ wf.name }}</span>
              <el-tag v-if="['wf_general', 'wf_agent'].includes(wf.id!)" size="small" type="warning">系统预置</el-tag>
              <el-button
                  v-else
                  type="danger"
                  :icon="Delete"
                  circle
                  plain
                  size="small"
                  @click="handleDelete(wf.id!)"
              />
            </div>
          </template>

          <div class="card-body">
            <p class="agent-desc">{{ wf.description || '暂无描述' }}</p>

            <div class="tools-area">
              <span class="label">能力:</span>
              <div v-if="wf.tools_config.length > 0" class="tags">
                <el-tag v-for="t in wf.tools_config" :key="t" size="small" effect="dark">{{ t }}</el-tag>
              </div>
              <span v-else class="no-tools">纯对话模式</span>
            </div>

            <div class="prompt-preview">
              <span class="label">人设预览:</span>
              <div class="prompt-text">{{ wf.system_prompt }}</div>
            </div>

            <div class="card-actions">
              <el-button type="primary" link size="small" :icon="View" @click="handleDetail(wf)">详情</el-button>
              <el-button 
                type="primary" 
                link 
                size="small" 
                :icon="Edit" 
                :disabled="['wf_general', 'wf_agent'].includes(wf.id!)"
                @click="handleEdit(wf)"
              >
                编辑
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 创建/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" title="配置智能体" width="600px" destroy-on-close>
      <el-form :model="form" label-width="100px" label-position="top">
        <el-form-item label="智能体名称" required>
          <el-input v-model="form.name" placeholder="例如：翻译官、代码审查员" />
        </el-form-item>

        <el-form-item label="功能描述">
          <el-input v-model="form.description" placeholder="简单描述它的用途" />
        </el-form-item>

        <el-form-item label="系统提示词 (System Prompt)" required>
          <el-input
              v-model="form.system_prompt"
              type="textarea"
              :rows="6"
              placeholder="你是谁？你的职责是什么？请详细描述..."
          />
          <div class="form-tip">支持使用 {current_time} 占位符注入当前时间。</div>
        </el-form-item>

        <el-form-item label="赋予能力 (Tools)">
          <el-checkbox-group v-model="form.tools_config">
            <el-checkbox label="add_todo" border>写待办 (add_todo)</el-checkbox>
            <el-checkbox label="query_todos" border>查日程 (query_todos)</el-checkbox>

            <!-- 🌟 新增这一行 -->
            <el-checkbox label="web_search" border>联网搜索 (web_search)</el-checkbox>

          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">保存配置</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { Plus, Delete, View, Edit } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getWorkflowsApi, createWorkflowApi, updateWorkflowApi, deleteWorkflowApi } from '@/api/modules/ai'
import type { Workflow } from '@/api/modules/ai'

const workflows = ref<Workflow[]>([])
const dialogVisible = ref(false)

// 表单数据，包含可选的 id
const form = reactive<Workflow>({
  id: undefined,
  name: '',
  description: '',
  system_prompt: '',
  tools_config: []
})

onMounted(loadData)

async function loadData() {
  try {
    const res = await getWorkflowsApi()
    workflows.value = res || []
  } catch (e) { console.error(e) }
}

function openCreateDialog() {
  // 重置表单 (必须清除 id)
  form.id = undefined
  form.name = ''
  form.description = ''
  form.system_prompt = '你是一个智能助手...'
  form.tools_config = []
  dialogVisible.value = true
}

async function handleSubmit() {
  if(!form.name || !form.system_prompt) {
    ElMessage.warning('名称和提示词不能为空')
    return
  }

  try {
    if (form.id) {
       // 更新模式
       await updateWorkflowApi(form.id, { ...form })
       ElMessage.success('智能体更新成功！')
    } else {
       // 创建模式
       await createWorkflowApi({ ...form })
       ElMessage.success('智能体创建成功！')
    }
    dialogVisible.value = false
    loadData() // 刷新列表
  } catch (e: any) {
    ElMessage.error('操作失败: ' + (e.response?.data?.detail || e.message))
  }
}

async function handleDelete(id: string) {
  try {
    await ElMessageBox.confirm('确定要销毁这个智能体吗？', '警告', { type: 'warning' })
    await deleteWorkflowApi(id)
    ElMessage.success('已销毁')
    loadData()
  } catch (e) {}
}

const handleDetail = (wf: Workflow) => {
  ElMessageBox.alert(
    `<div style="max-height: 400px; overflow-y: auto; white-space: pre-wrap;">${wf.system_prompt}</div>`,
    `智能体详情: ${wf.name}`,
    {
      dangerouslyUseHTMLString: true,
      customStyle: { maxWidth: '600px' }
    }
  )
}

const handleEdit = (wf: Workflow) => {
  // Populate form
  Object.assign(form, wf)
  // Logic for update vs create is needed here, checking if backend supports update by ID
  // For now, allow viewing/editing in dialog, but note that saving might create duplicate if backend doesn't handle UPSERT
  ElMessage.info('编辑模式：保存将尝试更新配置') 
  dialogVisible.value = true
}
</script>

<style scoped>
.agent-manager-container {
  padding: 30px;
  height: 100%;
  overflow-y: auto;
  background-color: var(--bg-color-deep-space);
  box-sizing: border-box;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  color: var(--primary-accent-color);
}
.page-desc {
  color: var(--text-color-secondary);
  margin-bottom: 30px;
  font-size: 14px;
}

.card-col { margin-bottom: 20px; }

.agent-card {
  height: 100%;
  background-color: var(--bg-color-panel);
  border: 1px solid var(--border-color-tech);
  color: var(--text-color-primary);
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.agent-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  border-color: rgba(100, 255, 218, 0.3);
}

:deep(.el-card__header) {
  border-bottom: 1px solid var(--border-color-tech);
  padding: 15px;
  background-color: rgba(255, 255, 255, 0.02);
}
:deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.agent-name {
  font-weight: bold;
  font-size: 16px;
  color: var(--primary-accent-color);
}

.agent-desc {
  color: var(--text-color-secondary);
  font-size: 13px;
  margin-bottom: 20px;
  height: 40px;
  line-height: 20px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.tools-area { margin-bottom: 15px; }
.label { font-size: 12px; color: var(--text-color-secondary); display: block; margin-bottom: 5px; opacity: 0.7; }
.tags { display: flex; gap: 5px; flex-wrap: wrap; }
.no-tools { font-size: 12px; color: #666; font-style: italic; }

.prompt-preview {
  flex: 1;
  background-color: #0d1b2e;
  padding: 10px;
  border-radius: 6px;
  font-size: 12px;
  color: var(--text-color-secondary);
  border: 1px solid var(--border-color-tech);
  margin-top: auto; /* Push to bottom */
}
.prompt-text {
  height: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  font-family: 'JetBrains Mono', monospace;
  opacity: 0.8;
}

.form-tip { font-size: 12px; color: var(--text-color-secondary); margin-top: 5px; }

.card-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 15px;
  padding-top: 10px;
  border-top: 1px dashed var(--border-color-tech);
  gap: 10px;
}
</style>