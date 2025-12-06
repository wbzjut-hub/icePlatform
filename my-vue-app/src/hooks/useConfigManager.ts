// src/hooks/useConfigManager.ts

import { ElMessage } from 'element-plus'

// 定义统一的配置文件结构
interface AppConfig {
    version: string;
    menuItems: any[];
    apiCards: any[];
}

const MENU_STORAGE_KEY = 'ice_platform_menu_items'
const CARDS_STORAGE_KEY = 'dynamic_api_cards_v2'

export function useConfigManager() {

    /**
     * 导出配置到 JSON 文件
     */
    const exportConfig = () => {
        try {
            const menuItems = JSON.parse(localStorage.getItem(MENU_STORAGE_KEY) || '[]')
            const apiCards = JSON.parse(localStorage.getItem(CARDS_STORAGE_KEY) || '[]')

            const config: AppConfig = {
                version: '1.0.0', // 版本号，用于未来可能的迁移
                menuItems,
                apiCards
            }

            const jsonString = JSON.stringify(config, null, 2)
            const blob = new Blob([jsonString], { type: 'application/json' })
            const url = URL.createObjectURL(blob)

            const a = document.createElement('a')
            a.href = url
            a.download = `ice-platform-config-${new Date().toISOString().split('T')[0]}.json`
            document.body.appendChild(a)
            a.click()
            document.body.removeChild(a)
            URL.revokeObjectURL(url)

            ElMessage.success('配置已成功导出！')

        } catch (error) {
            console.error('导出配置失败:', error)
            ElMessage.error('导出配置失败，请查看控制台。')
        }
    }

    /**
     * 从 JSON 文件导入配置
     */
    const importConfig = () => {
        const input = document.createElement('input')
        input.type = 'file'
        input.accept = '.json'

        input.onchange = (event) => {
            const file = (event.target as HTMLInputElement).files?.[0]
            if (!file) return

            const reader = new FileReader()
            reader.onload = (e) => {
                try {
                    const content = e.target?.result as string
                    const config: AppConfig = JSON.parse(content)

                    // 验证文件基本结构
                    if (config.version && config.menuItems && config.apiCards) {
                        localStorage.setItem(MENU_STORAGE_KEY, JSON.stringify(config.menuItems))
                        localStorage.setItem(CARDS_STORAGE_KEY, JSON.stringify(config.apiCards))

                        ElMessage.success({
                            message: '配置导入成功！页面即将刷新以应用新配置。',
                            duration: 3000,
                            onClose: () => {
                                window.location.reload()
                            }
                        })
                    } else {
                        throw new Error('无效的配置文件格式。')
                    }
                } catch (error: any) {
                    console.error('导入配置失败:', error)
                    ElMessage.error(`导入失败: ${error.message}`)
                }
            }
            reader.readAsText(file)
        }
        input.click()
    }

    return {
        exportConfig,
        importConfig
    }
}