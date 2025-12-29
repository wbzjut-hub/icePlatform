import axios from 'axios'
import type { AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/modules/userStore'

// --- 核心修改：动态 baseURL ---
// 开发环境 (npm run dev): 默认为 undefined 或 '/api' (取决于 .env)，走 Vite 代理转发
// 生产环境 (Electron 打包后): 必须显式指向本地 Python 后端地址，因为打包后没有 Vite 代理了
const isProduction = import.meta.env.PROD
// 在生产环境 (Electron) 中，必须显式加上 /api/v1 前缀，因为后端 router 定义了 prefix
// 在开发环境，如果 .env 没配，默认为 /api/v1 以匹配 vite proxy
const baseURL = isProduction
    ? 'http://127.0.0.1:8008/api/v1'
    : (import.meta.env.VITE_APP_BASE_API || '/api/v1')

// 创建 axios 实例
const service: AxiosInstance = axios.create({
    baseURL: baseURL,
    timeout: 60000 // 请求超时时间
})

// 请求拦截器
service.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        const userStore = useUserStore()
        if (userStore.token) {
            // 如果存在 token，则添加到请求头
            config.headers.Authorization = `Bearer ${userStore.token}`
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// 响应拦截器
service.interceptors.response.use(
    // onFulfilled - 处理成功的响应 (HTTP 状态码 2xx)
    (response: AxiosResponse) => {
        const res = response.data

        // --- 兼容性处理 ---
        // 检查响应体是否是我们约定的标准格式 { code, message, data }
        // 如果不是对象，或者没有 code 字段 (例如 JSONPlaceholder 返回的纯数组)，直接返回原始数据
        if (typeof res !== 'object' || res === null || res.code === undefined) {
            return res
        }

        // 是我们约定的标准格式，则根据 code 进行判断
        switch (res.code) {
            case 200:
                // 业务成功，返回核心数据
                return res.data
            case 40101:
                // Token 失效
                ElMessage.error('登录状态已过期，请重新登录')
                const userStore = useUserStore()
                userStore.logout()
                // 强制跳转回登录页
                window.location.href = '/login'
                return Promise.reject(new Error('Token Expired'))
            default:
                // 其他业务错误
                ElMessage.error(res.message || '请求失败')
                return Promise.reject(new Error(res.message || '请求失败'))
        }
    },
    // onRejected - 处理失败的响应 (HTTP 状态码非 2xx)
    (error) => {
        console.error('HTTP Request Error:', error) // 方便在 Electron 控制台调试

        // --- Auth Error Handling ---
        // 🌟 1. Suppression Logic (Highest Priority)
        // Suppress 5xx errors (Backend starting up) and Network errors
        if (
            error.code === 'ERR_NETWORK' ||
            error.message.includes('Network Error') ||
            (error.response && [500, 502, 503, 504].includes(error.response.status))
        ) {
            console.warn(`Backend connection failed (${error.response?.status || 'Network Error'}) - waiting for startup...`)
            return Promise.reject(error)
        }

        // 🌟 2. Auth Error
        if (error.response && error.response.status === 401) {
            const userStore = useUserStore()
            userStore.logout()
            ElMessage.error('登录已过期，请重新登录')
            window.location.href = '/login'
            return Promise.reject(error)
        }

        // 🌟 3. General Server Error (4xx, etc)
        if (error.response) {
            const message = error.response.data?.message || `请求失败 (${error.response.status})`
            ElMessage.error(message)
        } else {
            // Fallback
            ElMessage.error('无法连接到服务器')
        }

        return Promise.reject(error)
    }
)

export default service