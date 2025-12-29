<template>
  <div class="sticky-notepad">
    <!-- Header with title and navigation -->
    <div class="notepad-header">
      <div class="title-with-help">
        <h3>📝 临时记录</h3>
        <el-popover
          placement="bottom-start"
          :width="260"
          trigger="hover"
        >
          <template #reference>
            <el-icon class="help-icon"><QuestionFilled /></el-icon>
          </template>
          <div class="shortcut-help">
            <h4>快捷键帮助</h4>
            <table>
              <tr><td>⌘/Ctrl + S</td><td>保存退出</td></tr>
              <tr><td>⌘/Ctrl + B</td><td>加粗</td></tr>
              <tr><td>⌘/Ctrl + I</td><td>斜体</td></tr>
              <tr><td>⌘/Ctrl + D</td><td>删除线</td></tr>
              <tr><td>⌘/Ctrl + 1/2/3</td><td>标题</td></tr>
              <tr><td>⌘/Ctrl + U</td><td>无序列表</td></tr>
              <tr><td>⌘/Ctrl + O</td><td>有序列表</td></tr>
              <tr><td>⌘/Ctrl + `</td><td>行内代码</td></tr>
              <tr><td>⌘/Ctrl + Q</td><td>引用</td></tr>
              <tr><td>Tab</td><td>缩进</td></tr>
              <tr><td>Shift + Tab</td><td>取消缩进</td></tr>
              <tr><td>Enter</td><td>列表续行</td></tr>
              <tr><td>Esc</td><td>取消编辑</td></tr>
            </table>
          </div>
        </el-popover>
      </div>
      <div class="nav-controls">
        <el-button 
          :icon="ArrowUp" 
          circle 
          size="small" 
          :disabled="!canGoUp"
          @click="goUp"
        />
        <span class="page-indicator">{{ items.length > 0 ? `${currentIndex + 1} / ${items.length}` : '0 / 0' }}</span>
        <el-button 
          :icon="ArrowDown" 
          circle 
          size="small" 
          :disabled="!canGoDown"
          @click="goDown"
        />
      </div>
    </div>

    <!-- Toolbar -->
    <div class="editor-toolbar" v-if="isEditing">
      <el-tooltip content="加粗 (⌘B)" placement="top">
        <el-button size="small" text @click="insertFormat('bold')">
          <strong>B</strong>
        </el-button>
      </el-tooltip>
      <el-tooltip content="斜体 (⌘I)" placement="top">
        <el-button size="small" text @click="insertFormat('italic')">
          <em>I</em>
        </el-button>
      </el-tooltip>
      <el-tooltip content="删除线 (⌘D)" placement="top">
        <el-button size="small" text @click="insertFormat('strikethrough')">
          <s>S</s>
        </el-button>
      </el-tooltip>
      <span class="toolbar-divider"></span>
      <el-tooltip content="标题1 (⌘1)" placement="top">
        <el-button size="small" text @click="insertFormat('h1')">H1</el-button>
      </el-tooltip>
      <el-tooltip content="标题2 (⌘2)" placement="top">
        <el-button size="small" text @click="insertFormat('h2')">H2</el-button>
      </el-tooltip>
      <el-tooltip content="标题3 (⌘3)" placement="top">
        <el-button size="small" text @click="insertFormat('h3')">H3</el-button>
      </el-tooltip>
      <span class="toolbar-divider"></span>
      <el-tooltip content="无序列表 (⌘U)" placement="top">
        <el-button size="small" text @click="insertFormat('ul')">• 列表</el-button>
      </el-tooltip>
      <el-tooltip content="有序列表 (⌘O)" placement="top">
        <el-button size="small" text @click="insertFormat('ol')">1. 列表</el-button>
      </el-tooltip>
      <el-tooltip content="代码 (⌘`)" placement="top">
        <el-button size="small" text @click="insertFormat('code')">&lt;/&gt;</el-button>
      </el-tooltip>
      <el-tooltip content="引用 (⌘Q)" placement="top">
        <el-button size="small" text @click="insertFormat('quote')">❝</el-button>
      </el-tooltip>
    </div>

    <!-- Note Content Area -->
    <div class="note-body">
      <!-- Live Editor with Split View -->
      <div v-if="isEditing" class="edit-mode">
        <div class="split-view">
          <textarea
            ref="textareaRef"
            v-model="editingText"
            class="note-textarea"
            placeholder="支持 Markdown 语法..."
            @keydown="handleKeydown"
          ></textarea>
          <div class="live-preview">
            <div class="markdown-content" v-html="liveRenderedMarkdown"></div>
          </div>
        </div>
        <div class="edit-hint">
          ⌘S 保存 | Esc 取消 | ⌘B 加粗 | ⌘I 斜体 | ⌘1-3 标题
        </div>
      </div>
      
      <!-- Preview Mode -->
      <div v-else-if="currentNote" class="preview-mode" @dblclick="enterEdit">
        <div class="markdown-content" v-html="renderedMarkdown"></div>
        <div class="edit-hint">双击编辑 | Enter 快速编辑</div>
      </div>
      
      <!-- Empty State -->
      <div v-else class="empty-state">
        <el-icon :size="48"><Document /></el-icon>
        <p>暂无记录</p>
        <p class="hint">点击右下角 + 添加</p>
      </div>
    </div>

    <!-- Footer Actions -->
    <div class="notepad-footer">
      <el-button 
        type="danger" 
        :icon="Delete" 
        circle 
        size="small" 
        :disabled="!currentNote"
        @click="handleDelete"
      />
      <el-button 
        type="primary" 
        :icon="Plus" 
        circle 
        size="small" 
        @click="handleAdd"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { ArrowUp, ArrowDown, Delete, Plus, Document, QuestionFilled } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

