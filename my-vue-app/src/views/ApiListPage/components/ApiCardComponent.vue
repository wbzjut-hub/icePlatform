<template>
  <el-card class="box-card" shadow="never">
    <template #header>
      <div class="card-header">
        <div class="header-left">
          <el-tag
            :type="methodColor"
            effect="dark"
            size="small"
            class="method-tag"
          >
            {{ card.method }}
          </el-tag>
          <span class="card-title" :title="card.name">{{ card.name }}</span>
        </div>
        <div class="header-actions">
          <el-button class="action-btn" type="primary" :icon="Edit" circle size="small" plain @click="$emit('edit', card)" />
          <el-button class="action-btn" type="danger" :icon="Delete" circle size="small" plain @click="$emit('delete', card.id)" />
        </div>
      </div>
    </template>
    <div class="card-content">
      <div class="url-row">
        <span class="label">URL:</span>
        <code class="url-text" :title="card.url">{{ card.url }}</code>
      </div>
      
      <div class="content-body">
        <div class="response-area">
          <div class="response-header">
            <span class="label">响应预览:</span>
            <el-button
                :loading="state?.loading"
                type="primary"
                link
                size="small"
                @click="$emit('fetch', card)"
            >
              {{ state?.loading ? '请求中...' : '发送测试' }}
            </el-button>
          </div>
          <div class="response-code-wrapper">
             <pre v-if="state?.response" class="response-text">{{ state.response }}</pre>
             <pre v-else-if="state?.error" class="error-text">{{ state.error }}</pre>
             <span v-else class="no-response">点击“发送测试”查看结果</span>
          </div>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Delete, Edit } from '@element-plus/icons-vue'
import type { ApiCard } from '@/types/api'
import type { CardState } from '@/hooks/useApiCards'

const props = defineProps<{
  card: ApiCard,
  state?: CardState
}>()

defineEmits<{
  (e: 'edit', card: ApiCard): void
  (e: 'delete', id: string): void
  (e: 'fetch', card: ApiCard): void
}>()

const methodColor = computed(() => {
  switch (props.card.method) {
    case 'GET': return 'success'
    case 'POST': return 'warning'
    case 'DELETE': return 'danger'
    case 'PUT': return 'primary'
    default: return 'info'
  }
})
</script>

<style scoped>
.box-card {
  height: 100%;
  background-color: var(--bg-color-panel);
  border: 1px solid var(--border-color-tech);
  box-shadow: none;
  display: flex;
  flex-direction: column;
  transition: all 0.2s ease;
}
.box-card:hover {
  border-color: var(--primary-accent-color);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

:deep(.el-card__header) {
  padding: 12px 15px;
  border-bottom: 1px solid var(--border-color-tech);
  background-color: rgba(255, 255, 255, 0.02);
}

:deep(.el-card__body) {
  padding: 15px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  overflow: hidden;
}
.method-tag { font-weight: bold; border: none; }
.card-title {
  font-weight: 600;
  color: var(--text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 14px;
}
.header-actions {
  display: flex;
  gap: 5px;
  flex-shrink: 0;
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.url-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}
.label { color: var(--text-color-secondary); font-size: 12px; flex-shrink: 0; }
.url-text {
  background-color: rgba(0,0,0,0.2);
  padding: 2px 6px;
  border-radius: 4px;
  color: var(--primary-accent-color);
  font-family: 'JetBrains Mono', monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.content-body { flex: 1; display: flex; flex-direction: column; }

.response-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-top: 5px;
}
.response-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}
.response-code-wrapper {
  background-color: #0d1b2e;
  border: 1px solid var(--border-color-tech);
  border-radius: 6px;
  padding: 10px;
  height: 120px;
  overflow-y: auto;
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
}
.response-code-wrapper::-webkit-scrollbar { width: 4px; }
.response-code-wrapper::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }

.response-text { color: #a5d6ff; margin: 0; }
.error-text { color: #ff7b72; margin: 0; }
.no-response { color: rgba(255,255,255,0.2); font-style: italic; display: block; text-align: center; margin-top: 40px; }
</style>