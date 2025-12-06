// src/api/modules/common.ts

import request from '@/utils/request'
import type { ApiCard } from '@/types/api'

/**
 * 通用的API请求函数，现在直接接收整个ApiCard对象
 * @param card API卡片配置对象
 * @returns Promise<any> 返回后端响应的 data 部分
 */
export function fetchApi(card: ApiCard): Promise<any> {
    // 准备请求配置
    const config: { method: ApiCard['method']; url: string; params?: Record<string, any>; data?: any } = {
        method: card.method,
        url: card.url
    }

    // 1. 处理 GET 请求的 Params
    if (card.method === 'GET' && card.params && card.params.length > 0) {
        config.params = card.params
            .filter(p => p.enabled && p.key) // 只处理已启用且 key 不为空的
            .reduce((acc, p) => {
                acc[p.key] = p.value
                return acc
            }, {} as Record<string, any>)
    }

    // 2. 处理 POST/PUT 请求的 Body
    if ((card.method === 'POST' || card.method === 'PUT') && card.body) {
        try {
            // 尝试将 body 字符串解析为 JSON 对象
            config.data = JSON.parse(card.body)
        } catch (e) {
            // 如果解析失败，说明用户输入的不是合法的JSON
            return Promise.reject(new Error('请求体不是一个合法的JSON格式'))
        }
    }

    // 使用 axios 的通用请求方法
    return request(config)
}