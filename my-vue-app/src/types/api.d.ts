// src/types/api.d.ts

/**
 * 通用API响应类型
 * 用于包裹我们自己后端返回的数据结构
 */
export interface ApiResponse<T> {
    code: number;
    message: string;
    data: T;
}

/** 通用分页请求参数类型 */
export interface PaginationParams {
    page: number;
    pageSize: number;
    keyword?: string;
}

/** 通用分页响应数据类型 */
export interface PaginatedData<T> {
    total: number;
    list: T[];
}

/** 用户信息类型 */
export interface UserInfo {
    id: string | number;
    username: string;
    avatar?: string;
    roles: string[];
}

/** 登录接口请求参数 */
export interface LoginParams {
    username: string;
    password: string;
}

/** 登录接口响应数据 */
export interface LoginResponse {
    token: string;
}

/**
 * 描述一个动态API卡片配置的接口
 */
export interface ApiCard {
    id: string;
    name: string;
    url: string;
    method: 'GET' | 'POST' | 'PUT' | 'DELETE';
    // URL查询参数
    params?: Array<{ key: string; value: string; enabled: boolean }>;
    // 请求体，以JSON字符串形式存储
    body?: string;
}

/**
 * 描述一个菜单项的接口
 */
export interface MenuItem {
    id: string;
    name: string;
    path: string;
    icon: string;
}

/**
 * 描述一个待办事项或笔记的接口
 */
export interface TodoItem {
    id: string;
    text: string;
    done: boolean;
}