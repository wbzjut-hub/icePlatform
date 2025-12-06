// src/hooks/useTheme.ts

import { ref, onMounted } from 'vue'

export type ThemeName =
    'oceanic' | 'stardust' | 'meltdown' |
    'oceanic-light' | 'stardust-light' | 'meltdown-light';

const STORAGE_KEY = 'ice_platform_theme'
const currentTheme = ref<ThemeName>('oceanic')

export function useTheme() {
    const applyTheme = (themeName: ThemeName) => {
        // 1. 移除旧的主题标签
        document.querySelector('link[data-theme]')?.remove()

        // 2. 创建新的 link 标签
        const link = document.createElement('link')
        link.rel = 'stylesheet'

        // ！！！关键修改：使用 ./ 开头的相对路径！！！
        // 这告诉浏览器从当前 index.html 所在的目录开始寻找 themes 文件夹
        // 无论是在本地服务器还是打包后的应用中，这都是通用的
        link.href = `./themes/theme-${themeName}.css`

        link.dataset.theme = themeName
        document.head.appendChild(link)

        currentTheme.value = themeName
        localStorage.setItem(STORAGE_KEY, themeName)
    }

    onMounted(() => {
        const savedTheme = localStorage.getItem(STORAGE_KEY) as ThemeName | null
        // Always apply the theme on mount to ensure the <link> tag exists in the DOM.
        // Even if the state matches, the DOM might not have the CSS file loaded yet (e.g. on page refresh).
        applyTheme(savedTheme || 'oceanic')
    })

    return {
        currentTheme,
        applyTheme
    }
}