interface NoteItem {
  id: string
  text: string
  done: boolean
}

const props = defineProps<{
  items: NoteItem[]
}>()

const emit = defineEmits<{
  (e: 'add', text: string): void
  (e: 'remove', id: string): void
  (e: 'update', id: string, text: string): void
}>()

const currentIndex = ref(0)
const editingText = ref('')
const isEditing = ref(false)
const textareaRef = ref<HTMLTextAreaElement | null>(null)

// Current note based on index
const currentNote = computed(() => {
  if (props.items.length === 0) return null
  if (currentIndex.value >= props.items.length) {
    currentIndex.value = Math.max(0, props.items.length - 1)
  }
  return props.items[currentIndex.value]
})

// Navigation states
const canGoUp = computed(() => currentIndex.value > 0)
const canGoDown = computed(() => currentIndex.value < props.items.length - 1)

// Render Markdown for preview
const renderedMarkdown = computed(() => {
  if (!currentNote.value) return ''
  const html = marked.parse(currentNote.value.text || '', { breaks: true })
  return DOMPurify.sanitize(html as string)
})

// Live render for editing
const liveRenderedMarkdown = computed(() => {
  if (!editingText.value) return '<p style="opacity:0.5">实时预览...</p>'
  const html = marked.parse(editingText.value, { breaks: true })
  return DOMPurify.sanitize(html as string)
})

// Sync editingText when currentNote changes
watch(currentNote, (note) => {
  editingText.value = note?.text || ''
}, { immediate: true })

// Navigation functions
const goUp = () => {
  if (canGoUp.value) {
    saveIfEditing()
    currentIndex.value--
  }
}

const goDown = () => {
  if (canGoDown.value) {
    saveIfEditing()
    currentIndex.value++
  }
}

// Edit mode functions
const enterEdit = () => {
  if (!currentNote.value) return
  editingText.value = currentNote.value.text
  isEditing.value = true
  nextTick(() => {
    textareaRef.value?.focus()
  })
}

const saveAndExitEdit = () => {
  if (currentNote.value && editingText.value.trim() !== currentNote.value.text) {
    emit('update', currentNote.value.id, editingText.value.trim())
  }
  isEditing.value = false
}

const cancelEdit = () => {
  editingText.value = currentNote.value?.text || ''
  isEditing.value = false
}

const saveIfEditing = () => {
  if (isEditing.value) {
    saveAndExitEdit()
  }
}

