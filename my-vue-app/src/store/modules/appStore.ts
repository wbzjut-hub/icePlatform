// src/store/modules/appStore.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
    // 记录晨报是否已生成
    const hasGeneratedBriefing = ref(false)

    // 标记为已生成
    const setBriefingGenerated = () => {
        hasGeneratedBriefing.value = true
    }

    // 重置状态 (如果需要手动刷新时用)
    const resetBriefingState = () => {
        hasGeneratedBriefing.value = false
    }

    return {
        hasGeneratedBriefing,
        setBriefingGenerated,
        resetBriefingState
    }
})