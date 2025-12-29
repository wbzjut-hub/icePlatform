<template>
  <el-dialog
    :model-value="visible"
    title="系统设置"
    width="500px"
    append-to-body
    @update:model-value="onUpdateVisible"
  >
    <el-form :model="form" label-width="120px">
      <el-alert
          title="配置将保存在本地数据库中"
          type="info"
          show-icon
          :closable="false"
          style="margin-bottom: 20px"
      />
      <el-form-item label="Base URL">
        <el-input v-model="form.openai_base_url" placeholder="例如: https://api.deepseek.com" />
        <div class="form-tip">支持 OpenAI 格式的接口地址 (DeepSeek/Moonshot等)</div>
      </el-form-item>
      <el-form-item label="API Key">
        <el-input
            v-model="form.openai_api_key"
            type="password"
            show-password
            placeholder="sk-..."
        />
      </el-form-item>
      <el-form-item label="Tavily Key">
        <el-input
            v-model="form.tavily_api_key"
            type="password"
            show-password
            placeholder="tvly-..."
        />
        <div class="form-tip">用于联网搜索功能的 API Key</div>
      </el-form-item>
      <el-form-item label="系统维护">
        <el-button type="warning" plain size="small" @click="handleClearCache">
          清除界面缓存并重启
        </el-button>
        <div class="form-tip">如果遇到界面显示异常或更新不生效，请尝试此操作。</div>
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="close">取消</el-button>
        <el-button type="primary" @click="save" :loading="saving">
          保存配置
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSettingsApi, saveSettingsApi } from '@/api/modules/system'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'saved'): void
}>()

const saving = ref(false)
const form = ref({
  openai_api_key: '',
  openai_base_url: '',
  tavily_api_key: ''
})

const onUpdateVisible = (val: boolean) => {
  emit('update:visible', val)
}

const close = () => {
  emit('update:visible', false)
}

const loadSettings = async () => {
  try {
    const res = await getSettingsApi()
    if (res) {
      form.value = res
      if (!form.value.openai_base_url) {
        form.value.openai_base_url = 'https://api.deepseek.com'
      }
    }
  } catch (e) {
    console.error('获取设置失败', e)
  }
}

const save = async () => {
  saving.value = true
  try {
    await saveSettingsApi(form.value)
    ElMessage.success('配置已保存，即刻生效')
    emit('saved')
    close()
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// Watch visibility to load data when opened
watch(() => props.visible, (newVal) => {
  if (newVal) {
    loadSettings()
  }
})

const handleClearCache = async () => {
  try {
    await ElMessageBox.confirm('是否确认清除所有缓存并重启？此操作将重置界面状态。', '警告', {
      type: 'warning',
      confirmButtonText: '确定清除',
      cancelButtonText: '取消'
    })
    
    // Clear localStorage
    localStorage.clear()
    
    // Clear sessionStorage
    sessionStorage.clear()

    ElMessage.success('缓存已清除，正在重启...')
    
    // Reload via Electron API if available, or window.location
    if ((window as any).require) {
      const { ipcRenderer } = (window as any).require('electron')
      ipcRenderer.send('restart-app')
    } else {
      window.location.reload()
    }
  } catch (e) {
    // Cancelled
  }
}
</script>

<style scoped>
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.2;
}
</style>
