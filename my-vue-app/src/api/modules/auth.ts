// src/api/modules/auth.ts

import request from '@/utils/request'
import type { LoginParams, LoginResponse } from '@/types/api'

/**
 * 【模拟】用户登录API
 * @param data - 登录所需参数 { username, password }
 * @returns Promise<LoginResponse> - 返回包含 token 的 Promise
 */
export function loginApi(data: LoginParams): Promise<LoginResponse> {
    // --- 这是我们的模拟后端逻辑 ---
    return new Promise((resolve, reject) => {
        setTimeout(() => { // 模拟网络延迟
            // 检查用户名和密码是否正确
            if (data.username === 'admin' && data.password === 'admin') {
                // 模拟成功的响应
                console.log('模拟登录成功！')
                resolve({
                    token: 'fake-jwt-token-for-admin-user' // 返回一个假的 token
                })
            } else {
                // 模拟失败的响应
                console.log('模拟登录失败！')
                reject(new Error('用户名或密码错误'))
            }
        }, 500) // 延迟500毫秒
    })
    // --- 模拟逻辑结束 ---

    /*
    // ！！！注意：当您的真实后端准备好后，请删除上面的模拟逻辑，并取消下面的真实请求代码的注释！！！
    return request.post<LoginResponse>('/auth/login', data)
    */
}