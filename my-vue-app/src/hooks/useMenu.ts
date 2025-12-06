// src/hooks/useMenu.ts
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { MenuItem } from '@/types/api'
import { getMenusApi, syncMenusApi } from '@/api/modules/system'

// 默认核心菜单配置
const defaultMenuItems: MenuItem[] = [
    { id: 'menu_todo_list', name: '待办清单', path: '/todo-list', icon: 'Calendar' },
    { id: 'menu_ai_lab', name: 'AI 实验室', path: '/ai-lab', icon: 'Cpu' },
    { id: 'menu_api_list', name: 'API列表', path: '/api-list', icon: 'Memo' },
    { id: 'menu_agent_manager', name: '智能体中心', path: '/agent-manager', icon: 'Connection' }
]

export function useMenu() {
    const menuItems = ref<MenuItem[]>([])

    const loadMenus = async () => {
        try {
            // 从后端获取菜单数据
            const res = await getMenusApi()

            if (res && res.length > 0) {
                // --- 自动补全逻辑 Start ---
                // 检查当前数据库返回的菜单中，是否缺少了核心菜单（如 AI 实验室）
                const existingIds = res.map(item => item.id)
                const missingCoreItems = defaultMenuItems.filter(item => !existingIds.includes(item.id))

                if (missingCoreItems.length > 0) {
                    console.log('检测到旧数据缺失核心菜单，正在自动补全:', missingCoreItems)
                    // 合并：保留用户自定义的菜单，并追加缺失的核心菜单
                    const mergedMenus = [...res, ...missingCoreItems]
                    menuItems.value = mergedMenus

                    // 立即触发一次同步，将补全后的状态写入数据库
                    await syncMenusApi(mergedMenus)
                    ElMessage.success('系统已自动更新菜单结构')
                } else {
                    // 数据完整，但为了确保顺序（用户可能调整过代码），强制按默认配置重排核心菜单
                    const sorted = res.sort((a, b) => {
                        const indexA = defaultMenuItems.findIndex(d => d.id === a.id)
                        const indexB = defaultMenuItems.findIndex(d => d.id === b.id)

                        // 两个都是核心菜单：按 defaultMenuItems 顺序
                        if (indexA !== -1 && indexB !== -1) return indexA - indexB
                        // A是核心，B是自定义：A排前面
                        if (indexA !== -1) return -1
                        // B是核心，A是自定义：B排前面
                        if (indexB !== -1) return 1

                        return 0
                    })
                    menuItems.value = sorted

                    // 如果顺序有变化（与数据库不一致），同步一次
                    if (JSON.stringify(sorted) !== JSON.stringify(res)) {
                        syncMenusApi(sorted)
                    }
                }
                // --- 自动补全逻辑 End ---
            } else {
                // 数据库为空（首次运行），使用默认全量菜单
                menuItems.value = defaultMenuItems
                await syncMenusApi(defaultMenuItems)
            }
        } catch (e) {
            console.error('加载菜单失败: ', e)
            throw e // Re-throw to trigger retry logic
        }
    }

    // Retry logic wrapper
    const loadMenusWithRetry = async (retries = 5, delay = 1000) => {
        try {
            await loadMenus()
        } catch (e: any) {
            // Check if it's a connection error (common during startup)
            if (retries > 0 && String(e).includes('Network Error')) {
                // console.log(`Backend not ready, retrying in ${delay}ms... (${retries} left)`)
                setTimeout(() => loadMenusWithRetry(retries - 1, delay), delay)
            } else {
                console.error('Final Menu Load Failed:', e)
                // Fallback to default if all retries fail
                if (menuItems.value.length === 0) {
                    menuItems.value = defaultMenuItems
                }
            }
        }
    }

    // 组件挂载时加载
    onMounted(() => loadMenusWithRetry())

    // 监听菜单数据变化，自动同步到后端数据库
    watch(menuItems, async (newMenu) => {
        if (newMenu.length > 0) {
            await syncMenusApi(newMenu).catch(err => console.error('同步菜单失败', err))
        }
    }, { deep: true })

    /**
     * 新增页面菜单
     */
    const addMenuItem = (name: string) => {
        // 生成简单的路径，将空格替换为横杠
        const pathName = name.toLowerCase().replace(/\s+/g, '-')
        const newMenuItem: MenuItem = {
            id: `menu_${Date.now()}`,
            name,
            path: `/${pathName}`,
            icon: 'Document'
        }
        menuItems.value.push(newMenuItem)
        return newMenuItem
    }

    /**
     * 删除页面菜单
     * @returns Promise<string | null | undefined> 返回需要重定向的路径
     */
    const deleteMenuItem = (id: string, currentPath: string) => {
        const item = menuItems.value.find(i => i.id === id)
        if (!item) return Promise.resolve(null)

        // 核心菜单不允许删除
        const coreIds = defaultMenuItems.map(i => i.id)
        if (coreIds.includes(id)) {
            ElMessage.warning('核心系统页面无法删除')
            return Promise.resolve(null)
        }

        return ElMessageBox.confirm(`确定要删除页面 "${item.name}" 吗？`, '删除确认', {
            confirmButtonText: '删除',
            cancelButtonText: '取消',
            type: 'warning'
        }).then(() => {
            const path = item.path
            // 从列表中移除
            menuItems.value = menuItems.value.filter(i => i.id !== id)

            ElMessage.success('页面已删除')

            // 如果当前正在浏览该页面，则返回默认页路径以便跳转
            return currentPath === path ? defaultMenuItems[0]!.path : undefined
        }).catch(() => null)
    }

    return { menuItems, addMenuItem, deleteMenuItem }
}