// Keyboard shortcuts handler
const handleKeydown = (e: KeyboardEvent) => {
  const textarea = textareaRef.value
  if (!textarea) return

  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0
  const modKey = isMac ? e.metaKey : e.ctrlKey

  // Handle Escape
  if (e.key === 'Escape') {
    cancelEdit()
    return
  }

  // Handle Tab for indentation
  if (e.key === 'Tab') {
    e.preventDefault()
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const text = editingText.value
    
    // Find the start of current line
    const lineStart = text.lastIndexOf('\n', start - 1) + 1
    const lineEnd = text.indexOf('\n', start)
    const currentLine = text.substring(lineStart, lineEnd === -1 ? text.length : lineEnd)
    
    if (e.shiftKey) {
      // Shift+Tab: Remove indentation
      if (currentLine.startsWith('  ')) {
        editingText.value = text.substring(0, lineStart) + currentLine.substring(2) + text.substring(lineEnd === -1 ? text.length : lineEnd)
        nextTick(() => {
          textarea.setSelectionRange(Math.max(lineStart, start - 2), Math.max(lineStart, end - 2))
        })
      }
    } else {
      // Tab: Add indentation
      editingText.value = text.substring(0, lineStart) + '  ' + text.substring(lineStart)
      nextTick(() => {
        textarea.setSelectionRange(start + 2, end + 2)
      })
    }
    return
  }

  // Handle Enter for list auto-continue
  if (e.key === 'Enter' && !modKey) {
    const start = textarea.selectionStart
    const text = editingText.value
    
    // Find the current line
    const lineStart = text.lastIndexOf('\n', start - 1) + 1
    const currentLine = text.substring(lineStart, start)
    
    // Check for list patterns
    const unorderedMatch = currentLine.match(/^(\s*)([-*+])\s(.*)$/)
    const orderedMatch = currentLine.match(/^(\s*)(\d+)\.\s(.*)$/)
    
    if (unorderedMatch) {
      const [, indent, marker, content] = unorderedMatch
      if (!content || content.trim() === '') {
        // Empty list item - remove it and stop list
        e.preventDefault()
        editingText.value = text.substring(0, lineStart) + text.substring(start)
        nextTick(() => {
          textarea.setSelectionRange(lineStart, lineStart)
        })
      } else {
        // Continue unordered list
        e.preventDefault()
        const newLine = `\n${indent}${marker} `
        editingText.value = text.substring(0, start) + newLine + text.substring(start)
        nextTick(() => {
          const newPos = start + newLine.length
          textarea.setSelectionRange(newPos, newPos)
        })
      }
      return
    }
    
    if (orderedMatch) {
      const [, indent, num, content] = orderedMatch
      if (!content || content.trim() === '') {
        // Empty list item - remove it and stop list
        e.preventDefault()
        editingText.value = text.substring(0, lineStart) + text.substring(start)
        nextTick(() => {
          textarea.setSelectionRange(lineStart, lineStart)
        })
      } else {
        // Continue ordered list with next number
        e.preventDefault()
        const nextNum = parseInt(num || '1') + 1
        const newLine = `\n${indent}${nextNum}. `
        editingText.value = text.substring(0, start) + newLine + text.substring(start)
        nextTick(() => {
          const newPos = start + newLine.length
          textarea.setSelectionRange(newPos, newPos)
        })
      }
      return
    }
  }

  // Handle modifier key shortcuts
  if (modKey) {
    switch (e.key.toLowerCase()) {
      case 's':
        e.preventDefault()
        saveAndExitEdit()
        break
      case 'b':
        e.preventDefault()
        insertFormat('bold')
        break
      case 'i':
        e.preventDefault()
        insertFormat('italic')
        break
      case 'd':
        e.preventDefault()
        insertFormat('strikethrough')
        break
      case 'u':
        e.preventDefault()
        insertFormat('ul')
        break
      case 'o':
        e.preventDefault()
        insertFormat('ol')
        break
      case 'q':
        e.preventDefault()
        insertFormat('quote')
        break
      case '`':
        e.preventDefault()
        insertFormat('code')
        break
      case '1':
        e.preventDefault()
        insertFormat('h1')
        break
      case '2':
        e.preventDefault()
        insertFormat('h2')
        break
      case '3':
        e.preventDefault()
        insertFormat('h3')
        break
    }
  }
}

