// src/hooks/useApiCards.ts

import { ref, reactive, onMounted, watch } from 'vue'
import type { Ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { ApiCard } from '@/types/api'
import { fetchApi } from '@/api/modules/common'
import { getCardsApi, syncCardsApi } from '@/api/modules/system'

// 定义卡片独立状态的类型
export interface CardState {
    loading: boolean;
    response: any;
    error: string | null;
}

// 完整的默认卡片数据
// ！！！核心修改：使用完整的 HTTPS URL，绕过 baseURL 指向的本地后端！！！
const defaultApiCards: ApiCard[] = [
    {
        id: 'card_default_get',
        name: 'GET - 获取所有帖子',
        url: 'https://jsonplaceholder.typicode.com/posts', // 修改这里
        method: 'GET',
        params: [{ key: 'userId', value: '1', enabled: true }],
        body: ''
    },
    {
        id: 'card_default_post',
        name: 'POST - 创建一个新帖子',
        url: 'https://jsonplaceholder.typicode.com/posts', // 修改这里
        method: 'POST',
        params: [],
        body: JSON.stringify({
            title: 'My Awesome Title',
            body: 'This is the content of the new post.',
            userId: 1
        }, null, 2)
    },
    {
        id: 'card_default_put',
        name: 'PUT - 更新ID为1的帖子',
        url: 'https://jsonplaceholder.typicode.com/posts/1', // 修改这里
        method: 'PUT',
        params: [],
        body: JSON.stringify({
            id: 1,
            title: 'Updated Title',
            body: 'This content has been updated.',
            userId: 1
        }, null, 2)
    },
    {
        id: 'card_default_delete',
        name: 'DELETE - 删除ID为1的帖子',
        url: 'https://jsonplaceholder.typicode.com/posts/1', // 修改这里
        method: 'DELETE',
        params: [],
        body: ''
    }
]

export function useApiCards() {
    const apiCards: Ref<ApiCard[]> = ref([])
    const cardStates = reactive<Record<string, CardState>>({})

    // 加载数据
    const loadCards = async () => {
        try {
            const res = await getCardsApi()
            if (res && res.length > 0) {
                apiCards.value = res
            } else {
                // 第一次使用，加载默认卡片并初始化后端数据库
                apiCards.value = defaultApiCards
                // 注意：这里不需要手动 sync，因为赋值给 apiCards.value 后，
                // 下面的 watch 会自动触发 syncCardsApi
            }
        } catch (e) {
            console.error('加载卡片失败，使用空列表或默认列表', e)
            apiCards.value = defaultApiCards
        }
    }

    onMounted(() => {
        loadCards()
    })

    // 监听变化并同步到后端
    watch(apiCards, async (newCards) => {
        // 初始化状态
        newCards.forEach(card => {
            if (!cardStates[card.id]) {
                cardStates[card.id] = { loading: false, response: null, error: null }
            }
        })

        // 发送数据给后端保存
        try {
            await syncCardsApi(newCards)
        } catch (e) {
            console.error('同步卡片失败', e)
        }
    }, { deep: true })

    // --- 卡片操作方法 ---

    const addCard = (newCardData: Omit<ApiCard, 'id'>) => {
        const newCard: ApiCard = { id: `card_${Date.now()}`, ...newCardData }
        apiCards.value.push(newCard)
        ElMessage.success('新增成功！')
    }

    const updateCard = (updatedCard: ApiCard) => {
        const index = apiCards.value.findIndex(c => c.id === updatedCard.id)
        if (index !== -1) {
            apiCards.value[index] = updatedCard
            ElMessage.success('更新成功！')
        }
    }

    const deleteCard = (id: string) => {
        ElMessageBox.confirm('确定要删除这张卡片吗？', '提示', {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
        }).then(() => {
            apiCards.value = apiCards.value.filter(card => card.id !== id)
            delete cardStates[id]
            ElMessage.success('删除成功！')
        }).catch(() => {})
    }

    const fetchCardApi = async (card: ApiCard) => {
        const state = cardStates[card.id]
        if (!state) return

        state.loading = true
        state.error = null
        state.response = null

        try {
            // 调用 common.ts 中的通用请求函数
            const responseData = await fetchApi(card)
            state.response = JSON.stringify(responseData, null, 2)
        } catch (error: any) {
            console.error("API请求失败详情:", error)
            state.error = error.message || '请求失败，请查看控制台获取详情'
        } finally {
            state.loading = false
        }
    }

    return {
        apiCards,
        cardStates,
        addCard,
        updateCard,
        deleteCard,
        fetchCardApi
    }
}