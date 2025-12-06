// src/api/modules/system.ts
import request from '@/utils/request'
import type { MenuItem, ApiCard, TodoItem } from '@/types/api'

// === 1. 菜单相关接口 ===
export const getMenusApi = () => {
    return request.get<any, MenuItem[]>('/api/v1/menus/')
}

export const syncMenusApi = (menus: MenuItem[]) => {
    return request.post('/api/v1/menus/sync', menus)
}

// === 2. API卡片相关接口 ===
export const getCardsApi = () => {
    return request.get<any, ApiCard[]>('/api/v1/cards/')
}

export const syncCardsApi = (cards: ApiCard[]) => {
    return request.post('/api/v1/cards/sync', cards)
}

// === 3. 待办事项相关接口 ===
// 后端返回的是一个大对象: { "2023-11-01": { todos: [], notes: [] } }
export const getAllTodosApi = () => {
    return request.get<any, Record<string, { todos: TodoItem[], notes: TodoItem[] }>>('/api/v1/todos/all')
}

// 同步某一天的待办
export const syncDailyTodosApi = (date: string, data: { todos: TodoItem[], notes: TodoItem[] }) => {
    return request.post(`/api/v1/todos/sync/${date}`, data)
}

// === 4. 系统数据库管理接口 ===
export const getDbPathApi = () => {
    return request.get<any, { path: string }>('/api/v1/system/db-path')
}

export const moveDbApi = (path: string) => {
    return request.post('/api/v1/system/move-db', { path })
}

// === 5. [新增] 系统设置接口 (API Key 配置) ===

export interface SystemSettings {
    openai_api_key: string
    openai_base_url: string
}

// 获取当前配置
export const getSettingsApi = () => {
    return request.get<any, SystemSettings>('/api/v1/system/settings')
}

// 保存配置
export const saveSettingsApi = (data: SystemSettings) => {
    return request.post('/api/v1/system/settings', data)
}

// === 6. [新增] 天气接口 ===
export const getTodayWeatherApi = () => {
    return request.get<any, {
        source: string,
        weather_code: number,
        temp_min: number,
        temp_max: number,
        city: string
    }>('/api/v1/weather/today')
}