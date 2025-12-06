<template>
  <el-container class="app-layout-container" direction="horizontal">
    <AppSidebar
      :menu-items="menuItems"
      @add-page="promptAddPage"
      @delete-page="handleDeletePage"
    />

    <el-container direction="vertical">
      <AppHeader
        @open-settings="showSettings = true"
        @export-config="exportConfig"
        @import-config="importConfig"
        @change-db-path="handleChangeDbPath"
        @toggle-devtools="toggleDevTools"
        @logout="handleLogout"
      />

      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>

    <SettingsModal
      v-model:visible="showSettings"
    />
  </el-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store/modules/userStore'
import { useMenu } from '@/hooks/useMenu'
import { useConfigManager } from '@/hooks/useConfigManager'
import { ElMessageBox, ElMessage } from 'element-plus'
import type { MenuItem } from '@/types/api'
import { moveDbApi } from '@/api/modules/system'

// Components
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import SettingsModal from '@/components/common/SettingsModal.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const { menuItems, addMenuItem, deleteMenuItem } = useMenu()
const { exportConfig, importConfig } = useConfigManager()

// Settings Modal State
const showSettings = ref(false)

// Actions
const toggleDevTools = () => {
  if ((window as any).require) {
    try { (window as any).require('electron').ipcRenderer.send('toggle-devtools') } catch (e) { console.warn(e) }
  } else { ElMessage.warning('仅在桌面应用模式下可用') }
}

const handleChangeDbPath = async () => {
  if (!(window as any).require) { ElMessage.warning('此功能仅在桌面应用模式下可用'); return }
  try {
    const { ipcRenderer } = (window as any).require('electron')
    const newPath = await ipcRenderer.invoke('select-directory')
    if (newPath) {
      await ElMessageBox.confirm(`确定将数据库移动到: ${newPath} 吗？\n这需要重启应用。`, '确认移动', { confirmButtonText: '重启', cancelButtonText: '取消', type: 'warning' })
      await moveDbApi(newPath)
      setTimeout(() => { ipcRenderer.send('restart-app') }, 1500)
    }
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error('移动失败: ' + e.message)
  }
}

const handleLogout = () => {
  ElMessageBox.confirm('您确定要退出登录吗？', '提示', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
      .then(() => { userStore.logout(); router.push('/login'); ElMessage.success('已退出') })
      .catch(() => {})
}

const promptAddPage = () => {
  ElMessageBox.prompt('请输入新页面的名称', '新增页面', { confirmButtonText: '确定', cancelButtonText: '取消', inputPattern: /.+/, inputErrorMessage: '不能为空' })
      .then(({ value }) => {
        const newMenuItem = addMenuItem(value)
        if (newMenuItem) {
          router.addRoute('Layout', { path: newMenuItem.path, name: newMenuItem.name, component: () => import('@/views/GenericPage.vue'), meta: { name: newMenuItem.name } })
          router.push(newMenuItem.path)
        }
      }).catch(() => {})
}

const handleDeletePage = async (itemToDelete: MenuItem) => {
  const redirectPath = await deleteMenuItem(itemToDelete.id, route.path)
  if (redirectPath !== null) {
    if(router.hasRoute(itemToDelete.name)) router.removeRoute(itemToDelete.name)
    if (typeof redirectPath === 'string') await router.push(redirectPath)
  }
}
</script>

<style scoped>
.app-layout-container {
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: row; /* Explicitly enforce row for sidebar + main */
}

.app-main {
  background-color: transparent;
  padding: 0 !important;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.app-main > * {
  flex: 1;
  height: 100%;
}
</style>