// Insert markdown format
const insertFormat = (format: string) => {
  const textarea = textareaRef.value
  if (!textarea) return

  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const text = editingText.value
  const selectedText = text.substring(start, end)

  let before = ''
  let after = ''
  let defaultText = ''

  switch (format) {
    case 'bold':
      before = '**'
      after = '**'
      break
    case 'italic':
      before = '*'
      after = '*'
      break
    case 'strikethrough':
      before = '~~'
      after = '~~'
      break
    case 'code':
      before = '`'
      after = '`'
      break
    case 'h1':
      before = '# '
      after = ''
      break
    case 'h2':
      before = '## '
      after = ''
      break
    case 'h3':
      before = '### '
      after = ''
      break
    case 'ul':
      before = '- '
      after = ''
      break
    case 'ol':
      before = '1. '
      after = ''
      break
    case 'quote':
      before = '> '
      after = ''
      break
  }

  // 只插入格式符号，选中的文字保留，没选中就只插入符号
  const newText = text.substring(0, start) + before + selectedText + after + text.substring(end)
  editingText.value = newText

  // 光标移到符号后面（如果没有选中文字，就在符号中间）
  nextTick(() => {
    const newCursorPos = start + before.length + selectedText.length
    textarea.focus()
    textarea.setSelectionRange(newCursorPos, newCursorPos)
  })
}

// Global keyboard listener for quick edit
const handleGlobalKeydown = (e: KeyboardEvent) => {
  if (!isEditing.value && currentNote.value && e.key === 'Enter' && !e.metaKey && !e.ctrlKey) {
    // Quick edit on Enter when not editing
    const target = e.target as HTMLElement
    if (target.tagName !== 'INPUT' && target.tagName !== 'TEXTAREA') {
      enterEdit()
    }
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})

// Add new note
const handleAdd = () => {
  emit('add', '新记录')
  nextTick(() => {
    currentIndex.value = props.items.length - 1
    setTimeout(() => {
      enterEdit()
      editingText.value = ''
    }, 100)
  })
}

// Delete current note
const handleDelete = async () => {
  if (!currentNote.value) return
  
  try {
    await ElMessageBox.confirm('确定删除这条记录？', '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const idToRemove = currentNote.value.id
    if (currentIndex.value >= props.items.length - 1) {
      currentIndex.value = Math.max(0, props.items.length - 2)
    }
    emit('remove', idToRemove)
  } catch {
    // Cancelled
  }
}
</script>

<style scoped>
.sticky-notepad {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.03) 100%);
  border: 1px solid var(--border-color-tech);
  border-radius: 8px;
  box-shadow: 
    0 4px 20px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  overflow: hidden;
}

.notepad-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  background: rgba(0, 0, 0, 0.2);
  border-bottom: 1px solid var(--border-color-tech);
}

.title-with-help {
  display: flex;
  align-items: center;
  gap: 8px;
}

.help-icon {
  color: var(--text-color-secondary);
  cursor: pointer;
  opacity: 0.6;
  transition: all 0.2s;
}

.help-icon:hover {
  opacity: 1;
  color: var(--primary-accent-color);
}

.shortcut-help {
  font-size: 12px;
}

.shortcut-help h4 {
  margin: 0 0 10px;
  color: var(--primary-accent-color);
  font-size: 13px;
}

.shortcut-help table {
  width: 100%;
  border-collapse: collapse;
}

.shortcut-help td {
  padding: 4px 0;
  color: var(--text-color-primary);
}

.shortcut-help td:first-child {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--primary-accent-color);
  padding-right: 15px;
  white-space: nowrap;
}

.notepad-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--primary-accent-color);
  font-family: 'JetBrains Mono', monospace;
  text-shadow: 0 0 8px rgba(100, 255, 218, 0.4);
}

.nav-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-indicator {
  font-size: 12px;
  color: var(--text-color-secondary);
  font-family: 'JetBrains Mono', monospace;
  min-width: 50px;
  text-align: center;
}

/* Toolbar */
.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 15px;
  background: rgba(0, 0, 0, 0.15);
  border-bottom: 1px solid var(--border-color-tech);
}

.editor-toolbar :deep(.el-button) {
  padding: 4px 8px;
  min-height: unset;
  color: var(--text-color-secondary);
}

.editor-toolbar :deep(.el-button:hover) {
  color: var(--primary-accent-color);
  background: rgba(100, 255, 218, 0.1);
}

.toolbar-divider {
  width: 1px;
  height: 16px;
  background: var(--border-color-tech);
  margin: 0 4px;
}

.note-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.edit-mode,
.preview-mode {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 15px;
  min-height: 0;
}

.preview-mode {
  background: #1a1a1a;
  border-radius: 6px;
  margin: 10px;
  padding: 15px;
  border: 3px solid #3a3a3a;
  box-shadow: inset 0 0 30px rgba(0, 0, 0, 0.5);
}

