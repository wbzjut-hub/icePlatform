// src/store/modules/userStore.ts

import { defineStore } from 'pinia'
import type { UserInfo } from '@/types/api.d.ts'
import { loginApi } from '@/api/modules/auth'
import type { LoginParams } from '@/types/api'

/**
 * 用户状态管理 Store
 */
export const useUserStore = defineStore('user', {
    /**
     * State: 状态存储
     * - token: 从 localStorage 初始化，实现持久化登录
     * - userInfo: 存储当前用户信息
     */
    state: () => ({
        /** 用户认证令牌 */
        token: localStorage.getItem('token') as string | null,
        /** 用户信息 */
        userInfo: null as UserInfo | null
    }),

    /**
     * Getters: 计算属性
     * - isLoggedIn: 动态计算用户是否处于登录状态
     */
    getters: {
        /**
         * 检查用户是否已登录
         * @param state - 当前 state 对象
         * @returns {boolean} - 登录状态
         */
        isLoggedIn: (state): boolean => {
            // 检查 token 是否存在且不为空字符串
            return !!state.token && state.token.length > 0
        }
    },

    actions: {
        /**
         * 设置用户令牌并持久化
         * @param {string} newToken - 新的认证令牌
         */
        setToken(newToken: string) {
            this.token = newToken
            localStorage.setItem('token', newToken)
        },

        /**
         * 【新增】处理用户登录
         * @param {LoginParams} loginData - 登录表单数据
         * @returns {Promise<boolean>} - 返回一个 Promise，表示登录是否成功
         */
        async login(loginData: LoginParams): Promise<boolean> {
            try {
                const response = await loginApi(loginData)
                if (response && response.token) {
                    this.setToken(response.token)
                    return true
                }
                return false
            } catch (error) {
                console.error('Login failed:', error)
                return false
            }
        },

        /**
         * 用户登出
         * 清除 token 和用户信息，但不负责路由跳转。
         */
        logout() {
            this.token = null
            this.userInfo = null
            localStorage.removeItem('token')
        }
    }
})