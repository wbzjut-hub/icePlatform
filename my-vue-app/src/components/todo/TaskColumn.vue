<template>
  <div class="task-column">
    <div class="column-header">
      <h3>{{ title }}</h3>
      <el-input 
        v-model="newItemText" 
        :placeholder="placeholder" 
        @keyup.enter="handleAddItem" 
        size="small" 
      />
    </div>
    
    <draggable 
      :list="items" 
      item-key="id" 
      class="item-list" 
      handle=".drag-handle" 
      ghost-class="ghost"
      @change="$emit('update:list', items)"
    >
      <template #item="{ element: item }">
        <div class="task-item" :class="{ done: item.done }">
          <el-icon class="drag-handle"><Rank /></el-icon>
          <el-checkbox :model-value="item.done" @change="$emit('toggle', item.id)" />
          
          <span 
            v-if="editingId !== item.id" 
            @dblclick="startEditing(item)" 
            class="item-text"
          >{{ item.text }}</span>
          
          <el-input 
            v-else 
            :ref="(el: any) => setInputRef(el, item.id)" 
            v-model="editingText" 
            @blur="finishEditing(item)" 
            @keyup.enter="finishEditing(item)" 
            @keyup.esc="cancelEditing" 
            size="small" 
            class="edit-input" 
          />
          
          <el-button 
            type="danger" 
            :icon="Delete" 
            circle 
            plain 
            size="small" 
            @click="$emit('remove', item.id)" 
          />
        </div>
      </template>
    </draggable>
    
    <el-empty 
      v-if="!items || items.length === 0" 
      :description="emptyText" 
      :image-size="60" 
    />
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { Delete, Rank } from '@element-plus/icons-vue'
import draggable from 'vuedraggable'

interface TaskItem {
  id: string
  text: string
  done: boolean
}

const props = defineProps<{
  title: string
  placeholder: string
  emptyText: string
  items: TaskItem[]
}>()

const emit = defineEmits<{
  (e: 'add', text: string): void
  (e: 'remove', id: string): void
  (e: 'toggle', id: string): void
  (e: 'update', id: string, text: string): void
  (e: 'update:list', list: TaskItem[]): void
}>()

const newItemText = ref('')
const editingId = ref<string | null>(null)
const editingText = ref('')
const inputRefs = ref<Record<string, any>>({})

const setInputRef = (el: any, id: string) => { if (el) inputRefs.value[id] = el }

const handleAddItem = () => {
  if (newItemText.value.trim()) {
    emit('add', newItemText.value)
    newItemText.value = ''
  }
}

const startEditing = (item: TaskItem) => {
  editingId.value = item.id
  editingText.value = item.text
  nextTick(() => { inputRefs.value[item.id]?.focus() })
}

const finishEditing = (item: TaskItem) => {
  if (editingId.value === null) return
  if (editingText.value.trim() !== item.text) {
    emit('update', item.id, editingText.value)
  }
  cancelEditing()
}

const cancelEditing = () => {
  editingId.value = null
  editingText.value = ''
}
</script>

<style scoped>
.task-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-color-panel);
  border: 1px solid var(--border-color-tech);
  border-radius: 8px;
  padding: 15px;
  height: 100%;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  min-width: 0; /* Critical: Allow flex item to shrink below content size */
}

.column-header {
  margin-bottom: 15px;
}

.column-header h3 {
  margin: 0 0 10px;
  color: var(--primary-accent-color);
  font-family: 'JetBrains Mono', monospace;
  text-shadow: 0 0 5px rgba(100, 255, 218, 0.3);
}

.item-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 5px;
  min-height: 0;
}
/* Scrollbar specific for item list */
.item-list::-webkit-scrollbar { width: 4px; }
.item-list::-webkit-scrollbar-thumb { background: rgba(100,255,218,0.1); }

.task-item {
  display: flex;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  background-color: rgba(255, 255, 255, 0.02);
  border: 1px solid transparent;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.task-item:hover {
  background-color: rgba(100, 255, 218, 0.05);
  border-color: rgba(100, 255, 218, 0.2);
  transform: translateX(2px);
}

.item-text {
  flex-grow: 1;
  margin: 0 10px;
  color: var(--text-color-primary);
  cursor: pointer;
  font-size: 14px;
}

.drag-handle {
  cursor: grab;
  color: var(--text-color-secondary);
  margin-right: 8px;
  opacity: 0.5;
}
.task-item:hover .drag-handle { opacity: 1; }

.task-item.done .item-text {
  text-decoration: line-through;
  color: var(--text-color-secondary);
  opacity: 0.6;
}

.task-item.done :deep(.el-checkbox__inner) {
  background-color: var(--primary-accent-color);
  border-color: var(--primary-accent-color);
}
.task-item.done :deep(.el-checkbox__inner::after) {
  border-color: #0a192f;
}

.edit-input {
  flex-grow: 1;
  margin: 0 10px;
}

/* Deep customize Element Plus Input to match theme */
:deep(.el-input__wrapper) {
  background-color: rgba(0, 0, 0, 0.2);
  box-shadow: 0 0 0 1px var(--border-color-tech) inset;
}
:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--primary-accent-color) inset;
}
:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--primary-accent-color) inset !important;
}
:deep(.el-input__inner) {
  color: var(--text-color-primary);
}
</style>