.split-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 0;
}

.note-textarea {
  flex: 1;
  min-height: 80px;
  width: 100%;
  border: 2px solid #3a3a3a;
  background: #1a1a1a;
  border-radius: 4px;
  padding: 12px;
  resize: none;
  font-family: 'Ma Shan Zheng', 'Zhi Mang Xing', 'Long Cang', 'Kalam', cursive;
  font-size: 16px;
  line-height: 1.8;
  color: #ffffff;
  text-shadow: 
    0 0 2px rgba(255, 255, 255, 0.4),
    1px 1px 0 rgba(255, 255, 255, 0.1);
  outline: none;
}

.note-textarea::placeholder {
  color: rgba(245, 245, 220, 0.4);
  font-style: italic;
}

.note-textarea:focus {
  box-shadow: 0 0 8px rgba(245, 245, 220, 0.3);
}

.live-preview {
  flex: 1;
  overflow-y: auto;
  background: #1a1a1a;
  border: 2px solid #3a3a3a;
  border-radius: 4px;
  padding: 12px;
  box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.4);
}

.markdown-content {
  flex: 1;
  overflow-y: auto;
  color: #ffffff;
  font-family: 'Ma Shan Zheng', 'Zhi Mang Xing', 'Long Cang', 'Kalam', cursive;
  font-size: 16px;
  line-height: 1.8;
  text-shadow: 
    0 0 2px rgba(255, 255, 255, 0.4),
    1px 1px 0 rgba(255, 255, 255, 0.1);
}

/* Markdown styles - Chalkboard */
.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3) {
  color: #ffeb99;
  margin: 0.5em 0;
  text-shadow: 0 0 3px rgba(255, 235, 153, 0.4);
}

.markdown-content :deep(h1) { font-size: 1.6em; }
.markdown-content :deep(h2) { font-size: 1.4em; }
.markdown-content :deep(h3) { font-size: 1.2em; }

.markdown-content :deep(p) {
  margin: 0.5em 0;
}

.markdown-content :deep(strong) {
  color: #ffeb99;
}

.markdown-content :deep(code) {
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  color: #98fb98;
}

.markdown-content :deep(pre) {
  background: rgba(0, 0, 0, 0.3);
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  border: 1px dashed rgba(255, 255, 255, 0.2);
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 25px;
  margin: 0.5em 0;
}

.markdown-content :deep(li) {
  margin: 0.3em 0;
}

.markdown-content :deep(blockquote) {
  border-left: 3px solid #ffeb99;
  padding-left: 12px;
  margin: 0.5em 0;
  color: rgba(245, 245, 220, 0.8);
  font-style: italic;
}

.markdown-content :deep(del) {
  color: rgba(245, 245, 220, 0.5);
}

.markdown-content :deep(pre) {
  background: rgba(0, 0, 0, 0.4);
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 20px;
  margin: 0.5em 0;
}

.markdown-content :deep(blockquote) {
  border-left: 3px solid var(--primary-accent-color);
  padding-left: 12px;
  margin: 0.5em 0;
  color: var(--text-color-secondary);
}

.markdown-content :deep(del) {
  color: var(--text-color-secondary);
}

.edit-hint {
  text-align: center;
  font-size: 11px;
  color: var(--text-color-secondary);
  opacity: 0.6;
  padding-top: 8px;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-color-secondary);
  text-align: center;
  opacity: 0.6;
}

.empty-state p {
  margin: 8px 0 0;
  font-size: 13px;
}

.empty-state .hint {
  font-size: 11px;
}

.notepad-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 10px 15px;
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid var(--border-color-tech);
}

/* Override Element Plus button colors for sci-fi theme */
.nav-controls :deep(.el-button) {
  background: rgba(100, 255, 218, 0.1);
  border-color: var(--border-color-tech);
  color: var(--text-color-secondary);
}

.nav-controls :deep(.el-button:hover:not(:disabled)) {
  background: rgba(100, 255, 218, 0.2);
  border-color: var(--primary-accent-color);
  color: var(--primary-accent-color);
}

.nav-controls :deep(.el-button:disabled) {
  opacity: 0.3;
}

.notepad-footer :deep(.el-button--primary) {
  --el-button-bg-color: var(--primary-accent-color);
  --el-button-border-color: var(--primary-accent-color);
  --el-button-text-color: #0a192f;
}
</style>
