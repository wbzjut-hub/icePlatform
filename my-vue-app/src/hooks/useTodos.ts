// src/hooks/useTodos.ts

import { ref, watch, computed } from 'vue'
import type { Ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { TodoItem } from '@/types/api'
import { getAllTodosApi, syncDailyTodosApi } from '@/api/modules/system'

// 扩展数据结构，包含 todos 和 notes
interface DailyData {
    todos: TodoItem[];
    notes: TodoItem[];
}

// 全局状态，存储所有日期的数据
const dailyData: Ref<Record<string, DailyData>> = ref({})

// 🌟 [修改 1] 定义一个可复用的刷新函数 (替代原来的 loadAllTodos)
// 作用：从后端拉取最新数据并更新全局状态
const fetchTodos = async () => {
    try {
        // console.log('正在刷新待办数据...')
        const res = await getAllTodosApi()
        if (res) {
            // 直接替换 dailyData 的值，Vue 的响应式系统会自动更新 UI
            dailyData.value = res
        }
    } catch (e) {
        console.error('加载待办事项失败', e)
        // 可以选择是否提示用户，这里静默失败以免打扰
    }
}

// 🌟 [修改 2] 初始化时立即执行一次
fetchTodos()

export function useTodos(date: Ref<string>) {

    /**
     * 核心函数：获取当前日期的数据对象
     * 如果不存在则初始化空对象
     */
    const getDailyData = (): DailyData => {
        const key = date.value
        if (!dailyData.value[key]) {
            dailyData.value[key] = { todos: [], notes: [] }
        }
        return dailyData.value[key]
    }

    // 内部函数：将当前日期的数据同步到后端
    const syncCurrentDate = async () => {
        const currentData = getDailyData()
        try {
            await syncDailyTodosApi(date.value, currentData)
        } catch (e) {
            console.error('同步待办数据失败', e)
            ElMessage.error('数据同步失败，请检查网络')
        }
    }

    // --- 待办 (Todos) ---

    const dailyTodos = computed({
        get: () => {
            return getDailyData().todos
        },
        set: (newVal) => {
            const data = getDailyData()
            data.todos = newVal
        }
    })

    const addTodo = async (text: string) => {
        if (!text.trim()) { ElMessage.warning('内容不能为空'); return }

        const data = getDailyData()
        data.todos.push({ id: `todo_${Date.now()}`, text: text.trim(), done: false })

        await syncCurrentDate()
    }

    const removeTodo = async (id: string) => {
        const data = getDailyData()
        data.todos = data.todos.filter(t => t.id !== id)

        await syncCurrentDate()
    }

    const toggleTodo = async (id: string) => {
        const data = getDailyData()
        const todo = data.todos.find(t => t.id === id)
        if (todo) {
            todo.done = !todo.done
            await syncCurrentDate()
        }
    }

    const updateTodo = async (id: string, newText: string) => {
        const data = getDailyData()

        if (!newText.trim()) {
            ElMessage.warning('内容不能为空, 该条目已删除')
            await removeTodo(id)
            return
        }

        const todo = data.todos.find(t => t.id === id)
        if (todo) {
            todo.text = newText.trim()
            await syncCurrentDate()
        }
    }

    // --- 笔记 (Notes) ---

    const dailyNotes = computed({
        get: () => {
            return getDailyData().notes
        },
        set: (newVal) => {
            const data = getDailyData()
            data.notes = newVal
        }
    })

    const addNote = async (text: string) => {
        if (!text.trim()) { ElMessage.warning('内容不能为空'); return }

        const data = getDailyData()
        data.notes.push({ id: `note_${Date.now()}`, text: text.trim(), done: false })

        await syncCurrentDate()
    }

    const removeNote = async (id: string) => {
        const data = getDailyData()
        data.notes = data.notes.filter(n => n.id !== id)

        await syncCurrentDate()
    }

    const updateNote = async (id: string, newText: string) => {
        const data = getDailyData()

        if (!newText.trim()) {
            ElMessage.warning('内容不能为空, 该条目已删除')
            await removeNote(id)
            return
        }

        const note = data.notes.find(n => n.id === id)
        if (note) {
            note.text = newText.trim()
            await syncCurrentDate()
        }
    }

    const toggleNote = async (id: string) => {
        const data = getDailyData()
        const note = data.notes.find(n => n.id === id)
        if (note) {
            note.done = !note.done
            await syncCurrentDate()
        }
    }

    // 🌟 [修改 3] 将 fetchTodos 导出，供组件调用
    return {
        dailyTodos, addTodo, removeTodo, toggleTodo, updateTodo,
        dailyNotes, addNote, removeNote, updateNote, toggleNote,
        fetchTodos // <--- 新增导出
    }
}