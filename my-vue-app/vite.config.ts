// vite.config.ts

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
    base: './',
    plugins: [vue()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src')
        }
    },
    server: {
        port: 3008, // Custom Frontend Port
        proxy: {
            // 规则 1 (高优先级): 系统数据同步接口 -> 转发给本地 Python 后端
            // 后端地址是 http://127.0.0.1:8008/api/v1/...
            '^/api/v1/': {
                target: 'http://127.0.0.1:8008',
                changeOrigin: true,
                // Python 后端路由定义包含了 /api/v1，所以这里不需要 rewrite 去掉前缀
            },

            // 规则 2 (低优先级): 演示用的测试接口 -> 转发给 JSONPlaceholder
            // 例如前端请求 /api/posts，会转发给 https://jsonplaceholder.typicode.com/posts
            '^/api/': {
                target: 'https://jsonplaceholder.typicode.com',
                changeOrigin: true,
                // JSONPlaceholder 不认识 /api 前缀，所以需要去掉
                rewrite: (path) => path.replace(/^\/api\//, '')
            }
        }
    }
})