// src/router/index.ts

import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw, Router } from 'vue-router'
import { useUserStore } from '@/store/modules/userStore'
import type { MenuItem } from '@/types/api'

// 动态添加路由的辅助函数
const addDynamicRoutes = (routerInstance: Router) => {
    const storedMenu = localStorage.getItem('ice_platform_menu_items')
    if (storedMenu) {
        const dynamicItems = JSON.parse(storedMenu) as MenuItem[]
        dynamicItems.forEach(item => {
            // ！！！关键修改：将 '/ai-lab' 加入排除列表，避免重复添加静态路由！！！
            // 排除：API列表、待办清单、AI实验室
            if (!['/api-list', '/todo-list', '/ai-lab'].includes(item.path) && !routerInstance.hasRoute(item.name)) {
                routerInstance.addRoute('Layout', {
                    path: item.path,
                    name: item.name,
                    component: () => import('@/views/GenericPage.vue'),
                    meta: { name: item.name }
                })
            }
        })
    }
}

const routes: Array<RouteRecordRaw> = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('@/views/Login.vue')
    },
    {
        path: '/bubble',
        name: 'Bubble',
        component: () => import('@/views/BubblePage.vue')
    },
    {
        path: '/',
        name: 'Layout',
        component: () => import('@/views/Layout.vue'),
        redirect: '/todo-list',
        children: [
            {
                path: 'api-list', // 子路由不带前导斜杠
                name: 'API列表',
                component: () => import('@/views/ApiListPage/ApiListPage.vue'),
                meta: { name: 'API列表' }
            },
            {
                path: 'todo-list',
                name: '待办清单',
                component: () => import('@/views/TodoListPage.vue'),
                meta: { name: '待办清单' }
            },
            // ！！！新增：AI 实验室路由！！！
            {
                path: 'ai-lab',
                name: 'AI 实验室',
                component: () => import('@/views/AiLab/AiLabPage.vue'),
                meta: { name: 'AI 实验室' }
            },
            {
                path: 'agent-manager',
                name: '智能体中心',
                component: () => import('@/views/AgentManager/AgentManagerPage.vue'),
                meta: { name: '智能体中心' }
            }
        ]
    },
    {
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        component: () => import('@/views/NotFound.vue')
    }
]

const router = createRouter({
    // ！！！必须使用 Hash 模式以兼容 Electron！！！
    history: createWebHashHistory(),
    routes
})

// 初始化时加载动态路由
addDynamicRoutes(router)

// 全局前置守卫
router.beforeEach(async (to, from, next) => {
    const userStore = useUserStore()
    const token = userStore.token
    const whiteList = ['/login']

    if (token) {
        if (to.path === '/login') {
            next({ path: '/' })
        } else {
            next()
        }
    } else {
        if (whiteList.includes(to.path)) {
            next()
        } else {
            next(`/login?redirect=${to.path}`)
        }
    }
})

export default router